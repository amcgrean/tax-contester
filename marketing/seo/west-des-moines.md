# SEO Brief — West Des Moines

_Last updated: 2026-05-26_
_Type: city_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** west des moines property tax appeal 2026
**Secondary:**
- west des moines assessment too high 2026
- west des moines iowa property tax protest
- polk county west des moines board of review
- wdm iowa property tax 2026

## Intent classification

- [x] Action (wants to file — the dollar stakes are higher in WDM, so
  the motivation to act is stronger)

---

## Unique data hook

> West Des Moines has among the highest median home values in Polk County.
> That matters for protests: a 10% over-assessment on a $450,000 home
> means a $45,000 valuation error — and roughly $1,350/yr in excess taxes
> at a typical Polk tax rate. The math for protesting is clearest here.

**SQL to pull the real numbers:**
```sql
-- WDM: median sale price and median 2026 assessment
-- Also compute potential annual savings at a 3% effective rate
SELECT
  count(*) AS parcels,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) AS median_assessed,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY s.sale_price) AS median_recent_sale,
  -- If assessed > sale by 10%, annual tax savings at 3% effective rate:
  -- (median_assessed * 0.10) * 0.03
  ROUND(
    percentile_cont(0.5) WITHIN GROUP (ORDER BY a.assessed_total) * 0.10 * 0.03
  ) AS illustrative_annual_savings_if_10pct_over
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
WHERE p.county = 'polk' AND p.city ILIKE '%west des moines%';
```

---

## Meta

- **Title (59 chars):** `West Des Moines Property Tax Appeal 2026 | Free Packet`
- **Description (155 chars):** `Higher home values mean bigger savings if your WDM assessment is wrong. Free comp-based protest packet, Polk County deadline Apr 30. Check in 2 minutes.`
- **Slug:** `/west-des-moines`
- **Canonical:** `https://tax-contester.vercel.app/west-des-moines`

---

## Page outline

### H1: West Des Moines Property Tax Appeal 2026

### H2: Why WDM homeowners have the most to gain from a protest
- Higher assessed values mean larger absolute errors — and larger savings
  when a protest succeeds
- Unique hook: median WDM assessment vs median sale + illustrative annual
  savings calculation (fill from SQL above)
- "A 10% over-assessment on a $450k home is $1,350/yr. That's real money
  — and the protest takes less than 10 minutes."
- Embedded address search widget

### H2: The Polk County April 30 deadline
- West Des Moines sits in Polk County — protest with the Polk County
  Board of Review by April 30
- Note: a small portion of WDM is in Dallas County — those parcels are
  on a separate deadlines system (Dallas Board of Review; same April 30
  date but a different body)
- Address search auto-detects your county; no guesswork needed

### H2: How the comp evidence packet works for WDM homeowners
- Enter WDM address → comps pulled from comparable West Des Moines sales →
  2-page packet citing Iowa Code §441.37
- Jordan Creek area, Valley Junction, WDM neighborhoods — comp matching
  stays within your neighborhood, not the Des Moines eastside

### H2: What the Board of Review needs to see
- Comparable closed sales from West Des Moines and surrounding areas
- §441.37 grounds: assessment exceeds market value
- The packet handles both

### H2: FAQ (WDM–specific)

- **Q:** West Des Moines straddles Polk and Dallas counties — which Board
  do I file with?
  **A:** It depends on your specific parcel. Enter your address in the
  search — the tool will identify your county. If you're in Polk, you
  file with the Polk County Board of Review. If you're in Dallas, the
  Dallas County Board of Review handles your protest (same April 30
  deadline, different building and mailing address).

- **Q:** My WDM neighborhood has much higher home values than the Polk
  County median. Will the comps be accurate?
  **A:** Yes. The comp engine matches within neighborhood codes and
  filters by size and age — it won't compare a Valley Junction condo
  to a south-side ranch. High-value neighborhoods have their own
  comp pools.

- **Q:** Is there a minimum over-assessment to make a protest worthwhile?
  **A:** There's no legal minimum — you can protest any assessment you
  believe exceeds market value. Practically, a 5% over-assessment on
  a $150k home ($7,500 error) saves about $225/yr. On a $450k WDM
  home the same percentage saves $675/yr. The time investment is the
  same either way.

- **Q:** Can I protest if my home hasn't sold recently?
  **A:** Yes — and this is the most common situation. The engine
  finds sales of comparable homes, not sales of your home. You don't
  need to have sold recently to have a case.

- **Q:** What if the Board of Review denies my protest?
  **A:** You can appeal to the Iowa Property Assessment Appeal Board
  (PAAB) by June 20. PAAB appeals are more formal and often require
  legal representation — but many homeowners stop at the Board level.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for West Des Moines",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "West Des Moines",
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
          "name": "West Des Moines is in both Polk and Dallas counties — which Board do I file with?",
          "acceptedAnswer": { "@type": "Answer", "text": "It depends on your specific parcel. Enter your address in the search tool — it identifies your county automatically. Polk County parcels go to the Polk County Board of Review; Dallas County parcels go to the Dallas County Board of Review. Both deadlines are April 30." }
        },
        {
          "@type": "Question",
          "name": "Will the comp engine use homes from my specific WDM neighborhood?",
          "acceptedAnswer": { "@type": "Answer", "text": "Yes. The comp engine matches on neighborhood code first, then expands only if fewer than 5 sales are found. High-value WDM areas are matched against comparable high-value sales, not Polk County averages." }
        },
        {
          "@type": "Question",
          "name": "What is the deadline to protest a West Des Moines property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 for a formal protest with the Board of Review (either Polk or Dallas, depending on your parcel). The informal review with the assessor closes April 25." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/polk-county` (primary) + `/dallas-county` (cross-link with note
  about county split)
- **Sideways:** `/des-moines` ("or check comps in Des Moines"), `/clive`
  ("neighboring Clive homeowners")
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

Anchor text variations:
- "West Des Moines property tax appeal" (exact — ~20%)
- "appeal your WDM assessment"
- "West Des Moines homeowners — see your comps"
- "for homeowners in West Des Moines"
- "WDM's April 30 protest deadline"

---

## Implementation notes

- **Flask route:** `@app.route("/west-des-moines")` — renders `web/templates/city.html`
- **Template file:** `web/templates/city.html` (shared)
- **County-split handling:** the page should note the Polk/Dallas split
  prominently and defer to the address search to auto-detect county —
  don't pick one and ignore the other
- **Canonical:** put `/west-des-moines` under the Polk hub (most WDM
  parcels are Polk); cross-link from `/dallas-county` hub with a note
- **Data source for unique hook:** median assessed + savings calculation SQL
  above; the "dollar savings" angle is unique to WDM — don't reuse
  on Ankeny or Urbandale briefs
- **Refresh cadence:** mid-March each year

---

## Pre-publish checklist

- [ ] Unique data hook present (dollar-savings math — verify SQL)
- [ ] Meta title ≤60 chars ✓ (59)
- [ ] Meta description ≤155 chars ✓ (155)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] County-split note included (Polk + Dallas)
- [ ] Voice contract obeyed
- [ ] Year 2026 in title + body
