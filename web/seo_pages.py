"""
Server-rendered SEO pages: Polk County hub + Tier 1 city pages.

Content specs live in marketing/seo/*.md; numbers come from
marketing/seo/_DATA_2026.md (pulled from Neon 2026-11-15). Re-pull those
numbers each mid-March and update STATS below. They are hardcoded on
purpose: no DB hit per page view, and every figure has a source.

Waukee is deliberately absent: 0 Waukee parcels in the DB (it is Dallas
County), so a Waukee page would offer a search that finds nothing.
"""
import json
from datetime import date

SITE = "https://tax-contester.vercel.app"
DATA_AS_OF = "November 2026"
ASSESSOR_URL = "https://www.assess.co.polk.ia.us/"

COUNTY_STATS = {
    "parcels": "173,173",
    "sales": "381,000",
    "arms_length": "245,715",
}

# Source: marketing/seo/_DATA_2026.md
STATS = {
    "des-moines": {
        "parcels": "71,053", "median_assessed": "$199,300", "median_sale": "$207,500",
        "sales_since_2024": "6,882", "ppsf": "$187", "pct_over": "17.2%", "ratio_n": "3,904",
    },
    "ankeny": {
        "parcels": "28,239", "median_assessed": "$330,400", "median_sale": "$325,000",
        "sales_since_2024": "2,992", "ppsf": "$218", "pct_over": "7.1%", "ratio_n": "1,694",
    },
    "west-des-moines": {
        "parcels": "14,126", "median_assessed": "$315,250", "median_sale": "$307,500",
        "sales_since_2024": "1,301", "ppsf": "$201", "pct_over": "13.6%", "ratio_n": "729",
    },
    "urbandale": {
        "parcels": "11,434", "median_assessed": "$304,950", "median_sale": "$300,000",
        "sales_since_2024": "1,054", "ppsf": "$202", "pct_over": "11.9%", "ratio_n": "624",
    },
}

COMMON_FAQ = [
    ("Do I need an attorney to protest my assessment?",
     "No. Iowa Code §441.37 lets any property owner file their own protest with "
     "the Board of Review. Tax Contester builds the comparable-sales packet; you "
     "file it yourself."),
    ("What if my assessment turns out to be fair?",
     "Then the tool will say so. If the value implied by comparable sales is within "
     "10% of your assessment, the verdict is FAIR and there's no case to file."),
]

