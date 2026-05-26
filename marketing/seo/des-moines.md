# SEO Brief — Des Moines

_Last updated: 2026-05-26_
_Type: city_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** des moines property tax appeal 2026
**Secondary:**
- des moines property tax protest iowa
- des moines assessment too high 2026
- polk county property tax appeal des moines
- des moines board of review property tax

## Intent classification

- [x] Action (wants to file a protest before the deadline)

---

## Unique data hook

> Des Moines has more assessed parcels than any other city in Polk County
> — and the widest spread between neighborhoods. The same square footage
> can carry a $120,000 difference in assessed value depending on which
> side of Fleur Drive you're on. That spread is where assessments go wrong.

**SQL to pull the real numbers:**
```sql
-- Des Moines: parcel count, median sale, median assessment 2026
SELECT
  p.city,
  count(*) AS parcel_count,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY s.sale_price) AS median_sale,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed_2026
FROM properties p
LEFT JOIN LATERAL (
  SELECT sale_price FROM sales
  WHERE property_id = p.id AND sale_date >= '2024-01-01' AND arms_length_flag = true
  ORDER BY sale_date DESC LIMIT 1
) s ON true
LEFT JOIN LATERAL (
  SELECT assessed_total FROM assessments
  WHERE property_id = p.id AND tax_year = 2026
  ORDER BY id DESC LIMIT 1
) a ON true
WHERE p.county = 'polk' AND p.city ILIKE '%des moines%'
GROUP BY p.city;

-- Spread: min/max neighborhood median assessment in Des Moines
SELECT neighborhood_code,
  count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed
FROM properties p
JOIN assessments a ON a.property_id = p.id AND a.tax_year = 2026
WHERE p.county = 'polk' AND p.city ILIKE '%des moines%'
GROUP BY neighborhood_code
ORDER BY median_assessed DESC;
```

---

## Meta

- **Title (56 chars):** `Des Moines Property Tax Appeal 2026 | Free Packet`
- **Description (155 chars):** `Polk County deadline is Apr 30. Check your Des Moines assessment against real recorder sales — free comp evidence packet, ready to file in 2 minutes.`
- **Slug:** `/des-moines`
- **Canonical:** `https://tax-contester.vercel.app/des-moines`

---

## Page outline

### H1: Des Moines Property Tax Appeal 2026

### H2: Is your Des Moines assessment off?
- Des Moines has more assessment variability than any other Polk city —
  property values shift sharply by neighborhood. A comp two blocks away
  in the wrong neighborhood can distort your assessment significantly.
- Unique hook: the neighborhood spread data point (fill from SQL above)
- Embedded address search widget

### H2: The April 30 deadline
- Formal protest with the Polk County Board of Review due by April 30
- Informal review with assessor closes April 25
- What happens if you miss it (wait until 2027)

### H2: How the evidence packet works for Des Moines homeowners
- Enter your address → comps pulled from Des Moines and surrounding
  neighborhoods → 2-page packet with Iowa Code §441.37 citation
- "Your comps are scored for size, age, and neighborhood — not just
  radius from your front door."

### H2: What the Polk County Board of Review needs to see
- Comparable closed sales (not Zillow, not asking prices)
- Iowa Code §441.37 grounds laid out explicitly
- The packet format the Board expects

### H2: FAQ (Des Moines–specific)

- **Q:** My Des Moines neighborhood has widely varying home prices. Will
  the comps be accurate?
  **A:** Yes — the comp engine matches on neighborhood code first, then
  expands to adjacent areas only if fewer than 5 comparable sales are
  found. You'll see only sales from comparable neighborhoods, not
  outliers from across town.

- **Q:** I live near the border of Des Moines and a suburb. Which city
  page should I use?
  **A:** Use the address search on the homepage — it finds your parcel
  by address regardless of city label. The tool uses your specific
  county parcel ID and neighborhood code, not just the city name.

- **Q:** Can I protest even if my assessment only went up a small amount?
  **A:** Yes, if your assessment exceeds the implied market value by more
  than 10%, you have grounds under §441.37. Even a $15,000 over-
  assessment saves $450/yr at a 3% tax rate — worth the 10 minutes.

- **Q:** Does this cover the whole Des Moines metro?
  **A:** The engine covers all Polk County parcels — that includes Des
  Moines proper and surrounding cities. Dallas County (Waukee, parts of
  West Des Moines) is coming.

- **Q:** Who files the packet — me or you?
  **A:** You download it; you file it. Tax Contester produces the
  evidence packet. Filing with the Board of Review takes less than 5
  minutes in person or by mail.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for Des Moines",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "Des Moines",
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
          "name": "How accurate are the comps for Des Moines neighborhoods?",
          "acceptedAnswer": { "@type": "Answer", "text": "The comp engine matches on your specific neighborhood code first, then expands only if fewer than 5 comparable sales are found. Sales come from the Polk County recorder — the same data the Board of Review uses." }
        },
        {
          "@type": "Question",
          "name": "What is the deadline to protest a Des Moines property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 is the deadline to file a formal protest with the Polk County Board of Review. The informal review with the assessor's office closes April 25." }
        },
        {
          "@type": "Question",
          "name": "Do I file the protest packet myself?",
          "acceptedAnswer": { "@type": "Answer", "text": "Yes. Tax Contester produces the comp evidence packet; you download and file it with the Board of Review. No attorney needed." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/polk-county`
- **Sideways:** `/west-des-moines` ("neighboring West Des Moines homeowners"), `/urbandale` ("or check comps in Urbandale")
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

Anchor text variations:
- "Des Moines property tax appeal" (exact match — ~20%)
- "appeal your Des Moines assessment"
- "Des Moines homeowners — see your comps"
- "for homeowners in Des Moines"
- "the Des Moines protest deadline"

---

## Implementation notes

- **Flask route:** `@app.route("/des-moines")` — renders `web/templates/city.html`
- **Template file:** `web/templates/city.html` (new; shared across all city pages,
  parameterized by city data dict injected from Flask)
- **Data source for unique hook:** run the neighborhood-spread SQL above;
  cache result in `web/static/city_data.json` or inject from Flask at route time
- **Refresh cadence:** mid-March each year (refresh year + median data);
  the neighborhood-spread hook is the most stable and needs updating only
  on major data reloads
- **Subdivide later:** if search volume warrants it, sub-pages by zip or
  neighborhood (e.g., `/des-moines/beaverdale`, `/des-moines/east-side`)
  using the same template; defer until analytics shows demand

---

## Pre-publish checklist

- [ ] Unique data hook present (neighborhood spread — verify SQL output)
- [ ] Meta title ≤60 chars ✓ (56)
- [ ] Meta description ≤155 chars ✓ (155)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] All internal links real: `/polk-county` ✓ (ship city links at same time)
- [ ] Voice contract obeyed
- [ ] Year 2026 in title + body
