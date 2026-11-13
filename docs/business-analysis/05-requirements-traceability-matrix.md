# Requirements Traceability Matrix (RTM) — Project 4

**Document ID:** RTM-P4-005  
**Companion Workbook:** `docs/business-analysis/rtm_workbook.xlsx`  

| Req ID | Requirement | Architecture Component | Automated Test | Status |
|--------|-------------|------------------------|----------------|--------|
| FR-01 | Pipeline ingestion | `src/pipeline.py::run_pipeline` | `test_pipeline_populates_all_tables` | Verified |
| FR-02 | 5-regime stress engine | `src/config.py::SCENARIOS`, `src/analytics.py` | `test_scenarios_monotonic_stress_order` | Verified |
| FR-03 | Observed vs modeled separation | `src/analytics.py::get_dashboard_data` | `test_normal_vs_full_closure_separation` | Verified |
| FR-04 | Calendar & industry filtering | `src/analytics.py::FilterParams` | `test_industry_filter_restricts_companies` | Verified |
| FR-05 | HTTP API & error handling | `app/main.py::api_dashboard` | `test_api_dashboard_and_invalid_scenario` | Verified |
| FR-06 | CSV export endpoint | `app/main.py::export_exposure_csv` | `test_csv_export_endpoint` | Verified |
| FR-07 | BA Excel & PDF deliverables | `src/ba_artifacts.py` | `test_ba_artifacts_generated` | Verified |
