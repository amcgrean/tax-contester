"""
polk_sales_download.py
----------------------
Downloads ALL Polk County residential sales CSVs (1990-2026) plus
the current residential inventory snapshot.

Output:
  ./polk_data/sales/{year}.csv        — 37 annual sales files
  ./polk_data/inventory/POLKCOUNTY.csv — current parcel inventory

Total: ~38 files, ~320MB

Usage:
  python polk_sales_download.py
"""

import os
import time
import requests
from datetime import datetime

SALES_BASE = "https://www.assess.co.polk.ia.us/info/web/exports/res/sales/polk"
INVEN_URL  = "https://www.assess.co.polk.ia.us/info/web/exports/res/inven/polk/POLKCOUNTY.csv"
SALES_DIR  = "./polk_data/sales"
INVEN_DIR  = "./polk_data/inventory"
YEARS      = list(range(1990, 2027))  # 1990 through 2026

os.makedirs(SALES_DIR, exist_ok=True)
os.makedirs(INVEN_DIR, exist_ok=True)

print(f"Polk County Full Download -- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Sales:     {os.path.abspath(SALES_DIR)}")
print(f"Inventory: {os.path.abspath(INVEN_DIR)}")
print()

def download_file(url, out_path, label):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        lines = sum(1 for _ in open(out_path, encoding="utf-8", errors="replace")) - 1
        print(f"  {label}: already on disk ({lines:,} rows) -- skipping")
        return lines
    print(f"  {label}: downloading...", end=" ", flush=True)
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(r.text)
        lines = r.text.count("\n") - 1
        size_kb = len(r.content) // 1024
        print(f"{lines:,} rows, {size_kb:,} KB")
        return lines
    except Exception as e:
        print(f"FAILED: {e}")
        return 0

# Sales 1990-2026
print(f"=== Sales files ({len(YEARS)} years) ===")
total_sales = 0
for year in YEARS:
    n = download_file(
        f"{SALES_BASE}/{year}.csv",
        os.path.join(SALES_DIR, f"{year}.csv"),
        str(year)
    )
    total_sales += n
    time.sleep(0.3)

# Inventory snapshot
print()
print("=== Inventory snapshot ===")
inven_rows = download_file(
    INVEN_URL,
    os.path.join(INVEN_DIR, "POLKCOUNTY.csv"),
    "POLKCOUNTY inventory"
)

# Summary
print()
print("=" * 50)
print(f"Sales rows total:     {total_sales:,}")
print(f"Inventory rows:       {inven_rows:,}")
print(f"Grand total rows:     {total_sales + inven_rows:,}")
print()
print("What you have:")
print("  Sales (1990-2026):  37 CSVs, 78 cols -- full transaction history")
print("  Inventory:           1 CSV, 134 cols  -- current state of all parcels")
print("  Atlas (already):     3 NDJSON files   -- addresses + geometry")