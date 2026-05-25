# Agent Handoff — Iowa Property Tax Comp Engine

**Last updated:** 2026-05-21  
**Session summary:** Full stack built, Neon loaded, deployed to Vercel production.

---

## Current State — What Works

| Feature | Status | Notes |
|---|---|---|
| Flask SPA shell | LIVE | tax-contester.vercel.app |
| Search + autocomplete | LIVE | pg_trgm fuzzy, 180ms debounce |
| Parcel detail screen | LIVE | Assessment history, chart, YoY flag |
| Comp engine (Polk) | LIVE | 4-pass expansion, weighted scoring |
| Admin screen | LIVE | Real stats from Neon |
| Packet screen | PARTIAL | UI renders; PDF export returns 501 |
| Neon PostgreSQL | LIVE | 173K parcels, 381K sales, all indexes applied |
| Vercel production deploy | LIVE | Auto-deploys from GitHub `main` branch |
| Dallas County data | NOT STARTED | Scraper exists, never run |

---

## Verified Working in Production

Tested against https://tax-contester.vercel.app:

- `/api/autocomplete?q=maish` → 8 suggestions, fuzzy ranked ✓
- `/api/parcel/01004795950043` → 5604 MAISH AVE, $598,800, 2026 assessment ✓
- `/api/comps/01004795950043` → 6 comps, verdict FAIR (±5%), implied $631,870 ✓

---

## Immediate Next Tasks (Priority Order)

### 1. Fix branch workflow (5 min)
The repo has `master` as working branch but Vercel watches `main` for production.
**Fix:** Go to GitHub → Settings → Branches → change default branch to `main`.
Then locally: `git checkout -b main origin/main` won't be needed — just always push both:
```powershell
git push origin master main
```
Or better: just work on `main` going forward.

### 2. PDF Protest Packet — `/api/packet/<parcel_id>` (1–2 days)
Currently returns 501. This is the highest-value missing feature.

**Approach:** Use WeasyPrint (already in plan) to generate a PDF from an HTML template.

Install: add `weasyprint` to `requirements.txt`.

The packet should include:
- Cover page: property address, parcel ID, owner, assessment year
- Section 1: Subject property details (sqft, year built, beds/baths, assessed value)
- Section 2: Comp table (all comps with address, sale price, $/sqft, similarity score, why chosen)
- Section 3: Verdict + over-assessment amount
- Section 4: Protest argument template (boilerplate Iowa Board of Review language)
- Section 5: Iowa protest deadline reminder (Apr 2 – Apr 30)

**Vercel note:** WeasyPrint needs system libs (GTK/Pango). May not work on Vercel serverless.
Alternative: use `reportlab` (pure Python, no system deps) or generate HTML for browser print.
Simplest working version: return `Content-Type: text/html` with print-optimized CSS and `window.print()` on load.

### 3. Dallas County Data (2–4 hours)
The Beacon scraper at `dallas/dallas_beacon_scraper.py` exists but has never been run.

Steps:
1. Run scraper: `python dallas/dallas_beacon_scraper.py` (needs Selenium + Chrome)
2. Verify output schema matches `properties` + `assessments` tables
3. Load into Neon using same pattern as Polk loaders
4. Test a Dallas parcel through the comp engine

Dallas parcels use different neighborhood codes — comp engine should still work since
it falls back to tax_district then county-wide if neighborhood pool is thin.

### 4. YoY Flag Banner on Parcel Screen
The parcel API already returns `flagged: true` when assessment jumped >10% YoY.
The `screens.js` `renderParcel()` function needs to show a banner:
```
⚠ Assessment jumped +45.7% from 2024 → 2026. Strong protest candidate.
```
Check `parcelData.flagged` and `parcelData.yoy_pct` — both already in API response.

### 5. Map/Satellite View on Comps Screen
Each comp has `latitude`/`longitude` in the properties table (full coverage for Polk).
A simple Leaflet.js map showing subject (red pin) + comps (blue pins) would dramatically
improve the UI for protest prep. Add after PDF packet.

### 6. Protest Deadline Countdown
Iowa protest window: **April 2 – April 30** each year.
Add a banner on the Search screen when within 60 days of April 30 showing days remaining.
Simple JS date math, no backend needed.

---

## Architecture Decisions Already Made

- **No auth** — solo user tool, no login screen
- **No framework** — vanilla JS SPA, `window.__renderers` pattern
- **LATERAL joins everywhere** — never correlated subqueries (kills Neon performance)
- **Pooler for web, direct for comp engine** — `DATABASE_URL` vs `DATABASE_URL_UNPOOLED`
- **`to_float()` everywhere** — psycopg2 returns Decimal; all arithmetic must go through this
- **`ALWAYS_RENDER` set** — parcel/comps/packet re-render every nav; search/admin cache

---

## Key File Locations

| What | Where |
|---|---|
| All API routes | `web/app.py` |
| Comp algorithm | `comp_engine.py` — `run_comps()` |
| Frontend render functions | `web/static/screens.js` |
| Navigation / tab logic | `web/static/app.js` |
| DB schema | `setup_db.py` — `SCHEMA_SQL` constant |
| Neon indexes | `neon_indexes.sql` (already applied — don't re-run without IF NOT EXISTS) |
| Env vars | `.env` (local, gitignored) + Vercel dashboard |

---

## Test Parcels That Work

| Parcel ID | Address | Notes |
|---|---|---|
| `01004795950043` | 5604 MAISH AVE, DES MOINES | Good comps, verdict FAIR |
| Any on MAISH AVE | Various | Active new construction area, good comp pool |

Use `/api/autocomplete?q=<street>` to find more test parcels.

---

## Things NOT to Break

1. The LATERAL join pattern in `web/app.py` and `comp_engine.py` — correlated subqueries will time out on Vercel
2. `to_float()` wrapping all Decimal values before arithmetic
3. `ALWAYS_RENDER` set in `app.js` — removing it breaks parcel/comps navigation
4. `.env` must never be committed — it has live Neon credentials
5. `neon_indexes.sql` is gitignored (contains connection hints) — indexes are already applied to Neon

---

## Deployment Checklist (for any change)

```powershell
# 1. Test locally first
cd C:\Users\indha\python\taxes\web
python app.py
# → verify at http://localhost:5000

# 2. Commit
cd C:\Users\indha\python\taxes
git add web/app.py web/static/screens.js  # (specific files)
git commit -m "your message"

# 3. Push to both branches (main triggers Vercel production)
git push origin master main

# 4. Watch Vercel build (usually 45–90s)
# https://vercel.com/aarons-projects-bd143b6c/tax-contester

# 5. Verify production
# https://tax-contester.vercel.app/api/parcel/01004795950043
```
