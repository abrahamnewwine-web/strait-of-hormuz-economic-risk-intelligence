"""Scenario stress-testing, Hormuz Risk Index, and macro analytics engine."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.config import CHOKEPOINT_STATS, DB_PATH


@dataclass(frozen=True)
class FilterParams:
    """Interactive Strait of Hormuz dashboard parameters."""

    scenario: str = "Normal"
    year: int | None = None
    month: int | None = None
    industry: str | None = None


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        from src.pipeline import run_pipeline

        run_pipeline(refresh=False)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_filter_options() -> dict[str, Any]:
    """Return available scenarios, calendar slices, and corporate industries."""
    with _connect() as conn:
        scenarios = [
            dict(r)
            for r in conn.execute("SELECT * FROM dim_scenario ORDER BY scenario_id")
        ]
        years = [r[0] for r in conn.execute("SELECT DISTINCT year FROM dim_date ORDER BY year")]
        months = [
            {"month_num": r[0], "month_name": r[1]}
            for r in conn.execute("SELECT DISTINCT month_num, month_name FROM dim_date ORDER BY month_num")
        ]
        industries = [r[0] for r in conn.execute("SELECT DISTINCT industry FROM dim_company ORDER BY industry")]
    return {
        "scenarios": scenarios,
        "years": years,
        "months": months,
        "industries": industries,
    }


def _pct_delta(curr: float, prev: float) -> float:
    return round(((curr - prev) / prev * 100.0) if prev else 0.0, 1)


def get_dashboard_data(filters: FilterParams) -> dict[str, Any]:
    """Return observed historical baselines alongside modeled disruption stress estimates."""
    with _connect() as conn:
        scen_row = conn.execute(
            "SELECT * FROM dim_scenario WHERE scenario_name = ?",
            (filters.scenario,),
        ).fetchone()
        if scen_row is None:
            raise ValueError(f"Unknown scenario: {filters.scenario}")
        active_scen = dict(scen_row)
        all_scenarios = [dict(r) for r in conn.execute("SELECT * FROM dim_scenario ORDER BY scenario_id")]

        clauses: list[str] = []
        params: list[Any] = []
        if filters.year is not None:
            clauses.append("d.year = ?")
            params.append(filters.year)
        if filters.month is not None:
            clauses.append("d.month_num = ?")
            params.append(filters.month)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        macro_df = pd.read_sql_query(
            f"""
            SELECT d.period_date, d.year, d.month_num, d.year_month,
                   m.brent_usd, m.wti_usd, m.diesel_usd_gal, m.gasoline_usd_gal,
                   m.freight_index, m.transportation_cpi, m.energy_cpi, m.ppi_index
            FROM fact_macro_monthly m
            JOIN dim_date d ON m.date_key = d.date_key
            {where_sql}
            ORDER BY d.period_date
            """,
            conn,
            params=params,
        )

        # Full macro series for clean 12M YoY lookup even when year/month filter narrows window
        full_macro = pd.read_sql_query(
            """
            SELECT d.year_month, m.brent_usd, m.wti_usd, m.diesel_usd_gal, m.gasoline_usd_gal,
                   m.freight_index, m.transportation_cpi, m.energy_cpi, m.ppi_index
            FROM fact_macro_monthly m
            JOIN dim_date d ON m.date_key = d.date_key
            ORDER BY d.period_date
            """,
            conn,
        )

        ind_clauses: list[str] = []
        ind_params: list[Any] = []
        if filters.industry and filters.industry != "All":
            ind_clauses.append("c.industry = ?")
            ind_params.append(filters.industry)
        ind_where = f"WHERE {' AND '.join(ind_clauses)}" if ind_clauses else ""

        corp_df = pd.read_sql_query(
            f"""
            SELECT c.ticker, c.company_name, c.industry, c.base_exposure_score, c.impact_tier,
                   c.oil_beta, c.freight_beta,
                   e.as_of_date, e.latest_close_usd, e.return_1m_pct, e.annualized_vol_pct
            FROM fact_corporate_exposure e
            JOIN dim_company c ON e.company_id = c.company_id
            {ind_where}
            ORDER BY c.base_exposure_score DESC, e.return_1m_pct ASC
            """,
            conn,
            params=ind_params,
        )

    if macro_df.empty:
        return {"empty": True, "active_scenario": active_scen}

    latest = macro_df.iloc[-1]
    latest_ym = str(latest["year_month"])
    full_idx = full_macro.index[full_macro["year_month"] == latest_ym][0]
    prev_12 = full_macro.iloc[max(0, int(full_idx) - 12)]

    # Apply transparent modeled stress multipliers to latest observed baseline
    oil_mult = 1.0 + active_scen["oil_shock_pct"] / 100.0
    freight_mult = 1.0 + active_scen["freight_shock_pct"] / 100.0
    inf_mult = 1.0 + active_scen["inflation_pressure_pct"] / 100.0
    fuel_mult = 1.0 + (active_scen["oil_shock_pct"] * 0.65) / 100.0

    def _card(name: str, obs_val: float, prev_val: float, modeled_val: float, unit: str) -> dict[str, Any]:
        return {
            "label": name,
            "observed_value": round(float(obs_val), 2),
            "modeled_value": round(float(modeled_val), 2),
            "yoy_delta_pct": _pct_delta(float(obs_val), float(prev_val)),
            "unit": unit,
        }

    cards = {
        "brent": _card("BRENT OIL PRICE", latest["brent_usd"], prev_12["brent_usd"], latest["brent_usd"] * oil_mult, "$/bbl"),
        "wti": _card("WTI OIL PRICE", latest["wti_usd"], prev_12["wti_usd"], latest["wti_usd"] * oil_mult, "$/bbl"),
        "diesel": _card("DIESEL PRICE", latest["diesel_usd_gal"], prev_12["diesel_usd_gal"], latest["diesel_usd_gal"] * fuel_mult, "$/gal"),
        "gasoline": _card("GASOLINE PRICE", latest["gasoline_usd_gal"], prev_12["gasoline_usd_gal"], latest["gasoline_usd_gal"] * fuel_mult, "$/gal"),
        "freight": _card("FREIGHT INDEX", latest["freight_index"], prev_12["freight_index"], latest["freight_index"] * freight_mult, "idx"),
        "transport_cpi": _card("TRANSPORTATION CPI", latest["transportation_cpi"], prev_12["transportation_cpi"], latest["transportation_cpi"] * inf_mult, "idx"),
        "energy_cpi": _card("ENERGY CPI", latest["energy_cpi"], prev_12["energy_cpi"], latest["energy_cpi"] * (1.0 + active_scen["inflation_pressure_pct"] * 1.4 / 100.0), "idx"),
        "ppi": _card("PPI INDEX", latest["ppi_index"], prev_12["ppi_index"], latest["ppi_index"] * (1.0 + active_scen["inflation_pressure_pct"] * 1.15 / 100.0), "idx"),
    }

    # Modeled company stress impact under selected scenario
    corp_rows = []
    for _, r in corp_df.iterrows():
        modeled_eq_impact = round(
            float(r["oil_beta"]) * active_scen["oil_shock_pct"]
            + float(r["freight_beta"]) * active_scen["freight_shock_pct"],
            2,
        )
        corp_rows.append(
            {
                "ticker": r["ticker"],
                "company_name": r["company_name"],
                "industry": r["industry"],
                "impact_tier": r["impact_tier"],
                "base_exposure_score": int(r["base_exposure_score"]),
                "latest_close_usd": round(float(r["latest_close_usd"]), 2),
                "return_1m_pct": round(float(r["return_1m_pct"]), 2),
                "modeled_scenario_impact_pct": modeled_eq_impact,
            }
        )

    risk_narratives = {
        "Normal": "Baseline operating conditions: maritime transit flows normally with limited disruption premium.",
        "Limited Disruption": "Minor maritime insurance surcharges and intermittent tanker delays (+12% modeled crude shock).",
        "Moderate Disruption": "Substantial rerouting pressure elevates freight costs (+22%) and pass-through inflation.",
        "Severe Disruption": "Major supply curtailment triggers +55% crude shock and acute airline/logistics margin stress.",
        "Full Closure": "Extreme chokepoint blockade (+100% oil shock, +72% freight cost); severe stagflationary risk.",
    }

    return {
        "empty": False,
        "chokepoint_stats": CHOKEPOINT_STATS,
        "active_scenario": active_scen,
        "all_scenarios": all_scenarios,
        "as_of_period": latest_ym,
        "is_stressed": active_scen["scenario_name"] != "Normal",
        "risk_summary": risk_narratives.get(active_scen["scenario_name"], ""),
        "macro_cards": cards,
        "macro_series": macro_df.to_dict(orient="records"),
        "corporate_exposure": corp_rows,
    }
