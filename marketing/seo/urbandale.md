# SEO Brief — Urbandale

_Last updated: 2026-05-26_
_Type: city_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** urbandale property tax appeal 2026
**Secondary:**
- urbandale assessment too high 2026
- urbandale iowa property tax protest
- urbandale board of review property tax
- urbandale polk county assessment 2026

## Intent classification

- [x] Action (wants to file — steady homeowner base, older housing stock
  where comp accuracy matters most)

---

## Unique data hook

> Urbandale's housing stock skews toward homes built in the 1960s–1990s:
> split-levels, raised ranches, and brick colonials. Older homes have the
> most assessment variance — age and condition differences are hard to
> capture in a mass-appraisal model. The comp engine filters by year
> built (±15 years), which is exactly where Urbandale assessments tend
> to drift.

**SQL to pull the real numbers:**
```sql
-- Urbandale: parcel count by decade of construction, median assessment
SELECT
  (p.year_built / 10) * 10 AS decade_built,
  count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY s.sale_price) AS median_sale
FROM properties p
LEFT JOIN LATERAL (
  SELECT assessed_total FROM assessments
  WHERE property_id = p.id AND tax_year = 2026 LIMIT 1
) a ON true
LEFT JOIN LATERAL (
  SELECT sale_price FROM sales
  WHERE property_id = p.id AND sale_date >= '2024-01-01'
    AND arms_length_flag = true
  ORDER BY sale_date DESC LIMIT 1
) s ON true
WHERE p.county = 'polk' AND p.city ILIKE '%urbandale%'
  AND p.year_built IS NOT NULL
GROUP BY decade_built
ORDER BY decade_built;
```

---

## Meta

- **Title (57 chars):** `Urbandale Property Tax Appeal 2026 | Free Evidence Packet`
- **Description (154 chars):** `Polk County deadline is Apr 30. Urbandale's older homes are where assessments drift most. Free comp packet built from real sales. Check yours in 2 minutes.`
- **Slug:** `/urbandale`
- **Canonical:** `https://tax-contester.vercel.app/urbandale`

---

## Page outline

### H1: Urbandale Property Tax Appeal 2026

### H2: Why Urbandale homeowners should check their 2026 assessment
- Older homes (1960s–1990s) have the most assessment variance in
  Polk County's mass-appraisal model
- Unique hook: decade-of-construction breakdown (fill from SQL above)
- "The comp engine matches on year built — not just size — which is
  the key variable in Urbandale's housing stock."
- Embedded address search widget

### H2: The April 30 Polk County deadline
- Urbandale is in Polk County — protest with the Polk County Board of
  Review by April 30
- Informal review with the assessor closes April 25

### H2: How the evidence packet works for Urbandale homeowners
- Enter Urbandale address → comps from comparable Urbandale homes,
  scored on sqft, age, neighborhood, and recency → 2-page packet
  citing Iowa Code §441.37
- "Comps from similar-era Urbandale homes, not new construction
  across town."

### H2: What the Polk County Board of Review needs to see
- Closed sales — specifically arms-length sales of comparable homes
- §441.37 statutory grounds (assessment exceeds market value)
- A structured argument, not just a complaint

### H2: FAQ (Urbandale–specific)

- **Q:** My Urbandale home is a split-level from the 1970s. Will the
  comps be other split-levels?
  **A:** The comp engine filters by year built (±15 years) and living
  area (±20% sqft). Building style is not a direct filter, but because
  Urbandale's 1970s stock is predominantly split-levels and ranches,
  the comps will naturally be similar homes from the same era.

- **Q:** Urbandale hasn't had much new construction — does that affect the
  comp quality?
  **A:** It helps. A denser resale market (more sales of 1960–90s homes)
  means more comp candidates. Urbandale typically has a solid resale
  pool. The engine uses 24–36 months of sales, which should produce
  5+ good comps for most Urbandale parcels.

- **Q:** I'm in Urbandale but my address shows as Des Moines on some sites.
  Which city page applies to me?
  **A:** It depends on your actual parcel data. Enter your address in
  the search — the engine uses your county parcel record, not your mailing
  address city label. Both Urbandale and Des Moines entries are in the
  same Polk County database.

- **Q:** What is the appeal process timeline for Urbandale?
  **A:** File with the Polk County Board of Review by April 30. The Board
  issues its decision by May 31. If you disagree, appeal to the PAAB
  by June 20. All Urbandale homeowners follow this Polk County timeline.

- **Q:** Is this the right tool if my home is a condo or townhome in
  Urbandale?
  **A:** The comp engine works best for single-family homes. Condo
  assessments are often based on a different methodology, and comparable
  sales for condos are more limited. If you're in a condo, the results
  may be thinner — but try it; if the comp pool is too small, the engine
  will tell you.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for Urbandale",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "Urbandale",
        "containedInPlace": {
          "@type": "AdministrativeArea",
          "name": "Polk County, Iowa"
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
        {
          "@type": "Question",
          "name": "Will the comp engine find homes similar to my older Urbandale split-level?",
          "acceptedAnswer": { "@type": "Answer", "text": "Yes. The engine filters by year built (±15 years) and living area (±20%). Urbandale's 1970s stock is predominantly splits and ranches — the comp pool will reflect that." }
        },
        {
          "@type": "Question",
          "name": "What is the deadline to protest an Urbandale property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 for a formal protest with the Polk County Board of Review. Informal review with the assessor closes April 25. All Urbandale homeowners follow this Polk County timeline." }
        },
        {
          "@type": "Question",
          "name": "Where do I file a property tax protest for my Urbandale home?",
          "acceptedAnswer": { "@type": "Answer", "text": "With the Polk County Board of Review. Urbandale is in Polk County. Tax Contester produces the evidence packet; you file it with the Board in person or by mail." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/polk-county`
- **Sideways:** `/des-moines` ("Des Moines homeowners — see your comps"),
  `/clive` ("neighboring Clive assessment check")
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

Anchor text variations:
- "Urbandale property tax appeal" (exact — ~20%)
- "appeal your Urbandale assessment"
- "Urbandale homeowners — see your comps"
- "for homeowners in Urbandale"
- "Urbandale's April 30 deadline"

---

## Implementation notes

- **Flask route:** `@app.route("/urbandale")` — renders `web/templates/city.html`
- **Template file:** `web/templates/city.html` (shared)
- **Data source for unique hook:** decade-of-construction SQL above; the
  "older housing stock / year-built filter" angle is Urbandale's differentiator —
  don't reuse on Ankeny (new construction) or WDM (dollar savings)
- **Refresh cadence:** mid-March each year; the housing-era hook is stable
  and won't change much year over year unless there's major new development

---

## Pre-publish checklist

- [ ] Unique data hook present (housing stock decade breakdown — verify SQL)
- [ ] Meta title ≤60 chars ✓ (57)
- [ ] Meta description ≤155 chars ✓ (154)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] All internal links real
- [ ] Voice contract obeyed
- [ ] Year 2026 in title + body
