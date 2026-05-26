---
name: mkt-positioning
description: Produce positioning artifacts (ICP, value prop, messaging hierarchy, anti-positioning) for tax-contester. Anchored on April Dunford's framework. Invoke when the user asks "who is this for", "what's our message", or any other marketing skill needs a positioning anchor it doesn't have.
---

You produce positioning for **Tax Contester**. You are anchored on April
Dunford's *Obviously Awesome* framework, augmented with Jobs-to-be-Done.

## Required inputs

- `marketing/BRAND.md` — product facts, ICP v1, differentiators, voice.
- Optional: competitor URLs or screenshots the user pastes in.

If `marketing/BRAND.md` is missing, stop and tell the user — do not
guess product facts.

## Process

1. Load `KNOWLEDGE.md` (frameworks) and `EXAMPLES.md` (teardowns + Iowa-
   specific phrasings).
2. Run Dunford's five steps **explicitly**, in this order:
   1. Competitive alternatives (what does the customer do today instead?)
   2. Unique attributes (what only we have)
   3. Value (what those attributes deliver to the customer)
   4. Best-fit customer (segment that values it most)
   5. Market category (the shelf we sit on)
3. Pressure-test against the two Dunford tests:
   - *"Compared to ___, we are the only one that ___."*
   - *Would the customer understand the value without the category label?*
4. Produce `marketing/positioning.md` using `OUTPUT_TEMPLATE.md`.
5. End the file with one-sentence value prop + 3 messaging pillars +
   explicit anti-positioning ("things we will not say").

## Quality bar

- **Specific over clever.** "$400 saved on your Ankeny bill" beats
  "Save money".
- **Names a competitive alternative** by category if not by name (self-
  appeal cold, the 30%-firms, do nothing).
- **Identifies at least one anti-position** — a thing we will NOT say.
- **Honors voice contract** in BRAND.md. Reject your own draft if it
  contains "leverage", "AI-powered", "revolutionary", etc.

## When to re-run

Re-run positioning when any of these change:
- Pricing model
- ICP
- Geography
- A new significant differentiator (e.g. Dallas data loaded)
