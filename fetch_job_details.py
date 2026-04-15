from curl_cffi import requests
import json
import time
import random
import uuid
import os
import math

GRAPHQL_URL = "https://www.seek.com.au/graphql"
INPUT_FILE = "job_ids.json"
OUTPUT_DIR = "job_details"
JOBS_PER_FILE = 30

QUERY = """
query jobDetails($id: ID!, $tracking: JobDetailsTrackingInput, $locale: Locale!, $timezone: Timezone!, $zone: Zone!) {
  jobDetails(id: $id, tracking: $tracking) {
    job {
      id
      title
      phoneNumber
      isExpired
      expiresAt {
        dateTimeUtc
        __typename
      }
      isLinkOut
      contactMatches {
        type
        value
        __typename
      }
      isVerified
      abstract
      content(platform: WEB)
      status
      advertiser {
        id
        name(locale: $locale)
        isVerified
        registrationDate {
          dateTimeUtc
          __typename
        }
        __typename
      }
      location {
        label(locale: $locale, type: LONG)
        __typename
      }
      salary {
        currencyLabel(zone: $zone)
        label
        __typename
      }
      listedAt {
        label(locale: $locale, timezone: $timezone, context: JOB_POSTED, length: SHORT)
        dateTimeUtc
        __typename
      }
      __typename
    }
    __typename
  }
}
"""


def trim_job(job: dict) -> dict:
    """Keep only the fields we care about."""
    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "phoneNumber": job.get("phoneNumber"),
        "content": job.get("content"),
        "advertiser": {
            "id": (job.get("advertiser") or {}).get("id"),
            "name": (job.get("advertiser") or {}).get("name"),
        },
        "location": (job.get("location") or {}).get("label"),
    }


def fetch_job(session: requests.Session, job_id: str, session_id: str) -> dict | None:
    """Fetch a single job's details. Returns the trimmed job dict or None on failure."""
    headers = {
        "content-type": "application/json",
        "origin": "https://www.seek.com.au",
        "referer": f"https://www.seek.com.au/job/{job_id}",
        "seek-request-brand": "seek",
        "seek-request-country": "AU",
        "x-seek-site": "chalice",
    }

    payload = {
        "operationName": "jobDetails",
        "variables": {
            "id": job_id,
            "locale": "en-AU",
            "timezone": "Australia/Brisbane",
            "zone": "anz-2",
            "tracking": {
                "channel": "WEB",
                "jobDetailsViewedCorrelationId": str(uuid.uuid4()),
                "sessionId": session_id,
            },
        },
        "query": QUERY,
    }

    response = session.post(GRAPHQL_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    job = data.get("data", {}).get("jobDetails", {}).get("job")
    if job:
        return trim_job(job)
    return None


def batch_filename(batch_num: int) -> str:
    return os.path.join(OUTPUT_DIR, f"jobs_{batch_num:03d}.json")


def load_existing_results() -> dict[str, dict]:
    """Load all previously fetched results from batch files for resume support."""
    existing = {}
    if not os.path.isdir(OUTPUT_DIR):
        return existing
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for job in data.get("jobs", []):
            existing[job["id"]] = job
    return existing


def save_batch(jobs: list[dict], batch_num: int):
    path = batch_filename(batch_num)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"batch": batch_num, "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    job_ids = data["job_ids"]
    total = len(job_ids)
    print(f"Loaded {total} job IDs from {INPUT_FILE}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Resume: skip jobs already fetched
    existing = load_existing_results()
    if existing:
        print(f"Resuming -- {len(existing)} jobs already fetched")

    all_jobs = list(existing.values())
    fetched_ids = set(existing.keys())
    remaining = [jid for jid in job_ids if jid not in fetched_ids]
    failures = []

    # One session for the whole run (like a real browser tab)
    session = requests.Session(impersonate="chrome")
    session_id = str(uuid.uuid4())

    print(f"Fetching {len(remaining)} remaining jobs...\n")

    for i, job_id in enumerate(remaining, 1):
        try:
            job = fetch_job(session, job_id, session_id)
            if job:
                all_jobs.append(job)
                loc = job.get("location", "?")
                print(f"[{len(all_jobs)}/{total}] {job_id} -- {job.get('title', '?')} ({loc})")
            else:
                failures.append(job_id)
                print(f"[{len(all_jobs)}/{total}] {job_id} -- no data returned")
        except Exception as e:
            failures.append(job_id)
            print(f"[{len(all_jobs)}/{total}] {job_id} -- ERROR: {e}")

        # Save progress every 30 jobs (one batch)
        if len(all_jobs) % JOBS_PER_FILE == 0:
            batch_num = len(all_jobs) // JOBS_PER_FILE
            batch = all_jobs[(batch_num - 1) * JOBS_PER_FILE : batch_num * JOBS_PER_FILE]
            save_batch(batch, batch_num)

        # Randomized delay
        if i < len(remaining):
            if random.random() < 0.03:
                pause = random.uniform(8.0, 15.0)
            else:
                pause = random.uniform(1.0, 3.0)
            time.sleep(pause)

    # Save any remaining jobs in a final partial batch
    full_batches = len(all_jobs) // JOBS_PER_FILE
    leftover = all_jobs[full_batches * JOBS_PER_FILE:]
    if leftover:
        save_batch(leftover, full_batches + 1)

    # Re-save all complete batches (in case resume merged old + new)
    for b in range(1, full_batches + 1):
        batch = all_jobs[(b - 1) * JOBS_PER_FILE : b * JOBS_PER_FILE]
        save_batch(batch, b)

    total_batches = math.ceil(len(all_jobs) / JOBS_PER_FILE)
    print(f"\nDone. {len(all_jobs)} jobs saved across {total_batches} files in {OUTPUT_DIR}/")
    if failures:
        print(f"{len(failures)} failures: {failures}")


if __name__ == "__main__":
    main()
