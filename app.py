import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

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
            font-size: 1.8rem;
            font-weight: bold;
            color: #667eea;
        }
        .section-title {
            font-size: 1.3rem;
            font-weight: bold;
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #667eea;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🏆 DASHBOARD DE VENTAS</h1>
        <p>Análisis de ventas | Conciliación bancaria | Control de gestión</p>
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
# CARGA DE TODAS LAS HOJAS
# ============================================
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    # Hoja de ventas (para filtros por cajero)
    df_ventas_raw = cargar_hoja("1898188061")
    
    # Hojas de conciliación y tarjetas
    df_control_raw = cargar_hoja("1996710268")
    df_payway_raw = cargar_hoja("1397161452")
    df_efectivo_raw = cargar_hoja("1370399946")
    df_tarjetas_raw = cargar_hoja("2080576930")
    df_banco_raw = cargar_hoja("772941566")

st.success("✅ Datos cargados correctamente")

# ============================================
# PROCESAMIENTO DE VENTAS (para filtros)
# ============================================

def limpiar_monto(x):
    if pd.isna(x):
        return 0
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).replace(".", "").replace(",", ".")
        nums = re.findall(r"[\d\.]+", s)
        return float(nums[0]) if nums else 0
    except:
        return 0

df_ventas = df_ventas_raw.copy()
df_ventas = df_ventas[~df_ventas["ID CAJERO"].astype(str).str.contains("SUBTOTALES", na=False)]
df_ventas = df_ventas.dropna(subset=["Columna 1"])
df_ventas["FECHA"] = pd.to_datetime(df_ventas["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_ventas = df_ventas.dropna(subset=["FECHA"])

for col in ["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO"]:
    if col in df_ventas.columns:
        df_ventas[col] = df_ventas[col].apply(limpiar_monto)

df_ventas["VENTA_TOTAL"] = df_ventas["EFECTIVO RENDIDO"] + df_ventas["TARJETA CREDITO"] + df_ventas["TARJETA DEBITO"]
df_ventas["CAJERO"] = df_ventas["ID CAJERO"].astype(str).str.split("-").str[1].fillna("Sin nombre")
df_ventas["AÑO"] = df_ventas["FECHA"].dt.year
df_ventas["MES"] = df_ventas["FECHA"].dt.month
df_ventas["MES_NOMBRE"] = df_ventas["FECHA"].dt.strftime("%B %Y")
df_ventas["DIA"] = df_ventas["FECHA"].dt.date

# ============================================
# PROCESAMIENTO DE CONCILIACIÓN Y TARJETAS
# ============================================

# Control (conciliación)
df_control = df_control_raw.copy()
df_control = df_control[df_control["Columna 1"].astype(str).str.contains("2026-05", na=False)]
df_control["FECHA"] = pd.to_datetime(df_control["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_control = df_control.dropna(subset=["FECHA"])
df_control["Ventas_TR"] = pd.to_numeric(df_control["SUM de TR"], errors='coerce').fillna(0)
df_control["Payway_Bruto"] = pd.to_numeric(df_control["Payway Bruto"], errors='coerce').fillna(0)
df_control["Banco_Macro"] = pd.to_numeric(df_control["Banco Macro"], errors='coerce').fillna(0)
df_control["Diferencia"] = df_control["Ventas_TR"] - df_control["Banco_Macro"]
df_control["%_Conciliacion"] = (df_control["Banco_Macro"] / df_control["Ventas_TR"] * 100).fillna(0).round(1)

# Payway
df_payway = df_payway_raw.copy()
df_payway["FECHA"] = pd.to_datetime(df_payway["FECHA DE VENTA"], errors='coerce')
df_payway = df_payway.dropna(subset=["FECHA"])
df_payway["MONTO_BRUTO"] = pd.to_numeric(df_payway["SUM de MONTO BRUTO"], errors='coerce').fillna(0)
df_payway["MONTO_NETO"] = pd.to_numeric(df_payway["SUM de MONTO NETO"], errors='coerce').fillna(0)
df_payway["COMISION"] = pd.to_numeric(df_payway["SUM de TOTAL COSTO DE SERVICIO"], errors='coerce').fillna(0)

# Efectivo por Cajero
df_efectivo = df_efectivo_raw.copy()
df_efectivo = df_efectivo[~df_efectivo["ID CAJERO"].astype(str).str.contains("Total", na=False)]
df_efectivo["MONTO"] = pd.to_numeric(df_efectivo["SUM de EFECTIVO RENDIDO"], errors='coerce').fillna(0)

# Tarjetas por día
df_tarjetas = df_tarjetas_raw.copy()
df_tarjetas = df_tarjetas[df_tarjetas["Columna 1"].astype(str).str.contains("2026-05", na=False)]
df_tarjetas["FECHA"] = pd.to_datetime(df_tarjetas["Columna 1"], format='%d/%m/%Y', errors='coerce')
df_tarjetas = df_tarjetas.dropna(subset=["FECHA"])
df_tarjetas["MONTO"] = pd.to_numeric(df_tarjetas["SUM de TR"], errors='coerce').fillna(0)

# Banco Macro
df_banco = df_banco_raw.copy()
df_banco["FECHA"] = pd.to_datetime(df_banco["Fecha"], errors='coerce')
df_banco = df_banco.dropna(subset=["FECHA"])
df_banco["IMPORTE"] = pd.to_numeric(df_banco["SUM de Importe"], errors='coerce').fillna(0)

# ============================================
# FILTROS INTERACTIVOS (SIDEBAR)
# ============================================
st.sidebar.markdown("## 🎛️ Filtros de Ventas")
st.sidebar.markdown("---")

años = sorted(df_ventas["AÑO"].unique(), reverse=True)
año_sel = st.sidebar.selectbox("📅 Año", años)

df_ventas_año = df_ventas[df_ventas["AÑO"] == año_sel]
meses_disp = df_ventas_año[["MES_NOMBRE", "MES"]].drop_duplicates().sort_values("MES")["MES_NOMBRE"].tolist()
mes_sel = st.sidebar.selectbox("📅 Mes", meses_disp)

df_ventas_mes = df_ventas_año[df_ventas_año["MES_NOMBRE"] == mes_sel]
cajeros_disp = ["📊 Todos"] + sorted(df_ventas_mes["CAJERO"].unique())
cajero_sel = st.sidebar.selectbox("👤 Cajero", cajeros_disp)

medios_opciones = ["📊 Todos", "💰 Solo Efectivo", "💳 Solo Tarjeta"]
medio_sel = st.sidebar.selectbox("💵 Medio de pago", medios_opciones)

# Aplicar filtros
df_filtrado = df_ventas_mes.copy()
if cajero_sel != "📊 Todos":
    df_filtrado = df_filtrado[df_filtrado["CAJERO"] == cajero_sel]
if medio_sel == "💰 Solo Efectivo":
    df_filtrado = df_filtrado[df_filtrado["EFECTIVO RENDIDO"] > 0]
elif medio_sel == "💳 Solo Tarjeta":
    df_filtrado = df_filtrado[(df_filtrado["TARJETA CREDITO"] > 0) | (df_filtrado["TARJETA DEBITO"] > 0)]

st.sidebar.markdown("---")
st.sidebar.info(f"📊 {len(df_filtrado)} transacciones")
st.sidebar.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# MÉTRICAS CLAVE
# ============================================
st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

total_ventas = df_filtrado["VENTA_TOTAL"].sum()
total_efectivo = df_filtrado["EFECTIVO RENDIDO"].sum()
total_tarjeta = df_filtrado["TARJETA CREDITO"].sum() + df_filtrado["TARJETA DEBITO"].sum()
ticket_prom = df_filtrado["VENTA_TOTAL"].mean() if len(df_filtrado) > 0 else 0
total_transacciones = len(df_filtrado)

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value"></div><div>💰 Venta Total</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value"></div><div>💵 Efectivo</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value"></div><div>💳 Tarjeta</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-value"></div><div>🎫 Ticket Promedio</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{total_transacciones}</div><div>📄 Transacciones</div></div>', unsafe_allow_html=True)

# ============================================
# GRÁFICOS DE VENTAS (con filtros)
# ============================================
st.markdown('<div class="section-title">📈 ANÁLISIS DE VENTAS</div>', unsafe_allow_html=True)

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Top Cajeros
    top_cajeros = df_filtrado.groupby("CAJERO")["VENTA_TOTAL"].sum().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(top_cajeros, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True,
                 title="Top 10 Cajeros por Venta Total", color="VENTA_TOTAL", color_continuous_scale="Viridis")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with col_graf2:
    # Evolución diaria
    diario = df_filtrado.groupby("DIA")["VENTA_TOTAL"].sum().reset_index()
    fig = px.line(diario, x="DIA", y="VENTA_TOTAL", markers=True, title="Evolución Diaria de Ventas")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    # Distribución por medio de pago
    medios = pd.DataFrame({
        "Medio": ["Efectivo", "Tarjeta Crédito", "Tarjeta Débito"],
        "Monto": [df_filtrado["EFECTIVO RENDIDO"].sum(), df_filtrado["TARJETA CREDITO"].sum(), df_filtrado["TARJETA DEBITO"].sum()]
    })
    medios = medios[medios["Monto"] > 0]
    fig = px.pie(medios, values="Monto", names="Medio", hole=0.4, title="Distribución por Medio de Pago")
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with col_graf4:
    # Ticket promedio por cajero
    ticket_cajero = df_filtrado.groupby("CAJERO")["VENTA_TOTAL"].mean().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(ticket_cajero, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True,
                 title="Top 10 Ticket Promedio por Cajero", color="VENTA_TOTAL", color_continuous_scale="Oranges")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# CONCILIACIÓN BANCARIA (TODAS LAS HOJAS)
# ============================================
st.markdown('<div class="section-title">🏦 CONCILIACIÓN BANCARIA</div>', unsafe_allow_html=True)

# Métricas de conciliación
total_ventas_tr = df_control["Ventas_TR"].sum()
total_banco_macro = df_control["Banco_Macro"].sum()
diferencia_total = total_ventas_tr - total_banco_macro
porc_conciliacion = (total_banco_macro / total_ventas_tr * 100) if total_ventas_tr > 0 else 0

col_c1, col_c2, col_c3, col_c4 = st.columns(4)
with col_c1:
    st.metric("💳 Total Ventas TR", f"")
with col_c2:
    st.metric("🏦 Total Depósito Banco", f"")
with col_c3:
    st.metric("⚖️ Diferencia Total", f"")
with col_c4:
    st.metric("📈 % Conciliación", f"{porc_conciliacion:.1f}%")

# Gráfico de evolución
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Ventas_TR"], mode="lines+markers", name="Ventas TR", line=dict(color="#3498db", width=3)))
fig1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Banco_Macro"], mode="lines+markers", name="Depósito Banco Macro", line=dict(color="#2ecc71", width=3)))
fig1.update_layout(title="Evolución de Ventas vs Depósitos Bancarios", height=450, template="plotly_white", xaxis_title="Fecha", yaxis_title="Monto ($)")
st.plotly_chart(fig1, use_container_width=True)

# Gráfico de diferencias
colores_diff = ["#e74c3c" if x < 0 else "#2ecc71" for x in df_control["Diferencia"]]
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=df_control["FECHA"], y=df_control["Diferencia"], marker_color=colores_diff))
fig2.add_hline(y=0, line_dash="dash", line_color="black")
fig2.update_layout(title="Diferencia Diaria", height=400, template="plotly_white", xaxis_title="Fecha", yaxis_title="Diferencia ($)")
st.plotly_chart(fig2, use_container_width=True)

# Tabla de conciliación
tabla_conc = df_control[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia", "%_Conciliacion"]].copy()
tabla_conc["FECHA"] = tabla_conc["FECHA"].dt.strftime("%d/%m/%Y")
tabla_conc.columns = ["Fecha", "Ventas TR", "Depósito Banco", "Diferencia", "% Conciliación"]
tabla_conc["Estado"] = tabla_conc["% Conciliación"].apply(lambda x: "✅ OK" if x >= 98 else ("⚠️ Revisar" if x >= 95 else "❌ Alerta"))
st.dataframe(tabla_conc, use_container_width=True, hide_index=True)

# ============================================
# ANÁLISIS DE TARJETAS (PAYWAY)
# ============================================
st.markdown('<div class="section-title">💳 ANÁLISIS DE TARJETAS (PAYWAY)</div>', unsafe_allow_html=True)

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.metric("💰 Monto Bruto", f"")
with col_p2:
    st.metric("📊 Monto Neto", f"")
with col_p3:
    st.metric("🔧 Comisiones", f"")

payway_diario = df_payway.groupby("FECHA")["MONTO_BRUTO"].sum().reset_index()
fig = px.line(payway_diario, x="FECHA", y="MONTO_BRUTO", markers=True, title="Evolución Diaria Payway")
fig.update_layout(height=400, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# ============================================
# EFECTIVO Y TARJETAS POR DÍA
# ============================================
st.markdown('<div class="section-title">💵 CONTROL DE EFECTIVO Y TARJETAS</div>', unsafe_allow_html=True)

col_e1, col_e2 = st.columns(2)

with col_e1:
    st.markdown("#### Efectivo por Cajero")
    fig = px.bar(df_efectivo, x="MONTO", y="ID CAJERO", orientation="h", text_auto=True, title="Efectivo Rendido por Cajero")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with col_e2:
    st.markdown("#### Tarjetas por Día")
    fig = px.bar(df_tarjetas, x="FECHA", y="MONTO", text_auto=True, title="Ventas con Tarjeta por Día")
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# BANCO MACRO
# ============================================
st.markdown('<div class="section-title">🏦 MOVIMIENTOS BANCO MACRO</div>', unsafe_allow_html=True)

st.metric("Total Movimientos", f"")
fig = px.line(df_banco, x="FECHA", y="IMPORTE", markers=True, title="Movimientos Bancarios")
fig.update_layout(height=400, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df_banco, use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard completo | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
