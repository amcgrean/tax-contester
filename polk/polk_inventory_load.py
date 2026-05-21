"""
polk_inventory_load.py
----------------------
Loads POLKCOUNTY.csv (173K rows, 134 cols) into the iowa_propertytax database.

Populates two tables in one pass:
  - properties   : one row per parcel (upsert on county + county_parcel_id)
  - assessments  : 2026 assessed values from land_full / bldg_full / total_full

Coordinate conversion:
  x/y columns are Iowa State Plane South (EPSG:3418, US survey feet).
  Converted to WGS84 lat/lon (EPSG:4326) via pyproj.

Usage:
  pip install psycopg2-binary pyproj python-dotenv
  python polk_inventory_load.py

  # Preview first 500 rows without writing to DB:
  python polk_inventory_load.py --dry-run

  # Use a different CSV:
  python polk_inventory_load.py --csv path/to/POLKCOUNTY.csv
"""

import csv
import os
import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras
from pyproj import Transformer

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
log = logging.getLogger("polk_inventory_load")

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CSV     = Path(__file__).parent / "polk_data" / "inventory" / "POLKCOUNTY.csv"
PARSER_VERSION  = "v1.0.0"
SOURCE_SYSTEM   = "polk_inventory"
ASSESSMENT_YEAR = 2026          # current assessed value year in the inventory snapshot
BATCH_SIZE      = 2000          # rows per executemany batch
LOG_EVERY       = 10_000        # progress log interval

# Iowa State Plane South (EPSG:3418, US survey feet) → WGS84 (EPSG:4326)
_transformer = Transformer.from_crs("EPSG:3418", "EPSG:4326", always_xy=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host    = os.getenv("DB_HOST", "localhost"),
        port    = int(os.getenv("DB_PORT", 5432)),
        dbname  = os.getenv("DB_NAME", "iowa_propertytax"),
        user    = os.getenv("DB_USER", "postgres"),
        password= os.getenv("DB_PASS", "iowa2026"),
    )

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

def convert_coords(x_str, y_str):
    """Convert StatePlane Iowa South (EPSG:3418 US ft) → (lon, lat) WGS84."""
    x = pfloat(x_str)
    y = pfloat(y_str)
    if x is None or y is None or x == 0 or y == 0:
        return None, None
    try:
        lon, lat = _transformer.transform(x, y)
        # Sanity-check: Iowa is roughly 40.4–43.5°N, 90.1–96.7°W
        if 40.0 <= lat <= 44.0 and -97.5 <= lon <= -90.0:
            return lat, lon
        return None, None
    except Exception:
        return None, None

def map_row(row: dict) -> tuple[dict, dict]:
    """
    Map one CSV row to (property_dict, assessment_dict).
    Returns (None, None) if the row has no parcel ID.
    """
    dp = pstr(row.get("dp"))
    if not dp:
        return None, None

    # Neighborhood code: "AM01" + "A " → "AM01/A"
    nbhd   = pstr(row.get("nbhd")) or ""
    pocket = (row.get("pocket") or "").strip()
    nbhd_code = f"{nbhd}/{pocket}" if nbhd and pocket else (nbhd or None)

    # Bathrooms: full baths + 0.5 per toilet room (half-bath)
    full_baths  = pfloat(row.get("bathrooms")) or 0
    toilet_rms  = pfloat(row.get("toilet_rooms")) or 0
    bathrooms   = (full_baths + 0.5 * toilet_rms) if (full_baths or toilet_rms) else None

    # Garage spaces — use basement garage capacity; fall back to 1 if attached area present
    garage = pint(row.get("bsmt_gar_capacity"))
    if not garage:
        att_area = pfloat(row.get("att_garage_area")) or 0
        if att_area > 0:
            garage = 1  # attached garage present, count unknown — record as 1+

    lat, lon = convert_coords(row.get("x"), row.get("y"))

    prop = {
        "county"             : "polk",
        "county_parcel_id"   : dp,
        "alternate_parcel_id": pstr(row.get("gp")),
        "address_raw"        : pstr(row.get("address_line1")),
        "city"               : pstr(row.get("city")),
        "state"              : pstr(row.get("state")) or "IA",
        "zip"                : pstr(row.get("zip")),
        "latitude"           : lat,
        "longitude"          : lon,
        "neighborhood_code"  : nbhd_code,
        "year_built"         : pint(row.get("year_built")),
        "living_area_sqft"   : pint(row.get("total_living_area")),
        "basement_sqft"      : pint(row.get("basement_area")),
        "lot_sf"             : pfloat(row.get("land_sf")),
        "lot_acres"          : pfloat(row.get("land_acres")),
        "bedrooms"           : pint(row.get("bedrooms")),
        "bathrooms"          : bathrooms,
        "garage_spaces"      : garage,
        "stories"            : pstr(row.get("residence_type")),
        "quality_grade"      : pstr(row.get("grade")),
        "condition_rating"   : pstr(row.get("condition")),
        "bldg_style"         : pstr(row.get("bldg_style")),
        "property_class"     : pstr(row.get("class_descr")),
        "tax_district"       : pstr(row.get("jurisdiction")),
        "school_district"    : pstr(row.get("school_district")),
        "owner_name"         : pstr(row.get("title_holder1")),
        "source_system"      : SOURCE_SYSTEM,
        "parser_version"     : PARSER_VERSION,
        "source_url"         : None,
    }

    asmt = {
        "tax_year"             : ASSESSMENT_YEAR,
        "assessed_land"        : pfloat(row.get("land_full")),
        "assessed_improvements": pfloat(row.get("bldg_full")),
        "assessed_total"       : pfloat(row.get("total_full")),
        "classification"       : pstr(row.get("class_descr")),
        "source_system"        : SOURCE_SYSTEM,
        "parser_version"       : PARSER_VERSION,
    }

    return prop, asmt


