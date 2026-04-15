from curl_cffi import requests
import json
import time
import random
import re


def search_all_job_ids(keyword: str, location: str = "All-Australia") -> list[str]:
    """
    Search Seek and extract all job IDs across all pages.
    Uses curl_cffi with Chrome TLS fingerprint to bypass bot detection.
    """
    session = requests.Session(impersonate="chrome")
    slug = keyword.replace(" ", "-")
    seen = set()
    all_job_ids = []
    page = 1

    while True:
        url = f"https://www.seek.com.au/{slug}-jobs/in-{location}?page={page}"
        response = session.get(url)
        response.raise_for_status()

        # Extract job IDs from href="/job/DIGITS..."
        ids = re.findall(r'href="/job/(\d+)', response.text)
        new_ids = [jid for jid in dict.fromkeys(ids) if jid not in seen]

        if not new_ids:
            break

        seen.update(new_ids)
        all_job_ids.extend(new_ids)
        print(f"Page {page}: found {len(new_ids)} new jobs (total unique: {len(all_job_ids)})")

        # Check if there's a next page link
        if f"page={page + 1}" not in response.text:
            break

        page += 1
        # Random delay between pages to appear human
        time.sleep(random.uniform(2.0, 5.0))

    return all_job_ids


def get_job_details(job_id: str) -> dict:
    """Fetch full job details via Seek's GraphQL API."""
    session = requests.Session(impersonate="chrome")
    url = "https://www.seek.com.au/graphql"

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
                "jobDetailsViewedCorrelationId": "25466d40-875d-4fa2-b0a9-71bc283b8591",
                "sessionId": "25e1306d-a987-494c-9cbc-ec4ea989cd1f",
            },
        },
        "query": """
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
""",
    }

    response = session.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    keyword = "parts interpreter"

    print(f"Searching Seek for '{keyword}' jobs across all pages...\n")
    job_ids = search_all_job_ids(keyword)

    print(f"\nFound {len(job_ids)} total job IDs:")
    for jid in job_ids:
        print(f"  {jid}")

    # Save to file
    with open("job_ids.json", "w") as f:
        json.dump({"keyword": keyword, "count": len(job_ids), "job_ids": job_ids}, f, indent=2)
    print(f"\nSaved to job_ids.json")
