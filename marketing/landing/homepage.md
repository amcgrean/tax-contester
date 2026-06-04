# Landing Page Brief — Homepage (tax-contester.vercel.app)

_Last updated: 2026-05-26_
_Implements value prop from: `marketing/positioning.md`_
_Target files: `web/templates/index.html`, `web/static/screens.js`_

---

## Goals

- **Primary action:** Enter address → trigger parcel lookup (activation)
- **Secondary action:** Download protest packet (`/api/packet/<id>`)
- **Traffic source assumed:** Organic search ("polk county property tax protest",
  "des moines property tax assessment too high", "iowa board of review") + word
  of mouth from neighbors
- **5-second test must answer:** what / who / next-step

---

## Mode A — Critique of current page

The current page is a developer-facing tool shell, not a consumer landing page.
Key violations:

| Element | Current | Problem |
|---|---|---|
| `<title>` | "Iowa Property Tax Comp Engine" | Doesn't rank; no value prop; "comp engine" is jargon |
| `<meta name="description">` | "Iowa Property Tax Comp Engine · Polk + Dallas counties" | Duplicates title; no benefit |
| Topbar brand | "Iowa Property Tax Comp Engine v1.5" | Version number signals dev tool, erodes consumer trust |
| H1 | "Look up a parcel in Polk or Dallas County, then build a comp set in under a minute." | "Parcel" and "comp set" are assessor jargon — homeowners say "my house" and "similar homes nearby" |
| Kicker | "Step 1 / 5 · Find a property" | Internal workflow framing; cold visitor has no context for steps 2–5 |
| Lede | "...pull the latest assessment from the county's CAMA system and propose comparable sales within 0.75 mi." | "CAMA system" is jargon; "propose" undersells the data |
| CTA | "Search" | Generic; not first-person; gives no reason to act |
| Hero section | No mention of "free", no proof numbers, no audience signal, no deadline | Fails the objection sequence at step 1 |

**5-second test: FAIL on all three questions.**
- What is this? Unclear — "comp engine" means nothing to a homeowner
- Who is it for? Not stated
- What to do next? The search box is present but no reason to use it is given

---

## Hero — Variant A (default, recommended)

**Angle:** Audience + specificity

- **Headline:** Is your Polk County assessment too high?
  _(44 chars — safe for 375px mobile)_
- **Subhead:** Check it against 381,000 real Polk & Dallas County sales.
  Free comp evidence, ready to file by April 30.
  _(87 chars — wraps to 2 lines on mobile)_
- **CTA button:** Check my assessment →
- **Visual:** Address search box (already built) — no stock photo; the tool IS the visual
- **Trust strip (below CTA):** 173,000 parcels · 381,000 sales · Iowa Code §441.37 · Free

**5-second test against Variant A:**
- What is this? A tool to check whether your Polk County property tax assessment is too high
- Who is it for? Polk County homeowners (explicitly named)
- What to do next? "Check my assessment" — clear, first-person

---

## Hero — Variant B (A/B candidate)

**Angle:** Deadline + loss frame

- **Headline:** 30 days to contest your 2026 assessment.
  _(41 chars — safe for 375px mobile)_
- **Subhead:** Get free protest evidence built from Polk & Dallas County
  recorder sales — ready to file with the Board of Review.
  _(107 chars — wraps to 3 lines on mobile, acceptable)_
- **CTA button:** Find my parcel →
- **Visual:** Same address search box
- **Trust strip:** Free · No attorney · Iowa Code §441.37 · Polk + Dallas

**5-second test against Variant B:**
- What is this? A tool to protest a 2026 assessment before the 30-day deadline
- Who is it for? Iowa homeowners with a 2026 assessment (implied; could be sharper)
- What to do next? "Find my parcel" — clear, first-person

**Note:** Variant A is stronger for non-deadline-season traffic (the headline
holds year-round). Variant B performs better during the Apr 2–30 active
window when the deadline banner is already on screen — the two reinforce each
other. Ship Variant A as default; test B during protest season.

---

## Hero — Variant C (anti-firm, optional)

**Angle:** Anti-firm positioning

- **Headline:** The firms take 30%. You don't need them.
  _(39 chars ✓)_
- **Subhead:** Free protest evidence for Polk & Dallas County homeowners,
  built from real assessor data and ready to file by April 30.
  _(117 chars — 3 lines on mobile, acceptable)_
- **CTA button:** Start with my address →
- **Use when:** Running paid ads targeting "property tax appeal Iowa" or
  "property tax attorney fees iowa" — message-match is strong

---

## Section order (top to bottom)

1. Hero (Variant A default)
2. How it works — 3 steps, screenshots of actual UI
3. What you get — packet screenshot + callouts
4. Why this is free — short honest paragraph
5. What this is NOT — anti-positioning section
6. FAQ — 6 questions, real objections only
7. Repeated CTA + deadline countdown

---

## Section copy

### How it works

1. **Enter your address.** Fuzzy autocomplete finds your parcel in
   173,000 Polk and Dallas County records.
2. **See comparable sales.** Real recorder sales near you, scored
   against your home's size, age, and neighborhood.
3. **Download your packet.** 2-page PDF citing Iowa Code §441.37,
   ready to file with the Board of Review.

### What you get

A print-ready 2-page protest packet:

- **Comp table** — matched sales the Board of Review already has on file
- **§441.37 argument** — the statutory grounds laid out in the format the
  Board expects
- **Signature block + relief requested** — fill in, print, file

(Use a screenshot of `/api/packet/01004795950043` as the visual — it's
the real thing, not a mockup.)

### Why this is free