# ── DB upserts ────────────────────────────────────────────────────────────────

PROP_SQL = """
INSERT INTO properties (
    county, county_parcel_id, alternate_parcel_id,
    address_raw, city, state, zip,
    latitude, longitude, neighborhood_code,
    year_built, living_area_sqft, basement_sqft,
    lot_sf, lot_acres, bedrooms, bathrooms, garage_spaces,
    stories, quality_grade, condition_rating, bldg_style,
    property_class, tax_district, school_district,
    owner_name, source_system, parser_version, source_url,
    last_seen_at, created_at
) VALUES (
    %(county)s, %(county_parcel_id)s, %(alternate_parcel_id)s,
    %(address_raw)s, %(city)s, %(state)s, %(zip)s,
    %(latitude)s, %(longitude)s, %(neighborhood_code)s,
    %(year_built)s, %(living_area_sqft)s, %(basement_sqft)s,
    %(lot_sf)s, %(lot_acres)s, %(bedrooms)s, %(bathrooms)s, %(garage_spaces)s,
    %(stories)s, %(quality_grade)s, %(condition_rating)s, %(bldg_style)s,
    %(property_class)s, %(tax_district)s, %(school_district)s,
    %(owner_name)s, %(source_system)s, %(parser_version)s, %(source_url)s,
    NOW(), NOW()
)
ON CONFLICT (county, county_parcel_id) DO UPDATE SET
    alternate_parcel_id = EXCLUDED.alternate_parcel_id,
    address_raw         = COALESCE(EXCLUDED.address_raw,        properties.address_raw),
    city                = COALESCE(EXCLUDED.city,               properties.city),
    zip                 = COALESCE(EXCLUDED.zip,                properties.zip),
    latitude            = COALESCE(EXCLUDED.latitude,           properties.latitude),
    longitude           = COALESCE(EXCLUDED.longitude,          properties.longitude),
    neighborhood_code   = COALESCE(EXCLUDED.neighborhood_code,  properties.neighborhood_code),
    year_built          = COALESCE(EXCLUDED.year_built,         properties.year_built),
    living_area_sqft    = COALESCE(EXCLUDED.living_area_sqft,   properties.living_area_sqft),
    basement_sqft       = COALESCE(EXCLUDED.basement_sqft,      properties.basement_sqft),
    lot_sf              = COALESCE(EXCLUDED.lot_sf,             properties.lot_sf),
    lot_acres           = COALESCE(EXCLUDED.lot_acres,          properties.lot_acres),
    bedrooms            = COALESCE(EXCLUDED.bedrooms,           properties.bedrooms),
    bathrooms           = COALESCE(EXCLUDED.bathrooms,          properties.bathrooms),
    garage_spaces       = COALESCE(EXCLUDED.garage_spaces,      properties.garage_spaces),
    stories             = COALESCE(EXCLUDED.stories,            properties.stories),
    quality_grade       = COALESCE(EXCLUDED.quality_grade,      properties.quality_grade),
    condition_rating    = COALESCE(EXCLUDED.condition_rating,   properties.condition_rating),
    bldg_style          = COALESCE(EXCLUDED.bldg_style,         properties.bldg_style),
    property_class      = COALESCE(EXCLUDED.property_class,     properties.property_class),
    tax_district        = COALESCE(EXCLUDED.tax_district,       properties.tax_district),
    school_district     = COALESCE(EXCLUDED.school_district,    properties.school_district),
    owner_name          = COALESCE(EXCLUDED.owner_name,         properties.owner_name),
    parser_version      = EXCLUDED.parser_version,
    last_seen_at        = NOW()
RETURNING id
"""

