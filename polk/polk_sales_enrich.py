"""
polk_sales_enrich.py
--------------------
Back-fills missing building characteristics on the properties table
using data from the annual sales CSVs.

The inventory (POLKCOUNTY.csv) has NULL building data for ~18K parcels —
mainly vacant lots, condos where data sits on the parent parcel, or parcels
that have changed use since the snapshot.

Strategy:
  For each parcel with missing fields, scan all sales CSVs newest → oldest
  and take the first (most recent) row that has non-zero values for the
  missing fields.

  Fields enriched (only where currently NULL in properties):
    living_area_sqft  ← total_living_area
    basement_sqft     ← basement_area
    year_built        ← year_built
    bedrooms          ← bedrooms
    bathrooms         ← bathrooms + 0.5 * toilet_rooms
    bldg_style        ← bldg_style
    stories           ← residence_type
    quality_grade     ← grade
    condition_rating  ← condition
    garage_spaces     ← bsmt_gar_capacity / att_garage_area

Only updates where the sales value is non-null AND non-zero.
Never overwrites a populated inventory value.

Usage:
  python polk_sales_enrich.py
  python polk_sales_enrich.py --dry-run
"""

import csv
import os
import time
import glob
import argparse
import logging
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
log = logging.getLogger("polk_sales_enrich")

SALES_DIR  = Path(__file__).parent / "polk_data" / "sales"
BATCH_SIZE = 500

ENRICH_FIELDS = [
    "living_area_sqft",
    "basement_sqft",
    "year_built",
    "bedrooms",
    "bathrooms",
    "bldg_style",
    "stories",
    "quality_grade",
    "condition_rating",
    "garage_spaces",
]

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host    =os.getenv("DB_HOST", "localhost"),
        port    =int(os.getenv("DB_PORT", 5432)),
        dbname  =os.getenv("DB_NAME", "iowa_propertytax"),
        user    =os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "iowa2026"),
    )

