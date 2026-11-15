# SEO Brief — Ankeny

_Last updated: 2026-05-26_
_Type: city_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** ankeny property tax appeal 2026
**Secondary:**
- ankeny assessment too high 2026
- ankeny iowa property tax protest
- ankeny board of review property tax
- ankeny iowa assessment notice 2026

## Intent classification

- [x] Action (wants to file — high intent, knows the deadline is real)

---

## Unique data hook

> **Ankeny has the highest median 2026 assessment in Polk County: $330,400**
> across 28,239 homes. Assessments here track sale prices closely (median
> assessment-to-sale ratio 0.995), and about 7% of 2025 sales carry an
> assessment more than 10% above the sale price. That's the lowest rate of
> the Tier 1 cities, so check before you file. A 2-minute comp check tells
> you whether you're in that 7%.

> ⚠️ **Hook changed 2026-11-15.** The original "new construction is
> over-assessed" angle is **not supported by the data**. Post-2020 Ankeny homes
> are over-assessed by >10% *less* often (4.5%) than older ones (8.1%). The
> new-construction H2 and outline bullet were removed; the FAQ about new homes
> stays because the question is still legitimate. Source: `_DATA_2026.md`.

**SQL to pull the real numbers:**
```sql
-- Ankeny: parcel count, median sale, median assessment 2026
-- Also break out by construction era (pre/post 2020)
SELECT
  CASE WHEN p.year_built >= 2020 THEN 'post-2020' ELSE 'pre-2020' END AS era,
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
WHERE p.county = 'polk' AND p.city ILIKE '%ankeny%'
GROUP BY era;
```

---

## Meta

- **Title (54 chars):** `Ankeny Property Tax Appeal 2026 | Free Evidence Packet`
  _(Note: this title is 54 chars — safe)_
- **Description (152 chars):** `Polk County's Apr 30 deadline is coming. Get a free comp-based protest packet built from real assessor data. Ankeny homeowners — check yours in 2 minutes.`
- **Slug:** `/ankeny`
- **Canonical:** `https://tax-contester.vercel.app/ankeny`

---

## Page outline

### H1: Ankeny Property Tax Appeal 2026

### H2: Is your Ankeny assessment too high?
- Unique hook: highest median assessment in Polk ($330,400); ~7% of 2025 sales
  assessed >10% above sale price. Check before you file.
- Embedded address search widget

### H2: The April 30 deadline
- Formal protest due to the Polk County Board of Review by April 30
- Informal review with the Polk assessor closes April 25
- Both dates apply to Ankeny homeowners — Ankeny is in Polk County

### H2: How the evidence packet works for Ankeny homeowners
- Enter your Ankeny address → comp sales from comparable Ankeny homes →
  2-page packet citing Iowa Code §441.37
- Comps scored: sqft, year built, neighborhood, recency — not just
  "homes near you"

### H2: What the Polk County Board of Review needs to see
- Closed sales (not Zillow, not asking prices, not builder quotes)
- §441.37 grounds explicitly stated
- The evidence packet addresses all three

### H2: FAQ (Ankeny–specific)

- **Q:** My Ankeny home is new — can I still protest the assessment?
  **A:** Yes. New construction assessments are based on the cost approach
  but protested on the sales approach. If comparable new builds in Ankeny
  sold for less than your assessment, you have grounds under §441.37.

- **Q:** Ankeny is in Polk County — where do I file?
  **A:** You file with the Polk County Board of Review. The Board handles
  protests for all Polk County cities including Ankeny, regardless of
  whether you're in the City of Ankeny proper.

- **Q:** Is there an Ankeny-specific assessor?
  **A:** No. Ankeny properties are assessed by the Polk County Assessor.
  The Polk County Board of Review handles protests. There is no separate
  city-level assessor for Ankeny.

- **Q:** My Ankeny assessment jumped more than 10% — does that automatically
  mean I have a case?
  **A:** A large jump is a signal worth checking, but the legal test is
  whether your assessment exceeds market value — not whether it went up.
  Enter your address and see what comps say. If implied value from comps
  is more than 10% below your assessment, you have grounds.

- **Q:** How long does an Ankeny protest take?
  **A:** File by April 30. The Board issues decisions by May 31. If you're
  unhappy with the ruling, you can appeal to the PAAB by June 20.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for Ankeny",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "Ankeny",
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
          "name": "Can I protest an assessment on a new construction home in Ankeny?",
          "acceptedAnswer": { "@type": "Answer", "text": "Yes. New construction assessments are often based on the cost approach. You can protest using the sales approach — comparable new builds that sold for less than your assessed value." }
        },
        {
          "@type": "Question",
          "name": "Where do Ankeny homeowners file a property tax protest?",
          "acceptedAnswer": { "@type": "Answer", "text": "With the Polk County Board of Review. Ankeny is in Polk County; there is no city-level assessor or separate appeal process." }
        },
        {
          "@type": "Question",
          "name": "What is the deadline to protest an Ankeny property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 for a formal protest with the Polk County Board of Review. The informal review with the assessor closes April 25." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/polk-county`
- **Sideways:** `/urbandale` ("see Urbandale comps"), `/johnston` ("or Johnston, just south of Ankeny")
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

Anchor text variations (from neighbor pages):
- "Ankeny property tax appeal" (exact — ~20%)
- "appeal your Ankeny assessment"
- "Ankeny homeowners — check your comps"
- "for homeowners in Ankeny"
- "Ankeny's April 30 deadline"

---

## Implementation notes

- **Flask route:** `@app.route("/ankeny")` — renders `web/templates/city.html`
- **Template file:** `web/templates/city.html` (shared across cities, parameterized)
- **Data source for unique hook:** `_DATA_2026.md`. Ankeny's differentiator
  is the highest median assessment plus the lowest over-assessment rate. The
  new-construction angle was disproved, so don't revive it.
- **Refresh cadence:** mid-March each year; the new-construction hook holds
  across years — just update the year range (2021–2025, etc.) and re-run SQL

---

## Pre-publish checklist

- [ ] Unique data hook present (new-construction assessment angle — verify SQL)
- [ ] Meta title ≤60 chars ✓ (54)
- [ ] Meta description ≤155 chars ✓ (152)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] All internal links real
- [ ] Voice contract obeyed
- [ ] Year 2026 in title + body
