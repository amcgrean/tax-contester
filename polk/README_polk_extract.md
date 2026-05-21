# Polk County Data Extraction — Laptop Staging
Run these scripts anywhere Python 3.8+ is available. No database needed at this stage —
everything lands as flat NDJSON/HTML files you can move to the Pi later.

## Install deps (once)
```
pip install requests beautifulsoup4 lxml
```

## Step 1 — Atlas (parcel foundation)
```
python polk_atlas_extract.py
```
Runtime: ~2-4 min
Output:
  polk_data/atlas/layer4_parcel_attributes.ndjson  (~220K rows, addresses + owners)
  polk_data/atlas/layer3_parcel_polygons.ndjson    (~208K rows, parcel centroids)
  polk_data/atlas/layer0_unit_points.ndjson        (~12K rows, condo/apt points)

**Pull Layer 4 first** — it's the one that seeds the properties table.

## Step 2 — Assessor Sales (comp data)
```
python polk_assessor_sales_extract.py
```
Runtime: ~5-10 min (15 windows, 2018–present)
Output:
  polk_data/sales/sales_YYYY_HH.ndjson   one file per 6-month window
  polk_data/sales/sales_YYYY_HH_raw.html raw HTML snapshot per window (debug)

## Both scripts are resume-safe
If interrupted, re-run — completed files are skipped automatically.

## Watch for the 5000-row cap warning
If any sales window logs "⚠️ near/at 5000 cap", that window needs to be split into
3-month chunks. Edit build_windows() or just re-run with a smaller date range.

## Known issue: Vanguard migration
The general property search (generalform) is broken — "dp is not a base table" error.
Sales search is unaffected. The script will surface this error explicitly if it appears.

## Data volume estimate
Atlas:   ~270MB total NDJSON
Sales:   ~50-80MB total NDJSON (2018–present)

## After both scripts complete
All files go to:
  polk_data/
    atlas/
    sales/

Zip and move to Pi 5, then run the Postgres load scripts (next step).
