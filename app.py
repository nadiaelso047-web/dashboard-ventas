import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(page_title="Super Dashboard Ventas", layout="wide")

# CSS Personalizado
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .metric-card {
            background: white;
            border-radius: 20px;
            padding: 1rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #667eea;
        }
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 20px;
            margin-bottom: 1.5rem;
            text-align: center;
            color: white;
        }
        .main-header h1 { color: white; margin: 0; font-size: 2rem; }
        .warning-card {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 0.8rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .success-card {
            background: #d4edda;
            border-left: 4px solid #28a745;
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
    "control": "1996710268",           # Control
    "payway": "821291737",              # Payway
    "payway_tr": "1397161452",          # Payway Tr
    "control_z": "1489363385",          # Control Z
    "control_efectivo": "1370399946",   # Control Efectivo
    "control_tarjetas": "2080576930",   # Control Tarjetas
    "banco_macro": "1780050919",        # Banco Macro
    "control_banco_macro": "772941566", # Control Banco Macro
}

@st.cache_data(ttl=300)
def cargar_hoja(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error cargando hoja {gid}: {e}")
        return pd.DataFrame()

def limpiar_numero(x):
    if pd.isna(x):
        return 0
    if isinstance(x, (int, float)):
        return float(x) if pd.notna(x) else 0
    try:
        s = str(x).replace(".", "").replace(",", ".")
        nums = re.findall(r"[\d\.]+", s)
        if nums:
            return float(nums[0])
        return 0
    except:
        return 0

# ============================================
# CARGA DE TODAS LAS HOJAS
# ============================================
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    df_control = cargar_hoja(SHEETS["control"])
    df_payway = cargar_hoja(SHEETS["payway_tr"])
    df_control_efectivo = cargar_hoja(SHEETS["control_efectivo"])
    df_control_tarjetas = cargar_hoja(SHEETS["control_tarjetas"])
    df_banco_macro = cargar_hoja(SHEETS["control_banco_macro"])

st.success("✅ Datos cargados correctamente")

# ============================================
# PROCESAMIENTO DE DATOS
# ============================================

# Procesar Control (conciliación diaria)
df_control_proc = df_control.copy()
df_control_proc = df_control_proc[df_control_proc["Columna 1"].astype(str).str.contains("2026-05", na=False)]
df_control_proc["FECHA"] = pd.to_datetime(df_control_proc["Columna 1"], errors='coerce')
df_control_proc = df_control_proc.dropna(subset=["FECHA"])
df_control_proc["Ventas_TR"] = pd.to_numeric(df_control_proc["SUM of TR"], errors='coerce').fillna(0)
df_control_proc["Payway_Bruto"] = pd.to_numeric(df_control_proc["Payway Bruto"], errors='coerce').fillna(0)
df_control_proc["Banco_Macro"] = pd.to_numeric(df_control_proc["Banco Macro"], errors='coerce').fillna(0)
df_control_proc["Diferencia"] = df_control_proc["Ventas_TR"] - df_control_proc["Banco_Macro"]
df_control_proc["%_Conciliacion"] = (df_control_proc["Banco_Macro"] / df_control_proc["Ventas_TR"] * 100).round(1)
df_control_proc["Estado"] = df_control_proc["%_Conciliacion"].apply(
    lambda x: "✅ OK" if x >= 98 else ("⚠️ Parcial" if x >= 95 else "❌ Revisar")
)

# Procesar Payway
df_payway_proc = df_payway.copy()
if not df_payway_proc.empty:
    df_payway_proc.columns = df_payway_proc.iloc[0]
    df_payway_proc = df_payway_proc[1:].reset_index(drop=True)
    df_payway_proc["FECHA"] = pd.to_datetime(df_payway_proc["FECHA DE VENTA"], errors='coerce')
    df_payway_proc = df_payway_proc.dropna(subset=["FECHA"])
    for col in ["SUM of MONTO BRUTO", "SUM of MONTO NETO", "SUM of TOTAL COSTO DE SERVICIO"]:
        if col in df_payway_proc.columns:
            df_payway_proc[col] = pd.to_numeric(df_payway_proc[col], errors='coerce').fillna(0)

# Procesar Control Tarjetas
df_tarjetas_proc = df_control_tarjetas.copy()
if not df_tarjetas_proc.empty:
    df_tarjetas_proc.columns = df_tarjetas_proc.iloc[0]
    df_tarjetas_proc = df_tarjetas_proc[1:].reset_index(drop=True)
    df_tarjetas_proc = df_tarjetas_proc[df_tarjetas_proc["Columna 1"].astype(str).str.contains("2026-05", na=False)]
    df_tarjetas_proc["FECHA"] = pd.to_datetime(df_tarjetas_proc["Columna 1"], errors='coerce')
    df_tarjetas_proc = df_tarjetas_proc.dropna(subset=["FECHA"])
    df_tarjetas_proc["SUM of TR"] = pd.to_numeric(df_tarjetas_proc["SUM of TR"], errors='coerce').fillna(0)

# Procesar Control Efectivo
df_efectivo_proc = df_control_efectivo.copy()
if not df_efectivo_proc.empty:
    df_efectivo_proc.columns = df_efectivo_proc.iloc[0]
    df_efectivo_proc = df_efectivo_proc[1:].reset_index(drop=True)
    df_efectivo_proc = df_efectivo_proc[~df_efectivo_proc["ID CAJERO"].astype(str).str.contains("Total", na=False)]
    df_efectivo_proc["SUM of EFECTIVO RENDIDO"] = pd.to_numeric(df_efectivo_proc["SUM of EFECTIVO RENDIDO"], errors='coerce').fillna(0)

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE DEL PERÍODO</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_ventas = df_control_proc["Ventas_TR"].sum()
total_banco = df_control_proc["Banco_Macro"].sum()
diferencia_total = total_ventas - total_banco
porcentaje_conciliacion = (total_banco / total_ventas * 100) if total_ventas > 0 else 0

with col1:
    st.metric("💰 Venta Total Tarjeta", f"")
with col2:
    st.metric("🏦 Depósito Banco Macro", f"")
with col3:
    st.metric("⚖️ Diferencia", f"", 
             delta=f"{diferencia_total/total_ventas*100:.1f}%" if total_ventas > 0 else None)
with col4:
    st.metric("📈 % Conciliación", f"{porcentaje_conciliacion:.1f}%")

# ============================================
# PESTAÑAS PRINCIPALES
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Conciliación Diaria",
    "💳 Análisis Payway", 
    "👥 Control Efectivo",
    "💵 Control Tarjetas",
    "🏦 Banco Macro",
    "📋 Reporte Ejecutivo"
])

