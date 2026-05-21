"""
Iowa Property Tax Comp Engine — Flask web app
Serves the SPA shell + API endpoints backed by comp_engine.py
"""

import sys
import os
import statistics
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# Make comp_engine importable from the parent taxes directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import comp_engine as ce
import psycopg2
import psycopg2.extras

app = Flask(__name__)


# ─────────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host="localhost",
        dbname="iowa_propertytax",
        user="postgres",
        password="iowa2026",
    )


def query(sql, params=()):
    """Run SELECT → list of plain dicts."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def scalar(sql, params=()):
    """Run SELECT → first col of first row."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None


# ─────────────────────────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────────────────────────

def to_float(v):
    """Convert Decimal or any numeric to float; None or non-numeric → None."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def fmt_money(v):
    if v is None:
        return "—"
    return f"${int(float(v)):,}"


def fmt_date(d):
    if d is None:
        return "—"
    if isinstance(d, (datetime, date)):
        return d.strftime("%b %Y")
    return str(d)


def pct_change(new, old):
    new = to_float(new)
    old = to_float(old)
    if old and old != 0:
        return (new - old) / old * 100
    return None


# ─────────────────────────────────────────────────────────────────
# SPA shell
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────────
# API: Autocomplete  (fast typeahead — debounced from frontend)
# ─────────────────────────────────────────────────────────────────

@app.route("/api/autocomplete")
def api_autocomplete():
    q = request.args.get("q", "").strip()
    county = request.args.get("county", "both").lower()

    if len(q) < 2:
        return jsonify({"suggestions": []})

    county_sql = ""
    if county == "polk":
        county_sql = "AND p.county = 'polk'"
    elif county == "dallas":
        county_sql = "AND p.county = 'dallas'"

    # Parcel ID shortcut
    clean = q.replace("-", "").replace(" ", "")
    if clean.isdigit() and len(clean) >= 6:
        rows = query(f"""
            SELECT p.county_parcel_id, p.address_raw, p.city, p.county
            FROM properties p
            WHERE p.county_parcel_id ILIKE %s {county_sql}
            LIMIT 8
        """, (f"{q}%",))
        return jsonify({"suggestions": [
            {"label": f"{r['address_raw']} — {r['county_parcel_id']}",
             "address": r["address_raw"], "city": r["city"],
             "parcel_id": r["county_parcel_id"], "county": r["county"]}
            for r in rows
        ]})

    # Fuzzy address match using pg_trgm similarity
    # Split input into tokens so "42nd des moines" matches "808 42ND ST DES MOINES"
    tokens = [t for t in q.upper().split() if t]
    like = "%" + "%".join(tokens) + "%"

    rows = query(f"""
        SELECT p.county_parcel_id, p.address_raw, p.city, p.county,
               similarity(upper(p.address_raw), %s) AS sim
        FROM properties p
        WHERE upper(p.address_raw) ILIKE %s {county_sql}
        ORDER BY sim DESC, p.address_raw
        LIMIT 8
    """, (q.upper(), like))

    return jsonify({"suggestions": [
        {"label": f"{r['address_raw']}, {r['city']}",
         "address": r["address_raw"], "city": r["city"],
         "parcel_id": r["county_parcel_id"], "county": r["county"]}
        for r in rows
    ]})


# ─────────────────────────────────────────────────────────────────
# API: Search
# ─────────────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    county = request.args.get("county", "both").lower()

    if not q:
        return jsonify({"results": [], "error": None})

    county_sql = ""
    if county == "polk":
        county_sql = "AND p.county = 'polk'"
    elif county == "dallas":
        county_sql = "AND p.county = 'dallas'"

    results = []

    # Try parcel ID match first
    clean = q.replace("-", "").replace(" ", "")
    if clean.isdigit() and len(clean) >= 8:
        results = query(f"""
            SELECT p.id, p.county_parcel_id, p.address_raw, p.city, p.state, p.zip,
                   p.county, p.owner_name,
                   a.assessed_total, a.tax_year
            FROM properties p
            LEFT JOIN assessments a ON a.property_id = p.id
                AND a.tax_year = (SELECT MAX(a2.tax_year) FROM assessments a2 WHERE a2.property_id = p.id)
            WHERE (p.county_parcel_id ILIKE %s OR p.alternate_parcel_id ILIKE %s)
            {county_sql}
            LIMIT 10
        """, (f"%{q}%", f"%{clean}%"))

    # Fallback: address search
    if not results:
        terms = [t.strip() for t in q.replace(",", " ").split() if t.strip()]
        like = "%" + " ".join(terms) + "%"
        results = query(f"""
            SELECT p.id, p.county_parcel_id, p.address_raw, p.city, p.state, p.zip,
                   p.county, p.owner_name,
                   a.assessed_total, a.tax_year
            FROM properties p
            LEFT JOIN assessments a ON a.property_id = p.id
                AND a.tax_year = (SELECT MAX(a2.tax_year) FROM assessments a2 WHERE a2.property_id = p.id)
            WHERE p.address_raw ILIKE %s
            {county_sql}
            ORDER BY p.address_raw
            LIMIT 20
        """, (like,))

    def shape(r):
        county_name = (r["county"] or "").title()
        return {
            "property_id": r["id"],
            "parcel_id": r["county_parcel_id"] or "—",
            "address": r["address_raw"] or "—",
            "city_state": f"{r['city'] or ''}, {county_name} County",
            "owner": r["owner_name"] or "—",
            "assessed_value": to_float(r["assessed_total"]),
            "assessed_value_fmt": fmt_money(r["assessed_total"]),
            "county": county_name,
        }

    return jsonify({"results": [shape(r) for r in results], "error": None})


# ─────────────────────────────────────────────────────────────────
# API: Parcel detail
# ─────────────────────────────────────────────────────────────────

@app.route("/api/parcel/<parcel_id>")
def api_parcel(parcel_id):
    rows = query("""
        SELECT p.*,
               a.assessed_total, a.assessed_land, a.assessed_improvements,
               a.assessed_dwelling, a.tax_year, a.gross_taxes_due, a.net_taxes_due
        FROM properties p
        LEFT JOIN assessments a ON a.property_id = p.id
            AND a.tax_year = (SELECT MAX(a2.tax_year) FROM assessments a2 WHERE a2.property_id = p.id)
        WHERE p.county_parcel_id = %s OR p.id::text = %s
        LIMIT 1
    """, (parcel_id, parcel_id))

    if not rows:
        return jsonify({"error": "Parcel not found"}), 404

    p = rows[0]
    prop_id = p["id"]
    tax_year = p["tax_year"] or 2026

    # All assessments (for chart + tax history)
    history = query("""
        SELECT tax_year, assessed_total, assessed_land, assessed_improvements,
               gross_taxes_due, net_taxes_due
        FROM assessments
        WHERE property_id = %s
        ORDER BY tax_year
    """, (prop_id,))

    # Most recent arms-length sale
    last_sale_rows = query("""
        SELECT sale_price, sale_date, deed_type
        FROM sales
        WHERE property_id = %s AND arms_length_flag = TRUE
        ORDER BY sale_date DESC NULLS LAST
        LIMIT 1
    """, (prop_id,))
    last_sale = last_sale_rows[0] if last_sale_rows else None

    # YoY change — convert Decimal → float for arithmetic
    current_val = to_float(p["assessed_total"])
    prev_rows = query("""
        SELECT assessed_total FROM assessments
        WHERE property_id = %s AND tax_year = %s
        LIMIT 1
    """, (prop_id, tax_year - 1))
    prev_val = to_float(prev_rows[0]["assessed_total"]) if prev_rows else None

    yoy_pct = pct_change(current_val, prev_val) if (current_val and prev_val) else None
    yoy_amt = (current_val - prev_val) if (current_val and prev_val) else None

    # Estimated taxes — use actual if we have it, else rough rate
    est_taxes = to_float(p.get("gross_taxes_due") or p.get("net_taxes_due"))
    if not est_taxes and current_val:
        est_taxes = round(current_val * 0.019)

    # Chart data — last 6 assessed years
    chart_years = sorted({r["tax_year"] for r in history if r["tax_year"]})[-6:]
    chart = [{"year": yr, "value": to_float(next((r["assessed_total"] for r in history if r["tax_year"] == yr), None))}
             for yr in chart_years]

    # Tax history rows (most recent first, last 6)
    hist_desc = sorted(history, key=lambda r: r["tax_year"], reverse=True)[:6]
    tax_rows = []
    for i, row in enumerate(hist_desc):
        val = to_float(row["assessed_total"])
        taxes = to_float(row.get("gross_taxes_due")) or (round(val * 0.019) if val else None)
        prev_h = hist_desc[i + 1] if i + 1 < len(hist_desc) else None
        prev_taxes = None
        if prev_h:
            pv = to_float(prev_h["assessed_total"])
            prev_taxes = to_float(prev_h.get("gross_taxes_due")) or (round(pv * 0.019) if pv else None)
        chg = pct_change(taxes, prev_taxes) if (taxes and prev_taxes) else None
        tax_rows.append({
            "year": row["tax_year"],
            "estimated_tax": fmt_money(taxes),
            "change_pct": f"{chg:+.1f}%" if chg is not None else "—",
            "direction": "up" if (chg and chg > 0) else ("down" if (chg and chg < 0) else ""),
        })

    # County website link
    county = (p.get("county") or "").lower()
    county_url = None
    if county == "polk":
        county_url = f"https://www.assess.co.polk.ia.us/pat/BuildingSketch.aspx?q={p['county_parcel_id']}"
    elif county == "dallas":
        county_url = f"https://beacon.schneidercorp.com/?site=DallasCountyIA&id={p['county_parcel_id']}"

    return jsonify({
        "property_id": prop_id,
        "parcel_id": p["county_parcel_id"] or "—",
        "address": p["address_raw"] or "—",
        "city": p["city"] or "—",
        "state": p["state"] or "IA",
        "zip": p["zip"] or "",
        "county": (p["county"] or "").upper(),
        "owner": p["owner_name"] or "—",
        "year_built": p["year_built"],
        "living_area_sqft": to_float(p["living_area_sqft"]),
        "lot_sqft": to_float(p["lot_sf"]),
        "bedrooms": to_float(p["bedrooms"]),
        "bathrooms": to_float(p["bathrooms"]),
        "stories": p["stories"],  # stored as text e.g. "1 Story"
        "bldg_style": p["bldg_style"] or "—",
        "garage_spaces": to_float(p["garage_spaces"]),
        "class_code": p["property_class"] or "—",
        "neighborhood_code": p["neighborhood_code"] or "—",
        # Assessment
        "assessment_year": tax_year,
        "land_value_fmt": fmt_money(p["assessed_land"]),
        "improvement_value_fmt": fmt_money(p["assessed_improvements"]),
        "total_value": current_val,
        "total_value_fmt": fmt_money(current_val),
        "estimated_taxes_fmt": fmt_money(est_taxes),
        "yoy_pct": f"{yoy_pct:+.1f}%" if yoy_pct is not None else "—",
        "yoy_amt_fmt": fmt_money(abs(yoy_amt)) if yoy_amt else "—",
        "yoy_direction": "up" if (yoy_pct and yoy_pct > 0) else ("down" if (yoy_pct and yoy_pct < 0) else ""),
        "flagged": bool(yoy_pct and yoy_pct > 10),
        "prev_year_value_fmt": fmt_money(prev_val),
        "prev_year": tax_year - 1,
        # Sale
        "last_sale_price_fmt": fmt_money(last_sale["sale_price"]) if last_sale else "—",
        "last_sale_date_fmt": fmt_date(last_sale["sale_date"]) if last_sale else "—",
        # Chart + history
        "chart": chart,
        "tax_rows": tax_rows,
        # Link
        "county_site_url": county_url,
    })


# ─────────────────────────────────────────────────────────────────
# API: Comps
# ─────────────────────────────────────────────────────────────────

@app.route("/api/comps/<parcel_id>")
def api_comps(parcel_id):
    result = ce.run_comps(parcel_id=parcel_id)

    if result.get("status") == "error":
        return jsonify({"error": "; ".join(result.get("errors", ["Unknown error"]))}), 404

    subj = result["subject"]
    comps_raw = result.get("comps", [])
    verdict_raw = result.get("verdict", {})

    # ── Subject row ──
    s_val = subj.get("assessed_total")
    s_sqft = subj.get("living_area_sqft")
    subj_row = {
        "n": "S",
        "subj": True,
        "address": subj.get("address_raw") or "—",
        "city": subj.get("city") or "—",
        "parcel_id": subj.get("county_parcel_id") or "—",
        "sqft": s_sqft,
        "sqft_fmt": f"{s_sqft:,}" if s_sqft else "—",
        "bb": f"{subj.get('bedrooms','?')}/{subj.get('bathrooms','?')}",
        "year_built": subj.get("year_built"),
        "distance_fmt": "—",
        "sale_date_fmt": "—",
        "sale_price_fmt": (fmt_money(s_val) + "*") if s_val else "—",
        "psf_fmt": f"${s_val/s_sqft:.0f}" if (s_val and s_sqft) else "—",
        "similarity": 100,
        "why": "Subject property",
    }

    # ── Comp rows ──
    def shape_comp(c, idx):
        score = c.get("_score", 0)
        sqft = c.get("living_area_sqft")
        dist = c.get("_distance_miles")
        psf = c.get("price_per_sqft")
        return {
            "n": idx + 1,
            "subj": False,
            "address": c.get("address_raw") or "—",
            "city": c.get("city") or "—",
            "parcel_id": c.get("county_parcel_id") or "—",
            "sqft": sqft,
            "sqft_fmt": f"{sqft:,}" if sqft else "—",
            "bb": f"{c.get('bedrooms','?')}/{c.get('bathrooms','?')}",
            "year_built": c.get("year_built"),
            "distance_mi": dist,
            "distance_fmt": f"{dist:.2f} mi" if dist is not None else "—",
            "sale_date_fmt": fmt_date(c.get("sale_date")),
            "sale_price": c.get("sale_price"),
            "sale_price_fmt": fmt_money(c.get("sale_price")),
            "price_per_sqft": psf,
            "psf_fmt": f"${psf:.0f}" if psf else "—",
            "similarity": round(score),
            "why": c.get("_why_chosen", ""),
        }

    comp_rows = [shape_comp(c, i) for i, c in enumerate(comps_raw)]
    all_rows = [subj_row] + comp_rows

    # ── Verdict ──
    verdict_str = verdict_raw.get("verdict", "UNKNOWN")
    implied = verdict_raw.get("implied_value")
    assessed = verdict_raw.get("assessed_total")
    ratio = verdict_raw.get("assessment_ratio")
    n_comps = len(comp_rows)
    median_psf = verdict_raw.get("median_ppsf")

    if "OVER" in verdict_str:
        v_state = "over"
        pct_val = abs((ratio - 1) * 100) if ratio else 0
        pct_str = f"+{pct_val:.0f}%"
        lbl = "over"
        verdict_html = f'This parcel appears <em>over-assessed</em> by ~{pct_val:.0f}% relative to nearby sales.'
        why = (
            f"Assessor's {fmt_money(assessed)} sits {pct_val:.0f}% above the median $/sqft "
            f"of {n_comps} comparable sales "
            f"(${median_psf:.0f}/sqft → implies ~{fmt_money(implied)}). "
            f"Confidence: high (similarity-weighted)." if median_psf else ""
        )
    elif "UNDER" in verdict_str:
        v_state = "under"
        pct_val = abs((ratio - 1) * 100) if ratio else 0
        pct_str = f"-{pct_val:.0f}%"
        lbl = "under"
        verdict_html = f'This parcel appears <em>under-assessed</em> by ~{pct_val:.0f}% versus nearby sales.'
        why = (
            f"Assessor's {fmt_money(assessed)} sits ~{pct_val:.0f}% below the median $/sqft "
            f"of {n_comps} comparable sales — a protest is unlikely to succeed."
        )
    else:
        v_state = "fair"
        pct_val = abs((ratio - 1) * 100) if ratio else 0
        pct_str = f"±{pct_val:.0f}%"
        lbl = "fair"
        verdict_html = 'This parcel appears <em>roughly fair</em> versus nearby sales.'
        why = (
            f"Assessor's {fmt_money(assessed)} is within {pct_val:.0f}% of the median $/sqft "
            f"of {n_comps} comparable sales — likely not worth protesting on comps alone."
        )

    return jsonify({
        "subject": subj_row,
        "comps": comp_rows,
        "all_rows": all_rows,
        "verdict": {
            "state": v_state,
            "pct_str": pct_str,
            "lbl": lbl,
            "verdict_html": verdict_html,
            "why": why,
            "implied_value_fmt": fmt_money(implied),
            "assessed_fmt": fmt_money(assessed),
            "n_comps": n_comps,
        },
        "subject_detail": {
            "property_id": subj.get("id"),
            "parcel_id": subj.get("county_parcel_id"),
            "address": subj.get("address_raw"),
            "city": subj.get("city"),
            "county": subj.get("county"),
        },
        "expansion_note": result.get("expansion_note"),
        "error": None,
    })


# ─────────────────────────────────────────────────────────────────
# API: Admin stats
# ─────────────────────────────────────────────────────────────────

@app.route("/api/admin")
def api_admin():
    total_props   = scalar("SELECT COUNT(*) FROM properties") or 0
    polk_props    = scalar("SELECT COUNT(*) FROM properties WHERE county = 'polk'") or 0
    dallas_props  = scalar("SELECT COUNT(*) FROM properties WHERE county = 'dallas'") or 0
    total_sales   = scalar("SELECT COUNT(*) FROM sales") or 0
    arms_length   = scalar("SELECT COUNT(*) FROM sales WHERE arms_length_flag = TRUE") or 0
    recent_sales  = scalar("""
        SELECT COUNT(*) FROM sales
        WHERE arms_length_flag = TRUE
          AND sale_date >= '2025-01-01'
    """) or 0
    total_assess  = scalar("SELECT COUNT(*) FROM assessments") or 0
    no_latlon     = scalar("SELECT COUNT(*) FROM properties WHERE latitude IS NULL OR longitude IS NULL") or 0

    # Ingestion run log
    runs_raw = query("""
        SELECT source_name, status, started_at, completed_at,
               rows_inserted, rows_updated, errors_json, notes
        FROM ingestion_runs
        ORDER BY started_at DESC
        LIMIT 20
    """)

    def fmt_run(r):
        dur = None
        if r["started_at"] and r["completed_at"]:
            dur = f"{(r['completed_at'] - r['started_at']).total_seconds():.0f}s"
        return {
            "source": r["source_name"],
            "status": r["status"] or "unknown",
            "started": r["started_at"].strftime("%Y-%m-%d %H:%M:%S") if r["started_at"] else "—",
            "duration": dur or "—",
            "inserted": r["rows_inserted"] or 0,
            "updated": r["rows_updated"] or 0,
            "skipped": 0,
            "error": str(r["errors_json"]) if r["errors_json"] else None,
        }

    # Median A/V ratio
    av_rows = query("""
        SELECT s.sale_price, a.assessed_total
        FROM sales s
        JOIN assessments a ON a.property_id = s.property_id
            AND a.tax_year = EXTRACT(YEAR FROM s.sale_date)::int
        WHERE s.arms_length_flag = TRUE
          AND s.sale_date >= CURRENT_DATE - INTERVAL '12 months'
          AND s.sale_price > 50000
          AND a.assessed_total > 0
        LIMIT 2000
    """)
    ratios = [float(r["assessed_total"]) / float(r["sale_price"]) for r in av_rows
              if r["sale_price"] and r["assessed_total"]]
    median_ratio = round(statistics.median(ratios), 3) if ratios else None

    return jsonify({
        "stats": {
            "total_properties": total_props,
            "polk_properties": polk_props,
            "dallas_properties": dallas_props,
            "total_sales": total_sales,
            "arms_length_sales": arms_length,
            "recent_sales_2025_plus": recent_sales,
            "total_assessments": total_assess,
            "properties_no_latlon": no_latlon,
            "median_av_ratio": median_ratio,
        },
        "sources": [
            {
                "name": "Polk County CAMA",
                "desc": "Bulk CSV · annual snapshot (Tyler Munis)",
                "count": f"{polk_props:,} parcels",
                "stamp": "Loaded",
                "status": "good",
            },
            {
                "name": "Dallas County CAMA",
                "desc": "Beacon scraper · pending",
                "count": f"{dallas_props:,} parcels",
                "stamp": "Pending",
                "status": "warn" if dallas_props == 0 else "good",
            },
            {
                "name": "Polk Recorder · sales",
                "desc": "Annual CSVs 1990–2026",
                "count": f"{total_sales:,} sales",
                "stamp": "Loaded",
                "status": "good",
            },
            {
                "name": "Atlas lat/lon enrichment",
                "desc": "NDJSON unit + polygon layers",
                "count": f"{total_props - no_latlon:,} geocoded",
                "stamp": "Done",
                "status": "good" if no_latlon == 0 else "warn",
            },
        ],
        "runs": [fmt_run(r) for r in runs_raw],
        "config": {
            "Comp radius default": "0.75 mi",
            "Sales recency": "180 days (primary) / 270 days (expanded)",
            "Min comps before expansion": "5",
            "Scoring weights": "sqft 30%, recency 25%, nbhd 15%, age 15%, dist 10%, lot 5%",
            "Over-assessed threshold": ">10% above implied value",
            "Protest window": "Apr 2 – Apr 30",
        },
        "health": {
            "Total parcels": f"{total_props:,}",
            "Polk": f"{polk_props:,}",
            "Dallas": f"{dallas_props:,}",
            "Arms-length sales": f"{arms_length:,}",
            "Median A/V ratio (12 mo)": str(median_ratio) if median_ratio else "—",
            "Properties missing lat/lon": f"{no_latlon:,}",
            "Recent sales (2025+)": f"{recent_sales:,}",
        },
    })


# ─────────────────────────────────────────────────────────────────
# PDF packet placeholder
# ─────────────────────────────────────────────────────────────────

@app.route("/api/packet/<parcel_id>")
def api_packet(parcel_id):
    # Future: WeasyPrint PDF generation
    return jsonify({"error": "PDF generation not yet implemented. Use Print in browser."}), 501


# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
