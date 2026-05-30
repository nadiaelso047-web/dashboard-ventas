import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re

st.set_page_config(page_title="Dashboard Ventas", layout="wide", page_icon="📊")

st.title("📊 Dashboard de Ventas")
st.markdown("---")

@st.cache_data(ttl=300)
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg/export?format=csv&gid=1898188061"
    df = pd.read_csv(url)
    df = df[~df["ID CAJERO"].astype(str).str.contains("SUBTOTALES", na=False)]
    df = df.dropna(subset=["Columna 1"])
    df["FECHA"] = pd.to_datetime(df["Columna 1"], errors='coerce')
    df = df.dropna(subset=["FECHA"])
    
    def limpiar_numero(x):
        if pd.isna(x):
            return 0
        if isinstance(x, (int, float)):
            return float(x)
        try:
            s = str(x).replace(".", "").replace(",", ".")
            return float(re.search(r"[\d\.]+", s).group())
        except:
            return 0
    
    pagos = ["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO"]
    for col in pagos:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_numero)
    
    df["VENTA_TOTAL"] = df[pagos].sum(axis=1)
    df["CAJERO"] = df["ID CAJERO"].astype(str).str.split("-").str[1]
    df["MES"] = df["FECHA"].dt.strftime("%B %Y")
    df["DIA"] = df["FECHA"].dt.date
    return df

df = cargar_datos()

st.sidebar.header("🎛️ Filtros")
mes = st.sidebar.selectbox("Mes", sorted(df["MES"].unique()))
cajero = st.sidebar.selectbox("Cajero", ["Todos"] + sorted(df["CAJERO"].unique()))

filtro = df[df["MES"] == mes]
if cajero != "Todos":
    filtro = filtro[filtro["CAJERO"] == cajero]

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("💰 Venta Total", f"${filtro['VENTA_TOTAL'].sum():,.2f}")
with col2: st.metric("💵 Efectivo", f"${filtro['EFECTIVO RENDIDO'].sum():,.2f}")
with col3: st.metric("💳 Tarjeta", f"${filtro['TARJETA CREDITO'].sum() + filtro['TARJETA DEBITO'].sum():,.2f}")
with col4: st.metric("🎫 Ticket Promedio", f"${filtro['VENTA_TOTAL'].mean():,.2f}")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Ventas Diarias")
    diario = filtro.groupby("DIA")["VENTA_TOTAL"].sum().reset_index()
    fig = px.line(diario, x="DIA", y="VENTA_TOTAL", markers=True)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("👥 Top Cajeros")
    top = filtro.groupby("CAJERO")["VENTA_TOTAL"].sum().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(top, x="VENTA_TOTAL", y="CAJERO", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📋 Detalle de Transacciones")
# Mostrar solo las columnas que existen
columnas_disponibles = ["FECHA", "CAJERO", "VENTA_TOTAL"]
for col in columnas_disponibles:
    if col not in filtro.columns:
        columnas_disponibles.remove(col)
st.dataframe(filtro[columnas_disponibles].head(50))
