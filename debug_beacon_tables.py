"""
debug_beacon_tables.py
Run this to dump the exact table structure from a Beacon parcel page.
Usage: python3 debug_beacon_tables.py
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time, re

PROFILE_DIR = Path("./beacon_profile")
PROFILE_DIR.mkdir(exist_ok=True)

KEY_VALUE = "1225233013"  # 3405 146th St Urbandale

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900},
    )
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = context.new_page()

    # Warmup
    print("Loading search page...")
    page.goto("https://beacon.schneidercorp.com/Application.aspx?AppID=909&LayerID=17429&PageTypeID=2&PageID=7823",
              wait_until="domcontentloaded", timeout=30000)
    for _ in range(20):
        time.sleep(2)
        if 'moment' not in page.title().lower() and len(page.content()) > 5000:
            break
    page.evaluate("const b=document.querySelectorAll('.modal button');for(const x of b){if(x.textContent.trim().toLowerCase()==='agree'){x.click();break;}}")
    time.sleep(1)

    # Load parcel report
    print(f"Loading parcel {KEY_VALUE}...")
    page.goto(f"https://beacon.schneidercorp.com/Application.aspx?AppID=909&LayerID=17429&PageTypeID=4&PageID=7825&KeyValue={KEY_VALUE}",
              wait_until="domcontentloaded", timeout=30000)
    for _ in range(20):
        time.sleep(2)
        if 'moment' not in page.title().lower() and len(page.content()) > 5000:
            break
    page.evaluate("const b=document.querySelectorAll('.modal button');for(const x of b){if(x.textContent.trim().toLowerCase()==='agree'){x.click();break;}}")
    time.sleep(3)

    print(f"\nPage: {page.title()} ({len(page.content())} bytes)")

    tables = page.query_selector_all("table")
    print(f"\nTotal tables: {len(tables)}")

    for i, t in enumerate(tables):
        rows = t.query_selector_all("tr")
        if not rows:
            continue
        # Get header row
        first_row_cells = [c.inner_text().strip().replace('\n', ' ')[:40]
                           for c in rows[0].query_selector_all("td, th")]
        text_sample = t.inner_text()[:80].replace('\n', ' ')
        print(f"\n--- Table {i} ({len(rows)} rows) ---")
        print(f"  First row: {first_row_cells}")
        print(f"  Sample: {text_sample}")

        # Print all rows for tables that look interesting
        interesting = any(kw in t.inner_text().lower() for kw in
                          ['year built', 'assessed', 'sale', 'bedroom', 'bath',
                           'grade', 'sqft', 'area', 'style', 'seller', 'buyer'])
        if interesting:
            print(f"  *** INTERESTING TABLE ***")
            for j, row in enumerate(rows):
                cells = [c.inner_text().strip().replace('\n', ' ')[:50]
                         for c in row.query_selector_all("td, th")]
                print(f"    Row {j}: {cells}")

    context.close()
    print("\nDone.")
