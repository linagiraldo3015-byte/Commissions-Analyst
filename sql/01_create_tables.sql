-- ============================================================
-- 01_create_tables.sql
-- Commissions Liquidation System — Fintech (simulated)
-- Creates schema and loads agents, schemes, and sales data
-- ============================================================

-- Create schema to keep everything organized
CREATE SCHEMA IF NOT EXISTS commissions;

-- ── TABLE 1: agents ─────────────────────────────────────────
-- One row per commercial agent in the network
DROP TABLE IF EXISTS commissions.agents CASCADE;

CREATE TABLE commissions.agents (
    agent_id        INT PRIMARY KEY,
    agent_name      VARCHAR(100) NOT NULL,
    region          VARCHAR(50)  NOT NULL,
    channel         VARCHAR(20)  NOT NULL CHECK (channel IN ('Interno', 'Externo')),
    team_lead_id    INT,
    monthly_quota   INT          NOT NULL,
    hire_date       DATE         NOT NULL
);

-- ── TABLE 2: commission_schemes ─────────────────────────────
-- Tier-based commission rules by channel
-- This is the "business rule table" — all calculations derive from here
DROP TABLE IF EXISTS commissions.commission_schemes CASCADE;

CREATE TABLE commissions.commission_schemes (
    scheme_id           INT PRIMARY KEY,
    channel             VARCHAR(20)    NOT NULL,
    tier                VARCHAR(10)    NOT NULL,
    min_activations     INT            NOT NULL,
    max_activations     INT,           -- NULL means no upper limit (open tier)
    commission_pct      DECIMAL(5,4)   NOT NULL,
    bonus_pct           DECIMAL(5,4)   NOT NULL DEFAULT 0
);

-- ── TABLE 3: sales ──────────────────────────────────────────
-- 500,000 rows — one per transaction, full year 2024
-- Intentionally contains duplicates, nulls, and cancelled records
DROP TABLE IF EXISTS commissions.sales CASCADE;

CREATE TABLE commissions.sales (
    sale_id                 INT PRIMARY KEY,
    agent_id                INT          NOT NULL REFERENCES commissions.agents(agent_id),
    sale_date               DATE         NOT NULL,
    product_type            VARCHAR(50)  NOT NULL,
    transaction_value_usd   DECIMAL(10,2),  -- nullable: quality issue in Barranquilla region
    status                  VARCHAR(20)  NOT NULL CHECK (status IN ('Activo', 'Cancelado', 'Pendiente')),
    is_duplicate            BOOLEAN      NOT NULL DEFAULT FALSE
);

-- ── INDEXES for performance ─────────────────────────────────
-- These matter at 500K rows — queries without indexes will be slow
CREATE INDEX idx_sales_agent_id   ON commissions.sales(agent_id);
CREATE INDEX idx_sales_sale_date  ON commissions.sales(sale_date);
CREATE INDEX idx_sales_status     ON commissions.sales(status);
CREATE INDEX idx_sales_duplicate  ON commissions.sales(is_duplicate);

-- ── VERIFY tables were created ──────────────────────────────
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size('commissions.' || table_name)) AS size
FROM information_schema.tables
WHERE table_schema = 'commissions'
ORDER BY table_name;



ALTER TABLE commissions.commission_schemes 
ALTER COLUMN max_activations TYPE DECIMAL(10,1);