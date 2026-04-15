import subprocess
import sys
import os
import json

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BANNER = f"""
{CYAN}{BOLD}  ____            _       ____
 / ___|  ___  ___| | __  / ___|  ___ _ __ __ _ _ __   ___ _ __
 \\___ \\ / _ \\/ _ \\ |/ /  \\___ \\ / __| '__/ _` | '_ \\ / _ \\ '__|
  ___) |  __/  __/   <    ___) | (__| | | (_| | |_) |  __/ |
 |____/ \\___|\\___|_|\\_\\  |____/ \\___|_|  \\__,_| .__/ \\___|_|
                                               |_|              {RESET}
{DIM}  Job scraper & detail fetcher for seek.com.au{RESET}
"""


def separator():
    print(f"{DIM}{'-' * 52}{RESET}")


def status(label, value):
    print(f"  {DIM}{label}:{RESET} {BOLD}{value}{RESET}")


def show_stats():
    """Show current state of scraped data."""
    separator()
    if os.path.exists("job_ids.json"):
        with open("job_ids.json", encoding="utf-8") as f:
            data = json.load(f)
        status("Job IDs scraped", f"{data['count']} ({data.get('keyword', '?')})")
    else:
        status("Job IDs scraped", f"{RED}none{RESET}")

    details_dir = "job_details"
    if os.path.isdir(details_dir):
        total_jobs = 0
        file_count = 0
        for fname in os.listdir(details_dir):
            if fname.endswith(".json"):
                file_count += 1
                path = os.path.join(details_dir, fname)
                with open(path, encoding="utf-8") as f:
                    total_jobs += json.load(f).get("count", 0)
        status("Job details fetched", f"{total_jobs} across {file_count} files")
    else:
        status("Job details fetched", f"{RED}none{RESET}")
    separator()


def menu():
    print(f"""
  {BOLD}[1]{RESET} {GREEN}Scrape job IDs{RESET}        {DIM}search all pages, collect IDs{RESET}
  {BOLD}[2]{RESET} {GREEN}Fetch job details{RESET}     {DIM}get full info for each job ID{RESET}
  {BOLD}[3]{RESET} {GREEN}Run both{RESET}              {DIM}scrape IDs then fetch details{RESET}
  {BOLD}[q]{RESET} {DIM}Quit{RESET}
""")


def run_scrape():
    print(f"\n{CYAN}{BOLD}>>> Scraping job IDs...{RESET}\n")
    result = subprocess.run([sys.executable, "scrape_job_ids.py"])
    if result.returncode != 0:
        print(f"\n{RED}Scrape failed.{RESET}")
        return False
    print(f"\n{GREEN}Scrape complete.{RESET}")
    return True


def run_fetch():
    if not os.path.exists("job_ids.json"):
        print(f"\n{RED}No job_ids.json found. Run scrape first.{RESET}")
        return False
    print(f"\n{CYAN}{BOLD}>>> Fetching job details...{RESET}\n")
    result = subprocess.run([sys.executable, "fetch_job_details.py"])
    if result.returncode != 0:
        print(f"\n{RED}Fetch failed.{RESET}")
        return False
    print(f"\n{GREEN}Fetch complete.{RESET}")
    return True


def main():
    os.system("")  # enable ANSI on Windows
    print(BANNER)
    show_stats()
    menu()

    choice = input(f"  {YELLOW}>{RESET} ").strip().lower()

    if choice == "1":
        run_scrape()
    elif choice == "2":
        run_fetch()
    elif choice == "3":
        if run_scrape():
            run_fetch()
    elif choice in ("q", "quit", "exit"):
        print(f"\n  {DIM}Bye.{RESET}\n")
    else:
        print(f"\n  {RED}Invalid choice.{RESET}")


if __name__ == "__main__":
    main()
