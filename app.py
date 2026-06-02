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
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🏆 DASHBOARD DE VENTAS</h1>
        <p>Análisis y conciliación bancaria - Mayo 2026</p>
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

# --- Procesar Control (conciliación diaria) ---
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

# --- Procesar Banco Macro ---
df_banco = df_banco_raw.copy()
df_banco["FECHA"] = pd.to_datetime(df_banco["Fecha"], errors='coerce')
df_banco = df_banco.dropna(subset=["FECHA"])
df_banco["IMPORTE"] = pd.to_numeric(df_banco["SUM de Importe"], errors='coerce').fillna(0)

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_tarjetas = df_tarjetas["MONTO"].sum()
total_efectivo = df_efectivo["MONTO"].sum()
total_payway_bruto = df_payway["MONTO_BRUTO"].sum()
total_payway_comision = df_payway["COMISION"].sum()

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💳 Ventas con Tarjeta</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💵 Efectivo Rendido</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>💰 Payway Bruto</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"></div>
            <div>🔧 Comisiones Payway</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# GRÁFICOS
# ============================================

# GRÁFICO 1: Evolución de Ventas vs Depósitos
st.markdown('<div class="section-title">📈 EVOLUCIÓN DIARIA</div>', unsafe_allow_html=True)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Ventas_TR"], 
                         mode="lines+markers", name="Ventas TR", 
                         line=dict(color="#3498db", width=3), marker=dict(size=8)))
fig1.add_trace(go.Scatter(x=df_control["FECHA"], y=df_control["Banco_Macro"], 
                         mode="lines+markers", name="Depósito Banco Macro", 
                         line=dict(color="#2ecc71", width=3), marker=dict(size=8)))
fig1.update_layout(title="Ventas con Tarjeta vs Depósitos Bancarios",
                   xaxis_title="Fecha", yaxis_title="Monto ($)",
                   height=450, template="plotly_white", hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# GRÁFICO 2: Diferencia diaria de conciliación
st.markdown('<div class="section-title">⚖️ DIFERENCIA DIARIA</div>', unsafe_allow_html=True)

colors = ["#e74c3c" if x < 0 else "#2ecc71" for x in df_control["Diferencia"]]
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=df_control["FECHA"], y=df_control["Diferencia"], 
                      marker_color=colors, name="Diferencia"))
fig2.add_hline(y=0, line_dash="dash", line_color="black")
fig2.update_layout(title="Diferencia entre Ventas y Depósitos Bancarios",
                   xaxis_title="Fecha", yaxis_title="Diferencia ($)",
                   height=400, template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

# GRÁFICO 3: Top Cajeros por Efectivo
st.markdown('<div class="section-title">👥 TOP CAJEROS POR EFECTIVO</div>', unsafe_allow_html=True)

top_efectivo = df_efectivo.nlargest(10, "MONTO")
fig3 = px.bar(top_efectivo, x="MONTO", y="ID CAJERO", orientation="h", text_auto=True,
              title="Top 10 Cajeros - Monto de Efectivo Rendido",
              color="MONTO", color_continuous_scale="Viridis")
fig3.update_layout(height=450, template="plotly_white", xaxis_title="Monto ($)", yaxis_title="Cajero")
st.plotly_chart(fig3, use_container_width=True)

# GRÁFICO 4: Evolución Payway
st.markdown('<div class="section-title">💳 EVOLUCIÓN PAYWAY</div>', unsafe_allow_html=True)

payway_diario = df_payway.groupby("FECHA").agg({
    "MONTO_BRUTO": "sum",
    "MONTO_NETO": "sum"
}).reset_index()

fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=payway_diario["FECHA"], y=payway_diario["MONTO_BRUTO"], 
                         mode="lines+markers", name="Monto Bruto", line=dict(color="#3498db")))
fig4.add_trace(go.Scatter(x=payway_diario["FECHA"], y=payway_diario["MONTO_NETO"], 
                         mode="lines+markers", name="Monto Neto", line=dict(color="#2ecc71")))
fig4.update_layout(title="Evolución de Ventas Payway (Bruto vs Neto)",
                   xaxis_title="Fecha", yaxis_title="Monto ($)",
                   height=450, template="plotly_white")
st.plotly_chart(fig4, use_container_width=True)

# GRÁFICO 5: Distribución de Medios de Pago
st.markdown('<div class="section-title">🥧 DISTRIBUCIÓN DE PAGOS</div>', unsafe_allow_html=True)

col5a, col5b = st.columns(2)

with col5a:
    medios = pd.DataFrame({
        "Medio": ["Tarjeta", "Efectivo"],
        "Monto": [total_tarjetas, total_efectivo]
    })
    fig5 = px.pie(medios, values="Monto", names="Medio", hole=0.4,
                  title="Distribución Tarjeta vs Efectivo",
                  color_discrete_sequence=["#3498db", "#2ecc71"])
    fig5.update_traces(textinfo="percent+label")
    st.plotly_chart(fig5, use_container_width=True)

with col5b:
    # Evolución del ticket promedio
    ticket_promedio = df_control[df_control["Ventas_TR"] > 0].copy()
    ticket_promedio["Ticket_Promedio"] = ticket_promedio["Ventas_TR"] / 10  # Estimado
    fig6 = px.line(ticket_promedio, x="FECHA", y="Ticket_Promedio", markers=True,
                   title="Ticket Promedio Estimado por Día",
                   color_discrete_sequence=["#e74c3c"])
    fig6.update_layout(height=400, template="plotly_white", yaxis_title="Ticket Promedio ($)")
    st.plotly_chart(fig6, use_container_width=True)

# GRÁFICO 6: Tabla de conciliación con formato
st.markdown('<div class="section-title">📋 TABLA DE CONCILIACIÓN</div>', unsafe_allow_html=True)

tabla_conciliacion = df_control[["FECHA", "Ventas_TR", "Banco_Macro", "Diferencia", "%_Conciliacion"]].copy()
tabla_conciliacion["FECHA"] = tabla_conciliacion["FECHA"].dt.strftime("%d/%m/%Y")
tabla_conciliacion.columns = ["Fecha", "Ventas TR", "Depósito Banco", "Diferencia", "% Conciliación"]
tabla_conciliacion["Estado"] = tabla_conciliacion["% Conciliación"].apply(
    lambda x: "✅ OK" if x >= 98 else ("⚠️ Revisar" if x >= 95 else "❌ Alerta")
)

st.dataframe(tabla_conciliacion, use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard actualizado automáticamente | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
