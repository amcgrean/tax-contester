# Iowa Property Tax Comp Engine — Agent Docs

> Quick-start for any AI agent picking up this project cold.
> Read this first. Then read HANDOFF.md for the current task list.

---

## What This Is

A full-stack property tax protest tool for Polk and Dallas counties, Iowa.
It pulls assessor CAMA data, finds comparable sales, and tells a homeowner
whether their property is over-assessed and by how much.

**Live URL:** https://tax-contester.vercel.app  
**GitHub:** https://github.com/amcgrean/tax-contester  
**Owner:** Aaron (amcgrean) — solo user, no auth needed

---

## Tech Stack

| Layer | What | Notes |
|---|---|---|
| Database | Neon (PostgreSQL) | 173K Polk parcels, 381K sales, 527K assessments |
| Backend | Flask (Python 3.12) | Serverless via `@vercel/python` |
| Frontend | Vanilla JS SPA | 5 screens, no framework |
| Hosting | Vercel Pro | 60s function timeout |
| Local dev | PostgreSQL 18 (Windows) | `iowa_propertytax` DB |

---

## Repository Layout

```
taxes/
├── api/
│   └── index.py              # Vercel entry point — imports web/app.py
├── web/
│   ├── app.py                # Flask app — all API routes
│   ├── templates/
│   │   └── index.html        # SPA shell (Jinja)
│   └── static/
│       ├── app.js            # Navigation, tab routing, ALWAYS_RENDER logic
│       ├── screens.js        # 5 render functions (Search/Parcel/Comps/Admin/Packet)
│       └── styles.css        # oklch design system
├── comp_engine.py            # Core comp algorithm — run_comps(parcel_id=...)
├── setup_db.py               # Schema creation (run once on fresh Postgres)
├── neon_indexes.sql          # Performance indexes (applied to Neon — don't re-run blindly)
├── polk/
│   ├── polk_inventory_load.py    # Loads Polk CAMA CSV → properties table
│   ├── polk_atlas_load.py        # Loads Atlas NDJSON lat/lon → properties
│   ├── polk_sales_load.py        # Loads Polk recorder sales CSVs → sales table
│   ├── polk_sales_enrich.py      # Arms-length flag, price-per-sqft calc
│   └── polk_assessor_sales_extract.py  # Pulls assessments from CAMA data
├── dallas/
│   └── dallas_beacon_scraper.py  # Beacon scraper (NOT YET RUN — Dallas data pending)
├── requirements.txt          # flask, psycopg2-binary, python-dotenv
├── vercel.json               # Vercel build + routing config
├── run_web.bat               # Local dev launcher (Windows)
├── AGENTS.md                 # This file
└── HANDOFF.md                # Current task state + next steps
```

---

## Environment Variables

Set in `.env` (local, gitignored) and in Vercel dashboard.

| Variable | Used By | What |
|---|---|---|
| `DATABASE_URL` | `web/app.py` | Neon pooler URL (PgBouncer) — for short web queries |
| `DATABASE_URL_UNPOOLED` | `comp_engine.py` | Neon direct connection — for multi-query comp sessions |
| `DB_HOST/DB_NAME/DB_USER/DB_PASS` | both | Local Postgres fallback |

**Connection logic:** both files try `DATABASE_URL[_UNPOOLED]` first, fall back to local env vars, then hardcoded local defaults. Never commit `.env`.

---

## Database Schema (Key Tables)

```sql
properties      -- one row per parcel (173K Polk, 0 Dallas currently)
  id, county, county_parcel_id, address_raw, city, zip,
  latitude, longitude, neighborhood_code, year_built,
  living_area_sqft, lot_sf, bedrooms, bathrooms, stories,
  bldg_style, property_class, owner_name, tax_district

assessments     -- one row per parcel per tax year (527K rows)
  id, property_id, tax_year, assessed_total, assessed_land,
  assessed_improvements, gross_taxes_due, net_taxes_due

sales           -- one row per recorded sale (381K rows)
  id, property_id, sale_date, sale_price, deed_type,
  arms_length_flag, price_per_sqft

ingestion_runs  -- audit log for data loads
  id, source_name, status, started_at, completed_at,
  rows_inserted, rows_updated, errors_json, notes
```

**Critical join pattern — always use LATERAL, never correlated subquery:**
```sql
-- GOOD (fast on Neon)
LEFT JOIN LATERAL (
    SELECT assessed_total, tax_year FROM assessments
    WHERE property_id = p.id ORDER BY tax_year DESC LIMIT 1
) a ON true

-- BAD (slow — scans assessments for every row)
LEFT JOIN assessments a ON a.tax_year = (SELECT MAX(...) WHERE property_id = p.id)
```

---

## Comp Engine (comp_engine.py)

```python
result = ce.run_comps(parcel_id="01004795950043")
# or
result = ce.run_comps(address="5604 Maish Ave")
```

**Algorithm:**
1. Look up subject property + latest assessment (LATERAL join)
2. Pull candidates: same county, sqft ±20%, age ±15 yrs, arms-length, last 24 months
3. Score each candidate: sqft 30% + recency 25% + neighborhood 15% + age 15% + distance 10% + lot 5%
4. If < 5 comps: auto-expand to 36-month window; then expand to county-wide
5. Implied value = median(price_per_sqft of top comps) × subject sqft
6. Verdict: OVER-ASSESSED if implied > assessed by >10%, UNDER-ASSESSED if <10% below, FAIR otherwise

