# Agent Handoff — Iowa Property Tax Comp Engine

**Last updated:** 2026-05-25  
**Session summary:** Protest packet, Leaflet comp map, and deadline countdown shipped to main. Dallas County data is the only remaining task.

---

## Current State — What Works

| Feature | Status | Notes |
|---|---|---|
| Flask SPA shell | LIVE | tax-contester.vercel.app |
| Search + autocomplete | LIVE | pg_trgm fuzzy, 180ms debounce |
| Parcel detail screen | LIVE | Assessment history, SVG chart, YoY flag banner |
| Comp engine (Polk) | LIVE | 4-pass expansion, weighted scoring |
| Admin screen | LIVE | Real stats from Neon |
| Protest packet | LIVE | `/api/packet/<id>` returns 2-page print HTML; auto-triggers browser Print dialog |
| Leaflet comp map | LIVE | Real OSM map on Comps screen; subject (navy) + comp pins (blue) with popups |
| Protest deadline countdown | LIVE | Banner on Search screen — active Apr 2–30, heads-up 60 days prior |
| YoY flag banner | LIVE | Shows on Parcel screen when assessment jumped >10% YoY |
| Neon PostgreSQL | LIVE | 173K parcels, 381K sales, all indexes applied |
| Vercel production deploy | LIVE | Auto-deploys from GitHub `main` branch |
| Mobile / responsive UI | LIVE | Tablet ≤768px + phone ≤480px breakpoints in styles.css |
| Dallas County data | NOT STARTED | Scraper exists, never run against Neon |

---

## Verified Working in Production

Tested against https://tax-contester.vercel.app:

- `/api/autocomplete?q=maish` → 8 suggestions, fuzzy ranked ✓
- `/api/parcel/01004795950043` → 5604 MAISH AVE, $598,800, 2026 assessment ✓
- `/api/comps/01004795950043` → 6 comps, verdict FAIR (±5%), implied $631,870 ✓
- `/api/packet/01004795950043` → 2-page HTML, auto-prints, comp table + §441.37 argument ✓

---

## What Changed in the 2026-05-25 Session

Four files changed, zero DB migrations needed.

**`web/app.py`**
- `shape_comp()` now includes `latitude` / `longitude` on each comp row
- Subject row in `api_comps` also exposes `latitude` / `longitude`
- Replaced 501 stub: `api_packet()` now runs `ce.run_comps()`, formats all data, renders `packet.html`

**`web/templates/packet.html`** _(new file)_
- Self-contained print-optimized Jinja template; no external CSS/JS dependencies
- Page 1: property metadata grid, verdict box (red/green/blue by verdict), comp table, footnotes
- Page 2: Iowa Code §441.37 argument, relief requested, methodology, signature block
- `window.onload = () => window.print()` auto-triggers browser print dialog
- Screen-only hint banner explains "Save as PDF" if user lands on it directly
- WeasyPrint is NOT used — it requires GTK/Pango libs unavailable on Vercel

**`web/static/screens.js`**
- Removed fake CSS scatter map (hardcoded road/pin divs with random positions)
- Added `<div id="leaflet-map">` in comp layout + `_initLeafletMap(rows)` called after render
- Leaflet: subject navy pin, comp blue pins, popups with address/price/similarity, `fitBounds`
- Gracefully hides map div if subject has no lat/lon
- Added `#deadline-banner` slot at top of Search screen layout
- Countdown logic: shows urgent banner during Apr 2–30 window; softer heads-up in 60-day lead-in

**`web/templates/index.html`**
- Added Leaflet 1.9.4 CSS + JS (unpkg CDN, SRI hashes) in `<head>`

---

## Remaining Task — Dallas County Data

This is the only item left on the original game plan.

**What exists:** `dallas/dallas_beacon_scraper.py` — a Beacon scraper that hasn't been run.  
**What's needed:** scrape Dallas County parcels → load into Neon → test comp engine against a Dallas parcel.

**Steps (must run locally — needs Selenium + Chrome):**

1. `cd dallas && python dallas_beacon_scraper.py`  
   Outputs rows to stdout or a file — check the script for its output format.

2. Verify the output columns map to the `properties` and `assessments` tables (see schema below).  
   The key columns needed: `county_parcel_id`, `address_raw`, `city`, `zip`, `year_built`,  
   `living_area_sqft`, `lot_sf`, `bedrooms`, `bathrooms`, `bldg_style`, `property_class`,  
   `owner_name`, `neighborhood_code`, `tax_district`, `latitude`, `longitude`.

