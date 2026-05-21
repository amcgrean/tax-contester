"""
comp_engine.py
--------------
Iowa Property Tax Comp Engine — V1 (rule-based, explainable)

Entry point:
    result = run_comps(parcel_id="10007320402000")
    result = run_comps(address="4111 beaver ave")
    print(format_report(result))

Algorithm:
    1. Look up subject property + 2026 assessment
    2. SQL candidate pull: same neighborhood, arms-length, last 24 months,
       sqft ±20%, year_built ±15 yrs. Auto-expand if < 5 candidates.
    3. Python scorer: weighted score across sqft match, recency,
       neighborhood, age, distance, lot size. Keep top 5-8.
    4. Implied value: median(price_per_sqft) * subject_sqft
    5. Verdict: assessment vs implied value ±10% threshold

Usage (CLI):
    python comp_engine.py --parcel-id 10007320402000
    python comp_engine.py --address "4111 Beaver Ave"
    python comp_engine.py --parcel-id 10007320402000 --json
"""

import os
import math
import json
import argparse
import logging
import statistics
from datetime import date, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

log = logging.getLogger("comp_engine")

# ── Config ────────────────────────────────────────────────────────────────────

SQFT_BAND        = 0.20    # ±20% living area
AGE_BAND         = 15      # ±15 years
LOOKBACK_PRIMARY = 24      # months — first attempt
LOOKBACK_EXPAND  = 36      # months — if < MIN_COMPS in primary window
MIN_COMPS        = 5       # minimum before expansion
MAX_COMPS        = 50      # SQL cap for candidate pool
KEEP_COMPS       = 8       # final comps to return (top N by score)

# Scoring weights (must sum to 1.0)
WEIGHTS = {
    "sqft"         : 0.30,
    "recency"      : 0.25,
    "neighborhood" : 0.15,
    "age"          : 0.15,
    "distance"     : 0.10,
    "lot"          : 0.05,
}

# Over/Under/Fair thresholds (assessment vs implied value)
OVER_THRESHOLD  = 1.10   # assessed > 110% of implied → over-assessed
UNDER_THRESHOLD = 0.90   # assessed < 90%  of implied → under-assessed

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(
        host    =os.getenv("DB_HOST", "localhost"),
        port    =int(os.getenv("DB_PORT", 5432)),
        dbname  =os.getenv("DB_NAME", "iowa_propertytax"),
        user    =os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "iowa2026"),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

# ── Step 1: Subject lookup ────────────────────────────────────────────────────

