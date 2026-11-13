"""Configuration, chokepoint constants, and scenario model definitions."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
DOCS_BA_DIR = BASE_DIR / "docs" / "business-analysis"
SCREENSHOTS_DIR = BASE_DIR / "assets" / "screenshots"
DB_PATH = DATA_PROCESSED_DIR / "hormuz_risk.db"
MACRO_CSV = DATA_RAW_DIR / "hormuz_macro_monthly.csv"
CORP_CSV = DATA_RAW_DIR / "fortune500_snapshot.csv"

CHOKEPOINT_STATS = {
    "barrels_per_day_millions": 20.7,
    "global_oil_consumption_pct": 20,
    "global_seaborne_oil_pct": 25,
    "global_lng_trade_pct": 20,
    "asia_crude_share_pct": 84,
    "saudi_crude_share_pct": 38,
}

# Scenarios: (id, name, flow_disruption_pct, oil_shock_pct, freight_shock_pct, inflation_pressure_pct, risk_index, risk_band)
SCENARIOS = [
    (1, "Normal", 0.0, 0.0, 0.0, 0.0, 24, "LOW RISK"),
    (2, "Limited Disruption", 15.0, 12.0, 8.5, 2.1, 42, "MODERATE RISK"),
    (3, "Moderate Disruption", 35.0, 28.0, 22.0, 4.8, 61, "ELEVATED RISK"),
    (4, "Severe Disruption", 65.0, 55.0, 44.0, 8.6, 80, "HIGH RISK"),
    (5, "Full Closure", 100.0, 100.0, 72.0, 14.5, 96, "CRITICAL RISK"),
]

# Fortune 500 exposure cohort aligned with specification
COMPANIES = [
    (1, "DAL", "Delta Air Lines", "Airlines", 100, "Very High", -0.18, -0.05),
    (2, "UAL", "United Airlines", "Airlines", 100, "Very High", -0.19, -0.05),
    (3, "UPS", "UPS", "Logistics", 100, "Very High", -0.11, -0.14),
    (4, "FDX", "FedEx", "Logistics", 100, "Very High", -0.11, -0.15),
    (5, "WMT", "Walmart", "Retail", 55, "Moderate", -0.04, -0.09),
    (6, "AMZN", "Amazon", "Retail", 55, "Moderate", -0.03, -0.08),
    (7, "CVX", "Chevron", "Energy", 82, "High", 0.16, 0.02),
    (8, "XOM", "ExxonMobil", "Energy", 82, "High", 0.17, 0.02),
]
