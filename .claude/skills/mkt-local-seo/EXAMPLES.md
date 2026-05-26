# Local SEO Examples & Priority Page List

The concrete page roster for tax-contester v1, plus a worked Ankeny
example to anchor the template.

---

## Polk County — priority pages (v1)

| Slug | Type | Tier | Notes |
|---|---|---|---|
| `/polk-county` | county-hub | 1 | Links to all city pages; deadline + Board of Review info; breadcrumb root |
| `/des-moines` | city | 1 | Largest market, highest search volume; subdivide later by neighborhood if data supports |
| `/west-des-moines` | city | 1 | Affluent — high $-savings; also lives in Dallas (decide hub ownership below) |
| `/ankeny` | city | 1 | High growth, many new assessments |
| `/urbandale` | city | 1 | |
| `/clive` | city | 2 | |
| `/johnston` | city | 2 | |
| `/altoona` | city | 2 | |
| `/pleasant-hill` | city | 2 | Verify >50 sales/yr before publishing |
| `/norwalk` | city | 2 | |
| `/windsor-heights` | city | 3 | Tiny — likely roll into Des Moines |

## Dallas County — priority pages (v1)

| Slug | Type | Tier | Notes |
|---|---|---|---|
| `/dallas-county` | county-hub | 1 | Comp engine NOT live for Dallas — page ships with deadline + Board info + "notify me when Dallas launches" capture |
| `/waukee` | city | 1 | Straddles Polk/Dallas — assign to Dallas hub canonical, link from Polk hub |
| `/west-des-moines` | shared | — | Lives under Polk hub canonical; cross-linked from Dallas |
| `/grimes` | city | 2 | |
| `/adel` | city | 2 | |
| `/van-meter` | city | 3 | Probably too small — roll into county hub |

## Guides (cross-county, intent: Info)

| Slug | Intent | Notes |
|---|---|---|
| `/guide/how-to-appeal-property-tax-iowa` | Info | Statewide guide, cites §441.37, sends to county hubs |
| `/guide/what-to-do-when-your-assessment-arrives` | Info | Seasonal — refreshed yearly, published Apr 1 |
| `/guide/iowa-code-441-37-explained` | Info | The protest grounds plain-English; cites case law if available |
| `/guide/polk-board-of-review` | Navigation | The Board's process, addresses, what to bring |

## Pages we are NOT building (yet)

- Per-zip pages (too thin)
- Comparison pages vs named competitors (nothing honest to say yet)
- "Best property tax service in Iowa" (low-intent, wrong category)

---

## Worked example — `/ankeny`

### Frontmatter for the brief

- **Slug:** `/ankeny`
- **Type:** city
- **Tier:** 1
- **Intent:** Action (wants to file)
- **Primary keyword:** "ankeny property tax appeal"
- **Secondary keywords:** "ankeny assessment too high", "ankeny board
  of review", "ankeny iowa property tax 2026"

### Meta

- **Title (58 chars):** `Ankeny Property Tax Appeal 2026 | Free Evidence Packet`
- **Description (152 chars):** `Polk County's Apr 30 deadline is
  coming. Get a free comp-based protest packet built from real
  assessor data. Ankeny homeowners — check yours in 2 minutes.`

### Unique data hook (the line no other page has)

> "The median single-family sale in Ankeny in 2025 was **$385,400**. The
> median 2026 assessment for Ankeny homes was **$412,800**. If your
> assessment is more than 10% above sale comps, you have a case."

(Numbers above are illustrative. The skill should pull real numbers
from the live database when generating the actual brief.)

### Page outline

- H1: **Ankeny Property Tax Appeal 2026**
- H2: Is your Ankeny assessment too high?
  - Subject + the unique data hook
  - Inline address search widget
- H2: The April 30 Polk County deadline
  - 30-day countdown
  - What happens if you miss it
- H2: How the evidence packet works
  - 3-step explainer (find parcel → see comps → download packet)
  - Link to a sample packet
- H2: What the Polk Board of Review needs to see
  - Plain-English §441.37 grounds
  - Comp table format the Board expects
- H2: FAQ (Ankeny-specific)
  - 5 questions, voice-matched

### Schema.org

`Service` + `FAQPage` per the template in `KNOWLEDGE.md`, with
`areaServed.name = "Ankeny"` and `containedInPlace.name = "Polk County,
Iowa"`.

### Internal links

- **Up:** `/polk-county`
- **Sideways:** `/urbandale`, `/johnston`
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

### Implementation notes

- Flask route: add `@app.route("/<city_slug>")` with a city-data lookup.
- Template: new `web/templates/city.html` (Jinja); shared across all
  cities, parameterized by city data dict.
- Data source for unique hook: write a small `scripts/seo_data.py` that
  pulls median sale + median assessment per city from Neon, cached to a
  JSON file refreshed on a schedule (or on deploy).
- Refresh cadence: mid-March each year, plus on any data reload.

---

## Worked example — `/polk-county` (hub)

- **Title:** `Polk County Property Tax Appeal 2026 | Board of Review Guide`
- **Intent:** Navigation + Info hybrid (acceptable for a hub)
- **Unique hook:** total Polk parcels (173,000+), median 2025→2026
  assessment change %, deadline countdown.
- **Outline:**
  - H1: Polk County Property Tax Appeal 2026
  - H2: The April 30 deadline (countdown)
  - H2: How the Polk County Board of Review works
  - H2: Appeal-ready cities (links to every Polk city page in a grid)
  - H2: When the assessor's office is the right first call
  - H2: FAQ
- **Schema:** `Service` + `BreadcrumbList` (Home > Iowa > Polk County)
- **Links down:** every Polk city page; the §441.37 guide.

---

## Worked example — `/dallas-county` (honest hub, no comp engine yet)

- **Title:** `Dallas County Property Tax Appeal 2026 | Board of Review`
- **Intent:** Navigation + lead capture
- **Unique hook:** "Dallas County's median home price grew __% from
  2024 to 2026. The comp engine launches for Dallas in 2026 — drop
  your email and we'll ping you the day it's live."
- **CTA:** email capture (not the address-search widget, which would
  break — Polk-only data right now).
- **Note in body:** "For Polk County, our comp engine is live now."
  with link.

This is the honesty-as-moat play. Do not fake it.

---

## Anchor text plan (sample for `/ankeny` from neighboring pages)

| From page | Anchor variation |
|---|---|
| `/polk-county` | "Ankeny" (in a city grid) |
| `/urbandale` | "appeal your Ankeny assessment" |
| `/johnston` | "see Ankeny comps" |
| `/guide/how-to-appeal-property-tax-iowa` | "homeowners in Ankeny" |

---

## Hub-index format (Mode B output)

When generating all Tier 1 cities at once, end with
`marketing/seo/_HUB_INDEX.md`:

```
| Slug | Unique hook (first 80 chars) |
|---|---|
| /ankeny | Median 2025 sale $385,400; median 2026 assessment $412,800; +7.1%... |
| /urbandale | ... |
| /west-des-moines | ... |
```

If any two rows look identical, the briefs are too thin — go back and
deepen the data hook.