def load_null_parcels(conn) -> dict:
    """
    Load parcels that are missing at least one enrichable field.
    Returns: dp → {id, missing_fields: set}
    """
    log.info("Loading parcels with missing building data...")
    fields_sql = " OR ".join(f"{f} IS NULL" for f in ENRICH_FIELDS)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT county_parcel_id, id,
               living_area_sqft, basement_sqft, year_built,
               bedrooms, bathrooms, bldg_style, stories,
               quality_grade, condition_rating, garage_spaces
        FROM properties
        WHERE county='polk' AND ({fields_sql})
    """)
    parcels = {}
    for row in cur.fetchall():
        dp = row[0]
        pid = row[1]
        vals = row[2:]
        missing = {ENRICH_FIELDS[i] for i, v in enumerate(vals) if v is None}
        parcels[dp] = {"id": pid, "missing": missing, "updates": {}}
    cur.close()
    log.info("  %d parcels need enrichment", len(parcels))
    return parcels

# ── Helpers ───────────────────────────────────────────────────────────────────

def pint(s):
    if not s or not str(s).strip(): return None
    try: return int(float(str(s).replace(",", "").strip()))
    except: return None

def pfloat(s):
    if not s or not str(s).strip(): return None
    try: return float(str(s).replace(",", "").strip())
    except: return None

def pstr(s):
    v = str(s).strip() if s else ""
    return v if v else None

def extract_building(row: dict) -> dict:
    """Pull building characteristics from a sales CSV row."""
    full_baths  = pfloat(row.get("bathrooms")) or 0
    toilet_rms  = pfloat(row.get("toilet_rooms")) or 0
    bathrooms   = (full_baths + 0.5 * toilet_rms) if (full_baths or toilet_rms) else None

    garage = pint(row.get("bsmt_gar_capacity"))
    if not garage:
        att = pfloat(row.get("att_garage_area")) or 0
        if att > 0:
            garage = 1

    sqft = pint(row.get("total_living_area"))

    return {
        "living_area_sqft" : sqft if sqft and sqft > 0 else None,
        "basement_sqft"    : pint(row.get("basement_area")) or None,
        "year_built"       : pint(row.get("year_built")) or None,
        "bedrooms"         : pint(row.get("bedrooms")) or None,
        "bathrooms"        : bathrooms if bathrooms and bathrooms > 0 else None,
        "bldg_style"       : pstr(row.get("bldg_style")),
        "stories"          : pstr(row.get("residence_type")),
        "quality_grade"    : pstr(row.get("grade")),
        "condition_rating" : pstr(row.get("condition")),
        "garage_spaces"    : garage,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool):
    log.info("polk_sales_enrich starting | dry_run=%s", dry_run)

    conn    = get_db()
    parcels = load_null_parcels(conn)
    n_start = len(parcels)

    # Process CSVs newest → oldest so we capture the most recent building data first
    csv_files = sorted(SALES_DIR.glob("*.csv"), reverse=True)
    log.info("Scanning %d sales files (newest first)...", len(csv_files))

    t0 = time.time()
    total_rows_scanned = 0

    for csv_path in csv_files:
        # Stop early if all parcels are fully enriched
        remaining = {dp: p for dp, p in parcels.items() if p["missing"]}
        if not remaining:
            log.info("All parcels fully enriched — stopping early")
            break

        with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                dp = (row.get("dp") or "").strip()
                if dp not in remaining:
                    continue

                building = extract_building(row)
                parcel   = remaining[dp]
                filled   = False

                for field in list(parcel["missing"]):
                    val = building.get(field)
                    if val is not None:
                        parcel["updates"][field] = val
                        parcel["missing"].discard(field)
                        filled = True

                total_rows_scanned += 1

        log.info("  %s: %d parcels still need data", csv_path.stem, len(remaining))

    # Apply updates
    updates_by_fields: dict = {}
    for dp, parcel in parcels.items():
        if not parcel["updates"]:
            continue
        # Group by the exact set of fields being updated (for batch SQL)
        key = tuple(sorted(parcel["updates"].keys()))
        if key not in updates_by_fields:
            updates_by_fields[key] = []
        updates_by_fields[key].append((parcel["id"], parcel["updates"]))

    total_props_updated = 0
    total_fields_set    = 0

    if not dry_run:
        cur = conn.cursor()
        for fields_tuple, id_updates in updates_by_fields.items():
            set_clause = ", ".join(f"{f}=%({f})s" for f in fields_tuple)
            sql = f"UPDATE properties SET {set_clause}, last_seen_at=NOW() WHERE id=%(id)s"
            batch = []
            for pid, updates in id_updates:
                row = {"id": pid}
                row.update(updates)
                batch.append(row)
            psycopg2.extras.execute_batch(cur, sql, batch, page_size=BATCH_SIZE)
            total_props_updated += len(batch)
            total_fields_set    += len(batch) * len(fields_tuple)
        conn.commit()
        cur.close()
    else:
        for fields_tuple, id_updates in updates_by_fields.items():
            total_props_updated += len(id_updates)
            total_fields_set    += len(id_updates) * len(fields_tuple)

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("COMPLETE in %.1fs", elapsed)
    log.info("  Parcels needing enrichment : %d", n_start)
    log.info("  Parcels updated            : %d", total_props_updated)
    log.info("  Field values filled        : %d", total_fields_set)
    log.info("  Parcels with no sales data : %d", n_start - total_props_updated)

    if not dry_run:
        cur = conn.cursor()
        for col in ["living_area_sqft", "bedrooms", "year_built"]:
            cur.execute(f"SELECT COUNT(*) FROM properties WHERE county='polk' AND {col} IS NULL")
            log.info("  Still NULL %-20s: %d", col, cur.fetchone()[0])
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Enrich properties from sales CSV building data")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(args.dry_run)
