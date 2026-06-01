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

st.set_page_config(page_title="Dashboard Ventas", layout="wide")

# CSS
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
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard de Ventas</h1>
        <p>Análisis completo de ventas - Datos actualizados en tiempo real</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# CARGAR TODAS LAS HOJAS
# ============================================
SHEET_ID = "1IwcjGY4WhkkAABbyCdZmuOsdWrS99XAf7968rcV7GMg"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid="

# IDs de las hojas
SHEETS = {
    "ventas": "1898188061",  # INFORME CLOVER.V3
    "control": "0",           # Control (por confirmar)
    "payway_base": "1469634760",  # Payway Base Tr
    "payway_tr": "1392812585",     # Payway Tr
    "control_z": "513719905",      # Control Z
    "control_efectivo": "699126555", # Control Efectivo
    "control_tarjetas": "522240167", # Control Tarjetas
    "banco_macro": "946108344",      # Banco Macro
}

@st.cache_data(ttl=300)
def cargar_hoja(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# Cargar datos
with st.spinner("🔄 Cargando datos..."):
    df_ventas = cargar_hoja(SHEETS["ventas"])
    
    # Limpiar ventas
    df_ventas = df_ventas[~df_ventas["ID CAJERO"].astype(str).str.contains("SUBTOTALES", na=False)]
    df_ventas = df_ventas.dropna(subset=["Columna 1"])
    df_ventas["FECHA"] = pd.to_datetime(df_ventas["Columna 1"], format='%d/%m/%Y', errors='coerce')
    df_ventas = df_ventas.dropna(subset=["FECHA"])
    
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
    
    for col in ["EFECTIVO RENDIDO", "TARJETA CREDITO", "TARJETA DEBITO"]:
        if col in df_ventas.columns:
            df_ventas[col] = df_ventas[col].apply(limpiar_numero)
    
    df_ventas["VENTA_TOTAL"] = df_ventas["EFECTIVO RENDIDO"] + df_ventas["TARJETA CREDITO"] + df_ventas["TARJETA DEBITO"]
    df_ventas["CAJERO"] = df_ventas["ID CAJERO"].astype(str).str.split("-").str[1].fillna("Sin nombre")
    df_ventas["AÑO"] = df_ventas["FECHA"].dt.year
    df_ventas["MES"] = df_ventas["FECHA"].dt.month
    df_ventas["MES_NOMBRE"] = df_ventas["FECHA"].dt.strftime("%B %Y")
    df_ventas["MES_ORDEN"] = df_ventas["FECHA"].dt.year * 100 + df_ventas["FECHA"].dt.month
    df_ventas["DIA"] = df_ventas["FECHA"].dt.date
    df_ventas["DIA_SEMANA"] = df_ventas["FECHA"].dt.day_name()
    
    # Cargar otras hojas si existen
    df_payway = cargar_hoja(SHEETS["payway_tr"])
    df_control_efectivo = cargar_hoja(SHEETS["control_efectivo"])
    df_control_tarjetas = cargar_hoja(SHEETS["control_tarjetas"])

# ============================================
# FILTROS
# ============================================
st.sidebar.markdown("## 🎛️ Panel de control")

años = sorted(df_ventas["AÑO"].unique(), reverse=True)
año = st.sidebar.selectbox("📅 Año", años)

df_año = df_ventas[df_ventas["AÑO"] == año]

meses = df_año[["MES_NOMBRE", "MES_ORDEN"]].drop_duplicates().sort_values("MES_ORDEN")["MES_NOMBRE"].tolist()
mes = st.sidebar.selectbox("📅 Mes", meses)

filtro = df_año[df_año["MES_NOMBRE"] == mes]

if filtro.empty:
    st.error(f"No hay datos para {mes}")
    st.stop()

cajeros = ["📊 Todos"] + sorted(filtro["CAJERO"].unique())
cajero = st.sidebar.selectbox("👤 Cajero", cajeros)

if cajero != "📊 Todos":
    filtro = filtro[filtro["CAJERO"] == cajero]

st.sidebar.markdown("---")
st.sidebar.info(f"💡 Datos de {mes}")
st.sidebar.caption(f"Última carga: {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# PESTAÑAS
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Ventas Diarias", 
    "💰 Medios de Pago", 
    "👥 Rendimiento Cajeros",
    "💳 Tarjetas (Payway)",
    "🏦 Conciliación Bancaria"
])

