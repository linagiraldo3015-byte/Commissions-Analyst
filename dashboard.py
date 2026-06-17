import streamlit as st
import pandas as pd

# ── Config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Commissions Dashboard",
    page_icon="💳",
    layout="wide"
)

# ── Load and calculate data from CSVs ────────────────────────
@st.cache_data
def load_data():
    sales    = pd.read_csv('data/sales_2024.csv', parse_dates=['sale_date'])
    agents   = pd.read_csv('data/agents.csv')
    schemes  = pd.read_csv('data/commission_schemes.csv')

    # Clean sales — same rules as SQL
    clean = sales[
        (sales['status'] == 'Activo') &
        (sales['is_duplicate'] == False) &
        (sales['transaction_value_usd'].notna()) &
        (sales['sale_date'].between('2024-01-01', '2024-01-31'))
    ]

    # Aggregate per agent
    agg = clean.groupby('agent_id').agg(
        total_activations=('sale_id', 'count'),
        total_value_usd=('transaction_value_usd', 'sum')
    ).reset_index()

    # Join with agents
    df = agg.merge(agents, on='agent_id')

    # Assign tier
    def assign_tier(row):
        channel_schemes = schemes[schemes['channel'] == row['channel']]
        for _, s in channel_schemes.iterrows():
            min_a = s['min_activations']
            max_a = s['max_activations']
            if row['total_activations'] >= min_a and (pd.isna(max_a) or row['total_activations'] <= max_a):
                return s['tier'], s['commission_pct'], s['bonus_pct']
        return None, None, None

    df[['tier', 'commission_pct', 'bonus_pct']] = df.apply(
        lambda row: pd.Series(assign_tier(row)), axis=1
    )

    # Calculate commissions
    df['base_commission_usd'] = (df['total_value_usd'] * df['commission_pct']).round(2)
    df['bonus_usd'] = df.apply(
        lambda row: round(row['total_value_usd'] * row['bonus_pct'], 2)
        if row['total_activations'] >= row['monthly_quota'] else 0, axis=1
    )
    df['total_payout_usd'] = (df['base_commission_usd'] + df['bonus_usd']).round(2)
    df['quota_status'] = df.apply(
        lambda row: 'Cumplió meta' if row['total_activations'] >= row['monthly_quota']
        else 'No cumplió meta', axis=1
    )

    return df.sort_values('total_payout_usd', ascending=False)

df = load_data()

# ── Header ───────────────────────────────────────────────────
st.title("💳 Commissions Liquidation Dashboard")
st.caption("Lina's Fintech — Enero 2024 | Simulated dataset · 500K transactions")
st.divider()

# ── Section 1: Executive summary ─────────────────────────────
st.subheader("📊 Resumen Ejecutivo")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Agentes", len(df))
col2.metric(
    "Cumplieron Meta",
    f"{len(df[df['quota_status'] == 'Cumplió meta'])}",
    f"{len(df[df['quota_status'] == 'Cumplió meta']) / len(df) * 100:.1f}%"
)
col3.metric("Promedio Activaciones", f"{df['total_activations'].mean():.0f}")
col4.metric("Costo Total Comisiones", f"${df['total_payout_usd'].sum():,.0f} USD")

st.divider()

# ── Section 2: Data quality findings ─────────────────────────
st.subheader("🔍 Hallazgos de Calidad de Datos")
st.caption("Problemas detectados y resueltos antes de calcular comisiones")

q1, q2, q3 = st.columns(3)
q1.error("🔴 **25,000** transacciones duplicadas eliminadas (5%)")
q2.warning("🟡 **40,087** ventas canceladas excluidas (8%)")
q3.warning("🟡 **10,000** valores nulos en Barranquilla (2%)")

st.info("✅ **405,146 transacciones limpias** entraron al proceso de liquidación de un total de 500,000 registros.")

st.divider()

# ── Section 3: Top 10 agents ──────────────────────────────────
st.subheader("🏆 Top 10 Agentes por Comisión — Enero 2024")

top10 = df.head(10)[
    ['agent_name', 'channel', 'region', 'tier',
     'total_activations', 'total_payout_usd', 'quota_status']
].copy()
top10.columns = ['Agente', 'Canal', 'Región', 'Tier', 'Activaciones', 'Total a Pagar (USD)', 'Estado Meta']

st.dataframe(
    top10,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Total a Pagar (USD)': st.column_config.NumberColumn(format='$%.2f')
    }
)

st.divider()

