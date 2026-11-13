"""Automated test suite for Strait of Hormuz Economic Risk Intelligence."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from src.analytics import FilterParams, get_dashboard_data, get_filter_options
from src.ba_artifacts import generate_all_ba_artifacts
from src.config import DOCS_BA_DIR
from src.pipeline import run_pipeline

client = TestClient(app)


def test_pipeline_populates_all_tables() -> None:
    stats = run_pipeline(refresh=False)
    assert stats["dim_date"] >= 120
    assert stats["dim_company"] == 8
    assert stats["dim_scenario"] == 5
    assert stats["fact_macro_monthly"] == stats["dim_date"]
    assert stats["fact_corporate_exposure"] == 8


def test_scenarios_monotonic_stress_order() -> None:
    opts = get_filter_options()
    risks = [s["risk_index"] for s in opts["scenarios"]]
    assert risks == [24, 42, 61, 80, 96]
    brent_vals = [
        get_dashboard_data(FilterParams(scenario=s["scenario_name"]))["macro_cards"]["brent"]["modeled_value"]
        for s in opts["scenarios"]
    ]
    assert brent_vals == sorted(brent_vals)
    assert brent_vals[-1] > brent_vals[0]


def test_normal_vs_full_closure_separation() -> None:
    norm = get_dashboard_data(FilterParams(scenario="Normal"))
    full = get_dashboard_data(FilterParams(scenario="Full Closure"))
    assert norm["is_stressed"] is False
    assert full["is_stressed"] is True
    assert norm["macro_cards"]["brent"]["modeled_value"] == norm["macro_cards"]["brent"]["observed_value"]
    assert full["macro_cards"]["brent"]["modeled_value"] > full["macro_cards"]["brent"]["observed_value"]

    by_ticker = {r["ticker"]: r for r in full["corporate_exposure"]}
    assert by_ticker["DAL"]["modeled_scenario_impact_pct"] < 0
    assert by_ticker["FDX"]["modeled_scenario_impact_pct"] < 0
    assert by_ticker["XOM"]["modeled_scenario_impact_pct"] > 0


def test_industry_filter_restricts_companies() -> None:
    air = get_dashboard_data(FilterParams(scenario="Severe Disruption", industry="Airlines"))
    assert {r["ticker"] for r in air["corporate_exposure"]} == {"DAL", "UAL"}


def test_api_dashboard_and_invalid_scenario() -> None:
    ok_home = client.get("/")
    assert ok_home.status_code == 200
    assert "Strait of Hormuz" in ok_home.text

    ok_api = client.get("/api/dashboard?scenario=Moderate+Disruption&industry=Logistics")
    assert ok_api.status_code == 200
    payload = ok_api.json()
    assert payload["active_scenario"]["risk_index"] == 61
    assert len(payload["corporate_exposure"]) == 2

    bad = client.get("/api/dashboard?scenario=NonExistent")
    assert bad.status_code == 400


def test_csv_export_and_ba_artifacts(tmp_path: Path) -> None:
    csv_resp = client.get("/api/export/exposure.csv?scenario=Full+Closure")
    assert csv_resp.status_code == 200
    assert "DAL,Delta Air Lines,Airlines" in csv_resp.text

    artifacts = generate_all_ba_artifacts(out_dir=tmp_path)
    for p in artifacts.values():
        assert Path(p).exists() and Path(p).stat().st_size > 1000
    assert (DOCS_BA_DIR / "rtm_workbook.xlsx").exists()
    assert (DOCS_BA_DIR / "uat_test_log.xlsx").exists()
    assert (DOCS_BA_DIR / "executive_insights_report.pdf").exists()