def get_subject(conn, parcel_id: str = None, address: str = None) -> Optional[dict]:
    cur = conn.cursor()

    if parcel_id:
        cur.execute("""
            SELECT p.*,
                   a.assessed_total, a.assessed_land, a.assessed_improvements,
                   a.assessed_dwelling, a.tax_year
            FROM properties p
            LEFT JOIN assessments a
                ON a.property_id = p.id AND a.tax_year = (
                    SELECT MAX(tax_year) FROM assessments
                    WHERE property_id = p.id
                )
            WHERE p.county_parcel_id = %s AND p.county = 'polk'
            LIMIT 1
        """, (parcel_id.strip(),))

    elif address:
        cur.execute("""
            SELECT p.*,
                   a.assessed_total, a.assessed_land, a.assessed_improvements,
                   a.assessed_dwelling, a.tax_year
            FROM properties p
            LEFT JOIN assessments a
                ON a.property_id = p.id AND a.tax_year = (
                    SELECT MAX(tax_year) FROM assessments
                    WHERE property_id = p.id
                )
            WHERE p.county = 'polk'
              AND p.address_raw ILIKE %s
            ORDER BY p.living_area_sqft DESC NULLS LAST
            LIMIT 1
        """, (f"%{address.strip()}%",))
    else:
        raise ValueError("Must supply parcel_id or address")

    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def get_subject_last_sale(conn, property_id: int) -> Optional[dict]:
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM sales
        WHERE property_id = %s
        ORDER BY sale_date DESC NULLS LAST
        LIMIT 1
    """, (property_id,))
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None

# ── Step 2: Candidate SQL ─────────────────────────────────────────────────────

CANDIDATE_SQL = """
    SELECT
        s.id          AS sale_id,
        s.sale_date,
        s.sale_price,
        s.price_per_sqft,
        s.arms_length_flag,
        s.non_arms_length_reason,
        s.deed_type,
        s.buyer,
        s.seller,
        p.id          AS property_id,
        p.county_parcel_id,
        p.address_raw,
        p.city,
        p.neighborhood_code,
        p.living_area_sqft,
        p.year_built,
        p.bedrooms,
        p.bathrooms,
        p.lot_sf,
        p.lot_acres,
        p.bldg_style,
        p.quality_grade,
        p.condition_rating,
        p.latitude,
        p.longitude,
        a.assessed_total  AS comp_assessed_total,
        a.tax_year        AS comp_assess_year
    FROM sales s
    JOIN properties p ON p.id = s.property_id
    LEFT JOIN assessments a
        ON a.property_id = p.id
        AND a.tax_year = (
            SELECT MAX(tax_year) FROM assessments WHERE property_id = p.id
        )
    WHERE p.county = 'polk'
      AND s.arms_length_flag = TRUE
      AND s.sale_date >= CURRENT_DATE - INTERVAL '{lookback} months'
      AND p.living_area_sqft BETWEEN %(sqft_lo)s AND %(sqft_hi)s
      AND p.year_built       BETWEEN %(yr_lo)s   AND %(yr_hi)s
      AND p.id != %(subject_pid)s
      {nbhd_filter}
    ORDER BY s.sale_date DESC
    LIMIT {limit}
