# Agent Handoff — Iowa Property Tax Comp Engine

**Last updated:** 2026-06-04  
**Session summary:** All three Phase 1 marketing skills run end-to-end (PR #5, merged). `marketing/positioning.md`, `marketing/landing/homepage.md`, and all five Tier 1 SEO briefs now exist. SEO briefs have placeholder data hooks — Neon queries are written but couldn't run from the cloud agent (port 5432 blocked). Aaron needs to run the combined query in `marketing/seo/_HUB_INDEX.md` locally and update the briefs. Homepage copy changes are spec'd in `marketing/landing/homepage.md` but not yet implemented in `screens.js`/`index.html`.

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
| Marketing-director agent | LIVE | `.claude/agents/marketing-director.md` + 3 skills |
| Marketing BRAND.md | LIVE | `marketing/BRAND.md` — source of truth; review before generating artifacts |
| marketing/positioning.md | LIVE | Full Dunford 5-step positioning; value prop, pillars, anti-positioning |
| marketing/landing/homepage.md | LIVE (spec) | Mode A critique + Mode B hero variants; implementation checklist for screens.js + index.html — NOT YET CODED |
| marketing/seo/ (Tier 1) | LIVE (spec) | polk-county, des-moines, ankeny, urbandale, west-des-moines, waukee briefs + _HUB_INDEX.md — data hooks need real numbers from Neon |
| Dallas County data | NOT STARTED | Scraper exists, never run against Neon |

---

## Verified Working in Production

Tested against https://tax-contester.vercel.app:

- `/api/autocomplete?q=maish` → 8 suggestions, fuzzy ranked ✓
- `/api/parcel/01004795950043` → 5604 MAISH AVE, $598,800, 2026 assessment ✓
- `/api/comps/01004795950043` → 6 comps, verdict FAIR (±5%), implied $631,870 ✓
- `/api/packet/01004795950043` → 2-page HTML, auto-prints, comp table + §441.37 argument ✓

---

## What Changed in the 2026-05-26 Session

Shipped PR #3 — marketing-director agent + 3 sub-skills. **Config only,
no code, no DB, no deploy impact.** Adds two new top-level directories:

**`marketing/`** (artifacts directory)
- `BRAND.md` — single source of truth: product facts, ICP (DIY homeowners
  in Polk + Dallas), pricing (free, no monetization), voice rules,
  Iowa property tax calendar
- `README.md` — how to invoke the agent
- `landing/` and `seo/` — empty subdirs, will hold generated briefs

**`.claude/agents/marketing-director.md`** — router agent
- Loads `marketing/BRAND.md` first on every invocation
- Has a routing table mapping user request → sub-skill
- Enforces the voice contract from BRAND.md on every output
- Composes multi-step campaigns in dependency order
  (positioning → landing → SEO → email → ads)

**`.claude/skills/mkt-positioning/`** — April Dunford framework
- `SKILL.md` runs the 5-step Dunford process explicitly
- `KNOWLEDGE.md` carries the curated frameworks (Dunford, JTBD,
  messaging hierarchy, anti-positioning)
- `EXAMPLES.md` has Iowa-specific phrasings + good/bad value-prop
  teardowns
- `OUTPUT_TEMPLATE.md` defines `marketing/positioning.md` shape

**`.claude/skills/mkt-landing-page/`** — Wiebe / Dry CRO frameworks
- Produces 2 hero variants per page (audience+specificity, deadline+loss)
- Quality bar rejects "leverage", "AI-powered", generic stock heroes
- Ends every brief with concrete edits to `web/templates/index.html`

**`.claude/skills/mkt-local-seo/`** — programmatic county/city pages
- Intent classification (Action / Info / Navigation / Diagnostic / News)
- Priority page roster for Polk (11 cities) + Dallas (5–6 cities)
- Honest treatment of Dallas (comp engine not loaded — page ships with
  "notify me when Dallas launches" callout, never fakes the engine)
- Schema.org templates (Service + FAQPage + BreadcrumbList)

### Marketing — what's NOT done yet

- No actual marketing artifacts generated. The agent is scaffolded but
  hasn't been run end-to-end. The expected first run is `mkt-positioning`
  → produces `marketing/positioning.md`.
- Phase 2 skills (`mkt-lifecycle-email`, `mkt-ads-copy`) and Phase 3
  skills (`mkt-onboarding-audit`, `mkt-analytics`) are referenced in the
  router but not built.
- No analytics installed on the live site — `mkt-analytics` will need a
  first pass before that skill is useful.

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

## Remaining Tasks — Next Moves

### Marketing (highest leverage — site has ~0 traffic today)

**Move 1 — DONE:** BRAND.md reviewed; positioning.md produced.

**Move 2 — DONE:** `mkt-landing-page` critique + hero variants in
`marketing/landing/homepage.md`. Open questions for Aaron:
- Pick Variant A (audience+specificity) or B (deadline+loss) as default hero
- Confirm brand name change: "Iowa Property Tax Comp Engine" → "Tax Contester" in topbar
- Decide: hide the Admin tab from public nav?
- Packet screenshot: use live `/api/packet/01004795950043` or sanitize?

**Move 3 — IMPLEMENT the homepage changes:**
All edits are spec'd in `marketing/landing/homepage.md` (implementation checklist).
Key changes in `web/static/screens.js` `renderSearch()`:
- H1: "Is your Polk County assessment too high?"
- Lede: "Check it against 381,000 real Polk & Dallas County sales..."
- CTA: "Check my assessment" (not "Search")
- Trust strip below CTA: "173,000 parcels · 381,000 sales · Iowa Code §441.37 · Free"
And in `web/templates/index.html`: update `<title>`, `<meta description>`,
`.brand-title`, `.brand-sub`.

**Move 4 — Fill SEO data hooks:**
Run the combined query in `marketing/seo/_HUB_INDEX.md` against Neon
(port 5432 is blocked from the cloud agent — must run locally or from
Neon console). Paste results back to the agent to update all six briefs.

**Move 5 — Implement SEO pages:**
Flask routes + `web/templates/city.html` template. Each city brief
has the full spec. Publish order: `/polk-county` first, then all
Tier 1 city pages simultaneously.

**Move 6 (separate PR):** Scaffold Phase 2 skills — `mkt-lifecycle-email`
(April seasonal sequences) and `mkt-ads-copy` (Google/Meta).

### Product

## Dallas County Data

This is the only product item left on the original game plan.

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
| Marketing source of truth | `marketing/BRAND.md` |
| Marketing director agent | `.claude/agents/marketing-director.md` |
| Marketing skills | `.claude/skills/mkt-*/` (positioning, landing-page, local-seo) |
| Marketing artifacts (generated) | `marketing/positioning.md`, `marketing/landing/`, `marketing/seo/` |

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
8. `marketing/BRAND.md` is the spine — don't let downstream marketing artifacts drift from it. If a product fact changes, update BRAND.md FIRST, then re-run skills in dependency order (positioning → landing → SEO).

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