# ==================== TAB 1: VENTAS DIARIAS ====================
with tab1:
    st.markdown("### 📈 Evolución de Ventas")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Venta Total", f"")
    with col2:
        st.metric("💵 Efectivo", f"")
    with col3:
        st.metric("💳 Tarjeta", f"")
    with col4:
        st.metric("🎫 Ticket Promedio", f"")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("#### Evolución Diaria")
        diario = filtro.groupby("DIA")["VENTA_TOTAL"].sum().reset_index()
        fig = px.line(diario, x="DIA", y="VENTA_TOTAL", markers=True)
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("#### Evolución por Medio de Pago")
        diario_efectivo = filtro.groupby("DIA")["EFECTIVO RENDIDO"].sum()
        diario_tarjeta = filtro.groupby("DIA")["TARJETA CREDITO"].sum() + filtro.groupby("DIA")["TARJETA DEBITO"].sum()
        df_comp = pd.DataFrame({"Fecha": diario_efectivo.index, "Efectivo": diario_efectivo.values, "Tarjeta": diario_tarjeta.values})
        fig = px.line(df_comp, x="Fecha", y=["Efectivo", "Tarjeta"], markers=True)
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Distribución por Día de la Semana")
    dias_orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    semana = filtro.groupby("DIA_SEMANA")["VENTA_TOTAL"].sum().reindex(dias_orden).reset_index()
    semana.columns = ["Día", "Venta Total"]
    fig = px.bar(semana, x="Día", y="Venta Total", text_auto=True)
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 2: MEDIOS DE PAGO ====================
with tab2:
    st.markdown("### 💰 Análisis de Medios de Pago")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("#### Distribución por Medio de Pago")
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
        fig.update_layout(height=450, template="plotly_white")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_m2:
        st.markdown("#### Evolución del Ticket Promedio")
        ticket_diario = filtro.groupby("DIA")["VENTA_TOTAL"].mean().reset_index()
        fig = px.line(ticket_diario, x="DIA", y="VENTA_TOTAL", markers=True)
        fig.update_layout(height=450, template="plotly_white", yaxis_title="Ticket Promedio ($)")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Comparativa Efectivo vs Tarjeta por Día")
    comp_diario = filtro.groupby("DIA").agg({
        "EFECTIVO RENDIDO": "sum",
        "TARJETA CREDITO": "sum",
        "TARJETA DEBITO": "sum"
    }).reset_index()
    comp_diario["Tarjeta Total"] = comp_diario["TARJETA CREDITO"] + comp_diario["TARJETA DEBITO"]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Efectivo", x=comp_diario["DIA"], y=comp_diario["EFECTIVO RENDIDO"], marker_color="#2ecc71"))
    fig.add_trace(go.Bar(name="Tarjeta", x=comp_diario["DIA"], y=comp_diario["Tarjeta Total"], marker_color="#3498db"))
    fig.update_layout(barmode="group", height=450, template="plotly_white", xaxis_title="Fecha", yaxis_title="Monto ($)")
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 3: RENDIMIENTO CAJEROS ====================
with tab3:
    st.markdown("### 👥 Análisis por Cajero")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("#### Top 10 Venta Total")
        top_venta = filtro.groupby("CAJERO")["VENTA_TOTAL"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_venta, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True)
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col_c2:
        st.markdown("#### Top 10 Ticket Promedio")
        top_ticket = filtro.groupby("CAJERO")["VENTA_TOTAL"].mean().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_ticket, x="VENTA_TOTAL", y="CAJERO", orientation="h", text_auto=True)
        fig.update_layout(height=400, template="plotly_white", xaxis_title="Ticket Promedio ($)")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Resumen Detallado por Cajero")
    resumen = filtro.groupby("CAJERO").agg({
        "VENTA_TOTAL": ["sum", "mean", "count"],
        "EFECTIVO RENDIDO": "sum",
        "TARJETA CREDITO": "sum",
        "TARJETA DEBITO": "sum"
    }).round(2)
    resumen.columns = ["Venta Total", "Ticket Promedio", "Transacciones", "Efectivo", "Tarjeta Crédito", "Tarjeta Débito"]
    resumen = resumen.sort_values("Venta Total", ascending=False)
    resumen["% del Total"] = (resumen["Venta Total"] / resumen["Venta Total"].sum() * 100).round(1)
    
    for col in ["Venta Total", "Ticket Promedio", "Efectivo", "Tarjeta Crédito", "Tarjeta Débito"]:
        resumen[col] = resumen[col].apply(lambda x: f"")
    
    st.dataframe(resumen, use_container_width=True)

