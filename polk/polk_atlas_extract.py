"""
polk_atlas_extract.py
---------------------
Pulls all three Polk County Atlas FeatureServer layers to local NDJSON files.

Output (relative to script location):
  ./polk_data/atlas/layer0_unit_points.ndjson      ~12K rows  (condo/apt points)
  ./polk_data/atlas/layer3_parcel_polygons.ndjson  ~208K rows (parcel centroids)
  ./polk_data/atlas/layer4_parcel_attributes.ndjson ~220K rows (addresses + owners)

Runtime: ~2-4 minutes on a normal connection.
Resume-safe: if a layer file already exists and looks complete, it is skipped.

Usage:
  pip install requests
  python polk_atlas_extract.py
"""

import json
import os
import time
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL   = "https://atlas.polkcountyiowa.gov/server/Attribute_Query/FeatureServer"
PAGE_SIZE  = 2000
OUT_DIR    = "./polk_data/atlas"
LOG_FILE   = "./polk_data/atlas_extract.log"

LAYERS = [
    {
        "id": 4,
        "name": "layer4_parcel_attributes",
        "outFields": "Parcel_Number,HouseNo,PrimarySitus,AltSitus,MailingAddress,Owners",
        "returnGeometry": "false",
        "returnCentroid": "false",
        "description": "Parcel attributes + addresses (~220K rows)",
    },
    {
        "id": 3,
        "name": "layer3_parcel_polygons",
        "outFields": "Parcel_Number,HouseNo,Name",
        "returnGeometry": "true",
        "returnCentroid": "true",
        "description": "Parcel polygons + centroids (~208K rows)",
    },
    {
        "id": 0,
        "name": "layer0_unit_points",
        "outFields": "parcel_number,HouseNo,tax_parcel_point_type",
        "returnGeometry": "true",
        "returnCentroid": "false",
        "description": "Condo/apt unit points (~12K rows)",
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def fetch_page(layer_id, offset, params_extra):
    url = f"{BASE_URL}/{layer_id}/query"
    params = {
        "where":             "1=1",
        "outFields":         params_extra["outFields"],
        "resultOffset":      offset,
        "resultRecordCount": PAGE_SIZE,
        "returnGeometry":    params_extra["returnGeometry"],
        "returnCentroid":    params_extra["returnCentroid"],
        "outSR":             "4326",
        "f":                 "json",
        "orderByFields":     "OBJECTID ASC",
    }
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise ValueError(f"API error: {data['error']}")
            return data
        except Exception as e:
            wait = 2 ** attempt
            log(f"  Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Layer {layer_id} offset {offset} failed after 5 attempts")

def output_path(layer_name):
    return os.path.join(OUT_DIR, f"{layer_name}.ndjson")

def count_lines(path):
    try:
        with open(path) as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

# ── Main extract ──────────────────────────────────────────────────────────────
def extract_layer(layer):
    lid    = layer["id"]
    name   = layer["name"]
    desc   = layer["description"]
    path   = output_path(name)

    log(f"=== Layer {lid}: {desc} ===")

    # Check if already complete (has rows + no exceededTransferLimit on last probe)
    existing = count_lines(path)
    if existing > 1000:
        log(f"  File exists with {existing:,} rows — skipping (delete to re-pull)")
        return existing

    os.makedirs(OUT_DIR, exist_ok=True)
    total  = 0
    offset = 0

    with open(path, "w") as fout:
        while True:
            data     = fetch_page(lid, offset, layer)
            features = data.get("features", [])
            if not features:
                log(f"  No features returned at offset {offset} — done")
                break

            for feat in features:
                fout.write(json.dumps(feat) + "\n")

            total  += len(features)
            offset += len(features)

            exceeded = data.get("exceededTransferLimit", False)
            log(f"  offset={offset:>7,}  fetched={len(features):>5}  total={total:>7,}  more={exceeded}")

            if not exceeded:
                break

            time.sleep(0.1)  # gentle throttle

    log(f"  Layer {lid} complete: {total:,} rows -> {path}")
    return total

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    start = datetime.now()
    log(f"Polk Atlas extract started — {start.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Output directory: {os.path.abspath(OUT_DIR)}")

    totals = {}
    for i, layer in enumerate(LAYERS):
        n = extract_layer(layer)
        totals[layer["name"]] = n
        if i < len(LAYERS) - 1:
            log(f"  Pausing 10s before next layer...")
            time.sleep(10)

    elapsed = (datetime.now() - start).total_seconds()
    log(f"\n{'='*50}")
    log(f"COMPLETE in {elapsed:.0f}s")
    for name, n in totals.items():
        log(f"  {name}: {n:,} rows")
    log(f"Files in: {os.path.abspath(OUT_DIR)}")
if __name__ == "__main__":
    main()