# Tax Contester — Brand & Product Context

> **Loaded first by the `marketing-director` agent on every invocation.**
> If a product fact changes (pricing, geography, ICP, deadlines), update
> this file FIRST. Every marketing artifact downstream assumes this is current.

_Last updated: 2026-05-26_

---

## Product

**Tax Contester** — https://tax-contester.vercel.app
A free web app that helps Iowa homeowners contest over-assessed property
taxes. Enter your address, get a comp-based verdict, download a print-ready
protest packet that cites Iowa Code §441.37.

Built on real assessor CAMA data: 173K Polk parcels, 381K sales, 527K
assessment records (as of 2026-05-26). Dallas County data scraper exists
but has not been loaded yet.

---

## ICP — v1

**DIY homeowners in Polk + Dallas counties, Iowa.**

- **Demographics:** 35–70, own a single-family home, received a 2026
  assessment notice they suspect is too high.
- **Comfort level:** Will use a web form. Will not hire a tax attorney.
  Will not write code. Suspicious of slick SaaS pitches.
- **Pain:** Property tax bill jumped. Assessor's notice is opaque.
  The 30–50%-of-savings firms feel like a ripoff when the win is $200–$800.
  The April 30 deadline feels intimidating.
- **Trigger event:** Receives the 2026 assessment notice in early April
  → "I have 30 days to do something."
- **Disqualifiers:** Commercial property owners, multi-state portfolios,
  anyone whose property is income-valued, anyone outside Polk/Dallas.

---

## Geography — v1

**Polk + Dallas counties only.** Des Moines metro.

Priority cities (by intent volume × tax base):

| Tier | Cities |
|---|---|
| 1 (must) | Des Moines, West Des Moines, Ankeny, Waukee, Urbandale |
| 2 (should) | Clive, Johnston, Altoona, Pleasant Hill, Norwalk |
| 3 (if data supports) | Grimes, Windsor Heights, Adel, Van Meter |

~20 zips total. Polk has real comp data live; Dallas city pages can ship
with deadline + Board of Review info but must flag that the comp engine
is "Polk first, Dallas coming".

---

## Pricing & monetization

**Free. No monetization in place.**

Marketing optimizes for, in order:
1. **Protest packets generated** (primary North Star)
2. **Returning users next April** (this is an annual job)
3. **Word-of-mouth referrals** (the only viable growth channel at $0 CAC)

When monetization arrives, update this section and re-run
`mkt-positioning` — pricing changes the message.

---

## Core differentiators (the things we say uniquely)

1. **Real county-level data.** Polk CAMA + recorder sales, not generic
   Zillow estimates. 173K parcels, 381K arms-length sales.
2. **Comp engine, not a complaint form.** 4-pass weighted scoring explains
   *why* an assessment is off, not just that it is.
3. **Print-ready 2-page packet.** Cites Iowa Code §441.37. Ready to file
   with the Polk County Board of Review.
4. **Free.** No contingency cut. No subscription.
5. **Built by an Iowan.** Speaks Iowa property tax — knows the deadline,
   the Board of Review, the §441.37 grounds.

---

## Key dates (Iowa property tax calendar)

| Date | Event |
|---|---|
| Early April | Assessment notices mailed |
| Apr 2 – Apr 25 | Informal review window (with assessor) |
| Apr 2 – Apr 30 | **Formal protest window (Board of Review)** ← marketing pivot point |
| By May 31 | Board of Review decisions issued |
| By Jun 20 | PAAB appeal deadline |

The site already has a `deadline countdown banner` (active Apr 2–30,
heads-up 60 days prior). Marketing campaigns should align to this calendar.

---

## Voice & tone

- **Plainspoken Midwestern.** Not slick SaaS.
- **Confident on the data, humble on the verdict.** "Here's the evidence,
  you decide." Never promises savings.
- **Respectful of the assessor.** The assessor is a fellow Iowan doing
  their job — don't disparage.
- **Specific over clever.** Numbers, street names, deadlines.

**Words to avoid:** disrupting, AI-powered, revolutionary, leverage,
synergy, "unlock", "supercharge", "game-changing".

**Words that work:** evidence, comps, fair, neighbor, your assessment,
the deadline, the Board of Review, Iowa Code, packet.

---

## What this tool is NOT (anti-positioning)

- Not a tax attorney. Doesn't represent you at the hearing.
- Not a savings guarantee. The Board of Review can rule against you.
- Not for commercial or income-valued properties.
- Not a national tool. Polk + Dallas only.

---

## Current funnel — known state

- **Traffic source:** ~0. No marketing run yet.
- **Landing page:** `web/templates/index.html` (Flask + vanilla JS SPA).
- **Activation event:** protest packet downloaded (`/api/packet/<id>`).
- **Analytics installed:** none. This is a gap; flag for `mkt-analytics`
  skill when it ships.

---

## Open positioning questions (resolve before scaling)

- [ ] Lead with "free" or with "evidence"? (Free wins clicks, evidence
      wins trust.)
- [ ] Single-county landing variants vs one Des Moines metro page?
- [ ] Do we name the 30%-firms in anti-positioning, or stay polite?