CITIES = {
    "des-moines": {
        "name": "Des Moines",
        "title": "Des Moines Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("About 1 in 6 Des Moines homes sold in 2025 are assessed 10%+ above "
                        "their sale price. Check yours free before the April 30 deadline."),
        "hook_head": "About 1 in 6 Des Moines homes that sold in 2025 are assessed more than 10% above their sale price.",
        "hook_body": (
            "Of {ratio_n} Des Moines homes that sold in 2025, {pct_over} carry a 2026 "
            "assessment more than 10% above what the home actually sold for. That's the "
            "highest rate of any city we cover. Des Moines also has the widest range: "
            "{parcels} homes across 222 neighborhoods, with typical neighborhood medians "
            "running from about $144,000 to $418,000. When values swing that much "
            "block to block, comparing your home to the right neighborhood matters."),
        "why_head": "Why neighborhood-matched comps matter in Des Moines",
        "why_body": (
            "A mass-appraisal model has to value 71,000 homes at once. In a city where a "
            "few blocks can mean a $100,000 difference, some homes get pulled toward the "
            "wrong neighborhood's numbers. The comp engine looks at sales in your "
            "neighborhood first and only widens the search if it finds fewer than five "
            "good matches."),
        "faq": [
            ("My neighborhood has a wide range of home prices. Will the comps be accurate?",
             "The comp engine matches your neighborhood code first, then filters by size "
             "(±20% square feet) and age (±15 years). It only looks further out if it finds "
             "fewer than five comparable sales."),
            ("I live near the Des Moines city line. Does that matter?",
             "No. The search finds your parcel by address and uses its county record and "
             "neighborhood code, not the city name on your mail."),
        ],
        "neighbors": ["west-des-moines", "urbandale"],
    },
    "ankeny": {
        "name": "Ankeny",
        "title": "Ankeny Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("Ankeny has Polk County's highest median assessment ($330,400). "
                        "Check yours free against real Ankeny sales before the April 30 "
                        "protest deadline."),
        "hook_head": "Ankeny has the highest median assessment in Polk County: {median_assessed}.",
        "hook_body": (
            "Across {parcels} Ankeny homes, assessments track sale prices closely. The "
            "typical home that sold in 2025 was assessed at about 99.5% of its sale price, "
            "and {pct_over} were assessed more than 10% above it. That's the lowest rate of "
            "the cities we cover. So the honest advice for Ankeny is to check before you "
            "file. Two minutes with real comps tells you whether you're in that group."),
        "why_head": "Higher values, higher stakes",
        "why_body": (
            "At Ankeny's price points, even a 5% error is $16,000 or more of assessed "
            "value. The comp engine compares your home to recent Ankeny sales of similar "
            "size, age and neighborhood. With nearly 3,000 arms-length sales since 2024, "
            "there's usually a deep pool to match against."),
        "faq": [
            ("My Ankeny home is new. Can I still protest the assessment?",
             "Yes. Any assessment can be protested if comparable sales show it's above "
             "market value. In 2025 data, newer Ankeny homes were actually over-assessed "
             "less often than older ones, so let the comps decide."),
            ("Is there a separate Ankeny assessor?",
             "No. Ankeny homes are assessed by the Polk County Assessor, and protests go to "
             "the Polk County Board of Review."),
        ],
        "neighbors": ["urbandale", "des-moines"],
    },
    "west-des-moines": {
        "name": "West Des Moines",
        "title": "West Des Moines Property Tax Appeal {year} | Free Packet",
        "description": ("1 in 10 West Des Moines homes is assessed above $578,700, the "
                        "highest top end in Polk County. Check yours free before the "
                        "April 30 protest deadline."),
        "hook_head": "West Des Moines has the most expensive top end in Polk County.",
        "hook_body": (
            "One in ten West Des Moines homes is assessed above $578,700, the highest 90th "
            "percentile of any Polk city. And {pct_over} of WDM homes that sold in 2025 "
            "carry a 2026 assessment more than 10% above their sale price. On a $578,700 "
            "assessment, a 10% error is $57,870 of value, the biggest dollar stakes in "
            "the county."),
        "why_head": "Part of West Des Moines is in Dallas County",
        "why_body": (
            "West Des Moines crosses the Polk–Dallas county line. Our comparable-sales data "
            "covers the Polk County side ({parcels} homes) today. Dallas County data isn't "
            "loaded yet. If your home is on the Dallas side, the search won't find it, and "
            "your protest goes to the Dallas County Board of Review (same April 30 deadline)."),
        "faq": [
            ("I'm in West Des Moines. Which Board of Review do I file with?",
             "It depends on which county your parcel is in. Polk County parcels go to the "
             "Polk County Board of Review. Dallas County parcels go to the Dallas County "
             "Board of Review. Both deadlines are April 30."),
            ("Will the comps come from my part of West Des Moines?",
             "Yes. The engine matches your neighborhood code first, so a high-value home is "
             "compared to similar homes nearby, not to a county average."),
        ],
        "neighbors": ["des-moines", "urbandale"],
    },
    "urbandale": {
        "name": "Urbandale",
        "title": "Urbandale Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("About 65% of Urbandale homes were built 1960–1999. Compare yours "
                        "to same-era sales, free, before the April 30 Polk County deadline."),
        "hook_head": "About 65% of Urbandale homes were built between 1960 and 1999.",
        "hook_body": (
            "Urbandale's {parcels} homes are mostly split-levels, ranches and two-stories "
            "from the 1960s through the 1990s. The median 2026 assessment is "
            "{median_assessed}, and {pct_over} of homes that sold in 2025 were assessed "
            "more than 10% above their sale price. With so many same-era homes, there's a "
            "deep pool of close matches for yours."),
        "why_head": "Same-era comps, not new construction",
        "why_body": (
            "The comp engine only compares your home to sales within 15 years of its build "
            "year. A 1974 split-level gets measured against other 1960s–80s homes, not a "
            "2020 build across town."),
        "faq": [
            ("Will the comps be other homes like my 1970s split-level?",
             "The engine filters by year built (±15 years) and living area (±20%). In "
             "Urbandale that usually means homes of the same era and size."),
            ("Does this work for condos and townhomes?",
             "It works best for single-family homes. Condo comps are thinner. Try it, and "
             "if there aren't enough matches the tool will tell you."),
        ],
        "neighbors": ["des-moines", "ankeny"],
    },
}

CITY_ORDER = ["des-moines", "ankeny", "west-des-moines", "urbandale"]


