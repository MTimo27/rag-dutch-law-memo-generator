import os
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

SUBJECT_URI = "http://psi.rechtspraak.nl/rechtsgebied#bestuursrecht_socialezekerheidsrecht"
# Years and quarters to sample
YEARS = list(range(2020, 2025))    
QUARTERS = [
    ("01-01", "03-31"),  
    ("04-01", "06-30"),  
    ("07-01", "09-30"),  
    ("10-01", "12-31"), 
]
# Total cases to download across all years
DESIRED_COUNT = 200
# How many ECLIs per API page
PAGE_SIZE = 100
# Pause between each case download (seconds)
PAUSE_DOWNLOAD = 0.5
SAVE_DIR = "../_data/rechtspraak-xml"
os.makedirs(SAVE_DIR, exist_ok=True)

BASE_SEARCH_URL = "https://data.rechtspraak.nl/uitspraken/zoeken"
BASE_CONTENT_URL = "https://data.rechtspraak.nl/uitspraken/content"

# Known ECLIs whose XML→JSON conversion fails; we will not count these
SKIP_ECLIS = {
    "ECLI:NL:RBAMS:2022:3718",
    "ECLI:NL:RBNHO:2020:7643",
}

# Helpers
def build_search_url(subject, date_start, date_end, page_size, offset):
    params = [
        ("type", "uitspraak"),
        ("return", "DOC"),
        ("date", date_start),
        ("date", date_end),
        ("subject", subject),
        ("max", str(page_size)),
        ("from", str(offset)),
    ]
    return BASE_SEARCH_URL + "?" + urlencode(params)

def parse_eclis(atom_xml):
    root = ET.fromstring(atom_xml)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    return [e.find("atom:id", ns).text for e in root.findall("atom:entry", ns)]

def download_case(ecli):
    url = f"{BASE_CONTENT_URL}?id={ecli}"
    r = requests.get(url)
    if r.status_code == 200:
        fn = ecli.replace(":", "_") + ".xml"
        path = os.path.join(SAVE_DIR, fn)
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Saved {ecli}")
        return True
    else:
        print(f"Skipped {ecli} ({r.status_code})")
        return False

#Fetch up to target_count cases within a specific date window.
def fetch_range(date_start, date_end, target_count):
    saved = 0
    offset = 0
    print(f"\n-- Range {date_start} to {date_end}: target {target_count} cases --")
    while saved < target_count:
        url = build_search_url(SUBJECT_URI, date_start, date_end, PAGE_SIZE, offset)
        print(f"Fetching ECLIs (offset={offset}): {url}")
        resp = requests.get(url)
        resp.raise_for_status()
        eclis = parse_eclis(resp.text)
        if not eclis:
            print("No more ECLIs in this window.")
            break
        for ecli in eclis:
            if saved >= target_count:
                break
            if ecli in SKIP_ECLIS:
                print(f"Skipping {ecli} (in skip‐list)")
                continue
            if download_case(ecli):
                saved += 1
            time.sleep(PAUSE_DOWNLOAD)
        offset += PAGE_SIZE
    print(f"Completed window {date_start}–{date_end}: {saved}/{target_count} saved.")


def fetch_yearly(year, yearly_target):
    base, rem = divmod(yearly_target, len(QUARTERS))
    counts = [base + (1 if i < rem else 0) for i in range(len(QUARTERS))]
    print(f"\nYear {year}: total target {yearly_target} → per-quarter {counts}")
    for (start_m, end_m), q_count in zip(QUARTERS, counts):
        fetch_range(f"{year}-{start_m}", f"{year}-{end_m}", q_count)

def main():
    base, rem = divmod(DESIRED_COUNT, len(YEARS))
    yearly_counts = [ base + (1 if i < rem else 0) for i in range(len(YEARS)) ]

    for year, y_count in zip(YEARS, yearly_counts):
        fetch_yearly(year, y_count)

    print("\nAll done.")

if __name__ == "__main__":
    main()