> Built by an Iowan who got tired of watching neighbors hand 30% of
> their savings to appeal firms for a $300 win. The assessor data is
> public. The Board of Review process is public. The only thing missing
> was a tool that put them together. So here it is — free.

_(Keep this paragraph exactly as-is. Short. Honest. No "Series A coming"
language. If monetization is introduced, rewrite this section first before
changing anything else.)_

### What this is NOT

> - **Not a tax attorney.** We don't represent you at the hearing.
> - **Not a guarantee.** The Board of Review can rule against you.
> - **Not for commercial property** or income-valued buildings.
> - **Not statewide** (yet). Polk + Dallas counties only.

_(This section earns trust from skeptics. Do not remove it.)_

### FAQ (6 questions — real objections only)

**Q: How do I know the comps are accurate?**
A: They come from the Polk County recorder — the same recorded sales the
Board of Review already has. They're filtered for arms-length transactions,
sale recency (last 24–36 months), and properties matching your size and age.

**Q: What if my assessment is actually fair?**
A: The tool will tell you. If your implied value from comps is within 10%
of your assessment, the verdict is FAIR — no packet needed.

**Q: Will the assessor be mad at me?**
A: No. Protesting is a legal right under Iowa Code §441.37. The Polk County
Assessor's office handles hundreds of protests every April. It's routine.

**Q: What happens after I file the packet?**
A: The Polk County Board of Review schedules a hearing. They'll review your
comps and issue a decision by May 31. If you're unsatisfied, you can appeal
further to the PAAB (Property Assessment Appeal Board) by June 20.

**Q: Why is this free?**
A: Because the 30%-of-savings model doesn't pencil out for small wins. If
your assessment drops $8,000 and your tax rate is 3%, you save $240/yr.
A firm taking 30% takes $72 of that — every year. This tool takes nothing.

**Q: Do you work outside Polk and Dallas?**
A: Not yet. Dallas data is coming. If you're in another Iowa county,
we're not the right tool today.

---

## 5-second test self-check

Against Variant A:

- **What is this?** A free tool to check whether your Polk County property
  tax assessment is too high, using real county sales data.
- **Who is it for?** Polk and Dallas County homeowners who got a 2026
  assessment notice.
- **What would I do next?** Type my address into the search box and click
  "Check my assessment."

All three answers are available within 5 seconds. Variant A passes.

---

## Implementation checklist

### `web/templates/index.html`

- [ ] Update `<title>` from "Iowa Property Tax Comp Engine" to:
  `Tax Contester — Free Property Tax Protest Tool · Polk & Dallas County, Iowa`
- [ ] Update `<meta name="description">` to:
  `Free comp evidence for Polk and Dallas County homeowners. Enter your address, get a Board-ready protest packet before the April 30 deadline.`
- [ ] Change `.brand-title` text from "Iowa Property Tax Comp Engine" to
  "Tax Contester"
- [ ] Remove `.brand-sub` "v1.5 · Polk + Dallas counties" — or replace with
  "Polk + Dallas County · Free" (no version number)

### `web/static/screens.js` — `renderSearch()` function

- [ ] Replace kicker `"Step 1 / 5 · Find a property"` with either:
  - Nothing (remove entirely), OR
  - `"Polk + Dallas County · Free"`
- [ ] Replace H1:
  **Before:** `"Look up a parcel in Polk or Dallas County, then build a comp set in under a minute."`
  **After (Variant A):** `"Is your Polk County assessment too high?"`
  _(Keep the `<em>` wrapper around the county name for emphasis if desired)_
- [ ] Replace lede paragraph:
  **Before:** `"Enter an address or parcel ID. We'll pull the latest assessment from the county's CAMA system and propose comparable sales within 0.75 mi."`
  **After:** `"Check it against 381,000 real Polk & Dallas County sales. Free comp evidence, ready to file by April 30."`
- [ ] Replace CTA button text: `"Search"` → `"Check my assessment"`
- [ ] Update `placeholder` on `#search-input`:
  **Before:** `"e.g. 4823 Grand Ave, Des Moines · or · 010-12345-678-000"`
  **After:** `"Your address — e.g. 4823 Grand Ave, Des Moines"`
  _(Remove parcel ID from placeholder — homeowners don't know their parcel ID)_
- [ ] Add a trust strip below the CTA button:
  ```html
  <p class="trust-strip">
    173,000 Polk parcels · 381,000 recorded sales · Iowa Code §441.37 · Free
  </p>
  ```
- [ ] Add the "How it works", "What you get", "Why this is free",
  "What this is NOT", and "FAQ" sections below the search form — these can
  be hidden once a search is active (CSS class toggle or JS)

### Styles (`web/static/styles.css`)

- [ ] Add `.trust-strip` style: small muted text, centered, below the CTA.
  Something like: `font-size: 12px; color: var(--ink-3); margin-top: 8px;`
- [ ] Add `.search-hero-sub-sections` or equivalent wrapping class for the
  below-fold landing content (How it works, FAQ, etc.) so it can be
  hidden/shown on search activation

---

## Open questions for Aaron

- [ ] **Default hero:** Variant A or B for launch? (Recommended: A — holds
  outside protest season)
- [ ] **Packet screenshot:** Use live `/api/packet/01004795950043` output as
  the "What you get" visual, or sanitize the address first?
- [ ] **Brand name in topbar:** Change to "Tax Contester" or keep the longer
  name? (Recommended: "Tax Contester" — shorter, more memorable)
- [ ] **"Admin" tab in nav:** Should this be visible to public visitors?
  Consider hiding it behind a query param or removing from the public nav.
- [ ] **Below-fold content:** Implement "How it works" etc. as collapsible/
  hidden sections once a user has searched, or always visible on first load?
