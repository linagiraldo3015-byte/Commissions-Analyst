--CALCULAMOS CUANTO VENDIO CADA AGENTE:
SELECT
    agent_id,
    COUNT(*)                        AS total_activations,
    SUM(transaction_value_usd)      AS total_value_usd
FROM commissions.sales
WHERE status = 'Activo'
  AND is_duplicate = FALSE
  AND transaction_value_usd IS NOT NULL
  AND sale_date between '2024-01-01' AND '2024-01-31'
GROUP BY agent_id
ORDER BY total_activations DESC;



---ASIGNAMOS EL TIER QUE LE CORRESPONDE A CADA AGENTE SEGUN SU CANAL Y VOLUMEN DE ACTIVACIONES
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
)
SELECT
    cs.agent_id,
    a.agent_name,
    a.channel,
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
ORDER BY cs.total_activations DESC;




---AGREGAMOS COMISION BASE, BONO EN CASO DE QUE APLIQUE Y CALCULAMOS EL TOTAL A PAGAR

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
)
SELECT
    agent_id,
    agent_name,
    channel,
    region,
    monthly_quota,
    total_activations,
    ROUND(total_value_usd::NUMERIC, 2)                          AS total_value_usd,
    tier,
    ROUND((total_value_usd * commission_pct)::NUMERIC, 2)       AS base_commission_usd,
    CASE
        WHEN total_activations >= monthly_quota
        THEN ROUND((total_value_usd * bonus_pct)::NUMERIC, 2)
        ELSE 0
    END                                                          AS bonus_usd,
    ROUND((total_value_usd * commission_pct +
        CASE
            WHEN total_activations >= monthly_quota
            THEN total_value_usd * bonus_pct
            ELSE 0
        END)::NUMERIC, 2)                                        AS total_payout_usd
FROM tiered_sales
ORDER BY total_payout_usd DESC;
---Con este query final tenemos una tabla con todos los datos limpios y organizados con la liquidacion de las comisiones de los agentes.

