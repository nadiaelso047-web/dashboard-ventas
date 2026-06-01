import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

def autenticar():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.set_page_config(page_title="Acceso Restringido", page_icon="🔐")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_form"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar")
                if submitted:
                    if usuario == "admin" and password == "admin123":
                        st.session_state.autenticado = True
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
        return False
    return True

if not autenticar():
    st.stop()

st.set_page_config(page_title="Dashboard Ventas", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg/export?format=csv&gid=1898188061"

@st.cache_data(ttl=300)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
    df = df[~df["ID CAJERO"].astype(str).str.contains("SUBTOTALES", na=False)]
    df = df.dropna(subset=["Columna 1"])
    df["FECHA"] = pd.to_datetime(df["Columna 1"], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=["FECHA"])
    
    def limpiar_numero(x):
        if pd.isna(x):
            return 0
        try:
            s = str(x).replace(".", "").replace(",", ".")
            return float(re.search(r"[\d\.]+", s).group())
        except:
            return 0
    
    for col in ["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO"]:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_numero)
    
    df["VENTA_TOTAL"] = df[["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO"]].sum(axis=1)
    df["CAJERO"] = df["ID CAJERO"].astype(str).str.split("-").str[1]
    df["AÑO"] = df["FECHA"].dt.year
    df["MES_NOMBRE"] = df["FECHA"].dt.strftime("%B %Y")
    df["MES_ORDEN"] = df["FECHA"].dt.year * 100 + df["FECHA"].dt.month
    return df

df = cargar_datos()

st.sidebar.markdown("## Panel de control")
años = sorted(df["AÑO"].unique(), reverse=True)
año = st.sidebar.selectbox("Año", años)

df_año = df[df["AÑO"] == año]

meses = df_año[["MES_NOMBRE", "MES_ORDEN"]].drop_duplicates().sort_values("MES_ORDEN")["MES_NOMBRE"].tolist()
mes = st.sidebar.selectbox("Mes", meses)

filtro = df_año[df_año["MES_NOMBRE"] == mes]

if filtro.empty:
    st.warning(f"No hay datos para {mes}")
    st.stop()

st.markdown("## Dashboard de Ventas")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Venta Total", f"")
col2.metric("Efectivo", f"")
col3.metric("Tarjeta", f"")
col4.metric("Ticket Promedio", f"")

st.dataframe(filtro[["FECHA", "CAJERO", "VENTA_TOTAL"]].head(50))
