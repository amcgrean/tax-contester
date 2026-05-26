---
name: mkt-local-seo
description: Generate or audit local SEO content — programmatic county/city pages, schema.org markup, intent-classified keywords. Invoke when the user asks about SEO, ranking, "[city] property tax appeal", programmatic pages, county pages, or scaling content across cities.
---

You produce hyper-local SEO content for **Tax Contester**. Polk + Dallas
counties, ~12 priority cities, ~20 zips. Programmatic — one template,
many pages, no duplicate content.

## Required inputs

- `marketing/BRAND.md` — geography list, deadlines, voice.
- `marketing/positioning.md` — value prop. **Required.** If missing,
  stop and invoke `mkt-positioning` first.
- Optional: target keywords or competitor SERP screenshots from the user.

## Process

### Mode A — Single brief (one city or county hub)

1. Load `KNOWLEDGE.md` (programmatic SEO patterns + local intent) and
   `EXAMPLES.md` (the priority page list + a worked Ankeny example).
2. Identify the page type: `county-hub`, `city`, or `guide`.
3. Produce `marketing/seo/<slug>.md` using `OUTPUT_TEMPLATE.md`. Include:
   - Target keywords with intent classification
   - **Unique data hook** (at least one number no other page has)
   - H1, meta title (≤60 chars), meta description (≤155 chars)
   - Page outline (H2s)
   - Schema.org JSON-LD (Service or LocalBusiness + FAQPage)
   - Internal-link plan (up to county hub, sideways to 2 neighbors,
     down to a guide)
4. End with implementation notes: Flask route to add, template file,
   data source for the unique number, and refresh cadence.

### Mode B — Batch (all Tier 1 cities)

1. Load the priority list from `EXAMPLES.md` and `BRAND.md`.
2. Produce one file per city, batched. For each, ensure the unique
   data hook is genuinely different — pull from the live database if
   possible (median sale, top streets, sales volume).
3. Produce a single `marketing/seo/_HUB_INDEX.md` summary listing all
   pages with their unique hooks, so a human can sanity-check for
   duplicate content in one sweep.

## Quality bar (reject your own drafts if they fail)

- **Unique data hook per page.** If two cities can't be meaningfully
  differentiated by data, collapse them into a single page or roll into
  the county hub. Do NOT spin synonyms.
- **Meta title ≤60 chars.** Includes city + intent keyword + year.
- **Internal links go somewhere real.** No `/coming-soon` placeholders
  shipped.
- **Schema.org validates.** Run the JSON-LD through a mental
  schema-validator: required fields present, areaServed is a City or
  AdministrativeArea, FAQPage has at least 3 questions.
- **Intent purity.** A page targets ONE intent type (Action, Info,
  Navigation, Diagnostic, or News). Mixed-intent pages convert on none.
- **Honors voice contract.** Same Iowa-plain rules as the rest of the
  marketing system.

## Special case: Dallas County

Dallas comp data is not yet loaded (per `HANDOFF.md`). City pages for
Dallas can ship with:

- Deadline + Board of Review information
- A clear callout: "Comp engine launching for Dallas in 2026 — Polk
  available now."
- Email capture for "notify me when Dallas data is live"

Do NOT publish a Dallas city page that pretends the comp engine works
there. Honesty is the moat.

## When to re-run

- After every positioning update.
- Annually in mid-March (refresh year in titles, update unique data
  hooks from latest sales).
- When a new city tier is added to `BRAND.md`.
- When the live data set materially changes (e.g. Dallas loads).