# ==================== TAB 1: CONCILIACIÓN DIARIA ====================
with tab1:
    st.markdown("### 📈 Evolución Diaria de Ventas vs Depósitos")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_control_proc["FECHA"], y=df_control_proc["Ventas_TR"], 
                            mode="lines+markers", name="Ventas TR", line=dict(color="#3498db", width=3)))
    fig.add_trace(go.Scatter(x=df_control_proc["FECHA"], y=df_control_proc["Banco_Macro"], 
                            mode="lines+markers", name="Depósito Banco", line=dict(color="#2ecc71", width=3)))
    fig.update_layout(height=450, template="plotly_white", xaxis_title="Fecha", yaxis_title="Monto ($)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📊 Tabla de Conciliación Diaria")
    mostrar = df_control_proc[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia", "%_Conciliacion", "Estado"]].copy()
    mostrar["FECHA"] = mostrar["FECHA"].dt.strftime("%d/%m/%Y")
    mostrar.columns = ["Fecha", "Ventas TR", "Depósito Banco", "Diferencia", "%", "Estado"]
    st.dataframe(mostrar, use_container_width=True, hide_index=True)
    
    # Alertas
    dias_alerta = df_control_proc[df_control_proc["Estado"] != "✅ OK"]
    if not dias_alerta.empty:
        st.warning(f"⚠️ {len(dias_alerta)} días con diferencias en conciliación")
        for _, row in dias_alerta.iterrows():
            st.markdown(f'<div class="warning-card">📅 {row["FECHA"].strftime("%d/%m/%Y")} - Diferencia:  - {row["Estado"]}</div>', unsafe_allow_html=True)

# ==================== TAB 2: ANÁLISIS PAYWAY ====================
with tab2:
    if not df_payway_proc.empty:
        st.markdown("### 💳 Resumen Payway")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Monto Bruto", f"")
        with col_p2:
            st.metric("Monto Neto", f"")
        with col_p3:
            comisiones = df_payway_proc['SUM of TOTAL COSTO DE SERVICIO'].sum()
            st.metric("Comisiones", f"")
        
        st.markdown("### 📈 Evolución Diaria Payway")
        payway_diario = df_payway_proc.groupby("FECHA")["SUM of MONTO BRUTO"].sum().reset_index()
        fig = px.line(payway_diario, x="FECHA", y="SUM of MONTO BRUTO", markers=True)
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de Payway disponibles")

# ==================== TAB 3: CONTROL EFECTIVO ====================
with tab3:
    if not df_efectivo_proc.empty:
        st.markdown("### 💵 Efectivo Rendido por Cajero")
        fig = px.bar(df_efectivo_proc, x="SUM of EFECTIVO RENDIDO", y="ID CAJERO", 
                    orientation="h", text_auto=True, color="SUM of EFECTIVO RENDIDO",
                    color_continuous_scale="Viridis")
        fig.update_layout(height=500, template="plotly_white", xaxis_title="Monto Efectivo ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 Tabla de Efectivo por Cajero")
        st.dataframe(df_efectivo_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de efectivo disponibles")

# ==================== TAB 4: CONTROL TARJETAS ====================
with tab4:
    if not df_tarjetas_proc.empty:
        st.markdown("### 💳 Ventas con Tarjeta por Día")
        fig = px.bar(df_tarjetas_proc, x="FECHA", y="SUM of TR", text_auto=True,
                    color="SUM of TR", color_continuous_scale="Blues")
        fig.update_layout(height=450, template="plotly_white", xaxis_title="Fecha", yaxis_title="Monto ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📊 Tabla de Tarjetas por Día")
        mostrar_tarjetas = df_tarjetas_proc[["FECHA", "SUM of TR"]].copy()
        mostrar_tarjetas["FECHA"] = mostrar_tarjetas["FECHA"].dt.strftime("%d/%m/%Y")
        mostrar_tarjetas.columns = ["Fecha", "Monto Tarjetas"]
        st.dataframe(mostrar_tarjetas, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de tarjetas disponibles")

# ==================== TAB 5: BANCO MACRO ====================
with tab5:
    if not df_banco_macro.empty:
        st.markdown("### 🏦 Movimientos Banco Macro")
        df_banco = df_banco_macro.copy()
        df_banco.columns = df_banco.iloc[0]
        df_banco = df_banco[1:].reset_index(drop=True)
        df_banco["Fecha"] = pd.to_datetime(df_banco["Fecha"], errors='coerce')
        df_banco = df_banco.dropna(subset=["Fecha"])
        df_banco["Importe"] = pd.to_numeric(df_banco["Importe"], errors='coerce').fillna(0)
        
        st.metric("Total Movimientos", f"")
        
        fig = px.line(df_banco, x="Fecha", y="Importe", markers=True, title="Movimientos Bancarios")
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_banco, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos del banco disponibles")

# ==================== TAB 6: REPORTE EJECUTIVO ====================
with tab6:
    st.markdown("### 📋 REPORTE EJECUTIVO - MAYO 2026")
    
    st.markdown("#### ✅ Resumen General")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(f"""
        <div class="success-card">
            <strong>📊 INDICADORES PRINCIPALES</strong><br>
            • Total Ventas Tarjeta: <br>
            • Total Depositado: <br>
            • Diferencia Total: <br>
            • % Conciliación: {porcentaje_conciliacion:.1f}%
        </div>
        """, unsafe_allow_html=True)
    
    with col_r2:
        st.markdown(f"""
        <div class="success-card">
            <strong>🎯 ESTADÍSTICAS</strong><br>
            • Días analizados: {len(df_control_proc)}<br>
            • Días conciliados: {len(df_control_proc[df_control_proc['Estado'] == '✅ OK'])}<br>
            • Días con alerta: {len(df_control_proc[df_control_proc['Estado'] != '✅ OK'])}<br>
            • Mayor venta diaria: 
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("#### ⚠️ Alertas y Recomendaciones")
    
    if diferencia_total > 50000:
        st.markdown('<div class="danger-card">🔴 ALERTA CRÍTICA: Diferencia significativa en conciliación bancaria. Revisar depósitos pendientes.</div>', unsafe_allow_html=True)
    elif diferencia_total > 10000:
        st.markdown('<div class="warning-card">🟡 ATENCIÓN: Diferencia moderada en conciliación. Verificar comisiones y liquidaciones.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-card">✅ Conciliación dentro de parámetros normales.</div>', unsafe_allow_html=True)
    
    # Top 3 días con mayor diferencia
    st.markdown("#### 📅 Top 3 Días con Mayor Diferencia")
    top_diferencia = df_control_proc.nlargest(3, "Diferencia")[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia"]]
    top_diferencia["FECHA"] = top_diferencia["FECHA"].dt.strftime("%d/%m/%Y")
    st.dataframe(top_diferencia, use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        🏆 SUPER DASHBOARD | Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
