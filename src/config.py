"""
config.py - Healthcare Claims EDA & Cost Analysis
--------------------------------------------------
Paths, table schemas, analytical constants.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR  = PROJECT_ROOT / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Point this at your local copy of the CMS DE-SynPUF CSVs.
# Default matches the P3 provider-aberrant-billing-detection layout.
DESYNPUF_BASE = Path.home() / "Documents" / "PORTFOLIO" / \
    "Fraud-Waste-Abuse-FWA" / "CMS DE-SynPUF MEDICARE" / "data" / "desynpuf_csvs"

DESYNPUF_PATHS = {
    "beneficiary": DESYNPUF_BASE / "beneficiary",
    "inpatient":   DESYNPUF_BASE / "inpatient",
    "outpatient":  DESYNPUF_BASE / "outpatient",
    "carrier":     DESYNPUF_BASE / "carrier",
    "pde":         DESYNPUF_BASE / "pde",
}

# ── Expected row counts (all 20 samples combined) ───────────────────────────
EXPECTED_ROWS = {
    "beneficiary": 6_873_274,
    "carrier":     94_863_452,
    "inpatient":   1_332_822,
    "outpatient":  15_826_987,
    "pde":         111_085_969,
}

# ── Chronic-condition flag columns on the beneficiary table ──────────────────
CHRONIC_CONDITION_COLS = [
    "SP_ALZHDMTA",
    "SP_CHF",
    "SP_CHRNKIDN",
    "SP_CNCR",
    "SP_COPD",
    "SP_DEPRESSN",
    "SP_DIABETES",
    "SP_ISCHMCHT",
    "SP_OSTEOPRSS",
    "SP_RA_OA",
    "SP_STRKETIA",
]

CHRONIC_CONDITION_LABELS = {
    "SP_ALZHDMTA":  "Alzheimer's / Dementia",
    "SP_CHF":       "Heart Failure",
    "SP_CHRNKIDN":  "Chronic Kidney Disease",
    "SP_CNCR":      "Cancer",
    "SP_COPD":      "COPD",
    "SP_DEPRESSN":  "Depression",
    "SP_DIABETES":  "Diabetes",
    "SP_ISCHMCHT":  "Ischemic Heart Disease",
    "SP_OSTEOPRSS": "Osteoporosis",
    "SP_RA_OA":     "Rheumatoid Arthritis / OA",
    "SP_STRKETIA":  "Stroke / TIA",
}

# ── Age bands (Medicare population: mostly 65+, plus <65 disabled) ───────────
AGE_BANDS = [
    (0, 64, "<65 (Disabled)"),
    (65, 69, "65-69"),
    (70, 74, "70-74"),
    (75, 79, "75-79"),
    (80, 84, "80-84"),
    (85, 999, "85+"),
]

# ── Cost columns on the beneficiary summary ──────────────────────────────────
COST_COLS = {
    "inpatient":     {"reimb": "MEDREIMB_IP",  "bene": "BENRES_IP",  "primary": "PPPYMT_IP"},
    "outpatient":    {"reimb": "MEDREIMB_OP",  "bene": "BENRES_OP",  "primary": "PPPYMT_OP"},
    "carrier":       {"reimb": "MEDREIMB_CAR", "bene": "BENRES_CAR", "primary": "PPPYMT_CAR"},
}

# ── Carrier line grouping (from P3) ─────────────────────────────────────────
CARRIER_LINE_GROUPS = {
    "evaluation_mgmt": [str(i) for i in range(99201, 99500)],
    "surgery":         [str(i) for i in range(10000, 70000)],
    "radiology":       [str(i) for i in range(70000, 80000)],
    "pathology_lab":   [str(i) for i in range(80000, 90000)],
    "medicine":        [str(i) for i in range(90000, 100000)],
}

# ── Citation ─────────────────────────────────────────────────────────────────
DATA_SOURCE_CITATION = (
    "Data: CMS Linkable 2008-2010 Medicare Data Entrepreneurs' Synthetic "
    "Public Use File (DE-SynPUF). Synthetic data - not real patient records."
)

TECH_DISCLAIMER = (
    "Analysis by Alessandro Sousa | DuckDB + Python | Visual identity: "
    "Economist-inspired palette (AOS system)"
)
