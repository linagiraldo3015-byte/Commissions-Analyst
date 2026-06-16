SELECT 'agents'             AS tabla, COUNT(*) AS filas FROM commissions.agents
UNION ALL
SELECT 'commission_schemes', COUNT(*) FROM commissions.commission_schemes
UNION ALL
SELECT 'sales',              COUNT(*) FROM commissions.sales;

----VERIFICO ACTIVOS, CANCELADOS Y PENDIENTES

select *
from commissions.sales
limit 10;

select 
	status,
	count(*)
from commissions.sales
group by status;

---435.045 ventas activas
---0.087 canceladas 
---24.868 pendientes



---VERIFICO DUPLICADOS


SELECT COUNT(*)
FROM commissions.sales
WHERE is_duplicate = TRUE;
---25,000 duplicados


---VERIFICO NULOS
SELECT COUNT(*)
FROM commissions.sales
WHERE transaction_value_usd is NULL;




---VERIFICO POR REGION DONDE ESTÁN LOS NULOS

SELECT
    a.region,
    COUNT(*) AS null_values
FROM commissions.sales s
JOIN commissions.agents a ON s.agent_id = a.agent_id
WHERE s.transaction_value_usd IS NULL
GROUP BY a.region
ORDER BY null_values DESC;
---podemos observar que todos los valores nulos provienen de una misma ciudad (Barranquilla),
--- lo cual sugiere un problema operativo local, por ende hay que investigar y descartar cualquier error antes de procesar la liquidacion de comisiones.

}


--VALIDAMOS SI TODOS LOS AGENTES TIENEN UN ESQUEMA DE COMISIONES ASOCIADO
select *
from commissions.agents
limit 10;

SELECT
    a.agent_id,
    a.agent_name,
    a.channel,
    a.region
FROM commissions.agents a
LEFT JOIN commissions.commission_schemes cs ON a.channel = cs.channel
WHERE cs.scheme_id IS NULL;
---todos los agentes tienen un esquema asignado



--- VALIDAMOS QUE TODAS LAS VENTAS TENGAN UN AGENTE ASIGNADO
SELECT
    s.agent_id,
    COUNT(*) AS orphan_sales
FROM commissions.sales s
LEFT JOIN commissions.agents a ON s.agent_id = a.agent_id
WHERE a.agent_id IS NULL
GROUP BY s.agent_id;

---En este caso todas las ventas tienen un agente valido asignado




---REVISAMOS QUE LOS VALORES DE LAS TRANSACCIONES SEAN RAZONABLES
SELECT
    COUNT(*)                                        AS total_valid_sales,
    ROUND(MIN(transaction_value_usd)::NUMERIC, 2)   AS min_value,
    ROUND(AVG(transaction_value_usd)::NUMERIC, 2)   AS avg_value,
    ROUND(MAX(transaction_value_usd)::NUMERIC, 2)   AS max_value,
    COUNT(CASE WHEN transaction_value_usd > 5000 THEN 1 END) AS suspicious_high_values
FROM commissions.sales
WHERE transaction_value_usd IS NOT NULL;

--Tenemos que todos los valores estan dentro del rango de 5,000 usd, por ende son valores seguros para hacer la liquidacion



---QUERY FILTRADA PARA HACER LIQUIDACION : NUMERO DE FILAS VALIDAS DE SALES
SELECT
    COUNT(*) AS clean_sales_for_liquidation
FROM commissions.sales
WHERE status = 'Activo'
  AND is_duplicate = FALSE
  AND transaction_value_usd IS NOT NULL;
--- son 405,146 filas con datos validos eliminando duplicados, nulos y estados que no sean activo.








