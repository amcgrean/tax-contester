"""
polk_assessor_sales_extract.py
------------------------------
Pulls ALL Polk County Assessor arms-length SF residential sales from 2018 to present.
Loops in 6-month date windows to stay under the 5000-row response cap.

Output:
  ./polk_data/sales/sales_YYYY_HH.ndjson   one file per 6-month window
  ./polk_data/sales/sales_extract.log

Runtime: ~5-10 minutes for full 2018-present backfill (~15 windows).
Resume-safe: already-completed windows are skipped.

Usage:
  pip install requests beautifulsoup4 lxml
  python polk_assessor_sales_extract.py
"""

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date

# ── Config ────────────────────────────────────────────────────────────────────
ENDPOINT = "https://www.assess.co.polk.ia.us/cgi-bin/web/tt/form.cgi"
OUT_DIR  = "./polk_data/sales"
LOG_FILE = "./polk_data/sales_extract.log"

# Date windows: (start, end) pairs, 6-month chunks from 2018 to present
def build_windows():
    windows = []
    year = 2018
    while True:
        # H1: Jan 1 – Jun 30
        w_start = date(year, 1, 1)
        w_end   = date(year, 6, 30)
        windows.append((w_start, w_end))
        if w_start > date.today():
            break
        # H2: Jul 1 – Dec 31
        w_start = date(year, 7, 1)
        w_end   = date(year, 12, 31)
        windows.append((w_start, w_end))
        if w_start > date.today():
            break
        year += 1
        if year > date.today().year + 1:
            break
    # Trim future windows
    today = date.today()
    windows = [(s, e) for s, e in windows if s <= today]
    return windows

