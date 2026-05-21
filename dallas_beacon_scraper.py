"""
dallas_beacon_scraper.py  v1.1
------------------------------
Scrapes Dallas County Iowa property + assessment + sales data from Beacon.
Stores raw HTML snapshots and normalized records into local Postgres.

Designed to run on a residential IP (laptop or Pi 5).
Cloudflare passes on residential IPs — will NOT work from cloud/VPS.

Usage:
    python3 dallas_beacon_scraper.py --mode parcel --parcel-id 1613300008 --dry-run --debug
    python3 dallas_beacon_scraper.py --mode parcel-number --parcel-number 12-21-406-018 --dry-run
    python3 dallas_beacon_scraper.py --mode address --address "1440 NW Alderleaf Dr" --dry-run
    python3 dallas_beacon_scraper.py --mode sales --days 90

Requirements:
    pip install playwright psycopg2-binary python-dotenv
    python3 -m playwright install chromium

Environment (.env):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
    SNAPSHOT_DIR          (default: ./snapshots/dallas)
    BEACON_SESSION_FILE   (default: ./beacon_session.json)
"""

import os, re, json, time, logging, argparse, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import csv
import psycopg2
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("dallas_beacon")

# ── Config ────────────────────────────────────────────────────────────────────

BEACON_SEARCH_URL = (
    "https://beacon.schneidercorp.com/Application.aspx"
    "?AppID=909&LayerID=17429&PageTypeID=2&PageID=7823"
)
BEACON_PARCEL_URL = (
    "https://beacon.schneidercorp.com/Application.aspx"
    "?AppID=909&LayerID=17429&PageTypeID=4&PageID=7825&KeyValue={key_value}"
)

SESSION_FILE   = os.getenv("BEACON_SESSION_FILE", "./beacon_session.json")
SNAPSHOT_DIR   = Path(os.getenv("SNAPSHOT_DIR", "./snapshots/dallas"))
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGE_DELAY_SEC   = 1.5
SEARCH_DELAY_SEC = 2.0
MAX_RETRIES      = 3
REQUEST_TIMEOUT  = 30_000
PARSER_VERSION   = "v1.1.0"
CSV_OUTPUT_DIR   = Path(os.getenv("CSV_OUTPUT_DIR", "./csv_output"))

# ── CSV output (fallback when Postgres not available) ─────────────────────────

def write_csv(parsed: dict):
    """
    Append parsed parcel data to CSV files in CSV_OUTPUT_DIR.
    One file each for properties, assessments, sales.
    Safe to call repeatedly — appends with header only on first write.
    """
    CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prop = parsed.get("property", {})
    source_url = parsed.get("source_url", "")

    # Properties
    prop_file = CSV_OUTPUT_DIR / "properties.csv"
    prop_fields = [
        "county_parcel_id", "alternate_parcel_id", "address_raw", "city",
        "year_built", "living_area_sqft", "basement_sqft", "lot_sf", "lot_acres",
        "bedrooms", "bathrooms", "stories", "bldg_style", "quality_grade",
        "condition_rating", "property_class", "tax_district", "school_district",
        "owner_name", "source_url"
    ]
    write_header = not prop_file.exists()
    with open(prop_file, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["county"] + prop_fields + ["parser_version", "extracted_at"])
        if write_header:
            w.writeheader()
        row = {"county": "dallas", "parser_version": PARSER_VERSION,
               "extracted_at": datetime.now().isoformat(), "source_url": source_url}
        row.update({k: prop.get(k) for k in prop_fields})
        w.writerow(row)

    # Assessments
    asmt_file = CSV_OUTPUT_DIR / "assessments.csv"
    asmt_fields = ["tax_year", "assessed_total", "assessed_land", "assessed_improvements",
                   "assessed_dwelling", "net_assessed_value", "taxable_total",
                   "gross_taxes_due", "net_taxes_due", "classification"]
    write_header = not asmt_file.exists()
    with open(asmt_file, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["county_parcel_id"] + asmt_fields + ["source_url", "extracted_at"])
        if write_header:
            w.writeheader()
        for asmt in parsed.get("assessments", []):
            row = {"county_parcel_id": prop.get("county_parcel_id"),
                   "source_url": source_url,
                   "extracted_at": datetime.now().isoformat()}
            row.update({k: asmt.get(k) for k in asmt_fields})
            w.writerow(row)

    # Sales
    sale_file = CSV_OUTPUT_DIR / "sales.csv"
    sale_fields = ["sale_date", "sale_price", "price_per_sqft", "deed_type",
                   "sale_condition", "arms_length_flag", "multi_parcel",
                   "recording_number", "buyer", "seller"]
    write_header = not sale_file.exists()
    with open(sale_file, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["county_parcel_id"] + sale_fields + ["source_url", "extracted_at"])
        if write_header:
            w.writeheader()
        for sale in parsed.get("sales", []):
            row = {"county_parcel_id": prop.get("county_parcel_id"),
                   "source_url": source_url,
                   "extracted_at": datetime.now().isoformat()}
            row.update({k: sale.get(k) for k in sale_fields})
            w.writerow(row)

    log.info("CSV written: %s", prop.get("county_parcel_id"))


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "iowa_propertytax"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
    )

