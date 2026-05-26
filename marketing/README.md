# Marketing — Tax Contester

This directory holds the marketing **artifacts** (positioning, landing
copy, SEO briefs) produced by the `marketing-director` agent and its
sub-skills.

The agent and skills themselves live in `.claude/`:

```
.claude/
├── agents/
│   └── marketing-director.md       # router / orchestrator
└── skills/
    ├── mkt-positioning/
    ├── mkt-landing-page/
    └── mkt-local-seo/
```

## How to use it

In Claude Code, invoke the director:

> "Use the marketing-director agent to draft positioning."

or for a specific skill:

> "Run mkt-local-seo for the Tier 1 Polk cities."

The agent loads `BRAND.md` first on every call. Keep that file current.

## Files in this directory

| Path | Owner | Purpose |
|---|---|---|
| `BRAND.md` | Human (you) | Product facts, ICP, voice, deadlines. Source of truth. |
| `positioning.md` | `mkt-positioning` skill | Value prop, pillars, anti-positioning. Generated. |
| `landing/` | `mkt-landing-page` skill | Hero variants, page briefs. Generated. |
| `seo/` | `mkt-local-seo` skill | One brief per city/county/guide page. Generated. |

## Update order matters

If a product fact changes (pricing, geography, ICP), update in this order:

1. `BRAND.md` — humans only
2. `positioning.md` — re-run `mkt-positioning`
3. `landing/*.md` — re-run `mkt-landing-page`
4. `seo/*.md` — re-run `mkt-local-seo`

Skipping a step downstream means you're shipping copy built on a stale value prop.
