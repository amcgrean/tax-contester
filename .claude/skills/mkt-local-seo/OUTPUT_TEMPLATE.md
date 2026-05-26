# SEO Brief — <City>, <County> County

_Last updated: YYYY-MM-DD_
_Type: city | county-hub | guide_
_Tier: 1 | 2 | 3_
_Implements value prop from: `marketing/positioning.md`_

---

## Target keywords

**Primary:** ___
**Secondary:**
- ___
- ___
- ___

## Intent classification

- [ ] Action  (wants to file)
- [ ] Info  (wants steps / explanation)
- [ ] Navigation  (wants the entity / contact)
- [ ] Diagnostic  (wants a tool to check status)
- [ ] News  (wants the recent change)

Mixed intent? **Split the page.**

---

## Unique data hook

> ___

(At least one number no other page in this hub has. Pull from live
data — median sale, median assessment, top streets, sales volume,
deadline distance. If you can't produce one, this page is too thin.)

---

## Meta

- **Title (≤60 chars):** ___
- **Description (≤155 chars):** ___
- **Slug:** `/___`
- **Canonical:** `https://tax-contester.vercel.app/___`

---

## Page outline

### H1: ___

### H2: ___
- ___

### H2: ___
- ___

### H2: ___
- ___

### H2: FAQ
- **Q:** ___
  **A:** ___
- **Q:** ___
  **A:** ___
- **Q:** ___
  **A:** ___

(Minimum 3 FAQ items for valid FAQPage schema.)

---

## Schema.org JSON-LD

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
        {
          "@type": "Question",
          "name": "___",
          "acceptedAnswer": { "@type": "Answer", "text": "___" }
        }
      ]
    }
  ]
}
```

---

## Internal links

- **Up:** `/<county>-county`
- **Sideways:** `/<neighbor-1>`, `/<neighbor-2>`
- **Down:** `/guide/<topic>`

Anchor text variations (don't repeat exact-match more than ~20% of the
time):
- ___
- ___
- ___

---

## Implementation notes

- **Flask route:** ___
- **Template file:** ___
- **Data source for unique number:** ___
- **Refresh cadence:** ___
- **Notes:** ___

---

## Pre-publish checklist

- [ ] Unique data hook present and verifiably different from siblings
- [ ] Meta title ≤60 chars
- [ ] Meta description ≤155 chars
- [ ] FAQPage has ≥3 questions
- [ ] All internal links point to real pages (no `/coming-soon`)
- [ ] Voice contract obeyed (no "leverage", no "AI-powered", etc.)
- [ ] Mobile viewport sanity-check (375px)
- [ ] Year (2026) in title + body