def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id                  SERIAL PRIMARY KEY,
            county              TEXT NOT NULL DEFAULT 'dallas',
            county_parcel_id    TEXT NOT NULL,
            alternate_parcel_id TEXT,
            address_raw         TEXT,
            city                TEXT,
            state               TEXT DEFAULT 'IA',
            zip                 TEXT,
            latitude            DOUBLE PRECISION,
            longitude           DOUBLE PRECISION,
            neighborhood_code   TEXT,
            year_built          INTEGER,
            living_area_sqft    INTEGER,
            basement_sqft       INTEGER,
            lot_sf              DOUBLE PRECISION,
            lot_acres           DOUBLE PRECISION,
            bedrooms            INTEGER,
            bathrooms           NUMERIC(4,1),
            stories             TEXT,
            quality_grade       TEXT,
            condition_rating    TEXT,
            bldg_style          TEXT,
            property_class      TEXT,
            tax_district        TEXT,
            school_district     TEXT,
            owner_name          TEXT,
            homestead_flag      BOOLEAN,
            source_system       TEXT DEFAULT 'dallas_beacon',
            parser_version      TEXT,
            source_url          TEXT,
            last_seen_at        TIMESTAMPTZ DEFAULT NOW(),
            created_at          TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(county, county_parcel_id)
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id                      SERIAL PRIMARY KEY,
            property_id             INTEGER REFERENCES properties(id),
            tax_year                INTEGER,
            assessed_total          NUMERIC(14,2),
            assessed_land           NUMERIC(14,2),
            assessed_improvements   NUMERIC(14,2),
            assessed_dwelling       NUMERIC(14,2),
            net_assessed_value      NUMERIC(14,2),
            taxable_total           NUMERIC(14,2),
            gross_taxes_due         NUMERIC(14,2),
            net_taxes_due           NUMERIC(14,2),
            classification          TEXT,
            source_system           TEXT DEFAULT 'dallas_beacon',
            parser_version          TEXT,
            source_url              TEXT,
            extracted_at            TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(property_id, tax_year)
        );
        CREATE TABLE IF NOT EXISTS sales (
            id                  SERIAL PRIMARY KEY,
            property_id         INTEGER REFERENCES properties(id),
            sale_date           DATE,
            sale_price          NUMERIC(14,2),
            price_per_sqft      NUMERIC(10,2),
            deed_type           TEXT,
            sale_condition      TEXT,
            arms_length_flag    BOOLEAN,
            multi_parcel        BOOLEAN DEFAULT FALSE,
            recording_number    TEXT,
            buyer               TEXT,
            seller              TEXT,
            source_system       TEXT DEFAULT 'dallas_beacon',
            parser_version      TEXT,
            source_url          TEXT,
            extracted_at        TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(property_id, sale_date, sale_price)
        );
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id              SERIAL PRIMARY KEY,
            county          TEXT DEFAULT 'dallas',
            source_name     TEXT,
            started_at      TIMESTAMPTZ,
            completed_at    TIMESTAMPTZ,
            status          TEXT,
            rows_inserted   INTEGER DEFAULT 0,
            rows_updated    INTEGER DEFAULT 0,
            errors_json     JSONB,
            notes           TEXT
        );
        CREATE TABLE IF NOT EXISTS raw_source_snapshots (
            id              SERIAL PRIMARY KEY,
            county          TEXT DEFAULT 'dallas',
            source_name     TEXT,
            parcel_id       TEXT,
            captured_at     TIMESTAMPTZ DEFAULT NOW(),
            file_path       TEXT,
            payload_hash    TEXT
        );
        """)
        conn.commit()
    log.info("Schema verified.")

# ── Session / Browser ────────────────────────────────────────────────────────
#
# Uses a persistent Chromium profile directory so Cloudflare clearance cookies
# survive across runs — exactly like a real browser would.
#
# First run:  launches VISIBLE so you can watch CF auto-resolve on residential IP.
# Later runs: headless, reuses stored profile (cookies + fingerprint).

PROFILE_DIR = Path(os.getenv("BEACON_PROFILE_DIR", "./beacon_profile"))

def _profile_is_warm() -> bool:
    return (PROFILE_DIR / "Default" / "Preferences").exists()

def load_session(context):
    pass  # persistent context handles its own cookies via the profile dir

def save_session(context):
    pass  # auto-saved to profile dir on close

def make_browser_context(playwright):
    """
    Always launches a VISIBLE Chromium window with a persistent profile.

    Cloudflare's managed challenge requires real JS execution — headless fails
    intermittently even on residential IPs because the CF cookie expires and
    the challenge re-fires. Visible mode passes every time.

    The window will flash open and close quickly during normal runs.
    If you want it minimized, just minimize it — the script keeps running.
    Profile is saved to ./beacon_profile/ so cookies persist between runs.
    """
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Launching browser (visible) with profile: %s", PROFILE_DIR)

    context = playwright.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        timezone_id="America/Chicago",
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return None, context

# ── Page helpers ──────────────────────────────────────────────────────────────

def wait_for_beacon(page, timeout_sec=45):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        title = page.title()
        if title and "moment" not in title.lower() and len(page.content()) > 5000:
            return True
        log.debug("Waiting for Cloudflare... '%s'", title)
        time.sleep(2)
    raise TimeoutError(f"Beacon did not load in {timeout_sec}s — are you on a residential IP?")

def handle_tc_modal(page):
    """Accept T&C via JS click (avoids modal interception on element clicks)."""
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('.modal button, .modal .btn');
            for (const btn of btns) {
                if (btn.textContent.trim().toLowerCase() === 'agree') {
                    btn.click(); break;
                }
            }
        """)
        time.sleep(1.5)
    except Exception:
        pass

