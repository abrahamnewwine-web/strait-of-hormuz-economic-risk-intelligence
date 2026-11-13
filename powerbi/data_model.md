# Power BI Star Schema Data Model — Strait of Hormuz Risk Intelligence

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_MACRO_MONTHLY : "date_key"
    DIM_COMPANY ||--o{ FACT_CORPORATE_EXPOSURE : "company_id"
```
