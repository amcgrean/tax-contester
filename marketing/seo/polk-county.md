# SEO Brief — Polk County (County Hub)

_Last updated: 2026-05-26_
_Type: county-hub_
_Tier: 1_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** polk county property tax appeal 2026
**Secondary:**
- polk county board of review 2026
- polk county property tax protest iowa
- how to appeal property tax polk county
- polk county assessor appeal deadline

## Intent classification

- [x] Navigation + Info hybrid (acceptable for a county hub — this is
  the destination when someone searches for the Board entity, and also
  wants process steps)

---

## Unique data hook

> **173,000 Polk County parcels. 381,000 recorded sales. One deadline:
> April 30.**
>
> Polk County is the largest county in Iowa by both population and
> assessed property value. More parcels means more assessments — and
> more that can be wrong.

SQL to get the real numbers for the current year:
```sql
-- Total parcels and sales in Polk
SELECT
  (SELECT count(*) FROM properties WHERE county = 'polk') AS polk_parcels,
  (SELECT count(*) FROM sales s
   JOIN properties p ON s.property_id = p.id
   WHERE p.county = 'polk') AS polk_sales,
  (SELECT count(*) FROM assessments a
   JOIN properties p ON a.property_id = p.id
   WHERE p.county = 'polk') AS polk_assessments;

-- Median assessed total 2026 vs 2025 (YoY shift)
SELECT
  tax_year,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY assessed_total) AS median_assessed
FROM assessments a
JOIN properties p ON a.property_id = p.id
WHERE p.county = 'polk' AND tax_year IN (2025, 2026)
GROUP BY tax_year ORDER BY tax_year;
```

---

## Meta

- **Title (57 chars):** `Polk County Property Tax Appeal 2026 | Free Packet`
- **Description (153 chars):** `April 30 deadline for Polk County homeowners. Free comp-based protest packet built from 381,000 real sales. Check your assessment in 2 minutes.`
- **Slug:** `/polk-county`
- **Canonical:** `https://tax-contester.vercel.app/polk-county`

---

## Page outline

### H1: Polk County Property Tax Appeal 2026

### H2: The April 30 deadline — what it means and what happens if you miss it
- Filing a formal protest with the Polk County Board of Review is
  required by April 30.
- Miss it and you wait until the 2027 assessment cycle.
- The informal review window with the assessor's office closes April 25
  — earlier than most homeowners realize.

### H2: How the Polk County Board of Review works
- The Board is separate from the assessor's office — it reviews protests
  filed by homeowners and rules by May 31.
- What they look at: comparable sales, market data, assessor methodology.
- What they don't accept: Zillow, opinion, or comparable asking prices
  (only closed sales).

### H2: Check your Polk County assessment free
- Embed address search widget (same as homepage — `#search-input`)
- Pull live: 173,000 Polk parcels searchable, 381,000 sales in the database

### H2: Polk County cities — find your city

Link grid to all Tier 1 + Tier 2 city pages:
- [Des Moines](/des-moines)
- [West Des Moines](/west-des-moines)
- [Ankeny](/ankeny)
- [Urbandale](/urbandale)
- [Waukee](/waukee)
- [Clive](/clive) _(coming soon — Tier 2)_
- [Johnston](/johnston) _(coming soon — Tier 2)_
- [Altoona](/altoona) _(coming soon — Tier 2)_

### H2: Iowa Code §441.37 — the legal grounds for protest
- Plain-English: §441.37 allows a property owner to protest if the
  assessment is not at actual market value or if there's inequality
  compared to similar properties.
- Link down to `/guide/iowa-code-441-37-explained`

### H2: FAQ

- **Q:** What's the difference between the informal review and the formal protest?
  **A:** The informal review is a conversation with the assessor's office
  (April 2–25). The formal protest is a written filing with the Board of
  Review (April 2–30). The Board is independent of the assessor. The
  formal protest is the one with legal teeth.

