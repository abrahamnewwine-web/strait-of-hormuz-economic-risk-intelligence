-- Strait of Hormuz Global Economic Risk Intelligence - Production SQL Queries

-- 1. Latest Observed Macro & Energy Baseline with 12-Month Delta
WITH ordered AS (
    SELECT d.year_month, m.*,
           LAG(m.brent_usd, 12) OVER (ORDER BY d.year_month) AS brent_12m,
           LAG(m.wti_usd, 12) OVER (ORDER BY d.year_month) AS wti_12m,
           LAG(m.freight_index, 12) OVER (ORDER BY d.year_month) AS freight_12m,
           LAG(m.energy_cpi, 12) OVER (ORDER BY d.year_month) AS energy_cpi_12m
    FROM fact_macro_monthly m
    JOIN dim_date d ON m.date_key = d.date_key
)
SELECT
    year_month,
    brent_usd,
    ROUND(100.0 * (brent_usd - brent_12m) / NULLIF(brent_12m, 0), 1) AS brent_yoy_pct,
    wti_usd,
    ROUND(100.0 * (wti_usd - wti_12m) / NULLIF(wti_12m, 0), 1) AS wti_yoy_pct,
    diesel_usd_gal,
    gasoline_usd_gal,
    freight_index,
    transportation_cpi,
    energy_cpi,
    ppi_index
FROM ordered
ORDER BY year_month DESC
LIMIT 1;

-- 2. Fortune 500 Exposure Ranking by Industry
SELECT
    c.company_name,
    c.ticker,
    c.industry,
    c.impact_tier,
    c.base_exposure_score,
    e.latest_close_usd,
    e.return_1m_pct,
    e.annualized_vol_pct
FROM fact_corporate_exposure e
JOIN dim_company c ON e.company_id = c.company_id
ORDER BY c.base_exposure_score DESC, e.return_1m_pct ASC;
