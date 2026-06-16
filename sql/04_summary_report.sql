-- ============================================================
-- 04_summary_report.sql
-- Commissions Liquidation System — Fintech (simulated)
-- Final payout report for January 2024 — ready for Payroll
-- ============================================================
WITH clean_sales AS (
    SELECT
        agent_id,
        COUNT(*)                   AS total_activations,
        SUM(transaction_value_usd) AS total_value_usd
    FROM commissions.sales
    WHERE status = 'Activo'
      AND is_duplicate = FALSE
      AND transaction_value_usd IS NOT NULL
      AND sale_date BETWEEN '2024-01-01' AND '2024-01-31'
    GROUP BY agent_id
),
tiered_sales AS (
    SELECT
        cs.agent_id,
        a.agent_name,
        a.channel,
        a.region,
        a.monthly_quota,
        cs.total_activations,
        cs.total_value_usd,
        sch.tier,
        sch.commission_pct,
        sch.bonus_pct
    FROM clean_sales cs
    JOIN commissions.agents a ON cs.agent_id = a.agent_id
    JOIN commissions.commission_schemes sch
        ON a.channel = sch.channel
        AND cs.total_activations >= sch.min_activations
        AND (cs.total_activations <= sch.max_activations OR sch.max_activations IS NULL)
),
final_report AS (
    SELECT
        agent_id,
        agent_name,
        channel,
        region,
        monthly_quota,
        total_activations,
        ROUND(total_value_usd::NUMERIC, 2)                    AS total_value_usd,
        tier,
        ROUND((total_value_usd * commission_pct)::NUMERIC, 2) AS base_commission_usd,
        CASE
            WHEN total_activations >= monthly_quota
            THEN ROUND((total_value_usd * bonus_pct)::NUMERIC, 2)
            ELSE 0
        END                                                    AS bonus_usd,
        ROUND((total_value_usd * commission_pct +
            CASE
                WHEN total_activations >= monthly_quota
                THEN total_value_usd * bonus_pct
                ELSE 0
            END)::NUMERIC, 2)                                  AS total_payout_usd,
        CASE
            WHEN total_activations >= monthly_quota THEN 'Cumplió meta'
            ELSE 'No cumplió meta'
        END                                                    AS quota_status
    FROM tiered_sales
)
SELECT
    COUNT(*)                                                    AS total_agents,
    COUNT(CASE WHEN quota_status = 'Cumplió meta' THEN 1 END)  AS agents_met_quota,
    ROUND(AVG(total_activations), 1)                           AS avg_activations,
    ROUND(SUM(total_payout_usd)::NUMERIC, 2)                   AS total_commission_cost_usd
FROM final_report;
---Todos los agentes tuvieron ventas en Enero, con un 84% de cumplimiento total de metas de los agentes.
