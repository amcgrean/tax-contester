"""
polk_atlas_load.py
------------------
Enriches the properties table with precise lat/lon from the Atlas NDJSON layers.

Priority order (highest wins):
  1. Layer 0 — exact unit point geometry (condos/apt units, ~12K rows)
  2. Layer 3 — polygon centroid (regular parcels, ~208K rows)

Layer 3 only fills properties where lat/lon IS NULL — won't overwrite
inventory coords or Layer 0 points. Layer 0 always overwrites (unit points
are more precise than the StatePlane centroid from the inventory).

Join key:
  Layer 3 + Layer 0 Parcel_Number (12-digit gp) → properties.alternate_parcel_id

Usage:
  python polk_atlas_load.py
  python polk_atlas_load.py --dry-run
"""

import json
import os
import time
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
log = logging.getLogger("polk_atlas_load")

ATLAS_DIR      = Path(__file__).parent / "polk_data" / "atlas"
PARSER_VERSION = "v1.0.0"
BATCH_SIZE     = 2000

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host    =os.getenv("DB_HOST", "localhost"),
        port    =int(os.getenv("DB_PORT", 5432)),
        dbname  =os.getenv("DB_NAME", "iowa_propertytax"),
        user    =os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "iowa2026"),
    )

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_gp_map(conn) -> dict:
    """Load alternate_parcel_id (gp) → property id + current lat/lon."""
    log.info("Loading alternate_parcel_id map from DB...")
    cur = conn.cursor()
    cur.execute("""
        SELECT alternate_parcel_id, id, latitude, longitude
        FROM properties
        WHERE county='polk' AND alternate_parcel_id IS NOT NULL
    """)
    mapping = {row[0]: {"id": row[1], "lat": row[2], "lon": row[3]}
               for row in cur.fetchall()}
    cur.close()
    log.info("  Loaded %d alternate_parcel_id mappings", len(mapping))
    return mapping

def norm_parcel(s: str) -> str:
    return s.strip().upper() if s else ""

def read_ndjson(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def flush_updates(conn, updates: list, counts: dict):
    """Batch UPDATE lat/lon for a list of (lat, lon, property_id) tuples."""
    cur = conn.cursor()
    psycopg2.extras.execute_batch(
        cur,
        "UPDATE properties SET latitude=%s, longitude=%s, last_seen_at=NOW() WHERE id=%s",
        updates,
        page_size=BATCH_SIZE,
    )
    conn.commit()
    cur.close()
    counts["updated"] += len(updates)

# ── Layer loaders ─────────────────────────────────────────────────────────────

def load_layer0(path: Path, gp_map: dict, conn, dry_run: bool, counts: dict):
    """
    Layer 0 — unit points. Always update lat/lon (highest precision).
    parcel_number (lowercase) = 12-digit gp.
    geometry: {x: lon, y: lat}
    """
    log.info("Layer 0 (unit points): %s", path.name)
    updates = []
    for feat in read_ndjson(path):
        attrs = feat.get("attributes", {})
        geom  = feat.get("geometry", {})
        gp    = norm_parcel(attrs.get("parcel_number") or "")
        lat   = geom.get("y")
        lon   = geom.get("x")
        if not gp or lat is None or lon is None:
            counts["layer0_no_geom"] += 1
            continue
        # Sanity check — Iowa bounds
        if not (40.0 <= lat <= 44.0 and -97.5 <= lon <= -90.0):
            counts["layer0_bad_coords"] += 1
            continue
        entry = gp_map.get(gp)
        if entry is None:
            counts["layer0_no_match"] += 1
            continue
        if dry_run:
            counts["updated"] += 1
            continue
        updates.append((lat, lon, entry["id"]))
        if len(updates) >= BATCH_SIZE:
            flush_updates(conn, updates, counts)
            updates.clear()

    if updates and not dry_run:
        flush_updates(conn, updates, counts)

    log.info("  Layer 0 done: %d updated, %d no-match, %d no-geom",
             counts["updated"], counts["layer0_no_match"], counts["layer0_no_geom"])


def load_layer3(path: Path, gp_map: dict, conn, dry_run: bool, counts: dict):
    """
    Layer 3 — polygon centroids. Only fills lat/lon where currently NULL.
    Parcel_Number (capitalized) = 12-digit gp.
    centroid: {x: lon, y: lat}
    """
    log.info("Layer 3 (polygon centroids): %s", path.name)
    updates = []
    skipped_has_coords = 0

    for feat in read_ndjson(path):
        attrs    = feat.get("attributes", {})
        centroid = feat.get("centroid") or {}
        gp       = norm_parcel(attrs.get("Parcel_Number") or "")
        lat      = centroid.get("y")
        lon      = centroid.get("x")

        if not gp or lat is None or lon is None:
            counts["layer3_no_geom"] += 1
            continue
        if not (40.0 <= lat <= 44.0 and -97.5 <= lon <= -90.0):
            counts["layer3_bad_coords"] += 1
            continue

        entry = gp_map.get(gp)
        if entry is None:
            counts["layer3_no_match"] += 1
            continue

        # Only fill nulls — inventory + Layer 0 take priority
        if entry["lat"] is not None:
            skipped_has_coords += 1
            continue

        if dry_run:
            counts["layer3_filled"] += 1
            continue

        updates.append((lat, lon, entry["id"]))
        # Update the in-memory map so we don't count it twice
        entry["lat"] = lat
        entry["lon"] = lon

        if len(updates) >= BATCH_SIZE:
            flush_updates(conn, updates, counts)
            updates.clear()

    if updates and not dry_run:
        flush_updates(conn, updates, counts)

    counts["layer3_filled"] = counts.get("layer3_filled", 0) + (
        0 if dry_run else len(updates)
    )
    log.info("  Layer 3 done: %d null-fills, %d already had coords, %d no-match",
             counts.get("layer3_filled", 0), skipped_has_coords,
             counts["layer3_no_match"])


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool):
    log.info("polk_atlas_load starting | dry_run=%s", dry_run)

    conn   = get_db()
    gp_map = load_gp_map(conn)

    counts = {
        "updated": 0,
        "layer0_no_match": 0, "layer0_no_geom": 0, "layer0_bad_coords": 0,
        "layer3_no_match": 0, "layer3_no_geom": 0, "layer3_bad_coords": 0,
        "layer3_filled": 0,
    }

    t0 = time.time()

    # Layer 0 first (highest precision — always update)
    l0 = ATLAS_DIR / "layer0_unit_points.ndjson"
    if l0.exists():
        load_layer0(l0, gp_map, conn, dry_run, counts)
    else:
        log.warning("Layer 0 file not found: %s", l0)

    # Layer 3 (fill nulls only)
    l3 = ATLAS_DIR / "layer3_parcel_polygons.ndjson"
    if l3.exists():
        load_layer3(l3, gp_map, conn, dry_run, counts)
    else:
        log.warning("Layer 3 file not found: %s", l3)

    elapsed = time.time() - t0
    log.info("=" * 60)
    log.info("COMPLETE in %.1fs", elapsed)
    log.info("  Layer 0 unit updates : %d", counts["updated"])
    log.info("  Layer 3 null-fills   : %d", counts.get("layer3_filled", 0))

    if not dry_run:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM properties WHERE county='polk' AND latitude IS NULL")
        still_null = cur.fetchone()[0]
        log.info("  Properties still missing lat/lon: %d", still_null)
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Enrich properties lat/lon from Atlas NDJSON")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(args.dry_run)
