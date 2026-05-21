"""
polk_sales_load.py
------------------
Loads all Polk County annual sales CSVs (1990-2026, 400K rows) into:
  - sales       : one row per sale (upsert on property_id + sale_date + sale_price)
  - assessments : historical assessed values per sale year (ON CONFLICT DO NOTHING
                  — won't overwrite the 2026 inventory values already loaded)

Join strategy:
  Loads all dp → property_id mappings into memory (~173K entries) at startup,
  then does pure in-memory lookups per row. No per-row DB queries.

Arms-length flag:
  quality1 == 'Arms Length'  → True
  anything else              → False  (non_arms_length_reason = quality1 text)

Multi-parcel:
  legal_all_parcels contains '###' separator

Usage:
  python polk_sales_load.py                    # load all years 1990-2026
  python polk_sales_load.py --year 2024        # single year
  python polk_sales_load.py --dry-run          # parse only, no DB writes
  python polk_sales_load.py --arms-length-only # skip non-arms-length sales
"""

import csv
import os
import sys
import time
import glob
import argparse
import logging
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("polk_sales_load")

# ── Config ────────────────────────────────────────────────────────────────────

SALES_DIR      = Path(__file__).parent / "polk_data" / "sales"
PARSER_VERSION = "v1.0.0"
SOURCE_SYSTEM  = "polk_sales_csv"
BATCH_SIZE     = 2000
LOG_EVERY      = 20_000

# quality1 values that indicate non-arms-length
NON_ARMS = {
    "Vacant Lot",
    "Prior Improvement or Disimprovement",
    "Exchange, Trade, Gift, Estate Transfer",
    "Partial Assessment",
    "Other",
    "Family",
    "Government or Exempt",
    "Foreclosure, Forfeiture, Sheriff/Tax Sale, Default",
    "No Consideration",
    "Quit Claim",
    "Landlord to Tenant",
    "Partial Interest",
    "Change in Classification",
    "Court Order",
}

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host    =os.getenv("DB_HOST", "localhost"),
        port    =int(os.getenv("DB_PORT", 5432)),
        dbname  =os.getenv("DB_NAME", "iowa_propertytax"),
        user    =os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "iowa2026"),
    )

def load_parcel_id_map(conn) -> dict:
    """Load all polk county_parcel_id → id into memory."""
    log.info("Loading parcel ID map from DB...")
    cur = conn.cursor()
    cur.execute("SELECT county_parcel_id, id FROM properties WHERE county='polk'")
    mapping = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    log.info("  Loaded %d parcel → property_id mappings", len(mapping))
    return mapping

# ── Helpers ───────────────────────────────────────────────────────────────────

def pint(s):
    if not s or not str(s).strip():
        return None
    try:
        return int(float(str(s).replace(",", "").strip()))
    except (ValueError, TypeError):
        return None

def pfloat(s):
    if not s or not str(s).strip():
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return None

def pstr(s):
    v = str(s).strip() if s else ""
    return v if v else None