3. Load into Neon using the Polk loader as a template (`polk/polk_inventory_load.py`).  
   Set `county = 'dallas'` on every inserted row. Use `DATABASE_URL_UNPOOLED` (direct connection).

4. Load assessments into the `assessments` table the same way.

5. After load, run on Neon:
   ```sql
   ANALYZE properties;
   ANALYZE assessments;
   ```

6. Test: `/api/autocomplete?q=<dallas+street>` should return Dallas results.  
   Then: `/api/parcel/<dallas_parcel_id>` and `/api/comps/<dallas_parcel_id>`.

**Expected comp engine behavior for Dallas:**  
Dallas neighborhood codes differ from Polk. The engine auto-expands: same neighborhood → tax_district → county-wide. It will fall back cleanly without code changes. Comps will be thinner until more sales data is loaded.

**Lat/lon for Dallas:**  
If the Beacon scraper doesn't return coordinates, run the Atlas geocoder script (`polk/polk_atlas_load.py`) adapted for Dallas addresses, or geocode via the county GIS layer. Leaflet map on Comps screen will hide gracefully if lat/lon is missing.

---

## Architecture Decisions Already Made

- **No auth** — solo user tool, no login screen
- **No framework** — vanilla JS SPA, `window.__renderers` pattern
- **LATERAL joins everywhere** — never correlated subqueries (kills Neon pooler performance)
- **Pooler for web, direct for comp engine** — `DATABASE_URL` vs `DATABASE_URL_UNPOOLED`
- **`to_float()` everywhere** — psycopg2 returns Decimal; all arithmetic must go through this helper
- **`ALWAYS_RENDER` set** — parcel/comps/packet re-render every nav; search/admin cache after first render
- **Mobile breakpoints additive** — media queries appended at end of styles.css, don't reorganize the file
- **Packet = print HTML, not PDF** — WeasyPrint needs GTK; browser print to PDF works on Vercel with zero deps
- **Leaflet 1.9.4 via unpkg CDN** — SRI hashes pinned in index.html; don't upgrade without updating hashes

---

## Key File Locations

| What | Where |
|---|---|
| All API routes | `web/app.py` |
| Comp algorithm | `comp_engine.py` — `run_comps()` |
| Protest packet template | `web/templates/packet.html` |
| Frontend render functions | `web/static/screens.js` |
| Navigation / tab logic | `web/static/app.js` |
| All styles incl. mobile | `web/static/styles.css` — mobile queries at bottom |
| SPA shell template | `web/templates/index.html` — Leaflet CDN in head |
| DB schema | `setup_db.py` — `SCHEMA_SQL` constant |
| Neon indexes | `neon_indexes.sql` (already applied — don't re-run without checking IF NOT EXISTS) |
| Dallas scraper | `dallas/dallas_beacon_scraper.py` |
| Polk loaders (use as template) | `polk/polk_inventory_load.py`, `polk/polk_sales_load.py` |
| Env vars | `.env` (local, gitignored) + Vercel dashboard |

---

## Test Parcels That Work

| Parcel ID | Address | Notes |
|---|---|---|
| `01004795950043` | 5604 MAISH AVE, DES MOINES | Good comps, verdict FAIR |
| Any on MAISH AVE | Various | Active new construction neighborhood, good comp pool |

Use `/api/autocomplete?q=<street>` to find more. All 173K Polk parcels searchable.

---

## Things NOT to Break

1. LATERAL join pattern in `web/app.py` + `comp_engine.py` — correlated subqueries time out on Vercel
2. `to_float()` wrapping all Decimal values before arithmetic
3. `ALWAYS_RENDER` set in `app.js` — removing it breaks parcel/comps navigation after state changes
4. `.env` must never be committed — contains live Neon credentials
5. `neon_indexes.sql` is gitignored — indexes already applied to Neon, don't drop/recreate blindly
6. The existing `body.mobile-preview` CSS block in styles.css is the tweaks-panel preview mode — distinct from the real `@media` breakpoints, don't conflate them
7. Leaflet SRI hashes in `index.html` — if you bump the Leaflet version, update both hashes

---

## Deployment

Vercel auto-deploys on push to `main`. Work on a feature branch, open a PR, merge to main.

```bash
git checkout -b your-branch
git add web/app.py web/static/screens.js   # specific files — never git add -A (.env is in tree)
git commit -m "your message"
git push -u origin your-branch
# → open PR → merge → Vercel deploys automatically (~60s)
```

Verify production after deploy:
```
https://tax-contester.vercel.app/api/parcel/01004795950043
https://tax-contester.vercel.app/api/packet/01004795950043
```