# ── Section 4: Full report ────────────────────────────────────
with st.expander("📋 Ver reporte completo de liquidación"):
    full = df[['agent_name', 'channel', 'region', 'tier',
               'total_activations', 'base_commission_usd',
               'bonus_usd', 'total_payout_usd', 'quota_status']].copy()
    full.columns = ['Agente', 'Canal', 'Región', 'Tier', 'Activaciones',
                    'Comisión Base (USD)', 'Bono (USD)', 'Total (USD)', 'Estado Meta']
    st.dataframe(
        full,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Comisión Base (USD)': st.column_config.NumberColumn(format='$%.2f'),
            'Bono (USD)': st.column_config.NumberColumn(format='$%.2f'),
            'Total (USD)': st.column_config.NumberColumn(format='$%.2f')
        }
    )

# ── Section 5: Agentes en Riesgo de Abandono ─────────────────
st.divider()
st.subheader("🚨 Agentes en Riesgo de Abandono")
st.caption("Identifica agentes con bajo rendimiento sostenido antes de que abandonen la red comercial.")

@st.cache_data
def load_risk_data():
    sales   = pd.read_csv('data/sales_2024.csv', parse_dates=['sale_date'])
    agents  = pd.read_csv('data/agents.csv')
    schemes = pd.read_csv('data/commission_schemes.csv')

    # Clean sales
    clean = sales[
        (sales['status'] == 'Activo') &
        (sales['is_duplicate'] == False) &
        (sales['transaction_value_usd'].notna())
    ].copy()

    # Add month column
    clean['month'] = clean['sale_date'].dt.to_period('M')

    # Activations per agent per month
    monthly = clean.groupby(['agent_id', 'month']).agg(
        activations=('sale_id', 'count')
    ).reset_index()

    # Join with agents to get quota
    monthly = monthly.merge(agents[['agent_id', 'agent_name', 'region', 'channel', 'monthly_quota']], on='agent_id')

    # Calculate % of quota achieved
    monthly['pct_quota'] = (monthly['activations'] / monthly['monthly_quota'] * 100).round(1)

    # Use last 3 months of data available
    last_3 = sorted(monthly['month'].unique())[-3:]
    recent = monthly[monthly['month'].isin(last_3)]

    # Pivot to wide format
    pivot = recent.pivot_table(
        index=['agent_id', 'agent_name', 'region', 'channel', 'monthly_quota'],
        columns='month',
        values='pct_quota'
    ).reset_index()

    pivot.columns = [str(c) for c in pivot.columns]
    month_cols = [str(m) for m in last_3]

    # Assign risk level
    def assign_risk(row):
        values = [row.get(m, None) for m in month_cols]
        values = [v for v in values if v is not None]
        if len(values) == 0:
            return '⚪ Sin datos'
        consecutive_low = sum(1 for v in values[-2:] if v < 40)
        if consecutive_low >= 2:
            return '🔴 Riesgo Alto'
        elif any(v < 50 for v in values[-1:]):
            return '🟡 Riesgo Medio'
        else:
            return '🟢 En buen camino'

    pivot['riesgo'] = pivot.apply(assign_risk, axis=1)

    # Rename month columns to readable format
    month_labels = {}
    for m in month_cols:
        period = pd.Period(m)
        month_labels[m] = period.strftime('%b %Y')

    pivot = pivot.rename(columns=month_labels)

    return pivot, list(month_labels.values())

risk_df, month_labels = load_risk_data()

# Summary metrics
r1, r2, r3 = st.columns(3)
r1.metric("🔴 Riesgo Alto",    len(risk_df[risk_df['riesgo'] == '🔴 Riesgo Alto']))
r2.metric("🟡 Riesgo Medio",   len(risk_df[risk_df['riesgo'] == '🟡 Riesgo Medio']))
r3.metric("🟢 En buen camino", len(risk_df[risk_df['riesgo'] == '🟢 En buen camino']))

st.markdown("---")

# Filter
filtro = st.selectbox(
    "Filtrar por nivel de riesgo:",
    ["Todos", "🔴 Riesgo Alto", "🟡 Riesgo Medio", "🟢 En buen camino"]
)

if filtro != "Todos":
    display_df = risk_df[risk_df['riesgo'] == filtro]
else:
    display_df = risk_df

# Display table
cols_to_show = ['agent_name', 'region', 'channel'] + month_labels + ['riesgo']
display_df = display_df[cols_to_show].copy()
display_df.columns = ['Agente', 'Región', 'Canal'] + [f'% Meta {m}' for m in month_labels] + ['Riesgo']

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

st.info("💡 **¿Cómo leer esta tabla?** Cada columna de mes muestra qué porcentaje de su meta mensual alcanzó el agente. Un agente con 2 meses consecutivos bajo el 40% es candidato a intervención comercial inmediata.")

   


   

   # ── Section 6: Anomalías en Liquidación ──────────────────────
