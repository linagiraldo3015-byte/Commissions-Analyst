# Commissions Liquidation System — Fintech Sales Analytics

Automated end-to-end pipeline for calculating, validating, and reporting commercial agent commissions in a fintech environment. Built to simulate the real operational challenge faced by Sales Ops and Finance teams managing large agent networks.

---

## Business Context

In a fintech company with hundreds of commercial agents, commission liquidation is a monthly critical process. A single error in this process directly affects agent trust, retention, and morale — and without a structured pipeline, manual spreadsheets become a compliance and scalability risk.

This project solves three core problems:

**1. Data quality before calculation** — Raw sales data contains duplicates, cancelled transactions, and missing values. Calculating commissions on dirty data produces incorrect payments. This pipeline validates and flags every anomaly before a single commission is computed.

**2. Scalable, rule-based liquidation** — Commission schemes vary by agent channel (internal vs. external) and tier (based on monthly activation volume). Applying these rules manually across 100+ agents and 500K+ transactions is error-prone. The SQL engine applies all rules consistently and automatically.

**3. Full auditability** — Every agent must be able to understand why they received a specific payment. The pipeline generates a detailed breakdown — transactions counted, tier applied, bonus triggered — so Finance and Sales Ops can answer any dispute in minutes, not days.

---

## Dataset

Simulated dataset representing 12 months of commercial activity for a fintech agent network operating in Colombia.

| File | Rows | Description |
|---|---|---|
| `data/sales_2024.csv` | 500,000 | Individual transactions per agent, with embedded quality issues |
| `data/agents.csv` | 100 | Agent profiles: region, channel, team lead, monthly quota |
| `data/commission_schemes.csv` | 6 | Tier-based commission rules by channel |

**Intentional data quality issues (realistic production scenarios):**
- 5% duplicate transactions (`is_duplicate = TRUE`)
- 8% cancelled sales that must be excluded from liquidation
- 2% null transaction values concentrated in one region
- Mixed `Pendiente` status requiring business rule decisions

**Transaction values (USD):**
- Datáfono físico: $200 – $2,000
- Link de pago: $50 – $800
- Datáfono inalámbrico: $150 – $1,500
- Average: ~$855

---

## Commission Schemes

**Internal agents** (Internal employees):

| Tier | Activations/month | Commission | Bonus if quota met |
|---|---|---|---|
| Tier 1 | 0 – 30 | 3.0% | — |
| Tier 2 | 31 – 60 | 4.5% | — |
| Tier 3 | 61+ | 6.0% | +10% |

**External agents** (independent / allied):

| Tier | Activations/month | Commission | Bonus if quota met |
|---|---|---|---|
| Tier 1 | 0 – 20 | 2.0% | — |
| Tier 2 | 21 – 50 | 3.0% | — |
| Tier 3 | 51+ | 4.5% | +8% |

---

## Project Structure

```
commissions-analyst/
│
├── data/
│   ├── agents.csv
│   ├── sales_2024.csv
│   └── commission_schemes.csv
│
├── sql/
│   ├── 01_create_tables.sql        # Schema and data loading
│   ├── 02_data_quality_checks.sql  # Anomaly detection before liquidation
│   ├── 03_liquidation.sql          # Tier assignment and commission calculation
│   └── 04_summary_report.sql       # Final payout report per agent
│
├── python/
│   ├── 01_data_quality.py          # Automated quality checks with exportable report
│   ├── 02_liquidation_engine.py    # Commission calculation with audit trail
│   └── 03_export_report.py         # Formatted Excel output for Payroll
│
├── output/
│   ├── liquidacion_mayo_2025.xlsx  # Final deliverable for Payroll team
│   └── quality_report.txt          # Data quality summary before each run
│
└── README.md
```

---

## Pipeline Flow

```
Raw CSVs
    ↓
01_create_tables.sql       → Load data into PostgreSQL
    ↓
02_data_quality_checks.sql → Flag duplicates, nulls, cancelled, unmatched agents
    ↓
03_liquidation.sql         → Apply tier rules, calculate base commission + bonus
    ↓
04_summary_report.sql      → Aggregate payout per agent with full breakdown
    ↓
02_liquidation_engine.py   → Read report, log audit trail, detect anomalies
    ↓
03_export_report.py        → Export formatted Excel ready for Payroll
```

---

## Key SQL Concepts Used

- `CASE WHEN` — tier assignment based on activation volume ranges
- `CTEs` — multi-step liquidation logic organized for readability and debugging
- `Window functions` — agent rankings and cumulative metrics
- `LEFT JOIN` — matching agents to their applicable commission scheme
- `DATE_TRUNC` — filtering transactions by exact billing period
- `GROUP BY + SUM` — aggregating sales volume and transaction value per agent

---

## Business Impact

This pipeline directly addresses the operational challenges a Sales Ops or Finance team faces at scale:

- **Eliminates manual errors** — rule-based calculation replaces spreadsheet formulas that break at scale
- **Reduces dispute resolution time** — audit trail lets anyone trace exactly why an agent received a specific amount
- **Catches bad data before it costs money** — quality checks run before any commission is computed
- **Anomaly detection** — agents whose commission deviates more than 2 standard deviations from their historical average are automatically flagged for review
- **Scalable by design** — the pipeline handles 500K+ transactions and can be scheduled to run monthly without manual intervention

---

## Tech Stack

| Layer | Tool |
|---|---|
| Database | PostgreSQL |
| Transformation | SQL (CTEs, window functions) |
| Automation | Python (pandas) |
| Output | Excel (.xlsx) |
| Version control | Git / GitHub |

---

## How to Run

**1. Load data into PostgreSQL**
```bash
psql -U your_user -d your_db -f sql/01_create_tables.sql
```

**2. Run data quality checks**
```bash
psql -U your_user -d your_db -f sql/02_data_quality_checks.sql
```

**3. Run liquidation**
```bash
psql -U your_user -d your_db -f sql/03_liquidation.sql
psql -U your_user -d your_db -f sql/04_summary_report.sql
```

**4. Generate Excel report**
```bash
python python/03_export_report.py
```

---

## Author

**Lina Giraldo**
Data Analyst | SQL · Python · PostgreSQL
[www.linkedin.com/in/linagiraldom] · [github.com/linagiraldo3015-byte]

