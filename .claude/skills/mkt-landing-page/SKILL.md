---
name: mkt-landing-page
description: Critique or generate landing page copy for tax-contester. Anchored on Joanna Wiebe (Copyhackers), Harry Dry (Marketing Examples), and the 5-second test. Invoke when the user asks about the homepage, hero, above-the-fold, conversion rate, CRO, or wants landing copy.
---

You produce conversion-focused landing page copy and critiques for
**Tax Contester**.

## Required inputs

- `marketing/BRAND.md` — voice, ICP, deadlines, anti-positioning.
- `marketing/positioning.md` — value prop, pillars. **Required.**
  If missing, stop and invoke `mkt-positioning` first.
- Optional: current page URL, screenshot, or HTML file path.

## Process

### Mode A — Critique

1. Run the **5-second test** mentally: cover the page, look at the hero
   for 5 seconds, then write down (a) what the product is, (b) who it's
   for, (c) what to do next. Note any of the three that aren't
   immediately answerable.
2. Run the **message-match audit**: does the hero match the implied
   traffic source intent? (Generic hero on a "[city] property tax"
   landing = wasted click.)
3. Run the **objection sequence** check: does the page address, in order,
   (1) is this real, (2) is it for me, (3) what's the catch, (4) what do
   I do next?
4. Score against the **quality bar** below and list violations as
   concrete edits.

### Mode B — Generate

1. Load `KNOWLEDGE.md` (frameworks) and `EXAMPLES.md` (hero swipe file).
2. Produce **2 hero variants** following different angles:
   - Variant A: audience + specificity
   - Variant B: deadline + loss frame
   (Optionally Variant C: anti-firm positioning, if relevant.)
3. Fill out `OUTPUT_TEMPLATE.md` and write to
   `marketing/landing/<page-name>.md`.
4. End the file with an **implementation checklist** of concrete edits
   to `web/templates/index.html` (and `web/static/styles.css` if the
   change is visual).

## Quality bar (reject your own draft if it fails any of these)

- **Hero names the customer or the place.** "Polk", "Dallas County",
  "Iowa homeowner" — not "everyone".
- **Hero subhead carries one specific number or proof element.** Not
  "save money" — "$300/yr median Polk savings", "30-day deadline",
  "381,000 sales in the database".
- **CTA verb is concrete and first-person.** "Check my assessment",
  "Find my parcel" — never "Get started", "Submit", "Learn more".
- **One page, one primary CTA.** Repeat the same CTA, don't add
  competing ones.
- **Voice contract obeyed** — no "leverage", "AI-powered",
  "revolutionary", etc. See BRAND.md.
- **One thing the page does NOT do** is named explicitly somewhere on
  the page (the "What this is NOT" section earns trust).

## When to re-run

- After every positioning update.
- After a meaningful product change (new county, new packet format,
  pricing introduced).
- Quarterly, with a fresh 5-second test against the live page.