st.divider()
st.subheader("🔎 Detección de Anomalías en Liquidación")
st.caption("Agentes cuya comisión de enero se desvía significativamente de su promedio histórico — requieren revisión antes de procesar el pago.")

@st.cache_data
def load_anomaly_data():
    sales  = pd.read_csv('data/sales_2024.csv', parse_dates=['sale_date'])
    agents = pd.read_csv('data/agents.csv')
    schemes = pd.read_csv('data/commission_schemes.csv')

    clean = sales[
        (sales['status'] == 'Activo') &
        (sales['is_duplicate'] == False) &
        (sales['transaction_value_usd'].notna())
    ].copy()

    clean['month'] = clean['sale_date'].dt.to_period('M')

    # Monthly value per agent
    monthly = clean.groupby(['agent_id', 'month']).agg(
        total_value=('transaction_value_usd', 'sum'),
        activations=('sale_id', 'count')
    ).reset_index()

    # Assign commission
    monthly = monthly.merge(agents[['agent_id', 'agent_name', 'region', 'channel']], on='agent_id')

    def get_commission(row):
        ch_schemes = schemes[schemes['channel'] == row['channel']]
        for _, s in ch_schemes.iterrows():
            max_a = s['max_activations']
            if row['activations'] >= s['min_activations'] and (pd.isna(max_a) or row['activations'] <= max_a):
                return round(row['total_value'] * s['commission_pct'], 2)
        return 0

    monthly['commission'] = monthly.apply(get_commission, axis=1)

    # Historical average and std (all months except January 2024)
    historical = monthly[monthly['month'] != pd.Period('2024-01', 'M')]
    stats = historical.groupby('agent_id').agg(
        hist_mean=('commission', 'mean'),
        hist_std=('commission', 'std')
    ).reset_index()

    # January 2024
    january = monthly[monthly['month'] == pd.Period('2024-01', 'M')][
        ['agent_id', 'agent_name', 'region', 'channel', 'commission', 'activations']
    ].copy()

    # Merge
    result = january.merge(stats, on='agent_id')
    result['hist_std'] = result['hist_std'].fillna(0)

    # Flag anomalies — more than 2 std deviations from mean
    result['variacion_pct'] = ((result['commission'] - result['hist_mean']) / result['hist_mean'] * 100).round(1)
    result['es_anomalia'] = abs(result['commission'] - result['hist_mean']) > 2 * result['hist_std']

    result['flag'] = result.apply(
        lambda row: '🚨 Revisar' if row['es_anomalia'] and row['variacion_pct'] > 0
        else ('⚠️ Caída inusual' if row['es_anomalia'] and row['variacion_pct'] < 0
        else '✅ Normal'), axis=1
    )

    return result.sort_values('variacion_pct', ascending=False)

anomaly_df = load_anomaly_data()

# Summary
a1, a2, a3 = st.columns(3)
a1.metric("🚨 Requieren revisión", len(anomaly_df[anomaly_df['flag'] == '🚨 Revisar']))
a2.metric("⚠️ Caída inusual",      len(anomaly_df[anomaly_df['flag'] == '⚠️ Caída inusual']))
a3.metric("✅ Normales",            len(anomaly_df[anomaly_df['flag'] == '✅ Normal']))

st.markdown("---")

filtro_anomalia = st.selectbox(
    "Filtrar por tipo:",
    ["Todos", "🚨 Revisar", "⚠️ Caída inusual", "✅ Normal"],
    key="filtro_anomalia"
)

display = anomaly_df.copy()
if filtro_anomalia != "Todos":
    display = display[display['flag'] == filtro_anomalia]

display_cols = display[['agent_name', 'region', 'channel', 'activations',
                          'commission', 'hist_mean', 'variacion_pct', 'flag']].copy()
display_cols.columns = ['Agente', 'Región', 'Canal', 'Activaciones',
                         'Comisión Enero (USD)', 'Promedio Histórico (USD)',
                         'Variación (%)', 'Estado']

st.dataframe(
    display_cols,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Comisión Enero (USD)':      st.column_config.NumberColumn(format='$%.2f'),
        'Promedio Histórico (USD)':  st.column_config.NumberColumn(format='$%.2f'),
        'Variación (%)':             st.column_config.NumberColumn(format='%.1f%%')
    }
)

st.info("💡 **¿Cómo funciona?** Comparamos la comisión de enero de cada agente contra su promedio histórico. Si la diferencia supera 2 desviaciones estándar, el caso se flaggea para revisión manual antes de procesar el pago.")