def save_snapshot(html, parcel_id, source, conn=None):
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id  = re.sub(r"[^a-zA-Z0-9_-]", "_", str(parcel_id))
    filepath = SNAPSHOT_DIR / source / f"{date_str}_{safe_id}.html"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(html, encoding="utf-8")
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO raw_source_snapshots (county,source_name,parcel_id,file_path,payload_hash) "
                "VALUES ('dallas',%s,%s,%s,%s)",
                (source, str(parcel_id), str(filepath),
                 hashlib.md5(html.encode()).hexdigest()),
            )
        conn.commit()
    return str(filepath)

# ── Parsers ───────────────────────────────────────────────────────────────────

def pmoney(s) -> Optional[float]:
    if not s: return None
    c = re.sub(r"[^\d.]", "", str(s).replace(",", ""))
    try: return float(c) if c else None
    except ValueError: return None

def pint(s) -> Optional[int]:
    if not s: return None
    c = re.sub(r"[^\d]", "", str(s))
    try: return int(c) if c else None
    except ValueError: return None

def pdate(s) -> Optional[str]:
    if not s: return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y"):
        try: return datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError: continue
    return None

# ── Core parser ───────────────────────────────────────────────────────────────

def parse_parcel_page(page, key_value: str) -> dict:
    """
    Parse a Beacon Dallas County parcel report page.

    DOM structure confirmed by live inspection (April 2026):

    Summary table (first <table> on page):
        Rows are [label, value] pairs:
        Parcel ID, Alternate ID, Property Address (addr + newline + city),
        Sec/Twp/Rng, Brief Tax Description, Deed Book/Page,
        Gross Acres, Net Acres, Class, District, School District

    Section headers: <div class="module-header"> labels each block:
        Summary, Owner, Land, Residential/Commercial Buildings,
        Valuation, Sales, Permits, Tax History

    Residential buildings table headers (varies):
        Year Built, Gross Area / Sq Ft, Basement Area,
        Bedrooms, Bathrooms, Grade, Style, Condition, Stories

    Valuation table (multi-year):
        Header row: [blank, blank, 2026, 2025, 2024, 2023, 2022]
        Data rows:  [+/-/=, Label, $val, $val, ...]
        Labels: Assessed Land Value, Assessed Building Value,
                Assessed Dwelling Value, Gross/Net Assessed Value,
                Taxable Land/Building/Dwelling/Gross/Net Value,
                Gross/Net Taxes Due

    Sales table headers:
        Date, Seller, Buyer, Recording, Sale Condition - NUTC,
        Type, Multi Parcel, Amount
    """
    data = {
        "key_value":   key_value,
        "source_url":  page.url,
        "property":    {},
        "assessments": [],
        "sales":       [],
        "errors":      [],
    }
    prop = data["property"]

    try:
        all_tables = page.query_selector_all("table")

        # ── Summary (first table) ─────────────────────────────────────────────
        if all_tables:
            for row in all_tables[0].query_selector_all("tr"):
                cells = row.query_selector_all("td")
                if len(cells) == 2:
                    label = cells[0].inner_text().strip().lower().replace("\xa0", " ").rstrip(":")
                    value = cells[1].inner_text().strip().replace("\xa0", " ")
                    if label and value:
                        if label == "parcel id":
                            prop["county_parcel_id"] = value
                        elif label in ("alternate id", "alternate parcel id"):
                            prop["alternate_parcel_id"] = value
                        elif label == "property address":
                            parts = value.split("\n")
                            prop["address_raw"] = parts[0].strip()
                            prop["city"] = parts[1].strip() if len(parts) > 1 else None
                        elif label == "gross acres":
                            prop["lot_acres"] = pmoney(value)
                        elif label == "class":
                            prop["property_class"] = value.split("(")[0].strip()
                        elif label == "district":
                            prop["tax_district"] = value
                        elif label == "school district":
                            prop["school_district"] = value

        if not prop.get("county_parcel_id"):
            prop["county_parcel_id"] = key_value

        # ── Owner (second table-ish) ──────────────────────────────────────────
        for t in all_tables:
            ths = [th.inner_text().strip().lower() for th in t.query_selector_all("th")]
            if "deed holder" in ths:
                rows = t.query_selector_all("tr")
                for row in rows[1:]:
                    cells = row.query_selector_all("td")
                    if cells:
                        prop["owner_name"] = cells[0].inner_text().strip().split("\n")[0]
                        break
                break

        # ── Lot SF from Land section ──────────────────────────────────────────
        for t in all_tables:
            text = t.inner_text()
            if "lot area" in text.lower() or ("acres" in text.lower() and " sf" in text.lower()):
                sf_m = re.search(r"([\d,]+)\s*SF", text)
                if sf_m:
                    prop["lot_sf"] = pmoney(sf_m.group(1))
                if not prop.get("lot_acres"):
                    ac_m = re.search(r"([\d.]+)\s*[Aa]cres", text)
                    if ac_m:
                        prop["lot_acres"] = float(ac_m.group(1))
                break

        # ── Residential building characteristics ──────────────────────────────
        # Confirmed structure (Table 9): 2-column label/value rows, NO header row.
        # First row is ['Residential Dwelling', ''] — identify by that or by
        # containing 'year built' and 'total gross living area' in the table text.
        # Residential dwelling table is always a 2-col label/value table.
        # The debug script confirmed it is Table 9 (index 8 zero-based) on Dallas County pages.
        # Strategy: scan ALL tables for one that has 'year built' AND
        # 'total gross living area' as actual row label text after full normalization.
        # Use page.evaluate to extract directly to avoid Playwright td/th confusion.
        # Extract building characteristics using pure Playwright Python.
        # Get innerText of every td via JS element property (avoids encoding issues).
        lv = {}
        # Extract building data by getting full table innerText via JS,
        # then parsing label/value pairs with Python. Avoids all cell-iteration
        # encoding issues — innerText in the browser resolves   natively.
        lv = {}
        for t_idx, t in enumerate(all_tables):
            table_text = page.evaluate("el => el.innerText", t)
            if "Year Built" not in table_text or "Total Gross Living Area" not in table_text:
                continue
            log.debug("Building table candidate at index %d", t_idx)
            # Parse line by line — each row renders as "Label\tValue" or "Label\nValue"
            for line in table_text.replace("\r", "").split("\n"):
                # Tab-separated label/value
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                if len(parts) == 2:
                    label = " ".join(parts[0].split()).lower().rstrip(":")
                    value = parts[1].strip()
                    if label:
                        lv[label] = value
            log.debug("Building lv keys: %s", list(lv.keys())[:10])
            if "year built" in lv or "total gross living area" in lv:
                break
            lv = {}  # wrong table, keep looking

        if lv:

            prop["bldg_style"]    = lv.get("style") or lv.get("architectural style")
            prop["year_built"]    = pint(lv.get("year built"))

            # "Total Gross Living Area" → "3,613 SF"
            sqft_raw = lv.get("total gross living area", "")
            prop["living_area_sqft"] = pint(re.sub(r"[^\d]", "", sqft_raw.split("SF")[0])) if sqft_raw else None

            # Basement: "Basement Area" → "1,903"
            prop["basement_sqft"] = pint(lv.get("basement area")) or None

            # Bedrooms: "Number of Bedrooms" → "4 above; 0 below"
            bed_raw = lv.get("number of bedrooms", lv.get("bedrooms", ""))
            bed_match = re.match(r"(\d+)", bed_raw)
            prop["bedrooms"] = int(bed_match.group(1)) if bed_match else None

            # Bathrooms: "Plumbing" → "1 Full Bathroom; 1 Shower Stall Bathroom; 1 Half Bath"
            plumb_raw = lv.get("plumbing", "")
            full  = len(re.findall(r"full bathroom", plumb_raw, re.I))
            half  = len(re.findall(r"half bath", plumb_raw, re.I))
            shower = len(re.findall(r"shower stall", plumb_raw, re.I))
            if full or half or shower:
                prop["bathrooms"] = full + shower + (0.5 * half)

            prop["condition_rating"] = lv.get("condition") or lv.get("overall condition")
            prop["stories"]          = lv.get("architectural style") or lv.get("stories")

        # ── Valuation table (multi-year, confirmed structure) ─────────────────
        # Header row contains year numbers as column headers.
        # Identified by presence of "Assessed Land Value" in a row label.
        for t in all_tables:
            full_text = t.inner_text().lower()
            if "assessed land value" not in full_text:
                continue

            rows = t.query_selector_all("tr")

            # Find year columns from header row
            year_cols = {}
            for row in rows[:3]:  # year row is near the top
                cells = row.query_selector_all("td, th")
                for i, cell in enumerate(cells):
                    yr = pint(cell.inner_text().strip())
                    if yr and 2015 < yr <= datetime.now().year + 1:
                        year_cols[yr] = i
                if year_cols:
                    break

            if not year_cols:
                continue

            log.debug("Valuation years: %s", sorted(year_cols.keys()))

            # Parse all label rows.
            # Confirmed structure from live page inspection:
            #   cells[0] = operator (+/-/=) or blank
            #   cells[1] = human-readable label ("Assessed Land Value")
            #   cells[2..n] = values per year column
            row_map = {}  # label_lower → [all cell texts including operator]
            for row in rows:
                cells = row.query_selector_all("td, th")
                if len(cells) < 3:
                    continue
                # Label is always cells[1] — never cells[0] (that's the operator)
                label = cells[1].inner_text().strip().lower().replace("\xa0", " ")
                if label:
                    row_map[label] = [c.inner_text().strip().replace("\xa0", " ")
                                      for c in cells]

            log.debug("Valuation row labels: %s", list(row_map.keys()))

            for yr, col_idx in sorted(year_cols.items(), reverse=True):
                asmt = {"tax_year": yr}
                for label, cell_texts in row_map.items():
                    if col_idx >= len(cell_texts):
                        continue
                    raw = cell_texts[col_idx]
                    val = pmoney(raw)
                    if "assessed land value"       in label: asmt["assessed_land"]        = val
                    elif "assessed building value" in label: asmt["assessed_improvements"] = val
                    elif "assessed dwelling value" in label: asmt["assessed_dwelling"]     = val
                    elif "net assessed value"      in label: asmt["net_assessed_value"]    = val
                    elif "gross assessed value"    in label:
                        if "assessed_total" not in asmt:    asmt["assessed_total"]         = val
                    elif "gross taxable value"     in label: asmt["taxable_total"]         = val
                    elif "gross taxes due"         in label: asmt["gross_taxes_due"]       = val
                    elif "net taxes due"           in label: asmt["net_taxes_due"]         = val
                    elif "classification"          in label: asmt["classification"]        = raw

                if any(asmt.get(k) for k in ["assessed_land", "assessed_improvements", "assessed_total"]):
                    data["assessments"].append(asmt)
            break

        # ── Sales table (confirmed headers) ──────────────────────────────────
        # Date | Seller | Buyer | Recording | Sale Condition - NUTC | Type | Multi Parcel | Amount
        NON_ARM = {"no consideration", "family", "foreclosure", "vacant lot",
                   "court", "estate", "sheriff", "exempt", "non-arm"}

        for t in all_tables:
            # Sales table confirmed structure (Table 14):
            # Uses real <th> elements: Date|Seller|Buyer|Recording|Sale Condition - NUTC|Type|Multi Parcel|Amount
            # Identify by presence of ALL three: 'date', 'amount', and seller/buyer
            # Scope to thead to avoid grabbing data-row th elements
            thead = t.query_selector("thead")
            if thead:
                ths_els = thead.query_selector_all("th")
            else:
                # Fall back to first row
                first_tr = t.query_selector("tr")
                ths_els = first_tr.query_selector_all("th, td") if first_tr else []
            if not ths_els:
                continue
            ths = [el.inner_text().strip().lower().replace("\xa0", " ").replace("\n", " ")
                   for el in ths_els]
            if not ("date" in ths and "amount" in ths and
                    any("seller" in h or "buyer" in h for h in ths)):
                continue

            log.debug("Sales table headers: %s", ths)
            col = {}
            for i, h in enumerate(ths):
                if h == "date":                              col["date"]      = i
                elif "seller" in h or "grantor" in h:       col["seller"]    = i
                elif "buyer" in h or "grantee" in h:        col["buyer"]     = i
                elif "recording" in h or "book" in h:       col["recording"] = i
                elif "condition" in h or "nutc" in h:       col["condition"] = i
                elif h == "type" or "deed" in h:            col["type"]      = i
                elif "multi" in h or "parcel" in h and i > 4: col["multi"]  = i
                elif "amount" in h or h == "sale":          col["amount"]    = i

            # Get data rows from tbody if present, else skip header row
            tbody = t.query_selector("tbody")
            data_rows = tbody.query_selector_all("tr") if tbody else t.query_selector_all("tr")[1:]
            log.debug("Sales data rows: %d", len(data_rows))
            for row in data_rows:
                cells = row.query_selector_all("td")
                if not cells: continue
                all_row_els = row.query_selector_all("td, th")
                all_texts = [el.inner_text().strip().replace("\xa0", " ")
                             for el in all_row_els]

                def cv(k):
                    # Use all_texts (td+th) so date in th at index 0 aligns correctly
                    idx = col.get(k)
                    if idx is None or idx >= len(all_texts):
                        return None
                    return all_texts[idx] if all_texts[idx] else None

                sale_date  = pdate(cv("date"))
                sale_price = pmoney(cv("amount"))

                # If date still missing, scan all cells for a date pattern
                if not sale_date:
                    for txt in all_texts:
                        d = pdate(txt[:12])
                        if d:
                            sale_date = d
                            break

                if not sale_date or sale_price is None:
                    continue

                condition    = (cv("condition") or "").strip()
                arms_length  = not any(kw in condition.lower() for kw in NON_ARM)
                multi        = (cv("multi") or "").strip().lower() in ("yes", "y", "x", "1")
                recording    = re.sub(r"\s*opens in a new tab.*", "", cv("recording") or "", flags=re.I).strip()

                sale = {
                    "sale_date":        sale_date,
                    "sale_price":       sale_price,
                    "seller":           cv("seller"),
                    "buyer":            cv("buyer"),
                    "recording_number": recording,
                    "sale_condition":   condition,
                    "deed_type":        cv("type"),
                    "arms_length_flag": arms_length,
                    "multi_parcel":     multi,
                }
                sqft = prop.get("living_area_sqft")
                if sqft and sale_price and sale_price > 0:
                    sale["price_per_sqft"] = round(sale_price / sqft, 2)
                data["sales"].append(sale)
            break

    except Exception as e:
        log.warning("Parse error KeyValue=%s: %s", key_value, e, exc_info=True)
        data["errors"].append(str(e))

    log.debug("KeyValue=%s parcel=%s assessments=%d sales=%d errors=%d",
              key_value, prop.get("county_parcel_id","?"),
              len(data["assessments"]), len(data["sales"]), len(data["errors"]))
    return data

