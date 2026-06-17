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