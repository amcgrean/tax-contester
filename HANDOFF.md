# Agent Handoff — Iowa Property Tax Comp Engine

**Last updated:** 2026-05-24  
**Session summary:** Full stack live on Vercel + Neon. Mobile-responsive CSS merged.

---

## Current State — What Works

| Feature | Status | Notes |
|---|---|---|
| Flask SPA shell | LIVE | tax-contester.vercel.app |
| Search + autocomplete | LIVE | pg_trgm fuzzy, 180ms debounce |
| Parcel detail screen | LIVE | Assessment history, SVG chart, YoY flag |
| Comp engine (Polk) | LIVE | 4-pass expansion, weighted scoring |
| Admin screen | LIVE | Real stats from Neon |
| Packet screen | PARTIAL | UI renders draft text; PDF export returns 501 |
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

---

## Mobile-Friendly Work — What Changed

Two files only. Zero backend impact.

**`web/templates/index.html`** — one line:
```html
<!-- before -->
<meta name="viewport" content="width=1280" />
<!-- after -->
<meta name="viewport" content="width=device-width, initial-scale=1" />
```
This unlocked responsive layout on phones/tablets (previously the browser was forced to render at 1280px).

**`web/static/styles.css`** — 247 lines of media queries appended at end of file:
- `@media (max-width: 768px)` — tablet breakpoint:
  - Topbar: wraps to 2 rows, tabs scroll horizontally
  - Search: single-column grid, touch-sized buttons (44px min)
  - Parcel: single-column card grid
  - Comps: stacked layout, comp table scrolls horizontally (min-width 700px), map 240px tall
  - Admin: single-column grid
  - Packet: sidebar becomes horizontal pill scroll, paper loses fixed width
  - Tweaks panel: becomes bottom sheet (left/right 12px, max-height 60vh)
- `@media (max-width: 480px)` — phone-only:
  - Comp table hides columns 5+ (`nth-child(n+5)`) to fit narrow screens
  - Stats grids collapse to 1 column
  - Paper cover layout goes single-column

**No changes to:** `app.js`, `screens.js`, `web/app.py`, `comp_engine.py`, any SQL, any API routes.  
The existing `body.mobile-preview` CSS class (used by the tweaks panel) already existed and is unchanged — the new media queries are additive.

---

## Immediate Next Tasks (Priority Order)

### 1. PDF Protest Packet — `/api/packet/<parcel_id>`
Currently returns 501. The UI on the Packet screen already renders a full draft — just needs an actual downloadable PDF.

**Recommended approach — browser-print HTML (no system deps, works on Vercel):**

In `web/app.py`, replace the 501 stub with a route that:
1. Calls `ce.run_comps(parcel_id=parcel_id)` + `query("SELECT * FROM properties WHERE ...")`
2. Renders a Jinja template `web/templates/packet.html` with print-optimized CSS
3. Returns `Content-Type: text/html`

The template should open with `<script>window.onload = () => window.print()</script>` so it auto-opens the browser print dialog.

Packet content:
- Cover: property address, parcel ID, owner, assessment year, "Prepared for Iowa Board of Review"
- Subject details: sqft, year built, beds/baths, assessed value, estimated taxes
- Comp table: address, sale date, sale price, $/sqft, similarity %, distance, why chosen
- Verdict: over-assessment amount in dollars + percentage
- Protest argument boilerplate (Iowa Code §441.37 language)
- Deadline reminder: Apr 2 – Apr 30

Add a print stylesheet to `styles.css` (the `@media print` block already hides topbar/tabs/tweaks — extend it to format the packet nicely).

If PDF is preferred: `reportlab` (pure Python, no GTK) works on Vercel. WeasyPrint does NOT — it needs GTK/Pango system libs that aren't available in the Vercel Python runtime.

### 2. YoY Flag Banner on Parcel Screen
The API already returns `flagged: true` and `yoy_pct` when assessment jumped >10% YoY.
In `web/static/screens.js` → `renderParcel()`, after the parcel head section, insert:

```javascript
if (d.flagged) {
  html += `<div class="banner banner--warn">
    <span class="b-icon">⚠</span>
    <div class="b-body">
      <strong>Large assessment jump detected.</strong>
      Assessment rose ${d.yoy_pct} (${d.yoy_amt_fmt}) from ${d.prev_year} → ${d.assessment_year}.
      Run comps to see if a protest is warranted.
    </div>
    <div class="b-actions"><button class="btn btn-sm" onclick="window.__goto('comps')">Run Comps →</button></div>
  </div>`;
}
```

