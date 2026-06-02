import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np

# ============================================
# AUTENTICACIÓN
# ============================================

def autenticar():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.set_page_config(page_title="Acceso Restringido", page_icon="🔐")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 3rem 0;">
                    <h1>🔐 Dashboard de Ventas</h1>
                    <p style="color: #666;">Acceso autorizado solamente</p>
                </div>
            """, unsafe_allow_html=True)

            if "intentos" not in st.session_state:
                st.session_state.intentos = 0

            if st.session_state.intentos >= 5:
                st.error("❌ Demasiados intentos. Acceso bloqueado temporalmente.")
                return False

            with st.form("login_form"):
                usuario = st.text_input("👤 Usuario")
                password = st.text_input("🔒 Contraseña", type="password")
                submitted = st.form_submit_button("🔓 Ingresar", use_container_width=True)

                if submitted:
                    USUARIO_CORRECTO = st.secrets.get("USUARIO", "admin")
                    PASSWORD_CORRECTO = st.secrets.get("PASSWORD", "admin123")

                    if usuario == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
                        st.session_state.autenticado = True
                        st.session_state.intentos = 0
                        st.rerun()
                    else:
                        st.session_state.intentos += 1
                        st.error(f"Credenciales incorrectas. Intentos restantes: {5 - st.session_state.intentos}")
        return False
    return True

if not autenticar():
    st.stop()

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(page_title="Super Dashboard Ventas", layout="wide")

# CSS Personalizado
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 20px;
            margin-bottom: 1.5rem;
            text-align: center;
            color: white;
        }
        .main-header h1 { color: white; margin: 0; font-size: 2rem; }
        .success-card {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 0.8rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .warning-card {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 0.8rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .danger-card {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 0.8rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #667eea;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🏆 SUPER DASHBOARD DE VENTAS</h1>
        <p>Análisis completo - Conciliación bancaria - Control de gestión</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# IDs CORRECTOS DE LAS HOJAS
# ============================================
SHEET_ID = "1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg"

SHEETS = {
    "control": "1996710268",
    "payway_tr": "1397161452",
    "control_efectivo": "1370399946",
    "control_tarjetas": "2080576930",
    "control_banco_macro": "772941566",
}

@st.cache_data(ttl=300)
def cargar_hoja(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return pd.DataFrame()

# ============================================
# CARGA DE DATOS
# ============================================
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    df_control = cargar_hoja(SHEETS["control"])
    df_payway = cargar_hoja(SHEETS["payway_tr"])
    df_efectivo = cargar_hoja(SHEETS["control_efectivo"])
    df_tarjetas = cargar_hoja(SHEETS["control_tarjetas"])
    df_banco = cargar_hoja(SHEETS["control_banco_macro"])

st.success("✅ Datos cargados correctamente")

# ============================================
# PROCESAMIENTO DE DATOS (VERSIÓN ROBUSTA)
# ============================================

# --- 1. Control (conciliación) ---
df_control_proc = pd.DataFrame()
if not df_control.empty and len(df_control) > 1:
    # La primera fila son los encabezados
    df_control.columns = df_control.iloc[0]
    df_control = df_control[1:].reset_index(drop=True)
    
    # Filtrar por fechas de mayo
    df_control = df_control[df_control["Columna 1"].astype(str).str.contains("2026-05", na=False)]
    df_control["FECHA"] = pd.to_datetime(df_control["Columna 1"], errors='coerce')
    df_control = df_control.dropna(subset=["FECHA"])
    
    # Buscar columnas de montos
    for col in df_control.columns:
        if "TR" in str(col) or "tarjeta" in str(col).lower():
            df_control["Ventas_TR"] = pd.to_numeric(df_control[col], errors='coerce').fillna(0)
        if "Banco" in str(col) or "MACRO" in str(col).upper():
            df_control["Banco_Macro"] = pd.to_numeric(df_control[col], errors='coerce').fillna(0)
    
    if "Ventas_TR" not in df_control.columns:
        df_control["Ventas_TR"] = 0
    if "Banco_Macro" not in df_control.columns:
        df_control["Banco_Macro"] = 0
    
    df_control["Diferencia"] = df_control["Ventas_TR"] - df_control["Banco_Macro"]
    df_control["%_Conciliacion"] = (df_control["Banco_Macro"] / df_control["Ventas_TR"] * 100).fillna(0)
    df_control["Estado"] = df_control["%_Conciliacion"].apply(
        lambda x: "✅ OK" if x >= 98 else ("⚠️ Parcial" if x >= 95 else "❌ Revisar")
    )
    df_control_proc = df_control

# --- 2. Payway ---
df_payway_proc = pd.DataFrame()
if not df_payway.empty and len(df_payway) > 1:
    # Verificar si la primera fila son encabezados o datos
    primera_fila = df_payway.iloc[0].astype(str).str.lower()
    if "fecha" in " ".join(primera_fila.values):
        df_payway.columns = df_payway.iloc[0]
        df_payway = df_payway[1:].reset_index(drop=True)
    
    # Buscar columna de fecha
    for col in df_payway.columns:
        if "fecha" in str(col).lower() or "date" in str(col).lower():
            df_payway["FECHA"] = pd.to_datetime(df_payway[col], errors='coerce')
            break
    
    if "FECHA" in df_payway.columns:
        df_payway = df_payway.dropna(subset=["FECHA"])
        
        # Buscar columnas de montos
        for col in df_payway.columns:
            col_lower = str(col).lower()
            if "bruto" in col_lower or "monto" in col_lower:
                if "bruto" in col_lower or "monto" in col_lower:
                    df_payway["MONTO_BRUTO"] = pd.to_numeric(df_payway[col], errors='coerce').fillna(0)
            if "neto" in col_lower:
                df_payway["MONTO_NETO"] = pd.to_numeric(df_payway[col], errors='coerce').fillna(0)
            if "costo" in col_lower or "comision" in col_lower or "servicio" in col_lower:
                df_payway["COMISION"] = pd.to_numeric(df_payway[col], errors='coerce').fillna(0)
        
        df_payway_proc = df_payway

# --- 3. Efectivo por Cajero ---
df_efectivo_proc = pd.DataFrame()
if not df_efectivo.empty and len(df_efectivo) > 1:
    df_efectivo.columns = df_efectivo.iloc[0]
    df_efectivo = df_efectivo[1:].reset_index(drop=True)
    df_efectivo = df_efectivo[~df_efectivo["ID CAJERO"].astype(str).str.contains("Total", na=False)]
    df_efectivo["MONTO"] = pd.to_numeric(df_efectivo["SUM of EFECTIVO RENDIDO"], errors='coerce').fillna(0)
    df_efectivo_proc = df_efectivo[["ID CAJERO", "MONTO"]].copy()

# --- 4. Tarjetas por Día ---
df_tarjetas_proc = pd.DataFrame()
if not df_tarjetas.empty and len(df_tarjetas) > 1:
    df_tarjetas.columns = df_tarjetas.iloc[0]
    df_tarjetas = df_tarjetas[1:].reset_index(drop=True)
    df_tarjetas = df_tarjetas[df_tarjetas["Columna 1"].astype(str).str.contains("2026-05", na=False)]
    df_tarjetas["FECHA"] = pd.to_datetime(df_tarjetas["Columna 1"], errors='coerce')
    df_tarjetas = df_tarjetas.dropna(subset=["FECHA"])
    df_tarjetas["MONTO"] = pd.to_numeric(df_tarjetas["SUM of TR"], errors='coerce').fillna(0)
    df_tarjetas_proc = df_tarjetas[["FECHA", "MONTO"]].copy()

# --- 5. Banco Macro ---
df_banco_proc = pd.DataFrame()
if not df_banco.empty and len(df_banco) > 1:
    df_banco.columns = df_banco.iloc[0]
    df_banco = df_banco[1:].reset_index(drop=True)
    df_banco["FECHA"] = pd.to_datetime(df_banco["Fecha"], errors='coerce')
    df_banco = df_banco.dropna(subset=["FECHA"])
    df_banco["IMPORTE"] = pd.to_numeric(df_banco["Importe"], errors='coerce').fillna(0)
    df_banco_proc = df_banco[["FECHA", "IMPORTE"]].copy()

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
total_ventas = df_control_proc["Ventas_TR"].sum() if not df_control_proc.empty else 0
total_banco = df_control_proc["Banco_Macro"].sum() if not df_control_proc.empty else 0
diferencia_total = total_ventas - total_banco
porcentaje_conciliacion = (total_banco / total_ventas * 100) if total_ventas > 0 else 0

st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Venta Total Tarjeta", f"")
with col2:
    st.metric("🏦 Depósito Banco Macro", f"")
with col3:
    st.metric("⚖️ Diferencia", f"")
with col4:
    st.metric("📈 % Conciliación", f"{porcentaje_conciliacion:.1f}%")

# ============================================
# PESTAÑAS
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Conciliación Diaria",
    "💳 Payway", 
    "👥 Efectivo por Cajero",
    "💵 Tarjetas por Día",
    "🏦 Banco Macro"
])

# TAB 1: Conciliación
with tab1:
    if not df_control_proc.empty:
        st.markdown("### 📈 Evolución Diaria")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_control_proc["FECHA"], y=df_control_proc["Ventas_TR"], 
                                mode="lines+markers", name="Ventas TR", line=dict(color="#3498db")))
        fig.add_trace(go.Scatter(x=df_control_proc["FECHA"], y=df_control_proc["Banco_Macro"], 
                                mode="lines+markers", name="Depósito Banco", line=dict(color="#2ecc71")))
        fig.update_layout(height=450, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📋 Tabla de Conciliación")
        mostrar = df_control_proc[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia", "%_Conciliacion", "Estado"]].copy()
        mostrar["FECHA"] = mostrar["FECHA"].dt.strftime("%d/%m/%Y")
        st.dataframe(mostrar, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de conciliación")

# TAB 2: Payway
with tab2:
    if not df_payway_proc.empty:
        st.markdown("### 💳 Resumen Payway")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Monto Bruto", f"" if "MONTO_BRUTO" in df_payway_proc.columns else "N/A")
        with col_p2:
            st.metric("Monto Neto", f"" if "MONTO_NETO" in df_payway_proc.columns else "N/A")
        with col_p3:
            comision = df_payway_proc['COMISION'].sum() if "COMISION" in df_payway_proc.columns else 0
            st.metric("Comisiones", f"")
        
        if "FECHA" in df_payway_proc.columns and "MONTO_BRUTO" in df_payway_proc.columns:
            st.markdown("### 📈 Evolución Diaria")
            diario = df_payway_proc.groupby("FECHA")["MONTO_BRUTO"].sum().reset_index()
            fig = px.line(diario, x="FECHA", y="MONTO_BRUTO", markers=True)
            fig.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de Payway")

# TAB 3: Efectivo
with tab3:
    if not df_efectivo_proc.empty:
        st.markdown("### 💵 Efectivo por Cajero")
        fig = px.bar(df_efectivo_proc, x="MONTO", y="ID CAJERO", orientation="h", text_auto=True)
        fig.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_efectivo_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de efectivo")

# TAB 4: Tarjetas
with tab4:
    if not df_tarjetas_proc.empty:
        st.markdown("### 💳 Ventas con Tarjeta por Día")
        fig = px.bar(df_tarjetas_proc, x="FECHA", y="MONTO", text_auto=True)
        fig.update_layout(height=450, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_tarjetas_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de tarjetas")

# TAB 5: Banco Macro
with tab5:
    if not df_banco_proc.empty:
        st.markdown("### 🏦 Movimientos Banco Macro")
        st.metric("Total Movimientos", f"")
        fig = px.line(df_banco_proc, x="FECHA", y="IMPORTE", markers=True)
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_banco_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos del banco")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        🏆 SUPER DASHBOARD | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