def pdate(s):
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def map_row(row: dict, id_map: dict) -> tuple:
    """
    Returns (sale_dict, asmt_dict, property_id) or (None, None, None) if skip.
    """
    dp = (row.get("dp") or "").strip()
    if not dp:
        return None, None, None

    property_id = id_map.get(dp)
    if property_id is None:
        return None, None, None   # parcel not in properties (old/demolished/non-residential)

    sale_date  = pdate(row.get("sale_date"))
    sale_price = pfloat(row.get("price"))
    if sale_date is None or sale_price is None:
        return None, None, None

    q1        = pstr(row.get("quality1")) or ""
    arms      = (q1 == "Arms Length")
    non_arms_reason = q1 if not arms and q1 else None

    sqft      = pfloat(row.get("total_living_area"))
    ppsf      = round(sale_price / sqft, 2) if sqft and sqft > 0 and sale_price else None

    recording = None
    book = pstr(row.get("book"))
    pg   = pstr(row.get("pg"))
    if book and pg:
        recording = f"{book}/{pg}"

    multi = "###" in (row.get("legal_all_parcels") or "")

    sale = {
        "property_id"          : property_id,
        "sale_date"            : sale_date,
        "sale_price"           : sale_price,
        "price_per_sqft"       : ppsf,
        "sale_type"            : pstr(row.get("occupancy")),
        "deed_type"            : pstr(row.get("instrument")),
        "arms_length_flag"     : arms,
        "non_arms_length_reason": non_arms_reason,
        "multi_parcel"         : multi,
        "recording_number"     : recording,
        "buyer"                : pstr(row.get("buyer")),
        "seller"               : pstr(row.get("seller")),
        "source_system"        : SOURCE_SYSTEM,
        "parser_version"       : PARSER_VERSION,
        "source_url"           : None,
    }

    # Assessment backfill: one row per (property_id, yr)
    yr = pint(row.get("yr"))
    asmt = None
    if yr:
        land_full  = pfloat(row.get("land_full"))
        bldg_full  = pfloat(row.get("bldg_full"))
        total_full = pfloat(row.get("total_full"))
        if any(v for v in [land_full, bldg_full, total_full]):
            # Compute assessment ratio if arms-length sale
            ratio = None
            if arms and sale_price and total_full and sale_price > 0:
                ratio = round(total_full / sale_price, 4)
            asmt = {
                "property_id"          : property_id,
                "tax_year"             : yr,
                "assessed_land"        : land_full,
                "assessed_improvements": bldg_full,
                "assessed_total"       : total_full,
                "assessment_ratio"     : ratio,
                "classification"       : pstr(row.get("occupancy")),
                "source_system"        : SOURCE_SYSTEM,
                "parser_version"       : PARSER_VERSION,
            }

    return sale, asmt, property_id


# ── SQL ───────────────────────────────────────────────────────────────────────

SALE_SQL = """
INSERT INTO sales (
    property_id, sale_date, sale_price, price_per_sqft,
    sale_type, deed_type, arms_length_flag, non_arms_length_reason,
    multi_parcel, recording_number, buyer, seller,
    source_system, parser_version, source_url, extracted_at
) VALUES (
    %(property_id)s, %(sale_date)s, %(sale_price)s, %(price_per_sqft)s,
    %(sale_type)s, %(deed_type)s, %(arms_length_flag)s, %(non_arms_length_reason)s,
    %(multi_parcel)s, %(recording_number)s, %(buyer)s, %(seller)s,
    %(source_system)s, %(parser_version)s, %(source_url)s, NOW()
)
ON CONFLICT (property_id, sale_date, sale_price) DO NOTHING
"""

ASMT_SQL = """
INSERT INTO assessments (
    property_id, tax_year,
    assessed_land, assessed_improvements, assessed_total,
    assessment_ratio, classification,
    source_system, parser_version, extracted_at
) VALUES (
    %(property_id)s, %(tax_year)s,
    %(assessed_land)s, %(assessed_improvements)s, %(assessed_total)s,
    %(assessment_ratio)s, %(classification)s,
    %(source_system)s, %(parser_version)s, NOW()
)
ON CONFLICT (property_id, tax_year) DO NOTHING
"""

# ── Batch flush ───────────────────────────────────────────────────────────────

def flush(conn, sale_batch, asmt_batch, counts):
    cur = conn.cursor()
    if sale_batch:
        psycopg2.extras.execute_batch(cur, SALE_SQL, sale_batch, page_size=BATCH_SIZE)
        counts["sales"] += len(sale_batch)
    if asmt_batch:
        psycopg2.extras.execute_batch(cur, ASMT_SQL, asmt_batch, page_size=BATCH_SIZE)
        counts["asmts"] += len(asmt_batch)
    conn.commit()
    cur.close()

# ── Main ──────────────────────────────────────────────────────────────────────

