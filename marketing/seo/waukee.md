# SEO Brief — Waukee

_Last updated: 2026-05-26_
_Type: city_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** waukee property tax appeal 2026
**Secondary:**
- waukee iowa assessment too high 2026
- waukee property tax protest iowa
- dallas county waukee board of review
- waukee iowa home assessment 2026

## Intent classification

- [x] Action (wants to file — fast-growing city, many homeowners received
  first or second post-construction assessment in 2026)

---

## Unique data hook

> Waukee has grown faster than almost any Iowa city since 2020. When
> growth outpaces assessor capacity, new-construction assessments tend
> to cluster near builder cost — which may not reflect what comparable
> homes nearby actually sold for. **Waukee is where the comp gap is
> most likely to show up in 2026.**

**Special note — Dallas County data not yet loaded:**
> Waukee straddles Polk and Dallas counties. The comp engine is live
> for Polk County parcels only. Dallas County Waukee parcels will see
> the "Dallas coming soon" callout (see implementation notes below).

**SQL to check Polk-side Waukee coverage:**
```sql
-- Waukee parcels in Polk County (comp engine live)
SELECT
  p.county,
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
WHERE p.city ILIKE '%waukee%'
GROUP BY p.county;
```

---

## Meta

- **Title (57 chars):** `Waukee Property Tax Appeal 2026 | Free Evidence Packet`
- **Description (150 chars):** `Waukee is growing fast — and rapid appreciation means assessments drift. Free comp packet for Polk County Waukee homes. Dallas data coming. Check yours.`
- **Slug:** `/waukee`
- **Canonical:** `https://tax-contester.vercel.app/waukee`

---

## Page outline

### H1: Waukee Property Tax Appeal 2026

### H2: Why Waukee homeowners should check their 2026 assessment
- Fast growth = assessment lag or overreach — either can happen in a
  rapidly appreciating market
- Unique hook: Waukee growth rate + new-construction assessment pattern
  (fill from SQL above for Polk-side Waukee)
- **Honest note on county split:**
  "Waukee straddles Polk and Dallas counties. The comp engine is live
  for Polk County Waukee homes now. Dallas County Waukee — coming in 2026."
- Embedded address search widget (for Polk-side parcels)
- For Dallas-side Waukee: email capture ("Notify me when Dallas data
  launches")

### H2: Which county is your Waukee home in?
- The city of Waukee extends across the Polk/Dallas county line
- Polk County: the comp engine is live — enter your address to check now
- Dallas County: the comp engine is coming — drop your email below
- "Your mailing address says Waukee regardless of county — the parcel
  database knows which side you're on. Enter your address; we'll tell you."

### H2: The April 30 deadline
- Both Polk and Dallas boards of review have the same April 30 deadline
- Different mailing addresses and different boards — county matters
- Address search auto-detects county

### H2: How the evidence packet works for Waukee homeowners (Polk side)
- Enter Waukee address → comps from comparable Waukee and nearby sales
  → 2-page packet citing Iowa Code §441.37
- New construction comps: engine looks for similar new builds that sold,
  not just any Polk County home

### H2: FAQ (Waukee–specific)

- **Q:** I'm in Waukee — how do I know if I'm in Polk or Dallas County?
  **A:** Enter your address in the search tool. It will identify your
  county from the parcel record. If you're in Polk County, the comp
  engine is live now. If you're in Dallas County, the engine is coming —
  enter your email below to be notified when it launches.

- **Q:** I'm in Dallas County Waukee — can I still protest my 2026 assessment?
  **A:** Yes. The Dallas County Board of Review handles protests for Dallas
  County parcels, with the same April 30 deadline. Tax Contester's comp
  engine isn't live for Dallas yet, but the deadline and process are the
  same. Contact the Dallas County Assessor's office for informal review
  (closes April 25) or file directly with the Board of Review by April 30.

- **Q:** My Waukee home was just built. Can I protest the assessment?
  **A:** Yes. New construction is often assessed on a cost basis. If
  comparable new builds in Waukee sold for less than your assessed value,
  you have grounds under §441.37. The Polk side comp engine will look for
  those sales specifically.

- **Q:** What is the deadline to protest a Waukee property tax assessment?
  **A:** April 30 for both Polk County and Dallas County Board of Review.
  The informal review with the assessor closes April 25.

- **Q:** When will Dallas County Waukee be covered by the comp engine?
  **A:** We're loading Dallas County data in 2026. Drop your email above
  and we'll notify you the day it goes live — before the next assessment
  cycle.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for Waukee",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "City",
        "name": "Waukee",
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
          "name": "Is Waukee in Polk County or Dallas County?",
          "acceptedAnswer": { "@type": "Answer", "text": "Waukee straddles both. Enter your address in the search tool — it identifies your county from the parcel record. The comp engine is live for Polk County Waukee now; Dallas County Waukee coverage is coming in 2026." }
        },
        {
          "@type": "Question",
          "name": "What is the deadline to protest a Waukee property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 for both Polk County and Dallas County Board of Review. Informal review with the assessor closes April 25 in both counties." }
        },
        {
          "@type": "Question",
          "name": "Can I protest an assessment on a newly built Waukee home?",
          "acceptedAnswer": { "@type": "Answer", "text": "Yes. New construction is often assessed on a cost basis. If comparable new builds in Waukee sold for less than your assessed value, you have grounds under Iowa Code §441.37. The comp engine will search for those sales specifically (Polk County parcels only, currently)." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up (primary):** `/dallas-county` (Waukee's canonical hub is Dallas —
  most search intent will be Dallas-county-aware)
- **Up (secondary):** `/polk-county` (cross-link for Polk-side parcels)
- **Sideways:** `/west-des-moines` ("West Des Moines homeowners next door"),
  `/ankeny` ("Ankeny — another fast-growing Polk city")
- **Down:** `/guide/how-to-appeal-property-tax-iowa`

Anchor text variations:
- "Waukee property tax appeal" (exact — ~20%)
- "appeal your Waukee assessment"
- "Waukee homeowners — check your comps"
- "for homeowners in Waukee"
- "Waukee's April 30 protest deadline"

---

## Implementation notes

- **Flask route:** `@app.route("/waukee")` — renders `web/templates/city.html`
- **Template file:** `web/templates/city.html` (shared), but with a
  **conditional block:** if the user's detected parcel is in Dallas County,
  show the "notify me" email capture and suppress the comp search widget
- **County-split detection:** The address search already identifies county.
  Thread this into the city page render to show the right CTA per county.
- **Email capture (Dallas-side):** Simple form — name + email → store in
  Neon `leads` table or a separate table; no Mailchimp yet needed
- **Canonical note:** Set canonical to Waukee under Dallas hub once
  `/dallas-county` page ships. Cross-link from `/polk-county` hub as well.
- **Data source for unique hook:** Polk-side Waukee SQL above; the growth-rate
  angle differentiates from Des Moines (volume) and Urbandale (older stock)
- **Refresh cadence:** mid-March each year; update the "comp engine coming"
  note the day Dallas data loads (flip to "live now")

---

## Pre-publish checklist

- [ ] Unique data hook present (Waukee growth rate, new-construction angle)
- [ ] Meta title ≤60 chars ✓ (57)
- [ ] Meta description ≤155 chars ✓ (150)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] Dallas-side callout present — honest, not faked
- [ ] Email capture placeholder in template for Dallas-side users
- [ ] Voice contract obeyed
- [ ] Year 2026 in title + body
- [ ] "Dallas coming" note will be updated the day Dallas data loads
