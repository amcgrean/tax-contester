# SEO Hub Index — Tier 1 Pages

_Last updated: 2026-05-26_
_Run this sanity check before publishing any city page: if two rows look identical, the briefs are too thin._

---

## Polk County pages (comp engine LIVE)

| Slug | Type | Unique data hook | Differentiation angle |
|---|---|---|---|
| `/polk-county` | county-hub | 173K parcels + 381K sales + "largest county in Iowa" volume hook | Volume + hub authority; no city-specific angle |
| `/des-moines` | city | Widest neighborhood assessment spread in Polk County — valuation gap varies $120K by neighborhood | Variance across neighborhoods; subdividable later |
| `/ankeny` | city | New construction (post-2020) — assessments often based on cost approach vs market sales comps | Growth city; new-build assessment lag |
| `/urbandale` | city | 1960s–1990s housing stock; year-built filter is the key variable; comp quality anchored to era | Older housing stock; age-sensitive comp matching |
| `/west-des-moines` | city | Highest median home values in Polk → highest dollar savings from a protest (10% over on $450K = $1,350/yr) | Dollar savings math; high-value suburb |
| `/waukee` | city (split) | Fast growth → assessment drift for new builds; **honest Dallas split callout**; Polk side live, Dallas coming | Growth city + county-split transparency |

**Duplicate check:** Each row has a structurally different hook. No two are interchangeable. ✓

---

## Dallas County pages (comp engine NOT YET LIVE)

| Slug | Type | Unique data hook | Status |
|---|---|---|---|
| `/dallas-county` | county-hub | Board of Review info + email capture for Dallas launch | NOT BUILT — ship when Dallas data loads or as lead-capture stub |

---

## Guides (cross-county, not yet built)

| Slug | Intent | Status |
|---|---|---|
| `/guide/how-to-appeal-property-tax-iowa` | Info | NOT BUILT — Phase 2 |
| `/guide/iowa-code-441-37-explained` | Info | NOT BUILT — Phase 2 |
| `/guide/polk-board-of-review` | Navigation | NOT BUILT — Phase 2 |
| `/guide/what-to-do-when-your-assessment-arrives` | News/seasonal | NOT BUILT — publish early April |

---

## Internal link matrix (Tier 1 only)

| Page | Links up to | Links sideways to | Links down to |
|---|---|---|---|
| `/polk-county` | `/` (home) | — | `/des-moines`, `/ankeny`, `/urbandale`, `/west-des-moines`, `/waukee` + guides |
| `/des-moines` | `/polk-county` | `/west-des-moines`, `/urbandale` | `/guide/how-to-appeal-property-tax-iowa` |
| `/ankeny` | `/polk-county` | `/urbandale`, `/johnston` | `/guide/how-to-appeal-property-tax-iowa` |
| `/urbandale` | `/polk-county` | `/des-moines`, `/clive` | `/guide/how-to-appeal-property-tax-iowa` |
| `/west-des-moines` | `/polk-county` (+ `/dallas-county` cross-link) | `/des-moines`, `/clive` | `/guide/how-to-appeal-property-tax-iowa` |
| `/waukee` | `/dallas-county` (primary), `/polk-county` (cross) | `/west-des-moines`, `/ankeny` | `/guide/how-to-appeal-property-tax-iowa` |

**Link integrity check:** All sideways links (e.g., `/clive`, `/johnston`) are
Tier 2 pages not yet built. Do not ship Tier 1 pages with broken sideways links
— either link to the county hub as the interim or hold those anchors until Tier 2
is built.

---

## Data queries needed before publish

Run these against Neon and fill the `[VERIFY]` placeholders in each city brief:

```sql
-- Run once per city, fill into the brief's "unique data hook" section
-- Des Moines: neighborhood spread
SELECT neighborhood_code,
  count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.county = 'polk' AND p.city ILIKE '%des moines%'
GROUP BY neighborhood_code
ORDER BY median_assessed DESC;

-- Ankeny: new construction assessment
SELECT
  CASE WHEN p.year_built >= 2020 THEN 'post-2020' ELSE 'pre-2020' END AS era,
  count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.county = 'polk' AND p.city ILIKE '%ankeny%'
GROUP BY era;

-- Urbandale: decade-of-construction breakdown
SELECT (p.year_built / 10) * 10 AS decade, count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.county = 'polk' AND p.city ILIKE '%urbandale%' AND p.year_built IS NOT NULL
GROUP BY decade ORDER BY decade;

-- West Des Moines: median assessed + savings calculation
SELECT count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed,
  ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) * 0.10 * 0.03)
    AS annual_savings_if_10pct_over
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.county = 'polk' AND p.city ILIKE '%west des moines%';

-- Waukee: Polk vs Dallas county split
SELECT p.county, count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.city ILIKE '%waukee%'
GROUP BY p.county;
```

---

## Publish order (recommended)

1. `/polk-county` first — other pages link up to it; it must exist before city pages ship
2. `/des-moines`, `/ankeny`, `/urbandale`, `/west-des-moines` simultaneously
3. `/waukee` — ship after Polk-county-side data confirmed; Dallas callout is live from day 1
4. Tier 2 city pages (separate sprint)
5. Guides (separate sprint, higher word count needed)
6. `/dallas-county` hub + Dallas city pages — only after Dallas data loads

---

## Refresh cadence

| When | What |
|---|---|
| Mid-March annually | Bump year in all title tags + body copy; re-run data queries; update median numbers |
| Day Dallas data loads | Update `/waukee` "coming soon" → "live now"; publish `/dallas-county` hub; publish Dallas city pages |
| Day a new Tier 2 city page ships | Update sideways links on neighboring Tier 1 pages |