ASMT_SQL = """
INSERT INTO assessments (
    property_id, tax_year,
    assessed_land, assessed_improvements, assessed_total,
    classification, source_system, parser_version, extracted_at
) VALUES (
    %(property_id)s, %(tax_year)s,
    %(assessed_land)s, %(assessed_improvements)s, %(assessed_total)s,
    %(classification)s, %(source_system)s, %(parser_version)s, NOW()
)
ON CONFLICT (property_id, tax_year) DO UPDATE SET
    assessed_land         = COALESCE(EXCLUDED.assessed_land,         assessments.assessed_land),
    assessed_improvements = COALESCE(EXCLUDED.assessed_improvements, assessments.assessed_improvements),
    assessed_total        = COALESCE(EXCLUDED.assessed_total,        assessments.assessed_total),
    classification        = COALESCE(EXCLUDED.classification,        assessments.classification),
    extracted_at          = NOW()
"""


def flush_batch(conn, prop_batch, asmt_batch, counts):
    """Write one batch of properties + assessments, update counts in-place."""
    cur = conn.cursor()

    # Insert properties, collect returned IDs
    psycopg2.extras.execute_batch(cur, PROP_SQL, prop_batch, page_size=BATCH_SIZE)
    # Re-fetch IDs for the batch (execute_batch doesn't return rows easily)
    # Use a follow-up lookup by county_parcel_id
    dps = [p["county_parcel_id"] for p in prop_batch]
    cur.execute(
        "SELECT county_parcel_id, id FROM properties WHERE county='polk' AND county_parcel_id = ANY(%s)",
        (dps,)
    )
    id_map = {row[0]: row[1] for row in cur.fetchall()}

    counts["props"] += len(prop_batch)

    # Insert assessments
    asmt_rows = []
    for p, a in zip(prop_batch, asmt_batch):
        pid = id_map.get(p["county_parcel_id"])
        if pid and any(a.get(k) for k in ["assessed_land", "assessed_total"]):
            asmt_rows.append({**a, "property_id": pid})

    if asmt_rows:
        psycopg2.extras.execute_batch(cur, ASMT_SQL, asmt_rows, page_size=BATCH_SIZE)
        counts["asmts"] += len(asmt_rows)

    conn.commit()
    cur.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main(csv_path: Path, dry_run: bool):
    log.info("polk_inventory_load starting")
    log.info("CSV:     %s", csv_path)
    log.info("DB:      %s@%s/%s", os.getenv("DB_USER","postgres"),
             os.getenv("DB_HOST","localhost"), os.getenv("DB_NAME","iowa_propertytax"))
    log.info("Dry run: %s", dry_run)

    conn = None if dry_run else get_db()

    counts   = {"props": 0, "asmts": 0, "skipped": 0, "errors": 0}
    prop_batch: list[dict] = []
    asmt_batch: list[dict] = []
    t0 = time.time()

    with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            try:
                prop, asmt = map_row(row)
                if prop is None:
                    counts["skipped"] += 1
                    continue

                if dry_run:
                    if i < 5:
                        log.info("DRY RUN row %d: %s  lat=%s lon=%s",
                                 i, prop["county_parcel_id"],
                                 prop["latitude"], prop["longitude"])
                    counts["props"] += 1
                    continue

                prop_batch.append(prop)
                asmt_batch.append(asmt)

                if len(prop_batch) >= BATCH_SIZE:
                    flush_batch(conn, prop_batch, asmt_batch, counts)
                    prop_batch.clear()
                    asmt_batch.clear()

            except Exception as e:
                log.warning("Row %d error: %s", i, e)
                counts["errors"] += 1

            if (i + 1) % LOG_EVERY == 0:
                elapsed = time.time() - t0
                rate    = (i + 1) / elapsed
                log.info("  %7d rows processed | props=%d asmts=%d skipped=%d errors=%d | %.0f rows/s",
                         i + 1, counts["props"], counts["asmts"],
                         counts["skipped"], counts["errors"], rate)

    # Flush remainder
    if prop_batch and not dry_run:
        flush_batch(conn, prop_batch, asmt_batch, counts)

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("COMPLETE in %.1fs", elapsed)
    log.info("  Properties upserted : %d", counts["props"])
    log.info("  Assessments upserted: %d", counts["asmts"])
    log.info("  Rows skipped        : %d", counts["skipped"])
    log.info("  Errors              : %d", counts["errors"])

    if conn:
        # Final row counts
        cur = conn.cursor()
        for t in ("properties", "assessments"):
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            log.info("  DB %s: %s rows", t, f"{cur.fetchone()[0]:,}")
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load POLKCOUNTY.csv into iowa_propertytax DB")
    ap.add_argument("--csv",     default=str(DEFAULT_CSV), help="Path to POLKCOUNTY.csv")
    ap.add_argument("--dry-run", action="store_true",      help="Parse only, no DB writes")
    args = ap.parse_args()

    main(Path(args.csv), args.dry_run)