# ==================== TAB 4: TARJETAS (PAYWAY) ====================
with tab4:
    st.markdown("### 💳 Análisis de Transacciones con Tarjeta (Payway)")
    
    if not df_payway.empty:
        # Limpiar datos de Payway
        df_payway.columns = df_payway.iloc[0]
        df_payway = df_payway[1:].copy()
        df_payway["FECHA_VENTA"] = pd.to_datetime(df_payway["FECHA DE VENTA"], errors='coerce')
        df_payway = df_payway.dropna(subset=["FECHA_VENTA"])
        
        for col in ["SUM of MONTO BRUTO", "SUM of MONTO NETO", "SUM of TOTAL COSTO DE SERVICIO"]:
            if col in df_payway.columns:
                df_payway[col] = pd.to_numeric(df_payway[col], errors='coerce').fillna(0)
        
        df_payway["AÑO"] = df_payway["FECHA_VENTA"].dt.year
        df_payway["MES"] = df_payway["FECHA_VENTA"].dt.month
        
        payway_filtro = df_payway[df_payway["AÑO"] == año]
        if not payway_filtro.empty:
            payway_meses = payway_filtro.groupby("MES")["SUM of MONTO BRUTO"].sum()
            
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("💰 Monto Bruto Total", f"")
            with col_p2:
                st.metric("📊 Monto Neto Total", f"")
            with col_p3:
                st.metric("🔧 Costo de Servicio", f"")
            
            st.markdown("#### Evolución Mensual Payway")
            fig = px.bar(x=payway_meses.index, y=payway_meses.values, text_auto=True)
            fig.update_layout(xaxis_title="Mes", yaxis_title="Monto Bruto ($)", height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de Payway para el período seleccionado")
    else:
        st.info("No se pudieron cargar los datos de Payway")

# ==================== TAB 5: CONCILIACIÓN BANCARIA ====================
with tab5:
    st.markdown("### 🏦 Control de Depósitos - Banco Macro")
    
    if not df_control_efectivo.empty:
        st.markdown("#### Resumen de Efectivo por Cajero")
        df_control_efectivo.columns = df_control_efectivo.iloc[0]
        df_control_efectivo = df_control_efectivo[1:].copy()
        
        if "ID CAJERO" in df_control_efectivo.columns and "SUM of EFECTIVO RENDIDO" in df_control_efectivo.columns:
            df_efectivo = df_control_efectivo[["ID CAJERO", "SUM of EFECTIVO RENDIDO"]].dropna()
            df_efectivo = df_efectivo[df_efectivo["ID CAJERO"] != "Total general"]
            fig = px.bar(df_efectivo, x="SUM of EFECTIVO RENDIDO", y="ID CAJERO", orientation="h", text_auto=True)
            fig.update_layout(height=400, template="plotly_white", xaxis_title="Monto Efectivo ($)")
            st.plotly_chart(fig, use_container_width=True)
    
    if not df_control_tarjetas.empty:
        st.markdown("#### Resumen de Tarjetas por Día")
        df_control_tarjetas.columns = df_control_tarjetas.iloc[0]
        df_control_tarjetas = df_control_tarjetas[1:].copy()
        
        if "Columna 1" in df_control_tarjetas.columns and "SUM of TR" in df_control_tarjetas.columns:
            df_tarjetas = df_control_tarjetas[["Columna 1", "SUM of TR"]].dropna()
            df_tarjetas["Columna 1"] = pd.to_datetime(df_tarjetas["Columna 1"], errors='coerce')
            df_tarjetas = df_tarjetas.dropna()
            df_tarjetas = df_tarjetas[df_tarjetas["Columna 1"].dt.year == año]
            
            if not df_tarjetas.empty:
                fig = px.line(df_tarjetas, x="Columna 1", y="SUM of TR", markers=True)
                fig.update_layout(height=400, template="plotly_white", xaxis_title="Fecha", yaxis_title="Monto Tarjetas ($)")
                st.plotly_chart(fig, use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard actualizado automáticamente |
        🕐 Última sincronización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
