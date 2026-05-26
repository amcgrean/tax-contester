# Landing Page Knowledge Pack

The curated principles behind `mkt-landing-page`. Anchored on Joanna
Wiebe (Copyhackers), Harry Dry (Marketing Examples), and ConversionXL.

---

## The job of a landing page

Move a visitor from *"should I care?"* to *"I want to try this"* in
under 10 seconds, then give them a frictionless first step. That's it.
Everything below serves that single job.

---

## The above-the-fold stack

```
[Headline]      — names the outcome OR the audience (ideally both)
[Subhead]       — adds proof / specificity / removes the top objection
[Primary CTA]   — concrete verb, low-commitment, first-person
[Visual]        — shows the actual product, not a stock photo
[Trust strip]   — counties served, packets generated, code citation
```

If any one of these is missing, the hero is incomplete. Order matters —
the eye reads top-down on desktop, and the first complete pattern wins.

---

## PAS (Problem → Agitation → Solution)

Joanna Wiebe's workhorse formula. For tax-contester:

- **Problem:** "Your 2026 assessment jumped 14%."
- **Agitate:** "The 30-day clock started the day that letter hit your
  mailbox."
- **Solution:** "Get the comp evidence — free, in two minutes."

Use PAS in: the hero subhead, email subject + first line, ad copy,
section intros. Do not use it in FAQ or footer.

---

## Message match (the #1 conversion lever)

Every traffic source carries an intent. The landing must match.

- "des moines property tax appeal" → hero MUST say Des Moines.
- "iowa assessment too high" → hero MUST say Iowa + assessment.
- "ankeny board of review" → hero MUST mention Ankeny + Board of Review.

Generic hero on a place-keyword landing page = wasted click. The fix is
not "write a better generic hero" — it's "make per-place landing
pages". (That's why `mkt-local-seo` exists; this skill produces the
template they share.)

---

## Specificity beats cleverness (Harry Dry's rule)

| Bad | Good |
|---|---|
| "Save on your property taxes." | "The median Polk County over-assessment is $14,200. Check yours." |
| "Easy to use." | "Enter your address. 2 minutes. PDF in hand." |
| "Trusted by homeowners." | "1,247 packets generated for Polk County in 2026." |
| "Built different." | "Built from 381,000 real Polk County sales." |

Numbers earn trust. Adjectives don't.

---

## Loss aversion + deadline

People act on losses ~2× more than equivalent gains. Frame both:

- **Loss:** "April 30 deadline — after that, you wait until next year."
- **Gain:** "Median Polk savings: $300/yr for as long as you own the
  home."

The countdown banner on the live site (`Apr 2–30 active, 60-day
heads-up`) is already doing some of this work — the landing copy should
amplify it, not duplicate it.

---

## The objection sequence (silent script every visitor runs)

A good page addresses these in order. If you skip one, the visitor
bounces at that step.

1. **Is this real?** → proof, code citation, screenshot of the packet.
2. **Is it for me?** → county check, address-search teaser, ICP signals.
3. **What's the catch?** → "Free. We don't represent you at the hearing."
4. **What do I do next?** → CTA + 2-line "how it works".

The objection sequence is also the section order of the page.

---

## CTA conventions (the small thing that compounds)

- **Verb-first.** "Check my assessment", not "Assessment check".
- **First-person ownership.** "my", not "your" — converts ~10–20% better
  in Wiebe's tests because the visitor mentally takes the action.
- **No "Submit", "Click here", "Get started", "Learn more".** They tell
  the visitor nothing.
- **Above the fold AND repeated after each scroll section.**
- **One primary CTA per page.** Secondary actions (FAQ, "how it works")
  are links, not buttons.

Examples for tax-contester:
- "Check my assessment"
- "Find my parcel"
- "See if I have a case"
- "Build my packet" (post-activation)

---

## The 5-second test

Show the page for 5 seconds, hide it, ask the tester:

1. What is it?
2. Who is it for?
3. What would I do next?

If any tester misses any answer, the hero is broken. This is the
single highest-signal test for a landing page; cheaper and faster than
A/B testing live traffic.

---

## Sections that earn their slot (template)

1. **Hero** (one of A/B/C variants)
2. **How it works** — 3 steps with the actual product UI screenshots
3. **What you get** — screenshot of the 2-page packet, callouts
4. **Why this is free** — short honest paragraph, builds trust
5. **What this is NOT** — anti-positioning, rare and powerful
6. **FAQ** — 6 questions max, the actual objections, not corporate Q&A
7. **Repeated CTA + deadline countdown**

Everything that isn't on this list needs to justify its existence.

---

## Anti-patterns to reject on sight

- Hero stock photo of a generic house with sun flare.
- Three feature columns of "Fast / Easy / Free" with no specifics.
- "Trusted by thousands" with no logos, numbers, or links.
- Lifestyle headline ("Take control of your finances.").
- Founder story above the fold.
- Pricing section when the product is free — say "Free." next to the
  CTA, move on.
- Email capture as the primary CTA when the actual product (address
  search) is one click away.

---

## Mobile-first reminder

The site already has tablet (≤768px) and phone (≤480px) breakpoints in
`web/static/styles.css`. Every hero variant must hold up on a 375px
viewport. If a headline wraps awkwardly there, rewrite shorter.

---

## What to read next (for the human curator)

- Joanna Wiebe — *Copyhackers* (entire site, esp. "Stop fundraising,
  start selling")
- Harry Dry — *Marketing Examples* (newsletter; the specificity gospel)
- ConversionXL / CXL — landing page courses
- Peep Laja — *Conversion Rate Optimization* fundamentals
