import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
# CONFIGURACIÓN
# ============================================
st.set_page_config(page_title="Dashboard Ventas", layout="wide")

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
        .metric-card {
            background: white;
            border-radius: 15px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #667eea;
        }
        .filter-box {
            background: white;
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🏆 DASHBOARD DE VENTAS</h1>
        <p>Análisis y conciliación bancaria - Datos actualizados</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# IDs DE LAS HOJAS
# ============================================
SHEET_ID = "1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg"

@st.cache_data(ttl=300)
def cargar_hoja(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        return pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

# ============================================
# CARGA Y PROCESAMIENTO
# ============================================
with st.spinner("🔄 Cargando datos..."):
    # Cargar todas las hojas
    df_control_raw = cargar_hoja("1996710268")
    df_payway_raw = cargar_hoja("1397161452")
    df_efectivo_raw = cargar_hoja("1370399946")
    df_tarjetas_raw = cargar_hoja("2080576930")
    df_banco_raw = cargar_hoja("772941566")
    df_ventas_raw = cargar_hoja("1898188061")  # Hoja de ventas detalladas

# --- Procesar Ventas (para filtros por cajero) ---
df_ventas = df_ventas_raw.copy()
df_ventas = df_ventas[~df_ventas["ID CAJERO"].astype(str).str.contains("SUBTOTALES", na=False)]
df_ventas = df_ventas.dropna(subset=["Columna 1"])
df_ventas["FECHA"] = pd.to_datetime(df_ventas["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_ventas = df_ventas.dropna(subset=["FECHA"])

# Limpiar montos
def limpiar_monto(x):
    if pd.isna(x):
        return 0
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).replace(".", "").replace(",", ".")
        nums = [float(n) for n in re.findall(r"[\d\.]+", s)]
        return nums[0] if nums else 0
    except:
        return 0

import re
for col in ["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO", "MONTO"]:
    if col in df_ventas.columns:
        df_ventas[col] = df_ventas[col].apply(limpiar_monto)

df_ventas["VENTA_TOTAL"] = df_ventas["EFECTIVO RENDIDO"] + df_ventas["TARJETA CREDITO"] + df_ventas["TARJETA DEBITO"]
df_ventas["CAJERO"] = df_ventas["ID CAJERO"].astype(str).str.split("-").str[1].fillna("Sin nombre")
df_ventas["AÑO"] = df_ventas["FECHA"].dt.year
df_ventas["MES"] = df_ventas["FECHA"].dt.month
df_ventas["MES_NOMBRE"] = df_ventas["FECHA"].dt.strftime("%B %Y")
df_ventas["DIA"] = df_ventas["FECHA"].dt.date

# --- Procesar Control (conciliación) ---
df_control = df_control_raw.copy()
df_control = df_control[df_control["Columna 1"].astype(str).str.contains("2026-05", na=False)]
df_control["FECHA"] = pd.to_datetime(df_control["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_control = df_control.dropna(subset=["FECHA"])
df_control["Ventas_TR"] = pd.to_numeric(df_control["SUM de TR"], errors='coerce').fillna(0)
df_control["Payway_Bruto"] = pd.to_numeric(df_control["Payway Bruto"], errors='coerce').fillna(0)
df_control["Banco_Macro"] = pd.to_numeric(df_control["Banco Macro"], errors='coerce').fillna(0)
df_control["Diferencia"] = df_control["Ventas_TR"] - df_control["Banco_Macro"]
df_control["%_Conciliacion"] = (df_control["Banco_Macro"] / df_control["Ventas_TR"] * 100).fillna(0).round(1)

# --- Procesar Payway ---
df_payway = df_payway_raw.copy()
df_payway["FECHA"] = pd.to_datetime(df_payway["FECHA DE VENTA"], errors='coerce')
df_payway = df_payway.dropna(subset=["FECHA"])
df_payway["MONTO_BRUTO"] = pd.to_numeric(df_payway["SUM de MONTO BRUTO"], errors='coerce').fillna(0)
df_payway["MONTO_NETO"] = pd.to_numeric(df_payway["SUM de MONTO NETO"], errors='coerce').fillna(0)
df_payway["COMISION"] = pd.to_numeric(df_payway["SUM de TOTAL COSTO DE SERVICIO"], errors='coerce').fillna(0)

# --- Procesar Efectivo ---
df_efectivo = df_efectivo_raw.copy()
df_efectivo = df_efectivo[~df_efectivo["ID CAJERO"].astype(str).str.contains("Total", na=False)]
df_efectivo["MONTO"] = pd.to_numeric(df_efectivo["SUM de EFECTIVO RENDIDO"], errors='coerce').fillna(0)

# --- Procesar Tarjetas ---
df_tarjetas = df_tarjetas_raw.copy()
df_tarjetas = df_tarjetas[df_tarjetas["Columna 1"].astype(str).str.contains("2026-05", na=False)]
df_tarjetas["FECHA"] = pd.to_datetime(df_tarjetas["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_tarjetas = df_tarjetas.dropna(subset=["FECHA"])
df_tarjetas["MONTO"] = pd.to_numeric(df_tarjetas["SUM de TR"], errors='coerce').fillna(0)

# ============================================
# FILTROS INTERACTIVOS
# ============================================
st.sidebar.markdown("## 🎛️ Filtros Interactivos")
st.sidebar.markdown("---")

# Años disponibles
años = sorted(df_ventas["AÑO"].unique(), reverse=True)
año_seleccionado = st.sidebar.selectbox("📅 Año", años)

# Filtrar por año
df_ventas_año = df_ventas[df_ventas["AÑO"] == año_seleccionado]

# Meses disponibles
meses_orden = df_ventas_año[["MES_NOMBRE", "MES"]].drop_duplicates().sort_values("MES")
meses_disponibles = meses_orden["MES_NOMBRE"].tolist()
mes_seleccionado = st.sidebar.selectbox("📅 Mes", meses_disponibles)

# Filtrar por mes
df_ventas_mes = df_ventas_año[df_ventas_año["MES_NOMBRE"] == mes_seleccionado]

# Cajeros disponibles
cajeros = ["📊 Todos"] + sorted(df_ventas_mes["CAJERO"].unique())
cajero_seleccionado = st.sidebar.selectbox("👤 Cajero", cajeros)

# Medio de pago
medios_pago = ["📊 Todos", "💰 Solo Efectivo", "💳 Solo Tarjeta"]
medio_seleccionado = st.sidebar.selectbox("💵 Medio de pago", medios_pago)

# Aplicar filtros
df_filtrado = df_ventas_mes.copy()

if cajero_seleccionado != "📊 Todos":
    df_filtrado = df_filtrado[df_filtrado["CAJERO"] == cajero_seleccionado]

if medio_seleccionado == "💰 Solo Efectivo":
    df_filtrado = df_filtrado[df_filtrado["EFECTIVO RENDIDO"] > 0]
elif medio_seleccionado == "💳 Solo Tarjeta":
    df_filtrado = df_filtrado[(df_filtrado["TARJETA CREDITO"] > 0) | (df_filtrado["TARJETA DEBITO"] > 0)]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 Datos filtrados: {len(df_filtrado)} transacciones")
st.sidebar.caption(f"🕐 Actualizado: {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE</div>', unsafe_allow_html=True)

total_ventas_filtradas = df_filtrado["VENTA_TOTAL"].sum()
total_efectivo_filtrado = df_filtrado["EFECTIVO RENDIDO"].sum()
total_tarjeta_filtrado = df_filtrado["TARJETA CREDITO"].sum() + df_filtrado["TARJETA DEBITO"].sum()
ticket_promedio = df_filtrado["VENTA_TOTAL"].mean() if len(df_filtrado) > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💰 Venta Total</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💵 Efectivo</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💳 Tarjeta</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>🎫 Ticket Promedio</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# GRÁFICOS PRINCIPALES
# ============================================

# GRÁFICO 1: Top Cajeros por Venta Total
st.markdown('<div class="section-title">👥 TOP CAJEROS POR VENTA TOTAL</div>', unsafe_allow_html=True)

top_cajeros = df_filtrado.groupby("CAJERO")["VENTA_TOTAL"].sum().sort_values(ascending=False).head(10).reset_index()
fig_top = px.bar(top_cajeros, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True,
                 title=f"Top 10 Cajeros - {mes_seleccionado}",
                 color="VENTA_TOTAL", color_continuous_scale="Viridis")
fig_top.update_layout(height=450, template="plotly_white", xaxis_title="Monto ($)", yaxis_title="Cajero")
st.plotly_chart(fig_top, use_container_width=True)

# GRÁFICO 2: Evolución Diaria por Cajero Seleccionado
st.markdown('<div class="section-title">📈 EVOLUCIÓN DIARIA DE VENTAS</div>', unsafe_allow_html=True)

ventas_diarias = df_filtrado.groupby("DIA")["VENTA_TOTAL"].sum().reset_index()
fig_diario = px.line(ventas_diarias, x="DIA", y="VENTA_TOTAL", markers=True,
                     title=f"Evolución Diaria - {cajero_seleccionado if cajero_seleccionado != '📊 Todos' else 'Todos los cajeros'}")
fig_diario.update_layout(height=450, template="plotly_white", xaxis_title="Fecha", yaxis_title="Venta Total ($)")
st.plotly_chart(fig_diario, use_container_width=True)

# GRÁFICO 3: Distribución por Medio de Pago
st.markdown('<div class="section-title">🥧 DISTRIBUCIÓN POR MEDIO DE PAGO</div>', unsafe_allow_html=True)

medios = pd.DataFrame({
    "Medio": ["Efectivo", "Tarjeta Crédito", "Tarjeta Débito"],
    "Monto": [
        df_filtrado["EFECTIVO RENDIDO"].sum(),
        df_filtrado["TARJETA CREDITO"].sum(),
        df_filtrado["TARJETA DEBITO"].sum()
    ]
})
medios = medios[medios["Monto"] > 0]
fig_pie = px.pie(medios, values="Monto", names="Medio", hole=0.4,
                 title=f"Distribución de Pagos - {mes_seleccionado}",
                 color_discrete_sequence=["#2ecc71", "#3498db", "#1f77b4"])
fig_pie.update_traces(textinfo="percent+label")
st.plotly_chart(fig_pie, use_container_width=True)

# GRÁFICO 4: Comparativa Efectivo vs Tarjeta por Día
st.markdown('<div class="section-title">📊 COMPARATIVA DIARIA: EFECTIVO vs TARJETA</div>', unsafe_allow_html=True)

diario_efectivo = df_filtrado.groupby("DIA")["EFECTIVO RENDIDO"].sum()
diario_tarjeta = df_filtrado.groupby("DIA")["TARJETA CREDITO"].sum() + df_filtrado.groupby("DIA")["TARJETA DEBITO"].sum()
df_comparativo = pd.DataFrame({
    "Fecha": diario_efectivo.index,
    "Efectivo": diario_efectivo.values,
    "Tarjeta": diario_tarjeta.values
})
fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(name="Efectivo", x=df_comparativo["Fecha"], y=df_comparativo["Efectivo"], marker_color="#2ecc71"))
fig_comp.add_trace(go.Bar(name="Tarjeta", x=df_comparativo["Fecha"], y=df_comparativo["Tarjeta"], marker_color="#3498db"))
fig_comp.update_layout(barmode="group", height=450, template="plotly_white",
                       title="Comparativa Diaria: Efectivo vs Tarjeta",
                       xaxis_title="Fecha", yaxis_title="Monto ($)")
st.plotly_chart(fig_comp, use_container_width=True)

# GRÁFICO 5: Ticket Promedio por Cajero
st.markdown('<div class="section-title">🎫 TICKET PROMEDIO POR CAJERO</div>', unsafe_allow_html=True)

ticket_cajero = df_filtrado.groupby("CAJERO")["VENTA_TOTAL"].mean().sort_values(ascending=False).head(10).reset_index()
fig_ticket = px.bar(ticket_cajero, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True,
                    title="Top 10 Cajeros por Ticket Promedio",
                    color="VENTA_TOTAL", color_continuous_scale="Oranges")
fig_ticket.update_layout(height=450, template="plotly_white", xaxis_title="Ticket Promedio ($)", yaxis_title="Cajero")
st.plotly_chart(fig_ticket, use_container_width=True)

# ============================================
# GRÁFICOS DE CONCILIACIÓN (sin filtros)
# ============================================
st.markdown('<div class="section-title">🏦 CONCILIACIÓN BANCARIA (Período completo)</div>', unsafe_allow_html=True)

# Gráfico de evolución ventas vs depósitos
fig_conc1 = go.Figure()
fig_conc1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Ventas_TR"], 
                               mode="lines+markers", name="Ventas TR", line=dict(color="#3498db", width=3)))
fig_conc1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Banco_Macro"], 
                               mode="lines+markers", name="Depósito Banco Macro", line=dict(color="#2ecc71", width=3)))
fig_conc1.update_layout(title="Evolución de Ventas vs Depósitos Bancarios",
                        xaxis_title="Fecha", yaxis_title="Monto ($)",
                        height=450, template="plotly_white")
st.plotly_chart(fig_conc1, use_container_width=True)

# Gráfico de diferencias
colores_diff = ["#e74c3c" if x < 0 else "#2ecc71" for x in df_control["Diferencia"]]
fig_conc2 = go.Figure()
fig_conc2.add_trace(go.Bar(x=df_control["FECHA"], y=df_control["Diferencia"], marker_color=colores_diff))
fig_conc2.add_hline(y=0, line_dash="dash", line_color="black")
fig_conc2.update_layout(title="Diferencia Diaria entre Ventas y Depósitos",
                        xaxis_title="Fecha", yaxis_title="Diferencia ($)",
                        height=400, template="plotly_white")
st.plotly_chart(fig_conc2, use_container_width=True)

# Tabla de conciliación
tabla_conciliacion = df_control[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia", "%_Conciliacion"]].copy()
tabla_conciliacion["FECHA"] = tabla_conciliacion["FECHA"].dt.strftime("%d/%m/%Y")
tabla_conciliacion.columns = ["Fecha", "Ventas TR", "Depósito Banco", "Diferencia", "% Conciliación"]
tabla_conciliacion["Estado"] = tabla_conciliacion["% Conciliación"].apply(
    lambda x: "✅ OK" if x >= 98 else ("⚠️ Revisar" if x >= 95 else "❌ Alerta")
)
st.dataframe(tabla_conciliacion, use_container_width=True, hide_index=True)

# ============================================
# TABLA DETALLADA
# ============================================
st.markdown('<div class="section-title">📋 DETALLE DE TRANSACCIONES</div>', unsafe_allow_html=True)

tabla_detalle = df_filtrado[["FECHA", "CAJERO", "EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO", "VENTA_TOTAL"]].head(50).copy()
tabla_detalle["FECHA"] = tabla_detalle["FECHA"].dt.strftime("%d/%m/%Y")
tabla_detalle.columns = ["Fecha", "Cajero", "Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "Total"]
st.dataframe(tabla_detalle, use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard actualizado automáticamente | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
