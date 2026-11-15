"""
data_loader.py - Healthcare Claims EDA & Cost Analysis
------------------------------------------------------

DuckDB connection factory, table views, and EDA-specific helpers.

Supports two loading modes:
  1. CSV scan (default) - reads from desynpuf_csvs/ via read_csv_auto
  2. Persistent DuckDB file - attaches the pre-built desynpuf.duckdb

The beneficiary table has 60 files (3 years x 20 samples). Each row is
one member-year, so a member enrolled in all three years appears three
times. The enriched table extracts the year from the filename to enable
year-over-year trending.
"""

import duckdb
from pathlib import Path
from src.config import DESYNPUF_PATHS, DESYNPUF_BASE


# Path to the pre-built DuckDB file (faster than CSV scan)
DUCKDB_FILE = DESYNPUF_BASE.parent / "desynpuf.duckdb"


def get_connection(memory_limit: str = "6GB", threads: int = 4) -> duckdb.DuckDBPyConnection:
    """Return a configured in-memory DuckDB connection."""
    con = duckdb.connect(database=":memory:")
    con.execute(f"SET memory_limit = '{memory_limit}'")
    con.execute(f"SET threads = {threads}")
    return con


def create_views(con: duckdb.DuckDBPyConnection) -> None:
    """
    Create lazy CSV-scanning views for all five DE-SynPUF tables.

    Beneficiary files are named by year (2008/2009/2010), so we extract
    the year from the filename to allow year-over-year analysis.
    """
    # Beneficiary: extract year from filename
    bene_path = DESYNPUF_PATHS["beneficiary"]
    con.execute(f"""
        CREATE OR REPLACE VIEW beneficiary AS
        SELECT *,
            CAST(
                regexp_extract(filename, '(200[89]|2010)', 1)
                AS INTEGER
            ) AS bene_year
        FROM read_csv_auto(
            '{bene_path}/*.csv',
            header=true,
            union_by_name=true,
            filename=true
        )
    """)

    # Claims tables: single time range across 2008-2010
    for name in ["inpatient", "outpatient", "carrier", "pde"]:
        path = DESYNPUF_PATHS[name]
        con.execute(f"""
            CREATE OR REPLACE VIEW {name} AS
            SELECT *
            FROM read_csv_auto(
                '{path}/*.csv',
                header=true,
                union_by_name=true
            )
        """)


def create_beneficiary_enriched(con: duckdb.DuckDBPyConnection) -> None:
    """
    Materialize an enriched beneficiary table with:
    - bene_year (extracted from filename: 2008, 2009, or 2010)
    - computed age (as of Jan 1 of that benefit year)
    - age_band label
    - chronic condition count
    - total annual cost (Medicare reimbursement across IP/OP/Carrier)
    - member months (Part B / SMI coverage)
    """
    # BENE_BIRTH_DT is stored as a YYYYMMDD integer (BIGINT) in the DE-SynPUF
    # CSVs, because read_csv_auto sees no delimiters and infers numeric type.
    # DuckDB's AGE() requires (TIMESTAMP, TIMESTAMP), so we parse the BIGINT
    # to DATE first via a CTE, then compute age from that parsed column.
    con.execute("""
        CREATE OR REPLACE TABLE bene AS
        WITH parsed AS (
            SELECT *,
                -- Parse BIGINT birth date to proper DATE type
                COALESCE(
                    TRY_CAST(BENE_BIRTH_DT AS DATE),
                    TRY_STRPTIME(CAST(BENE_BIRTH_DT AS VARCHAR), '%Y%m%d')::DATE
                ) AS birth_dt_parsed
            FROM beneficiary
        )
        SELECT
            *,
            -- Age as of Jan 1 of the benefit year
            EXTRACT(YEAR FROM AGE(
                MAKE_DATE(bene_year, 1, 1)::TIMESTAMP,
                birth_dt_parsed::TIMESTAMP
            )) AS age,

            -- Age band
            CASE
                WHEN EXTRACT(YEAR FROM AGE(MAKE_DATE(bene_year, 1, 1)::TIMESTAMP, birth_dt_parsed::TIMESTAMP)) < 65
                    THEN '<65 (Disabled)'
                WHEN EXTRACT(YEAR FROM AGE(MAKE_DATE(bene_year, 1, 1)::TIMESTAMP, birth_dt_parsed::TIMESTAMP)) < 70
                    THEN '65-69'
                WHEN EXTRACT(YEAR FROM AGE(MAKE_DATE(bene_year, 1, 1)::TIMESTAMP, birth_dt_parsed::TIMESTAMP)) < 75
                    THEN '70-74'
                WHEN EXTRACT(YEAR FROM AGE(MAKE_DATE(bene_year, 1, 1)::TIMESTAMP, birth_dt_parsed::TIMESTAMP)) < 80
                    THEN '75-79'
                WHEN EXTRACT(YEAR FROM AGE(MAKE_DATE(bene_year, 1, 1)::TIMESTAMP, birth_dt_parsed::TIMESTAMP)) < 85
                    THEN '80-84'
                ELSE '85+'
            END AS age_band,

            -- Sex label
            CASE BENE_SEX_IDENT_CD
                WHEN 1 THEN 'Male'
                WHEN 2 THEN 'Female'
                ELSE 'Unknown'
            END AS sex,

            -- Chronic condition count (1 = yes, 2 = no in DE-SynPUF)
            (CASE WHEN SP_ALZHDMTA = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_CHF      = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_CHRNKIDN = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_CNCR     = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_COPD     = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_DEPRESSN = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_DIABETES = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_ISCHMCHT = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_OSTEOPRSS= 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_RA_OA    = 1 THEN 1 ELSE 0 END +
             CASE WHEN SP_STRKETIA = 1 THEN 1 ELSE 0 END
            ) AS chronic_count,

            -- Total Medicare reimbursement (annual, across service lines)
            COALESCE(MEDREIMB_IP, 0)
            + COALESCE(MEDREIMB_OP, 0)
            + COALESCE(MEDREIMB_CAR, 0)  AS total_reimb,

            -- Member months (use Part B / SMI coverage as denominator)
            COALESCE(BENE_SMI_CVRAGE_TOT_MONS, 0) AS member_months

        FROM parsed
    """)


def row_count(con: duckdb.DuckDBPyConnection, table: str) -> int:
    """Quick row count for a table or view."""
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
