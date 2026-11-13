# UAT Test Plan & Defect Log — Project 4

**Document ID:** UAT-P4-007  
**Companion Workbook:** `docs/business-analysis/uat_test_log.xlsx`  

## 1. UAT Scope & Exit Criteria
- All 6 pytest verification suites passing with zero skips or relaxed assertions.
- Playwright visual inspection verifying `Normal` (Observed Baseline) and `Full Closure` (Critical Risk = `96`) views render zero console errors and zero overlapping labels.
- Negative API input check confirming unknown scenarios return HTTP `400`.

## 2. Defect Resolution Log
| Defect ID | Severity | Description | Resolution | Status |
|-----------|----------|-------------|------------|--------|
| DEF-P4-01 | Medium | Ensure SQLite `.db` binary stays untracked while CSV snapshots persist in Git | Added `data/processed/*.db` to `.gitignore` | Closed |
| DEF-P4-02 | Medium | Prevent ambiguity between observed price baselines and scenario stress projections | Added `is_stressed` badge + `Obs:` subtitle on stressed KPI cards | Closed |
