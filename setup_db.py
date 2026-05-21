"""
setup_db.py
-----------
Creates the iowa_propertytax database and all canonical tables.
Run once on a fresh Postgres installation.

Usage:
    python3 setup_db.py

Requires Postgres to be running and a superuser connection.
Edit the constants below to match your setup.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ── Connection settings ───────────────────────────────────────────────────────
# Change these to match your local Postgres
PG_HOST     = "localhost"
PG_PORT     = 5432
PG_SUPERUSER = "postgres"       # superuser to create the db
PG_PASSWORD  = "iowa2026"
DB_NAME      = "iowa_propertytax"
DB_OWNER     = "postgres"       # owner of the new database

# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- Properties: one row per parcel, county-agnostic
CREATE TABLE IF NOT EXISTS properties (
    id                  SERIAL PRIMARY KEY,
    county              TEXT NOT NULL,                  -- 'polk' or 'dallas'
    county_parcel_id    TEXT NOT NULL,                  -- primary join key
    alternate_parcel_id TEXT,                           -- geoparcel / alternate format
    address_raw         TEXT,
    address_normalized  TEXT,
    city                TEXT,
    state               TEXT DEFAULT 'IA',
    zip                 TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    neighborhood_code   TEXT,                           -- Polk: nbhdpocket (e.g. DM71/A)
    year_built          INTEGER,
    living_area_sqft    INTEGER,
    basement_sqft       INTEGER,
    lot_sf              DOUBLE PRECISION,
    lot_acres           DOUBLE PRECISION,
    bedrooms            INTEGER,
    bathrooms           NUMERIC(4,1),
    garage_spaces       INTEGER,
    stories             TEXT,
    quality_grade       TEXT,
    condition_rating    TEXT,
    bldg_style          TEXT,
    property_class      TEXT,
    tax_district        TEXT,
    school_district     TEXT,
    owner_name          TEXT,
    homestead_flag      BOOLEAN,
    source_system       TEXT,                           -- e.g. 'polk_assessor_sales', 'dallas_beacon'
    parser_version      TEXT,                           -- e.g. 'v1.1.0'
    source_url          TEXT,
    last_seen_at        TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(county, county_parcel_id)
);

CREATE INDEX IF NOT EXISTS idx_properties_county       ON properties(county);
CREATE INDEX IF NOT EXISTS idx_properties_city         ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_neighborhood ON properties(neighborhood_code);
CREATE INDEX IF NOT EXISTS idx_properties_zip          ON properties(zip);
CREATE INDEX IF NOT EXISTS idx_properties_latlon       ON properties(latitude, longitude);

-- Assessments: one row per parcel per tax year
CREATE TABLE IF NOT EXISTS assessments (
    id                      SERIAL PRIMARY KEY,
    property_id             INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    tax_year                INTEGER NOT NULL,
    assessed_total          NUMERIC(14,2),
    assessed_land           NUMERIC(14,2),
    assessed_improvements   NUMERIC(14,2),
    assessed_dwelling       NUMERIC(14,2),              -- Dallas: separate dwelling line
    net_assessed_value      NUMERIC(14,2),
    taxable_total           NUMERIC(14,2),
    gross_taxes_due         NUMERIC(14,2),
    net_taxes_due           NUMERIC(14,2),
    assessment_ratio        NUMERIC(8,4),               -- Polk: assessed/sale ratio
    classification          TEXT,
    source_system           TEXT,
    parser_version          TEXT,
    source_url              TEXT,
    extracted_at            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(property_id, tax_year)
);

CREATE INDEX IF NOT EXISTS idx_assessments_property ON assessments(property_id);
CREATE INDEX IF NOT EXISTS idx_assessments_year     ON assessments(tax_year);

-- Sales: arms-length sales history
CREATE TABLE IF NOT EXISTS sales (
    id                  SERIAL PRIMARY KEY,
    property_id         INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    sale_date           DATE,
    sale_price          NUMERIC(14,2),
    price_per_sqft      NUMERIC(10,2),
    sale_type           TEXT,
    deed_type           TEXT,
    sale_condition      TEXT,                           -- Dallas: NUTC condition code
    arms_length_flag    BOOLEAN,
    non_arms_length_reason TEXT,                        -- Polk: quality2 code
    multi_parcel        BOOLEAN DEFAULT FALSE,
    recording_number    TEXT,
    buyer               TEXT,
    seller              TEXT,
    source_system       TEXT,
    parser_version      TEXT,
    source_url          TEXT,
    extracted_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(property_id, sale_date, sale_price)
);

CREATE INDEX IF NOT EXISTS idx_sales_property  ON sales(property_id);
CREATE INDEX IF NOT EXISTS idx_sales_date      ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_armlength ON sales(arms_length_flag);

-- Ingestion runs: audit log for every ingest job
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id              SERIAL PRIMARY KEY,
    county          TEXT,
    source_name     TEXT,                               -- e.g. 'dallas_beacon', 'polk_assessor_sales'
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    status          TEXT,                               -- 'running', 'complete', 'complete_with_errors', 'failed'
    rows_inserted   INTEGER DEFAULT 0,
    rows_updated    INTEGER DEFAULT 0,
    errors_json     JSONB,
    notes           TEXT
);

-- Raw source snapshots: HTML/file archives for replay and debugging
CREATE TABLE IF NOT EXISTS raw_source_snapshots (
    id              SERIAL PRIMARY KEY,
    county          TEXT,
    source_name     TEXT,
    parcel_id       TEXT,
    captured_at     TIMESTAMPTZ DEFAULT NOW(),
    file_path       TEXT,
    payload_hash    TEXT
);
"""


def create_database():
    """Create the database if it doesn't exist."""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname="postgres",          # connect to default db to create new one
        user=PG_SUPERUSER,
        password=PG_PASSWORD,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone():
        print(f"Database '{DB_NAME}' already exists.")
    else:
        cur.execute(f'CREATE DATABASE "{DB_NAME}" OWNER "{DB_OWNER}"')
        print(f"Created database '{DB_NAME}'.")

    cur.close()
    conn.close()


def create_schema():
    """Create all tables and indexes."""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=DB_NAME,
        user=PG_SUPERUSER,
        password=PG_PASSWORD,
    )
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print("Schema created / verified.")


def verify():
    """Print table row counts to confirm everything is set up."""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=DB_NAME,
        user=PG_SUPERUSER,
        password=PG_PASSWORD,
    )
    tables = ["properties", "assessments", "sales", "ingestion_runs", "raw_source_snapshots"]
    with conn.cursor() as cur:
        print("\nTable row counts:")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            print(f"  {t:30s} {count:>8,}")
    conn.close()


if __name__ == "__main__":
    print(f"Setting up database: {DB_NAME} on {PG_HOST}:{PG_PORT}")
    print("=" * 50)

    try:
        create_database()
        create_schema()
        verify()
        print("\nDone. Update your .env file:")
        print(f"  DB_HOST={PG_HOST}")
        print(f"  DB_PORT={PG_PORT}")
        print(f"  DB_NAME={DB_NAME}")
        print(f"  DB_USER={PG_SUPERUSER}")
        print(f"  DB_PASS={PG_PASSWORD or '(blank)'}")
    except psycopg2.OperationalError as e:
        print(f"\nConnection failed: {e}")
        print("\nTroubleshooting:")
        print("  Windows: check Services > postgresql-x64-XX is running")
        print("  Or run: pg_ctl start -D 'C:/Program Files/PostgreSQL/16/data'")
        print("  Then retry this script.")