- **Q:** Do I need an attorney to protest my Polk County assessment?
  **A:** No. Iowa Code §441.37 allows any property owner to file their
  own protest. Tax Contester produces the comp evidence packet — you file
  it yourself with the Board of Review. Most successful homeowner protests
  are self-filed.

- **Q:** What if the Board rules against me?
  **A:** You can appeal the Board's decision to the Iowa Property
  Assessment Appeal Board (PAAB) by June 20. PAAB appeals are more
  formal — many homeowners stop at the Board of Review level.

- **Q:** Does the Polk County assessor's office handle protests?
  **A:** No. The assessor sets the assessment. The Board of Review is a
  separate body that adjudicates protests. Filing with the wrong office
  means your protest isn't heard.

- **Q:** How accurate are the comps?
  **A:** They come from the Polk County recorder — the same arms-length
  sales the Board already has on file. We filter for recency (24–36
  months), matching size (±20% sqft), matching age (±15 years), and
  property class.

---

## Schema.org JSON-LD

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Service",
      "name": "Property Tax Appeal Evidence for Polk County",
      "serviceType": "Property tax assessment appeal preparation",
      "areaServed": {
        "@type": "AdministrativeArea",
        "name": "Polk County, Iowa"
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
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://tax-contester.vercel.app" },
        { "@type": "ListItem", "position": 2, "name": "Iowa", "item": "https://tax-contester.vercel.app" },
        { "@type": "ListItem", "position": 3, "name": "Polk County", "item": "https://tax-contester.vercel.app/polk-county" }
      ]
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "What is the deadline to protest a Polk County property tax assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "April 30 is the deadline to file a formal protest with the Polk County Board of Review. The informal review with the assessor closes April 25." }
        },
        {
          "@type": "Question",
          "name": "Do I need an attorney to protest my Polk County assessment?",
          "acceptedAnswer": { "@type": "Answer", "text": "No. Iowa Code §441.37 allows any property owner to file their own protest with the Board of Review." }
        },
        {
          "@type": "Question",
          "name": "How accurate are the comparable sales used in the protest packet?",
          "acceptedAnswer": { "@type": "Answer", "text": "Comps come from the Polk County recorder — the same arms-length sales the Board of Review already has on file. They are filtered for recency, size, age, and property class." }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/` (homepage)
- **Down:** `/des-moines`, `/ankeny`, `/urbandale`, `/west-des-moines`, `/waukee`
- **Down (guides):** `/guide/how-to-appeal-property-tax-iowa`, `/guide/iowa-code-441-37-explained`

Anchor text variations from external pages:
- "Polk County property tax appeal" (exact match — ~20% max)
- "appeal your Polk County assessment"
- "Polk County Board of Review protest"
- "for Polk County homeowners"

---

## Implementation notes

- **Flask route:** `@app.route("/polk-county")` — renders `web/templates/county.html`
- **Template file:** `web/templates/county.html` (new; hub layout)
- **Data source for unique hook:** `properties` + `sales` + `assessments` tables
  — run the SQL above, cache result to a JSON file updated on each deploy
- **Refresh cadence:** mid-March each year (update year in title, refresh
  median assessment data); content stays evergreen otherwise
- **External links to include:** Polk County Assessor site + Board of Review
  contact page (outbound links to authoritative local gov = trust signal)

---

## Pre-publish checklist

- [ ] Unique data hook present (173K parcels, 381K sales — verify current counts)
- [ ] Meta title ≤60 chars ✓ (57)
- [ ] Meta description ≤155 chars ✓ (153)
- [ ] FAQPage has ≥3 questions ✓ (5)
- [ ] All internal links point to real pages (hold city links until city pages ship)
- [ ] Voice contract obeyed — no "leverage", "AI-powered", etc.
- [ ] Year (2026) in title + body
- [ ] BreadcrumbList included in schema ✓
