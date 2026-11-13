-- Strait of Hormuz Global Economic Risk Intelligence - Star Schema DDL (SQLite)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_corporate_exposure;
DROP TABLE IF EXISTS fact_macro_monthly;
DROP TABLE IF EXISTS dim_scenario;
DROP TABLE IF EXISTS dim_company;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,
    period_date     TEXT NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    month_num       INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    year_month      TEXT NOT NULL
);

CREATE TABLE dim_company (
    company_id      INTEGER PRIMARY KEY,
    ticker          TEXT NOT NULL UNIQUE,
    company_name    TEXT NOT NULL,
    industry        TEXT NOT NULL,
    base_exposure_score INTEGER NOT NULL CHECK (base_exposure_score BETWEEN 0 AND 100),
    impact_tier     TEXT NOT NULL,
    oil_beta        REAL NOT NULL,
    freight_beta    REAL NOT NULL
);

CREATE TABLE dim_scenario (
    scenario_id     INTEGER PRIMARY KEY,
    scenario_name   TEXT NOT NULL UNIQUE,
    flow_disruption_pct REAL NOT NULL,
    oil_shock_pct   REAL NOT NULL,
    freight_shock_pct REAL NOT NULL,
    inflation_pressure_pct REAL NOT NULL,
    risk_index      INTEGER NOT NULL CHECK (risk_index BETWEEN 0 AND 100),
    risk_band       TEXT NOT NULL
);

CREATE TABLE fact_macro_monthly (
    macro_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    brent_usd       REAL NOT NULL,
    wti_usd         REAL NOT NULL,
    diesel_usd_gal  REAL NOT NULL,
    gasoline_usd_gal REAL NOT NULL,
    freight_index   REAL NOT NULL,
    transportation_cpi REAL NOT NULL,
    energy_cpi      REAL NOT NULL,
    ppi_index       REAL NOT NULL
);

CREATE TABLE fact_corporate_exposure (
    exposure_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL REFERENCES dim_company(company_id),
    as_of_date      TEXT NOT NULL,
    latest_close_usd REAL NOT NULL,
    return_1m_pct   REAL NOT NULL,
    annualized_vol_pct REAL NOT NULL
);

CREATE INDEX idx_macro_date ON fact_macro_monthly(date_key);
CREATE INDEX idx_corp_company ON fact_corporate_exposure(company_id);
