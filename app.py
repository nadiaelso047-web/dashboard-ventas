import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# ============================================
# AUTENTICACIÓN - TODO EN SECRETS
# ============================================

def autenticar():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.set_page_config(page_title="Acceso Restringido", page_icon="🔐")
        
        st.markdown("""
            <style>
                .login-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 80vh;
                }
                .login-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }
                .login-card h1 {
                    color: white;
                    margin-bottom: 1rem;
                }
                .login-card p {
                    color: rgba(255,255,255,0.8);
                    margin-bottom: 2rem;
                }
            </style>
        """, unsafe_allow_html=True)
        
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
                    USUARIO_CORRECTO = st.secrets.get("USUARIO")
                    PASSWORD_CORRECTO = st.secrets.get("PASSWORD")
                    
                    if USUARIO_CORRECTO is None or PASSWORD_CORRECTO is None:
                        st.error("❌ Error de configuración. Contacte al administrador.")
                        return False
                    
                    if usuario == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
                        st.session_state.autenticado = True
                        st.session_state.intentos = 0
                        st.rerun()
                    else:
                        st.session_state.intentos += 1
                        restantes = 5 - st.session_state.intentos
                        st.error(f"❌ Usuario o contraseña incorrectos. Intentos restantes: {restantes}")
        return False
    return True

# Verificar autenticación
if not autenticar():
    st.stop()