# ── DB upsert ─────────────────────────────────────────────────────────────────

def upsert_parcel_data(conn, parsed: dict):
    prop = parsed.get("property", {})
    if not prop.get("county_parcel_id"):
        log.warning("No parcel ID, skipping upsert.")
        return None, False
    url = parsed.get("source_url", "")

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO properties (
                county, county_parcel_id, alternate_parcel_id,
                address_raw, city,
                year_built, living_area_sqft, basement_sqft,
                lot_sf, lot_acres, bedrooms, bathrooms, stories,
                bldg_style, quality_grade, condition_rating,
                property_class, tax_district, school_district,
                owner_name, parser_version, source_url, last_seen_at
            ) VALUES (
                'dallas',%(county_parcel_id)s,%(alternate_parcel_id)s,
                %(address_raw)s,%(city)s,
                %(year_built)s,%(living_area_sqft)s,%(basement_sqft)s,
                %(lot_sf)s,%(lot_acres)s,%(bedrooms)s,%(bathrooms)s,%(stories)s,
                %(bldg_style)s,%(quality_grade)s,%(condition_rating)s,
                %(property_class)s,%(tax_district)s,%(school_district)s,
                %(owner_name)s,%(parser_version)s,%(source_url)s,NOW()
            )
            ON CONFLICT (county, county_parcel_id) DO UPDATE SET
                alternate_parcel_id = EXCLUDED.alternate_parcel_id,
                address_raw         = COALESCE(EXCLUDED.address_raw, properties.address_raw),
                city                = COALESCE(EXCLUDED.city, properties.city),
                year_built          = COALESCE(EXCLUDED.year_built, properties.year_built),
                living_area_sqft    = COALESCE(EXCLUDED.living_area_sqft, properties.living_area_sqft),
                lot_sf              = COALESCE(EXCLUDED.lot_sf, properties.lot_sf),
                lot_acres           = COALESCE(EXCLUDED.lot_acres, properties.lot_acres),
                bedrooms            = COALESCE(EXCLUDED.bedrooms, properties.bedrooms),
                bathrooms           = COALESCE(EXCLUDED.bathrooms, properties.bathrooms),
                bldg_style          = COALESCE(EXCLUDED.bldg_style, properties.bldg_style),
                quality_grade       = COALESCE(EXCLUDED.quality_grade, properties.quality_grade),
                property_class      = COALESCE(EXCLUDED.property_class, properties.property_class),
                tax_district        = COALESCE(EXCLUDED.tax_district, properties.tax_district),
                school_district     = COALESCE(EXCLUDED.school_district, properties.school_district),
                owner_name          = COALESCE(EXCLUDED.owner_name, properties.owner_name),
                parser_version      = EXCLUDED.parser_version,
                source_url          = EXCLUDED.source_url,
                last_seen_at        = NOW()
            RETURNING id, (xmax = 0) AS inserted
        """, {
            **{k: None for k in [
                "county_parcel_id","alternate_parcel_id","address_raw","city",
                "year_built","living_area_sqft","basement_sqft","lot_sf","lot_acres",
                "bedrooms","bathrooms","stories","bldg_style","quality_grade",
                "condition_rating","property_class","tax_district","school_district",
                "owner_name","source_url",
            ]},
            **prop,
            "parser_version": PARSER_VERSION,
            "source_url": url,
        })
        pid, inserted = cur.fetchone()

    for asmt in parsed.get("assessments", []):
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assessments (
                    property_id,tax_year,assessed_total,assessed_land,
                    assessed_improvements,assessed_dwelling,net_assessed_value,
                    taxable_total,gross_taxes_due,net_taxes_due,
                    classification,parser_version,source_url,extracted_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (property_id,tax_year) DO UPDATE SET
                    assessed_total        = COALESCE(EXCLUDED.assessed_total, assessments.assessed_total),
                    assessed_land         = COALESCE(EXCLUDED.assessed_land, assessments.assessed_land),
                    assessed_improvements = COALESCE(EXCLUDED.assessed_improvements, assessments.assessed_improvements),
                    assessed_dwelling     = COALESCE(EXCLUDED.assessed_dwelling, assessments.assessed_dwelling),
                    net_assessed_value    = COALESCE(EXCLUDED.net_assessed_value, assessments.net_assessed_value),
                    taxable_total         = COALESCE(EXCLUDED.taxable_total, assessments.taxable_total),
                    gross_taxes_due       = COALESCE(EXCLUDED.gross_taxes_due, assessments.gross_taxes_due),
                    net_taxes_due         = COALESCE(EXCLUDED.net_taxes_due, assessments.net_taxes_due),
                    classification        = COALESCE(EXCLUDED.classification, assessments.classification),
                    extracted_at          = NOW()
            """, (pid,
                  asmt.get("tax_year"), asmt.get("assessed_total"), asmt.get("assessed_land"),
                  asmt.get("assessed_improvements"), asmt.get("assessed_dwelling"),
                  asmt.get("net_assessed_value"), asmt.get("taxable_total"),
                  asmt.get("gross_taxes_due"), asmt.get("net_taxes_due"),
                  asmt.get("classification"), PARSER_VERSION, url))

    for sale in parsed.get("sales", []):
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sales (
                    property_id,sale_date,sale_price,price_per_sqft,
                    deed_type,sale_condition,arms_length_flag,multi_parcel,
                    recording_number,buyer,seller,parser_version,source_url,extracted_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (property_id,sale_date,sale_price) DO NOTHING
            """, (pid,
                  sale.get("sale_date"), sale.get("sale_price"), sale.get("price_per_sqft"),
                  sale.get("deed_type"), sale.get("sale_condition"), sale.get("arms_length_flag"),
                  sale.get("multi_parcel"), sale.get("recording_number"),
                  sale.get("buyer"), sale.get("seller"), PARSER_VERSION, url))

    conn.commit()
    return pid, inserted

# ── Search helpers ────────────────────────────────────────────────────────────

def extract_key_values(page) -> list:
    content = page.content()

    # Pattern 1: explicit KeyValue= param in href
    kv_list = re.findall(r"KeyValue=(\d+)", content)

    # Pattern 2: results page (PageTypeID=3) uses parcel ID as the link text/href
    # e.g. <a href="...PageTypeID=4...KeyValue=1225233013">1225233013</a>
    # but also plain parcel ID links in the results table
    kv_list += re.findall(r'PageTypeID=4[^"]*KeyValue=(\d+)', content)

    # Pattern 3: results table parcel ID column — linked parcel numbers
    # Beacon results table has <a href="...">1225233013</a> style links
    kv_list += re.findall(r'href="[^"]*PageTypeID=4[^"]*[&?]KeyValue=(\d+)[^"]*"', content)

    # Pattern 4: parcel ID links that ARE the KeyValue (no explicit param)
    # Match href containing the parcel number for Dallas County format (10 digits)
    kv_list += re.findall(r'href="Application\.aspx[^"]*&(?:amp;)?Q=(\d+)"', content)

    seen, unique = set(), []
    for kv in kv_list:
        if kv not in seen:
            seen.add(kv); unique.append(kv)

    log.debug("extract_key_values found: %s", unique[:10])
    return unique

def js_click(page, selector):
    el = page.query_selector(selector)
    if el:
        page.evaluate("(el) => el.click()", el)
        return True
    return False

def nav_and_search(page, inputs: dict, search_btn_selector: str, delay=SEARCH_DELAY_SEC):
    global _beacon_warmed_up
    page.goto(BEACON_SEARCH_URL, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
    wait_for_beacon(page)
    handle_tc_modal(page)
    _beacon_warmed_up = True
    time.sleep(1)

    for selector, value in inputs.items():
        el = page.query_selector(selector)
        if el:
            log.debug("Filling '%s' with '%s'", selector, value)
            el.fill(value)
            time.sleep(0.3)
        else:
            log.warning("Input not found: %s", selector)

    clicked = js_click(page, search_btn_selector)
    if not clicked:
        log.warning("Search button not found: %s", search_btn_selector)
    time.sleep(delay)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    try:
        log.debug("Post-search URL: %s", page.url)
        log.debug("Post-search title: %s", page.title())
        log.debug("Post-search content length: %d", len(page.content()))
    except Exception as e:
        log.debug("Post-search page state error (likely mid-navigation): %s", e)
        time.sleep(2)  # let navigation settle

        kvs = extract_key_values(page)
    log.debug("KeyValues extracted: %s", kvs[:10])
    return kvs

# ── Parcel fetcher ────────────────────────────────────────────────────────────

_beacon_warmed_up = False  # module-level flag, one warm-up per browser session

def _warmup(page):
    """
    Land on the search page first to establish Cloudflare clearance.
    Beacon grants a session token after passing the challenge on any page.
    Subsequent navigations within the same context reuse it.
    Only needs to happen once per browser context.
    """
    global _beacon_warmed_up
    if _beacon_warmed_up:
        return
    log.info("Warming up Beacon session (search page first)...")
    page.goto(BEACON_SEARCH_URL, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
    wait_for_beacon(page)
    handle_tc_modal(page)
    time.sleep(1)
    _beacon_warmed_up = True
    log.info("Beacon session established.")


def fetch_and_parse(page, key_value: str, conn=None) -> Optional[dict]:
    url = BEACON_PARCEL_URL.format(key_value=key_value)
    log.info("Fetching KeyValue=%s", key_value)
    _warmup(page)
    for attempt in range(MAX_RETRIES):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
            wait_for_beacon(page)
            handle_tc_modal(page)
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=10000)
            break
        except (PWTimeout, TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                log.warning("Timeout attempt %d, retrying...", attempt + 1)
                time.sleep(5)
            else:
                log.error("Failed after %d attempts: %s", MAX_RETRIES, e)
                return None
    # Wait until the valuation table is actually rendered (JS-driven content)
    try:
        page.wait_for_selector("table", timeout=10000)
        # Wait for the page to have real content — at least 10 tables
        for _ in range(15):
            tables = page.query_selector_all("table")
            if len(tables) >= 10:
                break
            time.sleep(0.5)
        log.debug("Tables present: %d", len(page.query_selector_all("table")))
    except Exception as e:
        log.warning("Table wait timeout: %s", e)

    html = page.content()
    if len(html) < 3000:
        log.warning("Short page (%d bytes) for KeyValue=%s", len(html), key_value)
        return None
    if conn:
        save_snapshot(html, key_value, "parcel_report", conn)
    return parse_parcel_page(page, key_value)

# ── Run modes ─────────────────────────────────────────────────────────────────

def run_parcel_mode(key_value: str, dry_run=False, use_csv=False):
    global _beacon_warmed_up
    _beacon_warmed_up = False
    conn = None
    if not dry_run and not use_csv:
        conn = get_db()
    if conn: ensure_schema(conn)
    with sync_playwright() as p:
        browser, context = make_browser_context(p)
        load_session(context)
        page = context.new_page()
        try:
            parsed = fetch_and_parse(page, key_value, conn if conn else None)
            if parsed:
                print(json.dumps(parsed, indent=2, default=str))
                if use_csv:
                    write_csv(parsed)
                elif conn:
                    pid, ins = upsert_parcel_data(conn, parsed)
                    log.info("property_id=%s inserted=%s", pid, ins)
        finally:
            context.close()
    if conn: conn.close()

def run_parcel_number_mode(parcel_number: str, dry_run=False):
    conn = None if dry_run else get_db()
    if conn: ensure_schema(conn)
    with sync_playwright() as p:
        browser, context = make_browser_context(p)
        load_session(context)
        page = context.new_page()
        try:
            kvs = nav_and_search(page,
                {"#ctlBodyPane_ctl01_ctl01_txtParcelID": parcel_number},
                "#ctlBodyPane_ctl01_ctl01_btnSearch")
            log.info("Parcel '%s' → %d result(s)", parcel_number, len(kvs))
            for kv in kvs[:5]:
                parsed = fetch_and_parse(page, kv, conn if not dry_run else None)
                if parsed:
                    print(json.dumps(parsed, indent=2, default=str))
                    if conn: upsert_parcel_data(conn, parsed)
                time.sleep(PAGE_DELAY_SEC)
        finally:
            context.close()
    if conn: conn.close()

def run_address_mode(address: str, dry_run=False, use_csv=False):
    conn = None
    if not dry_run and not use_csv:
        conn = get_db()
    if conn: ensure_schema(conn)
    with sync_playwright() as p:
        browser, context = make_browser_context(p)
        load_session(context)
        page = context.new_page()
        try:
            kvs = nav_and_search(page,
                {"#ctlBodyPane_ctl00_ctl01_txtAddress": address},
                "#ctlBodyPane_ctl00_ctl01_btnSearch")
            log.info("Address '%s' → %d result(s)", address, len(kvs))
            for kv in kvs[:10]:
                parsed = fetch_and_parse(page, kv, conn if conn else None)
                if parsed:
                    print(json.dumps(parsed, indent=2, default=str))
                    if use_csv:
                        write_csv(parsed)
                    elif conn:
                        upsert_parcel_data(conn, parsed)
                time.sleep(PAGE_DELAY_SEC)
        finally:
            context.close()
    if conn: conn.close()

def run_sales_mode(days=90, dry_run=False):
    global _beacon_warmed_up
    _beacon_warmed_up = False
    """
    Bulk nightly mode. Navigates to Beacon's Sales Results tab,
    searches by date range, paginates, fetches each parcel report.

    If sales search inputs aren't found, a warning is logged with instructions
    to inspect the form manually in a real browser.
    """
    conn = None if dry_run else get_db()
    if conn: ensure_schema(conn)
    run_id = None
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ingestion_runs (county,source_name,started_at,status) "
                "VALUES ('dallas','dallas_beacon_sales',NOW(),'running') RETURNING id")
            run_id = cur.fetchone()[0]
        conn.commit()

    inserted = updated = 0
    errors = []

    with sync_playwright() as p:
        browser, context = make_browser_context(p)
        load_session(context)
        page = context.new_page()
        try:
            page.goto(BEACON_SEARCH_URL, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
            wait_for_beacon(page)
            handle_tc_modal(page)
            time.sleep(1)

            # Click Sales Search nav tab
            js_click(page, "a:has-text('Sales Search'), a:has-text('Sales Results')")
            time.sleep(SEARCH_DELAY_SEC)

            date_from = (datetime.now() - timedelta(days=days)).strftime("%m/%d/%Y")
            date_to   = datetime.now().strftime("%m/%d/%Y")

            from_inp = page.query_selector("input[id*='DateFrom'],input[id*='SaleFrom'],input[id*='StartDate']")
            to_inp   = page.query_selector("input[id*='DateTo'],input[id*='SaleTo'],input[id*='EndDate']")

            if from_inp and to_inp:
                from_inp.fill(date_from)
                to_inp.fill(date_to)
                time.sleep(0.3)
                js_click(page, "input[type='submit'][value*='Search'], button:has-text('Search')")
                time.sleep(SEARCH_DELAY_SEC)
                try: page.wait_for_load_state("networkidle", timeout=15000)
                except Exception: pass
            else:
                log.warning(
                    "Sales date range inputs not found. "
                    "Open Beacon in Chrome DevTools, go to Sales Search tab, "
                    "inspect the date input IDs, then update run_sales_mode()."
                )

            key_values = extract_key_values(page)
            # Paginate
            while True:
                next_btn = page.query_selector(
                    "a:has-text('Next'), a[title='Next Page'], .pagination .next:not(.disabled) a"
                )
                if not next_btn: break
                page.evaluate("(el) => el.click()", next_btn)
                time.sleep(SEARCH_DELAY_SEC)
                try: page.wait_for_load_state("networkidle", timeout=10000)
                except Exception: pass
                new_kvs = extract_key_values(page)
                if not new_kvs or set(new_kvs).issubset(set(key_values)): break
                key_values.extend(kv for kv in new_kvs if kv not in key_values)

            log.info("Processing %d parcels", len(key_values))
            for i, kv in enumerate(key_values):
                try:
                    parsed = fetch_and_parse(page, kv, conn if not dry_run else None)
                    if parsed and not dry_run:
                        pid, was_inserted = upsert_parcel_data(conn, parsed)
                        if was_inserted: inserted += 1
                        else:            updated  += 1
                    if (i + 1) % 25 == 0:
                        log.info("Progress: %d/%d", i + 1, len(key_values))
                    time.sleep(PAGE_DELAY_SEC)
                except Exception as e:
                    log.error("KeyValue=%s error: %s", kv, e)
                    errors.append({"key_value": kv, "error": str(e)})
        finally:
            context.close()

    if conn and run_id:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE ingestion_runs SET completed_at=NOW(),status=%s,"
                "rows_inserted=%s,rows_updated=%s,errors_json=%s WHERE id=%s",
                ("complete" if not errors else "complete_with_errors",
                 inserted, updated, json.dumps(errors) if errors else None, run_id))
        conn.commit()
        conn.close()

    log.info("Done. Inserted=%d Updated=%d Errors=%d", inserted, updated, len(errors))

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Dallas County Beacon scraper")
    ap.add_argument("--mode", choices=["parcel","parcel-number","address","sales"], default="parcel")
    ap.add_argument("--parcel-id",     help="Beacon KeyValue ID")
    ap.add_argument("--parcel-number", help="County parcel number e.g. 12-21-406-018")
    ap.add_argument("--address",       help="Street address")
    ap.add_argument("--days",  type=int, default=90)
    ap.add_argument("--dry-run",  action="store_true", help="Parse and print only, no output")
    ap.add_argument("--csv",      action="store_true", help="Write to CSV files instead of Postgres")
    ap.add_argument("--debug",    action="store_true")
    args = ap.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if   args.mode == "parcel":
        if not args.parcel_id: ap.error("--parcel-id required")
        run_parcel_mode(args.parcel_id, args.dry_run, args.csv)
    elif args.mode == "parcel-number":
        if not args.parcel_number: ap.error("--parcel-number required")
        run_parcel_number_mode(args.parcel_number, args.dry_run)
    elif args.mode == "address":
        if not args.address: ap.error("--address required")
        run_address_mode(args.address, args.dry_run, args.csv)
    elif args.mode == "sales":
        run_sales_mode(args.days, args.dry_run)
