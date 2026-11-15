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
    "johnston": {
        "parcels": "7,853", "median_assessed": "$386,700", "median_sale": "$374,495",
        "sales_since_2024": "662", "ppsf": "$211", "pct_over": "8.0%", "ratio_n": "363",
    },
    "clive": {
        "parcels": "3,356", "median_assessed": "$370,200", "median_sale": "$360,750",
        "sales_since_2024": "284", "ppsf": "$203", "pct_over": "16.8%", "ratio_n": "173",
    },
    "grimes": {
        "parcels": "5,817", "median_assessed": "$339,400", "median_sale": "$341,000",
        "sales_since_2024": "581", "ppsf": "$229", "pct_over": "9.9%", "ratio_n": "322",
    },
    "pleasant-hill": {
        "parcels": "4,247", "median_assessed": "$308,500", "median_sale": "$300,000",
        "sales_since_2024": "373", "ppsf": "$210", "pct_over": "13.5%", "ratio_n": "215",
    },
    "altoona": {
        "parcels": "7,839", "median_assessed": "$299,500", "median_sale": "$315,000",
        "sales_since_2024": "735", "ppsf": "$218", "pct_over": "7.9%", "ratio_n": "429",
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
        "description": ("Ankeny has the highest median assessment of Polk's four largest cities "
                        "($330,400). Check yours free against real Ankeny sales before April 30."),
        "hook_head": "Ankeny has the highest median assessment of Polk County's four largest cities: {median_assessed}.",
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
        "description": ("1 in 10 West Des Moines homes is assessed above $578,700, the top "
                        "end of Polk's four largest cities. Check yours free before April 30."),
        "hook_head": "West Des Moines has the most expensive top end of Polk County's four largest cities.",
        "hook_body": (
            "One in ten West Des Moines homes is assessed above $578,700, the highest 90th "
            "percentile among Des Moines, Ankeny, Urbandale and WDM. And {pct_over} of WDM homes that sold in 2025 "
            "carry a 2026 assessment more than 10% above their sale price. On a $578,700 "
            "assessment, a 10% error is $57,870 of value."),
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
    "johnston": {
        "name": "Johnston",
        "title": "Johnston Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("Johnston's median assessment is $386,700, the highest of any Polk "
                        "city over 5,000 homes. Check yours free before the April 30 deadline."),
        "hook_head": "Johnston has the highest median assessment of any Polk County city with more than 5,000 homes: {median_assessed}.",
        "hook_body": (
            "Across {parcels} Johnston homes, the median 2026 assessment is {median_assessed}, "
            "and 1 in 10 is assessed above $669,000. Assessments mostly track sales here: "
            "{pct_over} of homes sold in 2025 were assessed more than 10% above their sale "
            "price. At these values, though, even a small percentage error is real money."),
        "why_head": "Small percentages, big numbers",
        "why_body": (
            "On a $386,700 home, a 5% over-assessment is about $19,000 of value. The comp "
            "engine compares your home to recent Johnston sales of similar size, age and "
            "neighborhood, drawn from {sales_since_2024} arms-length sales since 2024."),
        "faq": [
            ("Johnston assessments mostly match sale prices. Is it worth checking?",
             "It takes two minutes, and the tool tells you if your assessment is fair. If it "
             "is, there's nothing to file. If it isn't, you have the evidence ready."),
            ("Where do Johnston homeowners file?",
             "With the Polk County Board of Review. Johnston homes are assessed by the Polk "
             "County Assessor."),
        ],
        "neighbors": ["grimes", "urbandale"],
    },
    "clive": {
        "name": "Clive",
        "title": "Clive Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("16.8% of Clive homes sold in 2025 are assessed 10%+ above their sale "
                        "price, second only to Des Moines. Check yours free before April 30."),
        "hook_head": "Clive has the second-highest over-assessment rate in Polk County.",
        "hook_body": (
            "Of {ratio_n} Clive homes that sold in 2025, {pct_over} carry a 2026 assessment "
            "more than 10% above the sale price. Only Des Moines is higher. Clive homes are "
            "also expensive: the median assessment is {median_assessed}, and 1 in 10 is "
            "assessed above $678,000, the highest top end of any city we cover."),
        "why_head": "Part of Clive is in Dallas County",
        "why_body": "Clive crosses the Polk–Dallas county line. Our comparable-sales data covers "
            "the Polk County side ({parcels} homes) today. If your home is on the Dallas "
            "side, the search won't find it yet, and your protest goes to the Dallas County "
            "Board of Review (same April 30 deadline).",
        "faq": [
            ("Clive is in two counties. Which Board of Review do I file with?",
             "It depends on your parcel. Polk County parcels go to the Polk County Board of "
             "Review and Dallas County parcels to the Dallas County Board. Both deadlines "
             "are April 30."),
            ("Why are Clive homes over-assessed more often?",
             "We can't say from the data alone. What we can show is how your own assessment "
             "compares to recent sales of similar homes nearby."),
        ],
        "neighbors": ["west-des-moines", "urbandale"],
    },
    "grimes": {
        "name": "Grimes",
        "title": "Grimes Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("Nearly half of Grimes homes were built since 2010, the newest of any "
                        "large Polk city. Compare yours to recent sales, free, before April 30."),
        "hook_head": "Grimes has the newest housing of any Polk County city with more than 5,000 homes: 47% were built since 2010.",
        "hook_body": (
            "The median Grimes home was built in 2008, and {parcels} homes carry a median "
            "2026 assessment of {median_assessed}. Grimes homes also sell for {ppsf} a square "
            "foot, near the top of the county. {pct_over} of homes sold in 2025 were assessed "
            "more than 10% above their sale price."),
        "why_head": "Part of Grimes is in Dallas County",
        "why_body": "Grimes crosses the Polk–Dallas county line. Our comparable-sales data covers "
            "the Polk County side ({parcels} homes) today. If your home is on the Dallas "
            "side, the search won't find it yet, and your protest goes to the Dallas County "
            "Board of Review (same April 30 deadline).",
        "faq": [
            ("My Grimes home is only a few years old. Can I protest?",
             "Yes. Any assessment can be protested if comparable sales show it's above market "
             "value. The comp engine compares your home to recent sales of similar-age homes."),
            ("Grimes is in two counties. Where do I file?",
             "Polk County parcels go to the Polk County Board of Review and Dallas County "
             "parcels to the Dallas County Board. Both deadlines are April 30."),
        ],
        "neighbors": ["johnston", "urbandale"],
    },
    "pleasant-hill": {
        "name": "Pleasant Hill",
        "title": "Pleasant Hill Property Tax Appeal {year} | Free Packet",
        "description": ("Pleasant Hill homes are over-assessed almost twice as often as "
                        "neighboring Altoona and Ankeny. Check yours free before April 30."),
        "hook_head": "Pleasant Hill homes are over-assessed almost twice as often as their east-side neighbors.",
        "hook_body": (
            "{pct_over} of Pleasant Hill homes sold in 2025 carry a 2026 assessment more than "
            "10% above their sale price. In neighboring Altoona it's 7.9%, and in Ankeny "
            "7.1%. Pleasant Hill has {parcels} homes with a median assessment of "
            "{median_assessed}."),
        "why_head": "Comps from Pleasant Hill, not the east side as a whole",
        "why_body": (
            "Pleasant Hill homes are compared to recent sales nearby with similar size and "
            "age. Its {sales_since_2024} arms-length sales since 2024 give the engine a "
            "workable local pool, and it only widens the search if it needs to."),
        "faq": [
            ("Why are Pleasant Hill assessments off more often?",
             "The data shows the gap but not the reason. Your own comp check tells you whether "
             "your home is one of them."),
            ("Where do Pleasant Hill homeowners file?",
             "With the Polk County Board of Review. Pleasant Hill homes are assessed by the "
             "Polk County Assessor."),
        ],
        "neighbors": ["altoona", "des-moines"],
    },
    "altoona": {
        "name": "Altoona",
        "title": "Altoona Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("About 1 in 3 Altoona homes were built since 2010, and assessments track "
                        "sales closely. Check yours free before the April 30 deadline."),
        "hook_head": "About 1 in 3 Altoona homes were built since 2010, and assessments here track sale prices closely.",
        "hook_body": (
            "Altoona has {parcels} homes with a median 2026 assessment of {median_assessed}. "
            "Only {pct_over} of homes sold in 2025 "
            "were assessed more than 10% above their sale price. Two minutes with real comps "
            "tells you whether yours is one of them."),
        "why_head": "A deep pool of recent sales",
        "why_body": (
            "With {sales_since_2024} arms-length sales since 2024, Altoona has one of the "
            "deeper comp pools among Polk suburbs. The engine matches on size, age and "
            "neighborhood before it looks anywhere else."),
        "faq": [
            ("Altoona assessments mostly match sales. Should I bother checking?",
             "It's free and takes two minutes. If your assessment is fair, the tool says so "
             "and there's nothing to file."),
            ("Where do Altoona homeowners file?",
             "With the Polk County Board of Review. Altoona homes are assessed by the Polk "
             "County Assessor."),
        ],
        "neighbors": ["pleasant-hill", "ankeny"],
    },
    "urbandale": {
        "name": "Urbandale",
        "title": "Urbandale Property Tax Appeal {year} | Free Evidence Packet",
        "description": ("About two-thirds of Urbandale homes were built 1960–1999. Compare yours "
                        "to same-era sales, free, before the April 30 Polk County deadline."),
        "hook_head": "About two-thirds of Urbandale homes were built between 1960 and 1999.",
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

CITY_ORDER = ["des-moines", "ankeny", "west-des-moines", "urbandale",
              "johnston", "altoona", "grimes", "pleasant-hill", "clive"]


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
