# Landing Page Brief — <page name>

_Last updated: YYYY-MM-DD_
_Implements value prop from: `marketing/positioning.md`_
_Target file: `web/templates/<file>.html`_

---

## Goals

- **Primary action:** ___
- **Secondary action:** ___
- **Traffic source assumed:** ___
- **5-second test must answer:** what / who / next-step

---

## Hero — Variant A (default)

- **Headline:** ___
- **Subhead:** ___
- **CTA button:** ___
- **Visual:** ___ (file path or description)
- **Trust strip:** ___

## Hero — Variant B (A/B candidate)

- **Headline:** ___
- **Subhead:** ___
- **CTA button:** ___

---

## Section order (top to bottom)

1. Hero
2. How it works (3 steps)
3. What you get (packet screenshot + callouts)
4. Why this is free
5. What this is NOT
6. FAQ (6 questions max)
7. Repeated CTA + deadline countdown

---

## Section copy

### How it works

1. **___.** ___
2. **___.** ___
3. **___.** ___

### What you get

- Callout 1: ___
- Callout 2: ___
- Callout 3: ___

### Why this is free (paragraph)

> ___

### What this is NOT

- ___
- ___
- ___
- ___

### FAQ

**Q:** ___
**A:** ___

**Q:** ___
**A:** ___

(...)

---

## 5-second test self-check

- What is this? ___
- Who is it for? ___
- What would I do next? ___

If any answer is fuzzy, revise the hero before publishing.

---

## Implementation checklist

- [ ] Update hero in `web/templates/index.html`
- [ ] Confirm countdown banner is still wired (`Apr 2–30 active`)
- [ ] Add packet screenshot to "What you get" section
- [ ] Add FAQ section
- [ ] Verify mobile breakpoints in `web/static/styles.css` (≤768, ≤480)
- [ ] Run 5-second test against the deployed page

---

## Open questions for the user

- [ ] Default variant (A or B) for first deploy?
- [ ] Packet screenshot — use the live `/api/packet/01004795950043`
      sample, or a sanitized mockup?