**Result shape:**
```python
{
  "status": "ok",
  "subject": { ...property fields, assessed_total, living_area_sqft, ... },
  "comps": [ { ...sale fields, _score, _distance_miles, _why_chosen, ... }, ... ],
  "verdict": { "verdict": "OVER-ASSESSED"|"UNDER-ASSESSED"|"FAIR",
               "assessment_ratio": float, "implied_value": float,
               "assessed_total": float, "median_ppsf": float },
  "expansion_note": "same neighborhood, last 36 months (expanded window)" | None,
  "errors": []
}
```

---

## Flask API Endpoints (web/app.py)

| Method | Route | What |
|---|---|---|
| GET | `/` | SPA shell (index.html) |
| GET | `/api/autocomplete?q=&county=` | Fuzzy address typeahead (pg_trgm) |
| GET | `/api/search?q=&county=` | Full search results |
| GET | `/api/parcel/<parcel_id>` | Parcel detail + assessment history + chart |
| GET | `/api/comps/<parcel_id>` | Run comp engine, return verdict + comp table (includes `latitude`/`longitude` on each row) |
| GET | `/api/admin` | Stats, data source status, ingestion run log |
| GET | `/api/packet/<parcel_id>` | 2-page print-optimized HTML packet (auto-triggers browser print dialog) |

All routes except `/api/packet/` return JSON. `to_float()` helper converts psycopg2 `Decimal` → `float` everywhere before arithmetic.

`/api/packet/` runs `ce.run_comps()` server-side and renders `web/templates/packet.html` via Jinja. No separate parcel lookup needed — comp engine result has all required fields.

---

## Frontend (web/static/)

**app.js** — navigation shell:
- `window.__goto(name)` — switches active screen tab
- `ALWAYS_RENDER = Set(['parcel', 'comps', 'packet'])` — these re-render every nav (state-dependent)
- `RENDERED` set — other screens cached after first render

**screens.js** — render functions:
- `window.__state = { currentParcelId, parcelData, compsData }` — shared state
- `setState(patch)` — update state + trigger re-renders if needed
- Each screen fetches its own API endpoint and builds DOM from scratch
- Autocomplete: 180ms debounce, keyboard nav (↑↓ Enter Esc), `selectSuggestion()` → `__goto('parcel')`
- Comps screen: after `host.innerHTML` is set, `_initLeafletMap(rows)` is called to initialize the Leaflet map; requires Leaflet 1.9.4 (loaded via CDN in `index.html`)
- Search screen: protest deadline countdown banner rendered immediately via IIFE after `host.innerHTML`
- Packet screen (`renderPacket`): renders in-app draft from cached `compsData`/`parcelData`; the "Download PDF" button opens `/api/packet/<id>` in a new tab

**index.html** — SPA shell:
- Leaflet 1.9.4 CSS + JS loaded from unpkg CDN with SRI hashes — update hashes if bumping version

---

## Local Dev

```powershell
# Option A: batch file
cd C:\Users\indha\python\taxes
.\run_web.bat

# Option B: manual
cd C:\Users\indha\python\taxes\web
python app.py
# → http://localhost:5000
```

Local uses PostgreSQL 18 on Windows (`iowa_propertytax` DB, user: postgres, pass: iowa2026).

---

## Deploy Workflow

```powershell
cd C:\Users\indha\python\taxes
git add -A
git commit -m "your message"
git push origin master main   # push both — main triggers Vercel production
```

Vercel auto-deploys on push to `main`. The `master` branch builds as a preview only.

---

## Responsive / Mobile Layout

The site is fully responsive. Two breakpoints live at the **bottom of `styles.css`**:

- `@media (max-width: 768px)` — tablet: tabs scroll horizontally, grids collapse to 1 col, comp table scrolls, tweaks panel becomes a bottom sheet
- `@media (max-width: 480px)` — phone: comp table hides columns 5+ (`nth-child(n+5)`), all stat grids 1-col, paper cover single-col

Viewport meta in `index.html` is `width=device-width, initial-scale=1` (was previously locked to 1280 — don't revert this).

The `body.mobile-preview` class in styles.css is **separate** — it's a design-tool preview mode toggled by the tweaks panel. Don't confuse it with the real media queries.

---

## Known Gotchas

1. **Decimal arithmetic** — psycopg2 returns `decimal.Decimal` for `NUMERIC` columns. Always use `to_float(v)` before math. Never do `decimal_val * 0.019`.

2. **`stories` column** — stored as text ("1 Story", "2 Story") not a number. Pass through as string, don't `to_float()` it.

3. **ALWAYS_RENDER** — Parcel, Comps, and Packet screens must re-render on every navigation because they depend on `currentParcelId` state. If you add a new stateful screen, add it to this Set in `app.js`.

4. **Branch discipline** — Vercel production branch is `main`. Work on a feature branch, open a PR, merge to main. Vercel auto-deploys on merge.

5. **Neon pooler vs direct** — Web routes use `DATABASE_URL` (pooler/PgBouncer, good for short queries). Comp engine uses `DATABASE_URL_UNPOOLED` (direct, good for multi-step transactions). Don't swap them.

6. **Dallas data is empty** — `properties WHERE county = 'dallas'` returns 0 rows. Dallas Beacon scraper exists but has never been run against Neon.

7. **Leaflet CDN SRI hashes** — `index.html` loads Leaflet 1.9.4 with `integrity=` SRI hashes. If you bump the version, update both the CSS and JS hashes or the browser will block the scripts.

8. **Packet route returns HTML, not JSON** — `/api/packet/<id>` is the only route that returns `text/html`. Don't call it with `apiFetch()` (which expects JSON). The "Download PDF" button opens it in a new tab via `<a href=...>`, which is correct.
