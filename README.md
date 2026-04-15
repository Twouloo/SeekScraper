# Seek Scraper
Scrape jobs from Seek.com

## Requirements

- Python 3.10+
- A Proxy / VPN just in-case to not get banned

## Setup

```bash
git clone <repo-url>
cd Webscrape
pip install -r requirements.txt
```

## Usage

Run the interactive menu:

```bash
python run_scrape.py
```

Options:

1. **Scrape job IDs** — searches Seek for a keyword and saves all job IDs to `job_ids.json`
2. **Fetch job details** — reads `job_ids.json` and fetches full details for each job, saved in batches to `job_details/`
3. **Run both** — scrape IDs then fetch details in one go

### Running scripts individually

```bash
python scrape_job_ids.py      # scrape job IDs
python fetch_job_details.py   # fetch details (requires job_ids.json)
```

## Output

- `job_ids.json` — list of job IDs from the search
- `job_details/` — batched JSON files with full job details (title, location, salary, advertiser, content, etc.)

Fetching supports **resume** — if interrupted, re-running will skip already fetched jobs.