def process_file(csv_path: Path, id_map: dict, conn,
                 dry_run: bool, arms_only: bool, counts: dict):
    year = csv_path.stem
    file_sales = 0
    file_skipped = 0
    sale_batch = []
    asmt_batch = []

    # Deduplicate assessments within this file — one assessment row per (pid, yr)
    seen_asmts: set = set()

    with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            sale, asmt, pid = map_row(row, id_map)
            if sale is None:
                counts["no_match"] += 1
                file_skipped += 1
                continue

            if arms_only and not sale["arms_length_flag"]:
                counts["skipped_non_arms"] += 1
                continue

            if dry_run:
                file_sales += 1
                counts["sales"] += 1
                continue

            sale_batch.append(sale)

            if asmt:
                key = (pid, asmt["tax_year"])
                if key not in seen_asmts:
                    seen_asmts.add(key)
                    asmt_batch.append(asmt)

            if len(sale_batch) >= BATCH_SIZE:
                flush(conn, sale_batch, asmt_batch, counts)
                sale_batch.clear()
                asmt_batch.clear()

            file_sales += 1

    # Flush remainder for this file
    if not dry_run and (sale_batch or asmt_batch):
        flush(conn, sale_batch, asmt_batch, counts)

    return file_sales, file_skipped


def main(year_filter, dry_run, arms_only):
    log.info("polk_sales_load starting")
    log.info("Sales dir: %s", SALES_DIR)
    log.info("Dry run:   %s | Arms-length only: %s", dry_run, arms_only)

    conn = None if dry_run else get_db()
    id_map = {}
    if not dry_run:
        id_map = load_parcel_id_map(conn)
    else:
        # In dry-run, load map anyway to measure match rate
        tmp = get_db()
        id_map = load_parcel_id_map(tmp)
        tmp.close()

    # Collect CSV files
    if year_filter:
        files = [SALES_DIR / f"{year_filter}.csv"]
        files = [f for f in files if f.exists()]
    else:
        files = sorted(SALES_DIR.glob("*.csv"))

    if not files:
        log.error("No CSV files found in %s", SALES_DIR)
        sys.exit(1)

    log.info("Files to process: %d (%s → %s)",
             len(files), files[0].stem, files[-1].stem)

    counts = {
        "sales": 0, "asmts": 0,
        "no_match": 0, "skipped_non_arms": 0, "errors": 0,
    }
    grand_total = 0
    t0 = time.time()

    for i, csv_path in enumerate(files):
        t_file = time.time()
        try:
            n_sales, n_skip = process_file(
                csv_path, id_map, conn, dry_run, arms_only, counts
            )
            elapsed_file = time.time() - t_file
            log.info("  %s: %5d sales loaded, %4d no-match  (%.1fs)",
                     csv_path.stem, n_sales, n_skip, elapsed_file)
            grand_total += n_sales
        except Exception as e:
            log.error("  %s: FAILED — %s", csv_path.stem, e)
            counts["errors"] += 1

        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            log.info("  --- %d/%d files | sales=%s asmts=%s | %.0fs elapsed ---",
                     i + 1, len(files),
                     f"{counts['sales']:,}", f"{counts['asmts']:,}", elapsed)

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("COMPLETE in %.1fs", elapsed)
    log.info("  Sales inserted  : %s", f"{counts['sales']:,}")
    log.info("  Assessments ins : %s", f"{counts['asmts']:,}")
    log.info("  No property match: %s", f"{counts['no_match']:,}")
    if arms_only:
        log.info("  Skipped non-arms: %s", f"{counts['skipped_non_arms']:,}")
    log.info("  File errors      : %d", counts["errors"])

    if conn:
        cur = conn.cursor()
        for t in ("properties", "assessments", "sales"):
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            log.info("  DB %-15s: %s rows", t, f"{cur.fetchone()[0]:,}")
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load Polk County annual sales CSVs")
    ap.add_argument("--year",            help="Load a single year (e.g. 2024)")
    ap.add_argument("--dry-run",         action="store_true", help="Parse only, no DB writes")
    ap.add_argument("--arms-length-only",action="store_true", help="Skip non-arms-length sales")
    args = ap.parse_args()
    main(args.year, args.dry_run, args.arms_length_only)