"""

def pull_candidates(conn, subject: dict, lookback: int,
                    same_nbhd: bool = True) -> list[dict]:
    sqft = subject["living_area_sqft"] or 1500
    yr   = subject["year_built"] or 2000

    nbhd_filter = (
        "AND p.neighborhood_code = %(neighborhood_code)s"
        if same_nbhd else
        "AND p.tax_district = %(tax_district)s"
    )

    sql = CANDIDATE_SQL.format(
        lookback    = lookback,
        nbhd_filter = nbhd_filter,
        limit       = MAX_COMPS,
    )

    cur = conn.cursor()
    cur.execute(sql, {
        "sqft_lo"          : sqft * (1 - SQFT_BAND),
        "sqft_hi"          : sqft * (1 + SQFT_BAND),
        "yr_lo"            : yr - AGE_BAND,
        "yr_hi"            : yr + AGE_BAND,
        "subject_pid"      : subject["id"],
        "neighborhood_code": subject.get("neighborhood_code"),
        "tax_district"     : subject.get("tax_district"),
    })
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    return rows


def get_candidates(conn, subject: dict) -> tuple[list[dict], str]:
    """
    Returns (candidates, expansion_note).
    Tries same neighborhood first; expands if < MIN_COMPS.
    """
    # Pass 1: same neighborhood, 24 months
    candidates = pull_candidates(conn, subject, LOOKBACK_PRIMARY, same_nbhd=True)
    if len(candidates) >= MIN_COMPS:
        return candidates, "same neighborhood, last 24 months"

    # Pass 2: same neighborhood, 36 months
    candidates = pull_candidates(conn, subject, LOOKBACK_EXPAND, same_nbhd=True)
    if len(candidates) >= MIN_COMPS:
        return candidates, "same neighborhood, last 36 months (expanded window)"

    # Pass 3: same jurisdiction, 24 months
    candidates = pull_candidates(conn, subject, LOOKBACK_PRIMARY, same_nbhd=False)
    if len(candidates) >= MIN_COMPS:
        return candidates, "same jurisdiction (neighborhood expanded — limited sales)"

    # Pass 4: same jurisdiction, 36 months
    candidates = pull_candidates(conn, subject, LOOKBACK_EXPAND, same_nbhd=False)
    return candidates, "same jurisdiction, 36 months (maximum expansion)"

# ── Step 3: Scoring ───────────────────────────────────────────────────────────

def haversine_miles(lat1, lon1, lat2, lon2) -> float:
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(max(0, min(1, a))))


def score_candidate(subject: dict, comp: dict) -> tuple[float, dict]:
    """
    Returns (total_score 0-100, breakdown_dict).
    """
    breakdown = {}
    today = date.today()

    # ── sqft score ──
    s_sqft = subject.get("living_area_sqft") or 0
    c_sqft = comp.get("living_area_sqft") or 0
    if s_sqft and c_sqft:
        pct_diff = abs(s_sqft - c_sqft) / s_sqft
        breakdown["sqft"] = max(0.0, 1.0 - pct_diff / SQFT_BAND)
    else:
        breakdown["sqft"] = 0.5

    # ── recency score ──
    sale_date = comp.get("sale_date")
    if sale_date:
        if isinstance(sale_date, str):
            sale_date = date.fromisoformat(sale_date)
        days_ago = (today - sale_date).days
        if   days_ago <= 180:  breakdown["recency"] = 1.00
        elif days_ago <= 365:  breakdown["recency"] = 0.80
        elif days_ago <= 545:  breakdown["recency"] = 0.55
        else:                  breakdown["recency"] = 0.30
    else:
        breakdown["recency"] = 0.0

    # ── neighborhood score ──
    s_nbhd = subject.get("neighborhood_code") or ""
    c_nbhd = comp.get("neighborhood_code") or ""
    if s_nbhd and c_nbhd and s_nbhd == c_nbhd:
        breakdown["neighborhood"] = 1.00
    elif (subject.get("tax_district") or "") == (comp.get("tax_district") or ""):
        breakdown["neighborhood"] = 0.50
    else:
        breakdown["neighborhood"] = 0.25

    # ── age score ──
    s_yr = subject.get("year_built") or 0
    c_yr = comp.get("year_built") or 0
    if s_yr and c_yr:
        yr_diff = abs(s_yr - c_yr)
        breakdown["age"] = max(0.0, 1.0 - yr_diff / AGE_BAND)
    else:
        breakdown["age"] = 0.5

    # ── distance score ──
    s_lat = subject.get("latitude")
    s_lon = subject.get("longitude")
    c_lat = comp.get("latitude")
    c_lon = comp.get("longitude")
    if all(v is not None for v in [s_lat, s_lon, c_lat, c_lon]):
        dist = haversine_miles(s_lat, s_lon, c_lat, c_lon)
        comp["_distance_miles"] = round(dist, 3)
        if   dist <= 0.25:  breakdown["distance"] = 1.00
        elif dist <= 0.50:  breakdown["distance"] = 0.80
        elif dist <= 1.00:  breakdown["distance"] = 0.55
        elif dist <= 2.00:  breakdown["distance"] = 0.30
        else:               breakdown["distance"] = 0.10
    else:
        breakdown["distance"] = 0.50  # neutral if no coords

    # ── lot score ──
    s_lot = subject.get("lot_sf") or 0
    c_lot = comp.get("lot_sf") or 0
    if s_lot and c_lot:
        pct_diff = abs(s_lot - c_lot) / max(s_lot, 1)
        breakdown["lot"] = max(0.0, 1.0 - pct_diff / 0.50)  # ±50% band
    else:
        breakdown["lot"] = 0.50

    # ── weighted total ──
    total = sum(WEIGHTS[k] * v for k, v in breakdown.items())
    return round(total * 100, 1), breakdown


def score_all(subject: dict, candidates: list[dict]) -> list[dict]:
    scored = []
    for comp in candidates:
        score, breakdown = score_candidate(subject, comp)
        comp["_score"]     = score
        comp["_breakdown"] = breakdown
        scored.append(comp)
    return sorted(scored, key=lambda c: c["_score"], reverse=True)

# ── Step 4: Implied value + verdict ──────────────────────────────────────────

def compute_verdict(subject: dict, top_comps: list[dict]) -> dict:
    """
    Implied value: median(price_per_sqft across top comps) × subject sqft.
    Falls back to median(raw sale price) if sqft unavailable.
    """
    s_sqft    = subject.get("living_area_sqft")
    assessed  = subject.get("assessed_total")

    ppsf_vals = [c["price_per_sqft"] for c in top_comps
                 if c.get("price_per_sqft") and c["price_per_sqft"] > 0]

    if ppsf_vals and s_sqft:
        median_ppsf   = round(statistics.median(ppsf_vals), 2)
        implied_value = round(median_ppsf * s_sqft)
        method        = f"median(price/sqft) × {s_sqft:,} sqft"
    else:
        prices        = [c["sale_price"] for c in top_comps if c.get("sale_price")]
        if not prices:
            return {"error": "No sale prices in comps"}
        implied_value = round(statistics.median(prices))
        median_ppsf   = None
        method        = "median(raw sale price) — sqft unavailable"

    # Assessment ratio
    if assessed and assessed > 0 and implied_value > 0:
        ratio = assessed / implied_value
        if ratio >= OVER_THRESHOLD:
            verdict = "LIKELY OVER-ASSESSED"
            pct_str = f"+{(ratio - 1) * 100:.1f}% above market"
        elif ratio <= UNDER_THRESHOLD:
            verdict = "LIKELY UNDER-ASSESSED"
            pct_str = f"{(ratio - 1) * 100:.1f}% below market"
        else:
            verdict = "ROUGHLY FAIR"
            pct_str = f"{(ratio - 1) * 100:+.1f}% vs market"
        over_under_amt = round(assessed - implied_value)
    else:
        ratio     = None
        verdict   = "UNKNOWN (no assessment data)"
        pct_str   = "n/a"
        over_under_amt = None

    # Neighborhood median assessment ratio from DB data
    nbhd_ratios = [c.get("_nbhd_ratio") for c in top_comps
                   if c.get("_nbhd_ratio") is not None]
    nbhd_median_ratio = round(statistics.median(nbhd_ratios), 4) if nbhd_ratios else None

    return {
        "implied_value"      : implied_value,
        "median_ppsf"        : median_ppsf,
        "method"             : method,
        "assessed_total"     : assessed,
        "assessment_ratio"   : round(ratio, 4) if ratio else None,
        "over_under_amount"  : over_under_amt,
        "nbhd_median_ratio"  : nbhd_median_ratio,
        "verdict"            : verdict,
        "pct_vs_market"      : pct_str,
    }


def get_nbhd_stats(conn, subject: dict, lookback: int = 24) -> dict:
    """Neighborhood-wide market stats for context."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*)                       AS sale_count,
            AVG(s.price_per_sqft)          AS avg_ppsf,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_sqft)
                                           AS median_ppsf,
            AVG(a.assessed_total::float / NULLIF(s.sale_price, 0))
                                           AS avg_assess_ratio,
            MIN(s.sale_date)               AS oldest_sale,
            MAX(s.sale_date)               AS newest_sale
        FROM sales s
        JOIN properties p ON p.id = s.property_id
        LEFT JOIN assessments a
            ON a.property_id = p.id AND a.tax_year = %(tax_year)s
        WHERE p.county = 'polk'
          AND p.neighborhood_code = %(nbhd)s
          AND s.arms_length_flag = TRUE
          AND s.sale_date >= CURRENT_DATE - INTERVAL '{lookback} months'
          AND s.price_per_sqft > 0
    """.format(lookback=lookback), {
        "nbhd"    : subject.get("neighborhood_code"),
        "tax_year": subject.get("tax_year") or 2026,
    })
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else {}

# ── Explainability strings ────────────────────────────────────────────────────

def explain_comp(subject: dict, comp: dict) -> str:
    parts = []
    bd = comp.get("_breakdown", {})

    # Neighborhood
    s_nbhd = subject.get("neighborhood_code") or ""
    c_nbhd = comp.get("neighborhood_code") or ""
    if s_nbhd == c_nbhd:
        parts.append(f"same neighborhood ({c_nbhd})")
    else:
        parts.append(f"different neighborhood ({c_nbhd})")

    # sqft
    s_sqft = subject.get("living_area_sqft") or 0
    c_sqft = comp.get("living_area_sqft") or 0
    if s_sqft and c_sqft:
        diff_pct = (c_sqft - s_sqft) / s_sqft * 100
        parts.append(f"sqft {c_sqft:,} ({diff_pct:+.1f}%)")

    # Age
    s_yr = subject.get("year_built") or 0
    c_yr = comp.get("year_built") or 0
    if s_yr and c_yr:
        yr_diff = c_yr - s_yr
        parts.append(f"built {c_yr} ({yr_diff:+d} yrs)")

    # Recency
    sale_date = comp.get("sale_date")
    if sale_date:
        if isinstance(sale_date, str):
            sale_date = date.fromisoformat(sale_date)
        days = (date.today() - sale_date).days
        if days < 30:
            parts.append(f"sold {days}d ago")
        elif days < 365:
            parts.append(f"sold {days // 30}mo ago")
        else:
            parts.append(f"sold {days // 365}yr {(days % 365) // 30}mo ago")

    # Distance
    dist = comp.get("_distance_miles")
    if dist is not None:
        parts.append(f"{dist:.2f} mi away")

    return "; ".join(parts)

# ── Main entry point ──────────────────────────────────────────────────────────

def run_comps(parcel_id: str = None, address: str = None) -> dict:
    conn    = get_db()
    result  = {"status": "ok", "errors": []}

    try:
        # 1. Subject
        subject = get_subject(conn, parcel_id=parcel_id, address=address)
        if not subject:
            return {"status": "error", "errors": ["Property not found"]}
        result["subject"] = subject
        result["last_sale"] = get_subject_last_sale(conn, subject["id"])

        if not subject.get("living_area_sqft"):
            result["errors"].append(
                "Warning: subject has no living_area_sqft — comp selection may be limited"
            )

        # 2. Candidates
        candidates, expansion_note = get_candidates(conn, subject)
        result["expansion_note"] = expansion_note
        result["candidate_count"] = len(candidates)

        if not candidates:
            result["status"] = "no_comps"
            result["errors"].append("No comparable sales found. Try expanding search manually.")
            return result

        # 3. Score + select top comps
        scored = score_all(subject, candidates)
        top_comps = scored[:KEEP_COMPS]
        result["comps"] = top_comps
        result["all_candidates_count"] = len(candidates)

        # Add explanation to each comp
        for comp in top_comps:
            comp["_why_chosen"] = explain_comp(subject, comp)

        # 4. Neighborhood stats
        result["nbhd_stats"] = get_nbhd_stats(conn, subject)

        # 5. Verdict
        result["verdict"] = compute_verdict(subject, top_comps)

    except Exception as e:
        log.exception("comp engine error")
        result["status"] = "error"
        result["errors"].append(str(e))
    finally:
        conn.close()

    return result

# ── Text report ───────────────────────────────────────────────────────────────

def format_report(result: dict) -> str:
    lines = []
    sep   = "-" * 72

    if result.get("status") == "error":
        return f"ERROR: {result.get('errors')}"

    subj = result.get("subject", {})
    v    = result.get("verdict", {})
    nb   = result.get("nbhd_stats", {})

    lines += [
        sep,
        "IOWA PROPERTY TAX COMP ANALYSIS",
        sep,
        f"  Subject   : {subj.get('address_raw')}, {subj.get('city')} IA {subj.get('zip')}",
        f"  Parcel ID : {subj.get('county_parcel_id')}",
        f"  Neighborhood: {subj.get('neighborhood_code')}  |  District: {subj.get('tax_district')}",
        f"  Building  : {subj.get('living_area_sqft', 'n/a'):,} sqft  "
        f"| yr {subj.get('year_built', 'n/a')}  "
        f"| {subj.get('bedrooms', '?')}bd/{subj.get('bathrooms', '?')}ba  "
        f"| {subj.get('bldg_style', 'n/a')}",
        f"  Lot       : {int(subj['lot_sf']):,} sqft ({subj.get('lot_acres', 'n/a')} acres)"
        if subj.get('lot_sf') else "  Lot       : n/a",
        f"  Assessed  : ${v.get('assessed_total', 0):,.0f}  (tax year {subj.get('tax_year', 'n/a')})"
        if v.get('assessed_total') else "  Assessed  : n/a",
        "",
    ]

    # Last sale
    ls = result.get("last_sale")
    if ls:
        lines.append(
            f"  Last sale : ${ls['sale_price']:,.0f}  on {ls['sale_date']}  "
            f"({'arms-length' if ls.get('arms_length_flag') else 'non-arms-length'})"
        )
        lines.append("")

    # Neighborhood market
    if nb.get("sale_count"):
        lines += [
            f"  Neighborhood market ({result.get('expansion_note', '')}):",
            f"    {nb['sale_count']} arms-length sales  |  "
            f"median $/sqft ${nb.get('median_ppsf') or 0:.2f}  |  "
            f"avg assess ratio {(nb.get('avg_assess_ratio') or 0):.3f}",
            "",
        ]

    # Comps table
    lines += [sep, f"  TOP COMPS ({len(result.get('comps', []))} of {result.get('candidate_count', 0)} candidates)", sep]
    for i, c in enumerate(result.get("comps", []), 1):
        ppsf = c.get("price_per_sqft") or 0
        lines += [
            f"  #{i}  {c.get('address_raw')}, {c.get('city')}",
            f"      ${c.get('sale_price', 0):>10,.0f}  |  ${ppsf:>6.2f}/sqft  |  {c.get('sale_date')}",
            f"      Score {c['_score']:4.1f}/100  |  {c.get('_why_chosen', '')}",
            "",
        ]

    # Verdict
    lines += [
        sep,
        "  ASSESSMENT VERDICT",
        sep,
        f"  Implied market value : ${v.get('implied_value', 0):>12,.0f}",
        f"  Method               : {v.get('method','')}",
        f"  Current assessment   : ${v.get('assessed_total', 0):>12,.0f}",
        f"  Over/Under amount    : ${v.get('over_under_amount', 0):>+12,.0f}",
        f"  Assessment ratio     : {v.get('assessment_ratio', 0):.4f}  ({v.get('pct_vs_market','')})",
        "",
        f"  >> VERDICT: {v.get('verdict', 'UNKNOWN')}",
        sep,
    ]

    if result.get("errors"):
        lines += ["", "  NOTES:"] + [f"  • {e}" for e in result["errors"]]

    return "\n".join(lines)

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    ap = argparse.ArgumentParser(description="Iowa Property Tax Comp Engine")
    ap.add_argument("--parcel-id", help="14-digit Polk County parcel ID (dp)")
    ap.add_argument("--address",   help="Street address (partial match)")
    ap.add_argument("--json",      action="store_true", help="Output raw JSON")
    ap.add_argument("--debug",     action="store_true")
    args = ap.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.parcel_id and not args.address:
        ap.error("Supply --parcel-id or --address")

    result = run_comps(parcel_id=args.parcel_id, address=args.address)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_report(result))
