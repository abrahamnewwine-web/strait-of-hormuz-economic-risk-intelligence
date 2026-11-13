# Business Requirements Document (BRD) — Project 4

**Document ID:** BRD-P4-002  
**Author:** Abraham Adetola  

## 1. Functional Requirements
| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| **FR-01** | Dual-Source Macro & Equity Ingestion | Must Have | `run_pipeline()` loads 138 monthly macro observations and 8 Fortune 500 equity records into SQLite + CSVs. |
| **FR-02** | 5-Scenario Stress Regime Engine | Must Have | Selecting any of 5 scenarios recomputes Hormuz Risk Index (24–96) and flow/oil/freight/inflation parameters. |
| **FR-03** | Baseline vs. Modeled Labeling | Must Have | UI and API explicitly label observed metrics vs. modeled stress outputs under active disruption. |
| **FR-04** | Multi-Faceted Filtering | Must Have | Users filter dynamically by Scenario, Year, Month, and Industry (`Airlines`, `Logistics`, `Retail`, `Energy`). |
| **FR-05** | 8 Macroeconomic Stress Cards | Must Have | Displays Brent, WTI, Diesel, Gasoline, Freight Index, Transportation CPI, Energy CPI, and PPI with 12M YoY deltas. |
| **FR-06** | Corporate Beta Impact Table & Chart | Must Have | Calculates directional modeled equity impact using documented `oil_beta` and `freight_beta` weights. |
| **FR-07** | CSV Stress Exposure Export | Must Have | `/api/export/exposure.csv` exports active scenario parameters and filtered company impacts. |

## 2. Non-Functional Requirements
- **Analytical Transparency:** Formula assumptions (`oil_beta`, `freight_beta`, shock multipliers) documented in SQL/DAX/README.
- **API Input Validation:** Unknown scenario names raise `ValueError` mapped to HTTP `400`.
- **Offline Determinism:** Verified local CSV snapshots allow zero-network reproduction when upstream endpoints are unavailable.