# All 27 fields from the game plan
FIELDS = {
    "fields_state":                    "1",
    "fields_result__p_address":        "p_address",
    "fields_address__city":            "city",
    "fields_address__zip":             "zip",
    "fields_xysall__x":                "x",
    "fields_xysall__y":                "y",
    "fields_compute__nbhdpocket":      "nbhdpocket",
    "fields_sresidence__tsfla":        "tsfla",
    "fields_sresidence__year_built":   "year_built",
    "fields_sresidence__bedrooms":     "bedrooms",
    "fields_sresidence__num_bathroom": "num_bathroom",
    "fields_compute__fullgrade":       "fullgrade",
    "fields_sresidence__bldg_style":   "bldg_style",
    "fields_rsale__land_full":         "land_full",
    "fields_rsale__bldg_full":         "bldg_full",
    "fields_rsale__total_full":        "total_full",
    "fields_rsale__sale_date":         "sale_date",
    "fields_rsale__price":             "price",
    "fields_expression__pricepersf":   "pricepersf",
    "fields_rsale__quality1":          "quality1",
    "fields_rsale__quality2":          "quality2",
    "fields_rsale__ratio":             "ratio",
    "fields_rsale__seller":            "seller",
    "fields_rsale__buyer":             "buyer",
    "fields_dptogp__gp":               "gp",
    "fields_slandtotal__sf":           "sf",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def window_key(start, end):
    half = "H1" if start.month == 1 else "H2"
    return f"{start.year}_{half}"

def window_path(start, end):
    return os.path.join(OUT_DIR, f"sales_{window_key(start, end)}.csv")

def parse_html_table(html):
    """Parse the assessor HTML table response into a list of dicts."""
    soup = BeautifulSoup(html, "lxml")
    
    # Find all tables — the data table has many columns
    tables = soup.find_all("table")
    data_table = None
    for t in tables:
        headers = t.find_all("th")
        if len(headers) > 5:
            data_table = t
            break
    
    if not data_table:
        # Try finding by row count
        for t in tables:
            rows = t.find_all("tr")
            if len(rows) > 3:
                data_table = t
                break

    if not data_table:
        return [], []

    rows = data_table.find_all("tr")
    if not rows:
        return [], []

    # Extract headers — check both th and td in first row
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    records = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        values = [c.get_text(strip=True) for c in cells]
        if len(values) != len(headers):
            # Pad or trim to match
            while len(values) < len(headers):
                values.append("")
            values = values[:len(headers)]
        records.append(dict(zip(headers, values)))

    return records, headers

def fetch_window(start, end):
    """POST to assessor for one date window. Returns list of record dicts."""

    # Single field, space-separated range operators — this is how the Perl CGI expects it
    date_range = f">={start.strftime('%m/%d/%Y')} <={end.strftime('%m/%d/%Y')}"

    payload = {
        "tt":                        "rsaleform",
        "submit_form":               "Perform Search",
        "rsale__quality1__0":        "0",         # arms-length filter
        "sresidence__occupancy__SF": "SF",         # single family only
        "rsale__sale_date":          date_range,
        "results_output":            "csv",        # CSV is cleaner than HTML table parsing
        "results_max":               "5000",
    }
    payload.update(FIELDS)

    req_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer":      "https://www.assess.co.polk.ia.us/cgi-bin/web/tt/form.cgi?tt=rsaleform",
        "Accept":       "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    for attempt in range(5):
        try:
            r = requests.post(
                ENDPOINT,
                data=payload,
                timeout=120,
                headers=req_headers,
            )
            r.raise_for_status()

            # Check for DB error (Vanguard migration) — still comes back as HTML even on csv mode
            if "dp is not a base table" in r.text or "Software error" in r.text:
                raise ValueError(f"Server error in response: {r.text[:300]}")

            return r.text  # raw CSV text

        except Exception as e:
            wait = 5 * (attempt + 1)   # 5s, 10s, 15s, 20s, 25s
            log(f"  Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"Window {start}-{end} failed after 5 attempts")

# ── Main extract ──────────────────────────────────────────────────────────────
def extract_window(start, end):
    path = window_path(start, end)
    key  = window_key(start, end)

    # Skip if already done
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = sum(1 for _ in f) - 1  # minus header row
        if existing > 0:
            log(f"  {key}: {existing:,} rows already on disk — skipping")
            return existing

    log(f"  {key}: fetching {start} -> {end} ...")
    csv_text = fetch_window(start, end)

    # Check if response looks like CSV or an error page
    if not csv_text or csv_text.strip().startswith("<"):
        log(f"  {key}: got HTML instead of CSV — saving as probe_{key}.html for inspection")
        with open(os.path.join(OUT_DIR, f"probe_{key}.html"), "w", encoding="utf-8") as f:
            f.write(csv_text or "")
        return 0

    # Count data rows (subtract 1 for header)
    lines = [l for l in csv_text.splitlines() if l.strip()]
    row_count = max(0, len(lines) - 1)

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    log(f"  {key}: {row_count:,} records saved -> {path}")

    if row_count >= 4900:
        log(f"  WARNING: {key} returned {row_count} rows — near/at 5000 cap. Consider splitting this window.")

    time.sleep(2.0)  # polite pause between windows
    return row_count

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    start_time = datetime.now()
    log(f"Polk Assessor Sales extract started — {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Output directory: {os.path.abspath(OUT_DIR)}")

    windows = build_windows()
    log(f"Windows to pull: {len(windows)} ({windows[0][0]} → {windows[-1][1]})")

    grand_total = 0
    for w_start, w_end in windows:
        n = extract_window(w_start, w_end)
        grand_total += n

    elapsed = (datetime.now() - start_time).total_seconds()
    log(f"\n{'='*50}")
    log(f"COMPLETE in {elapsed:.0f}s")
    log(f"Total records across all windows: {grand_total:,}")
    log(f"Files in: {os.path.abspath(OUT_DIR)}")
    log(f"\nNext step: run polk_atlas_extract.py if not done, then load both into Postgres.")

if __name__ == "__main__":
    main()