### 3. Dallas County Data
The Beacon scraper at `dallas/dallas_beacon_scraper.py` exists but has never been run against Neon.

Steps:
1. Run scraper locally: `python dallas/dallas_beacon_scraper.py` (needs Selenium + Chrome)
2. Verify output schema matches `properties` + `assessments` tables
3. Load into Neon using same pattern as Polk loaders (see `polk/polk_inventory_load.py`)
4. Run `ANALYZE properties;` on Neon after load
5. Test a Dallas parcel: `/api/parcel/<dallas_parcel_id>`

Dallas uses different neighborhood codes — comp engine will fall back through tax_district → county-wide if neighborhood pool is thin. Should work without engine changes.

### 4. Leaflet Comp Map
Each comp has `latitude`/`longitude` in Neon (full Polk coverage). A map on the Comps screen would be high value for visual review.

In `screens.js` → `renderComps()`:
- Load Leaflet via CDN in `index.html` head
- Add a `<div id="comp-map" style="height:300px">` to the comps layout
- After render, `L.map('comp-map')`, plot subject as red marker, each comp as blue marker with popup showing address + sale price
- Coordinates are on comp objects as `latitude`/`longitude` — need to expose them from `/api/comps/<id>` response (currently not included, need to add to `shape_comp()` in `web/app.py`)

### 5. Protest Deadline Countdown
Iowa window: **April 2 – April 30** each year. No backend needed.

In `screens.js` → `renderSearch()`, add at top of rendered HTML:
```javascript
const now = new Date();
const deadline = new Date(now.getFullYear(), 3, 30); // April 30
const daysLeft = Math.ceil((deadline - now) / 86400000);
if (daysLeft > 0 && daysLeft <= 60) {
  // show banner: "X days until protest deadline (April 30)"
}
```

---

## Branch Workflow

```powershell
# For any change — push master for preview, push to main for production
git push origin master        # preview deploy
git push origin master:main --force   # production deploy (Vercel watches main)
```

To simplify: go to GitHub → Settings → Branches → change default branch to `main`,
then always work and push to `main` directly.

---

## Architecture Decisions Already Made

- **No auth** — solo user tool, no login screen
- **No framework** — vanilla JS SPA, `window.__renderers` pattern
- **LATERAL joins everywhere** — never correlated subqueries (kills Neon pooler performance)
- **Pooler for web, direct for comp engine** — `DATABASE_URL` vs `DATABASE_URL_UNPOOLED`
- **`to_float()` everywhere** — psycopg2 returns Decimal; all arithmetic must go through this helper
- **`ALWAYS_RENDER` set** — parcel/comps/packet re-render every nav; search/admin cache after first render
- **Mobile breakpoints additive** — media queries appended at end of styles.css, don't reorganize the file

---

## Key File Locations

| What | Where |
|---|---|
| All API routes | `web/app.py` |
| Comp algorithm | `comp_engine.py` — `run_comps()` |
| Frontend render functions | `web/static/screens.js` |
| Navigation / tab logic | `web/static/app.js` |
| All styles incl. mobile | `web/static/styles.css` — mobile queries at bottom |
| SPA shell template | `web/templates/index.html` |
| DB schema | `setup_db.py` — `SCHEMA_SQL` constant |
| Neon indexes | `neon_indexes.sql` (already applied — don't re-run without checking IF NOT EXISTS) |
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
6. The existing `body.mobile-preview` CSS block in styles.css is the tweaks-panel preview mode — distinct from the new `@media` breakpoints, don't conflate them

---

## Deployment Checklist

```powershell
# 1. Test locally
cd C:\Users\indha\python\taxes\web
python app.py
# → http://localhost:5000

# 2. Commit specific files (never git add -A blindly — .env is in the tree)
cd C:\Users\indha\python\taxes
git add web/app.py web/static/screens.js   # whichever files changed
git commit -m "your message"

# 3. Push — master for preview, master:main for production
git push origin master
git push origin master:main --force

# 4. Verify production (~60s build time)
# https://tax-contester.vercel.app/api/parcel/01004795950043
```