def protest_window(today=None):
    """Next (or current) Apr 2–30 protest window."""
    today = today or date.today()
    year = today.year if today <= date(today.year, 4, 30) else today.year + 1
    start, end = date(year, 4, 2), date(year, 4, 30)
    days_to_end = (end - today).days
    return {
        "year": year,
        "open": start <= today <= end,
        "days_to_start": (start - today).days,
        "days_to_end": days_to_end,
    }


def _faq_ld(faq):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq
        ],
    }


def _deadline_faq(year):
    return (f"What is the deadline to protest my {year} assessment?",
            f"File a formal protest with the Board of Review between April 2 and April 30, "
            f"{year}. The informal review with the assessor's office runs April 2–25.")


def city_context(slug):
    c = CITIES[slug]
    s = STATS[slug]
    win = protest_window()
    faq = [_deadline_faq(win["year"])] + c["faq"] + COMMON_FAQ
    url = f"{SITE}/{slug}"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "name": f"Property Tax Appeal Evidence for {c['name']}",
                "serviceType": "Property tax assessment appeal preparation",
                "url": url,
                "areaServed": {
                    "@type": "City", "name": c["name"],
                    "containedInPlace": {"@type": "AdministrativeArea", "name": "Polk County, Iowa"},
                },
                "provider": {"@type": "Organization", "name": "Tax Contester", "url": SITE},
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Polk County", "item": SITE + "/polk-county"},
                    {"@type": "ListItem", "position": 3, "name": c["name"], "item": url},
                ],
            },
            _faq_ld(faq),
        ],
    }
    return {
        "kind": "city",
        "slug": slug,
        "name": c["name"],
        "title": c["title"].format(year=win["year"]),
        "description": c["description"],
        "canonical": url,
        "h1": f"{c['name']} Property Tax Appeal {win['year']}",
        "hook_head": c["hook_head"].format(**s),
        "hook_body": c["hook_body"].format(**s),
        "why_head": c["why_head"],
        "why_body": c["why_body"].format(**s),
        "stats": s,
        "faq": faq,
        "neighbors": [(n, CITIES[n]["name"]) for n in c["neighbors"]],
        "window": win,
        "data_as_of": DATA_AS_OF,
        "assessor_url": ASSESSOR_URL,
        "jsonld": json.dumps(ld, ensure_ascii=False, indent=1),
    }


def county_context():
    win = protest_window()
    faq = [
        _deadline_faq(win["year"]),
        ("What's the difference between the informal review and a formal protest?",
         "The informal review is a conversation with the assessor's office (April 2–25). "
         "The formal protest is a written filing with the Board of Review (April 2–30). "
         "The Board is separate from the assessor, and the formal protest is the one "
         "that gets a ruling."),
        ("What happens after I file?",
         "The Board of Review issues decisions by May 31. If you disagree, you can appeal "
         "to Iowa's Property Assessment Appeal Board (PAAB), generally by June 20."),
        ("Where does the sales data come from?",
         "Official Polk County assessor (CAMA) records and recorded sales. Comps are "
         "limited to arms-length sales from the last 24–36 months."),
    ] + COMMON_FAQ
    url = f"{SITE}/polk-county"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "name": "Property Tax Appeal Evidence for Polk County",
                "serviceType": "Property tax assessment appeal preparation",
                "url": url,
                "areaServed": {"@type": "AdministrativeArea", "name": "Polk County, Iowa"},
                "provider": {"@type": "Organization", "name": "Tax Contester", "url": SITE},
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Polk County", "item": url},
                ],
            },
            _faq_ld(faq),
        ],
    }
    return {
        "kind": "county",
        "slug": "polk-county",
        "name": "Polk County",
        "title": f"Polk County Property Tax Appeal {win['year']} | Free Packet",
        "description": (f"Free comp evidence for Polk County homeowners, built from "
                        f"{COUNTY_STATS['sales']} recorded sales. Check your assessment "
                        f"before the April 30 Board of Review deadline."),
        "canonical": url,
        "h1": f"Polk County Property Tax Appeal {win['year']}",
        "county_stats": COUNTY_STATS,
        "cities": [(slug, CITIES[slug]["name"], STATS[slug]) for slug in CITY_ORDER],
        "faq": faq,
        "window": win,
        "data_as_of": DATA_AS_OF,
        "assessor_url": ASSESSOR_URL,
        "jsonld": json.dumps(ld, ensure_ascii=False, indent=1),
    }


def sitemap_urls():
    return [SITE + "/", SITE + "/polk-county"] + [f"{SITE}/{s}" for s in CITY_ORDER]