# ============================================
# CONFIGURACIÓN DEL DASHBOARD
# ============================================
st.set_page_config(
    page_title="Dashboard Ventas",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
        /* Fondo general */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Tarjetas de métricas */
        .metric-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 35px rgba(0,0,0,0.15);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
        }
        
        /* Títulos */
        .section-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1.5rem 0 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #667eea;
        }
        
        /* Header principal */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
        }
        .main-header p {
            color: rgba(255,255,255,0.9);
            margin-top: 0.5rem;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: linear-gradient(180deg, #f5f7fa 0%, #e9ecef 100%);
        }
        
        /* Botones */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 2rem;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .stButton > button:hover {
            transform: scale(1.02);
        }
    </style>
""", unsafe_allow_html=True)

# ============================================
# HEADER PRINCIPAL
# ============================================
st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard de Ventas</h1>
        <p>Análisis completo de ventas - Datos actualizados en tiempo real</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# CARGAR DATOS
# ============================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg/export?format=csv&gid=1898188061"

@st.cache_data(ttl=300)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
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

with st.spinner("🔄 Cargando datos..."):
    df = cargar_datos()

# ============================================
# FILTROS (orden cronológico)
# ============================================
st.sidebar.markdown("## 🎛️ Panel de control")
st.sidebar.markdown("---")

# Ordenar meses cronológicamente
meses_ordenados = sorted(df["MES"].unique(), key=lambda x: datetime.strptime(x, "%B %Y"))
mes = st.sidebar.selectbox("📅 Mes", meses_ordenados)

cajeros = ["📊 Todos"] + sorted(df["CAJERO"].unique())
cajero = st.sidebar.selectbox("👤 Cajero", cajeros)

st.sidebar.markdown("---")
st.sidebar.info("💡 Los datos se actualizan automáticamente cada 5 minutos")
st.sidebar.markdown("---")
st.sidebar.caption(f"📌 Última carga: {datetime.now().strftime('%H:%M:%S')}")

# Aplicar filtros
filtro = df[df["MES"] == mes]
if cajero != "📊 Todos":
    filtro = filtro[filtro["CAJERO"] == cajero]

if filtro.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados")
    st.stop()

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================
st.markdown('<div class="section-title">📈 Indicadores Clave</div>', unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

venta_total = filtro["VENTA_TOTAL"].sum()
efectivo = filtro["EFECTIVO RENDIDO"].sum()
tarjeta = filtro["TARJETA CREDITO"].sum() + filtro["TARJETA DEBITO"].sum()
ticket_promedio = filtro["VENTA_TOTAL"].mean()

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${venta_total:,.2f}</div>
            <div class="metric-label">💰 Venta Total</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${efectivo:,.2f}</div>
            <div class="metric-label">💵 Efectivo</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${tarjeta:,.2f}</div>
            <div class="metric-label">💳 Tarjeta</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${ticket_promedio:,.2f}</div>
            <div class="metric-label">🎫 Ticket Promedio</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# GRÁFICOS PRINCIPALES
# ============================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("### 📈 Evolución Diaria")
    diario = filtro.groupby("DIA")["VENTA_TOTAL"].sum().reset_index()
    fig = px.line(diario, x="DIA", y="VENTA_TOTAL", markers=True)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Venta Total ($)",
        height=400,
        template="plotly_white",
        hovermode="x unified"
    )
    fig.update_traces(line=dict(width=3, color="#667eea"), marker=dict(size=8, color="#764ba2"))
    st.plotly_chart(fig, use_container_width=True)

with col_graf2:
    st.markdown("### 👥 Top 10 Cajeros")
    top = filtro.groupby("CAJERO")["VENTA_TOTAL"].sum().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(top, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True)
    fig.update_layout(
        xaxis_title="Venta Total ($)",
        yaxis_title="Cajero",
        height=400,
        template="plotly_white"
    )
    fig.update_traces(marker_color="#667eea", texttemplate='$%{value:,.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# GRÁFICOS ADICIONALES
# ============================================
st.markdown('<div class="section-title">📊 Análisis Adicionales</div>', unsafe_allow_html=True)
st.markdown("---")

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    st.markdown("### 🥧 Distribución por Medio de Pago")
    
    # Calcular medios de pago
    medios = pd.DataFrame({
        "Medio": ["Efectivo", "Tarjeta Crédito", "Tarjeta Débito"],
        "Monto": [
            filtro["EFECTIVO RENDIDO"].sum(),
            filtro["TARJETA CREDITO"].sum(),
            filtro["TARJETA DEBITO"].sum()
        ]
    })
    medios = medios[medios["Monto"] > 0]
    
    fig = px.pie(medios, values="Monto", names="Medio", hole=0.4)
    fig.update_layout(height=400, template="plotly_white")
    fig.update_traces(textposition="inside", textinfo="percent+label", marker_colors=["#2ecc71", "#3498db", "#1f77b4"])
    st.plotly_chart(fig, use_container_width=True)

with col_graf4:
    st.markdown("### 📊 Resumen por Cajero")
    resumen = filtro.groupby("CAJERO").agg({
        "VENTA_TOTAL": "sum",
        "EFECTIVO RENDIDO": "sum"
    }).head(10).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Venta Total", x=resumen["CAJERO"], y=resumen["VENTA_TOTAL"], marker_color="#667eea"))
    fig.add_trace(go.Bar(name="Efectivo", x=resumen["CAJERO"], y=resumen["EFECTIVO RENDIDO"], marker_color="#2ecc71"))
    fig.update_layout(
        barmode="group",
        xaxis_title="Cajero",
        yaxis_title="Monto ($)",
        height=400,
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# TABLA DE DATOS
# ============================================
st.markdown('<div class="section-title">📋 Detalle de Transacciones</div>', unsafe_allow_html=True)
st.markdown("---")

# Formatear la tabla
tabla = filtro[["FECHA", "CAJERO", "VENTA_TOTAL"]].head(50).copy()
tabla["VENTA_TOTAL"] = tabla["VENTA_TOTAL"].apply(lambda x: f"${x:,.2f}")
tabla["FECHA"] = tabla["FECHA"].dt.strftime("%d/%m/%Y")

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True,
    column_config={
        "FECHA": "Fecha",
        "CAJERO": "Cajero",
        "VENTA_TOTAL": "Monto"
    }
)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard actualizado automáticamente | 
        🕐 Última sincronización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} |
        📍 Datos en tiempo real desde Google Sheets
    </div>
""", unsafe_allow_html=True)
