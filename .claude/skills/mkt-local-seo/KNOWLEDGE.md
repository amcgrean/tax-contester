# Local + Programmatic SEO Knowledge Pack

The curated playbook behind `mkt-local-seo`. Anchored on the Zapier /
TripAdvisor / NerdWallet programmatic-SEO tradition + standard local
SEO essentials.

---

## Why programmatic SEO is the right shape for tax-contester

Search intent for this product is **fragmented by place**:

- "ankeny property tax appeal"
- "waukee assessment too high"
- "des moines polk county protest"
- "is my urbandale assessment fair"

A single generic page cannot rank for all of these. A template-driven
approach — one page per place, each with unique local data — can. The
moat is the data (173K parcels, 381K sales) that competitors don't
have city-by-city.

The pattern:

1. **Single template, hundreds of pages.**
2. **Each page injects local data:** city name, median sale, top
   streets, sales volume, deadline distance.
3. **Internal linking forms a hub:** county → city → zip → guide.

---

## Local SEO essentials (always-true rules)

1. **NAP consistency** — name, address (or service area), phone match
   across the page, the schema markup, and any directory listings (GBP,
   Bing Places, etc.).
2. **LocalBusiness or Service schema** with `areaServed` set to the
   county. Use `Service` if there's no physical storefront, which is
   our case.
3. **FAQPage schema on every city page.** FAQ rich results still earn
   real estate in the SERP — worth the markup.
4. **Internal links from a county hub** to each city; cities link back
   to the county and sideways to 2 neighbors.
5. **City-specific testimonial, example, or anonymized case study.**
   Even a one-line example does work: *"A 1950 ranch on 4th St in
   Ankeny was assessed $42k over comps — appeal won."* (Only use real
   examples if you have permission; otherwise mark as illustrative.)

---

## Intent classification (the discipline that prevents bloat)

Every page targets ONE of these intents. Mixed-intent pages convert on
none.

| Query type | Intent | Page that should rank |
|---|---|---|
| "ankeny property tax appeal" | **Action** — wants to file | City page with CTA |
| "how to appeal property tax iowa" | **Info** — wants steps | Guide page |
| "polk county board of review" | **Navigation** — wants the entity | County hub with link |
| "is my property assessment too high" | **Diagnostic** — wants a tool | Homepage / address search |
| "2026 polk assessment notice" | **News** — wants a change | News-style page, refreshed yearly |

If you can't classify a target keyword into exactly one of these, you
don't understand the intent yet. Don't write the page.

---

## What kills local SEO pages (avoid)

- **Duplicate content across cities.** #1 killer. If 80%+ of the page
  is the same string across cities, Google folds them into one. Cure:
  unique data hook per page, real local detail.
- **Thin pages** (<300 words of unique content). Either expand or roll
  into the county hub.
- **Fake addresses.** Never. NAP violation + ethics violation.
- **Spammy internal anchors** ("best property tax appeal Ankeny"
  repeated 12x). Vary anchors naturally.
- **Forgotten dates.** A page titled "Ankeny Property Tax Appeal 2025"
  in May 2026 is a bounce.

---

## What earns local SEO pages (do)

- **Unique local data** — sales medians, top streets, zip-level numbers.
- **A real (or clearly-flagged illustrative) example per city.**
- **Embedded mini-map.** We already have Leaflet on the comps screen;
  re-use it on city pages.
- **Locally relevant external links** — Polk County Board of Review
  page, county assessor URL. (Outbound links to authoritative local
  sources help, not hurt.)
- **Yearly refresh** — fresh date in title + content.

---

## Deadline-driven content cadence

The April calendar IS the marketing engine. Plan content around it:

| When | Action |
|---|---|
| Mid-March | Refresh all city pages — bump year in titles, refresh data hooks |
| Early April | Publish "What to do when your 2026 assessment notice arrives" guide |
| April 1–30 | Countdown banner on every city page (already wired) |
| May 1 | Pivot: "Missed the deadline? Here's what to do next year." |
| June (PAAB) | Optional: "Lost at the Board? PAAB by Jun 20" guide |
| Off-season (Jul–Feb) | Build evergreen guides; collect testimonials |

---

## Title / meta patterns (proven, copy these)

**City page title (≤60 chars):**
```
<City> Property Tax Appeal 2026 | Free Evidence Packet
```

**City page meta (~155 chars):**
```
Polk County deadline is Apr 30. Free comp-based protest packet built
from real assessor data. <City> homeowners — check your assessment in
2 minutes.
```

**County hub title:**
```
Polk County Property Tax Appeal 2026 | Board of Review Guide
```

**Guide page title:**
```
How to Appeal Your Iowa Property Tax Assessment (2026 Guide)
```

---

## Hub-and-spoke architecture (the link graph)

```
/                                  (homepage — address search)
/polk-county                       (county hub)
├── /des-moines
├── /west-des-moines
├── /ankeny
├── /waukee
├── /urbandale
└── ...
/dallas-county                     (county hub)
├── /waukee                        (decide: which hub owns Waukee?)
└── ...
/guide/how-to-appeal-property-tax-iowa
/guide/what-to-do-when-your-assessment-arrives
/guide/iowa-code-441-37-explained
```

Linking rules:

- Every city page links **up** to its county hub.
- Every city page links **sideways** to 2 nearby cities.
- Every city page links **down** to the most relevant guide.
- County hubs link to **all** their cities.
- Guides link to the homepage CTA + 1–2 county hubs.

---

## Schema.org templates (copy/paste, then fill)

### City page — Service + FAQPage

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for <City>",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "<City>",
        "containedInPlace": {
          "@type": "AdministrativeArea",
          "name": "<County> County, Iowa"
        }
      },
      "provider": {
        "@type": "Organization",
        "name": "Tax Contester",
        "url": "https://tax-contester.vercel.app"
      },
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        { "@type": "Question", "name": "...", "acceptedAnswer": { "@type": "Answer", "text": "..." } }
      ]
    }
  ]
}
```

### County hub — adds `BreadcrumbList`

Include a breadcrumb chain `Home > Iowa > <County> County` to help the
SERP render breadcrumbs and reinforce the hub structure.

---

## Anchor text variation (avoid the spam pattern)

For internal links pointing TO a city page, vary the anchor:

- "Ankeny property tax appeal" (exact match — use ~20% of the time)
- "appeal your Ankeny assessment"
- "see Ankeny comps"
- "Ankeny's 2026 deadline"
- "for homeowners in Ankeny"

Same destination, different anchors. Mix naturally inside paragraphs.

---

## Pages we should NOT build

- One page per zip code (too thin; zip-level data is usually subsumed
  by city). Exception: a few high-value zips where the data is
  meaningfully different.
- Pages targeting branded keywords of competitors ("ownwell vs
  taxcontester") until we have something honest to say.
- "Best property tax appeal service in Iowa" — generic, low-intent,
  competes with directories.

---

## What to read next (for the human curator)

- Programmatic SEO playbook — Eli Schwartz, *Product-Led SEO*
- Local SEO — Sterling Sky / Joy Hawkins
- Schema.org docs — schema.org/Service, schema.org/FAQPage
- Google Search Central — "Helpful content" + "Site reputation abuse"
  (avoid the latter)
