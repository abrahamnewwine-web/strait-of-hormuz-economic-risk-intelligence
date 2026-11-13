"""FastAPI web server and REST endpoints for Strait of Hormuz Economic Risk Intelligence."""

from __future__ import annotations

from contextlib import asynccontextmanager
import csv
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.analytics import FilterParams, get_dashboard_data, get_filter_options
from src.config import BASE_DIR
from src.pipeline import run_pipeline


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    run_pipeline(refresh=False)
    yield


app = FastAPI(title="Strait of Hormuz Economic Risk Intelligence", version="1.0.0", lifespan=_lifespan)

STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    """Render main Strait of Hormuz geopolitical macro cockpit."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/filters")
def api_filters() -> dict:
    """Return scenario options, calendar slices, and industry facets."""
    return get_filter_options()


@app.get("/api/dashboard")
def api_dashboard(
    scenario: str = Query(default="Normal"),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    industry: str | None = Query(default=None),
) -> dict:
    """Return Strait of Hormuz baseline macro data and stress scenario outputs."""
    try:
        return get_dashboard_data(
            FilterParams(scenario=scenario, year=year, month=month, industry=industry)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/export/exposure.csv")
def export_exposure_csv(
    scenario: str = Query(default="Normal"),
    industry: str | None = Query(default=None),
) -> StreamingResponse:
    """Download filtered Fortune 500 scenario exposure table as CSV."""
    try:
        payload = get_dashboard_data(FilterParams(scenario=scenario, industry=industry))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Scenario", "RiskIndex", "RiskBand", "Ticker", "Company", "Industry",
        "ImpactTier", "BaseExposureScore", "LatestCloseUSD", "Observed1MReturnPct",
        "ModeledScenarioImpactPct",
    ])
    scen = payload["active_scenario"]
    for row in payload.get("corporate_exposure", []):
        writer.writerow([
            scen["scenario_name"], scen["risk_index"], scen["risk_band"],
            row["ticker"], row["company_name"], row["industry"], row["impact_tier"],
            row["base_exposure_score"], row["latest_close_usd"], row["return_1m_pct"],
            row["modeled_scenario_impact_pct"],
        ])
    buf.seek(0)
    safe_name = scenario.lower().replace(" ", "_")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=hormuz_exposure_{safe_name}.csv"},
    )
