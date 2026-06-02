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
        .success-card {
            background: #d4edda;
            border-left: 4px solid #28a745;
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
        <h1>🏆 DASHBOARD DE VENTAS</h1>
        <p>Análisis y conciliación bancaria</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# IDs DE LAS HOJAS
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
with st.spinner("🔄 Cargando datos..."):
    df_raw_control = cargar_hoja(SHEETS["control"])
    df_raw_payway = cargar_hoja(SHEETS["payway_tr"])
    df_raw_efectivo = cargar_hoja(SHEETS["control_efectivo"])
    df_raw_tarjetas = cargar_hoja(SHEETS["control_tarjetas"])
    df_raw_banco = cargar_hoja(SHEETS["control_banco_macro"])

# ============================================
# FUNCIÓN PARA MOSTRAR INFO DE CADA HOJA
# ============================================

def mostrar_info_hoja(df, nombre):
    """Muestra información de una hoja para depuración"""
    if df.empty:
        st.warning(f"⚠️ Hoja '{nombre}' está vacía")
        return None
    else:
        with st.expander(f"📄 Ver estructura de '{nombre}'"):
            st.write(f"**Filas:** {len(df)}")
            st.write(f"**Columnas:** {list(df.columns)}")
            st.dataframe(df.head(3), use_container_width=True)
        return df

st.markdown('<div class="section-title">📋 ESTRUCTURA DE DATOS</div>', unsafe_allow_html=True)

# Mostrar estructura de cada hoja (solo para depuración)
df_control = mostrar_info_hoja(df_raw_control, "Control")
df_payway = mostrar_info_hoja(df_raw_payway, "Payway Tr")
df_efectivo = mostrar_info_hoja(df_raw_efectivo, "Control Efectivo")
df_tarjetas = mostrar_info_hoja(df_raw_tarjetas, "Control Tarjetas")
df_banco = mostrar_info_hoja(df_raw_banco, "Control Banco Macro")

# ============================================
# PROCESAMIENTO DE CADA HOJA
# ============================================

# --- 1. Control (Conciliación) ---
control_proc = pd.DataFrame()
if df_control is not None and len(df_control) > 2:
    # La primera fila suele ser encabezados en Google Sheets exportado
    # Buscamos la fila que contiene "SUBTOTALES" o fechas
    for idx, row in df_control.iterrows():
        row_str = " ".join(row.astype(str))
        if "SUBTOTALES" in row_str or "2026-05" in row_str:
            if idx > 0:
                # Usar fila anterior como encabezados
                df_control.columns = df_control.iloc[idx-1]
                df_control = df_control[idx:].reset_index(drop=True)
            break
    
    # Buscar columna de fechas
    col_fecha = None
    for col in df_control.columns:
        if "fecha" in str(col).lower() or "columna" in str(col).lower() or df_control[col].astype(str).str.contains("2026-05").any():
            col_fecha = col
            break
    
    if col_fecha:
        df_control["FECHA"] = pd.to_datetime(df_control[col_fecha], errors='coerce')
        df_control = df_control.dropna(subset=["FECHA"])
        
        # Buscar columnas numéricas (posibles montos)
        for col in df_control.columns:
            if col != col_fecha:
                df_control[col] = pd.to_numeric(df_control[col], errors='coerce').fillna(0)
        
        control_proc = df_control
        st.success(f"✅ Control: {len(control_proc)} filas procesadas")

# --- 2. Payway ---
payway_proc = pd.DataFrame()
if df_payway is not None and len(df_payway) > 2:
    # Buscar fila de encabezados
    for idx, row in df_payway.iterrows():
        row_str = " ".join(row.astype(str))
        if "FECHA" in row_str or "MONTO" in row_str:
            df_payway.columns = df_payway.iloc[idx]
            df_payway = df_payway[idx+1:].reset_index(drop=True)
            break
    
    # Buscar columna de fecha
    for col in df_payway.columns:
        if "fecha" in str(col).lower():
            df_payway["FECHA"] = pd.to_datetime(df_payway[col], errors='coerce')
            break
    
    if "FECHA" in df_payway.columns:
        df_payway = df_payway.dropna(subset=["FECHA"])
        payway_proc = df_payway
        st.success(f"✅ Payway: {len(payway_proc)} filas procesadas")

# --- 3. Efectivo ---
efectivo_proc = pd.DataFrame()
if df_efectivo is not None and len(df_efectivo) > 2:
    # Buscar fila de encabezados
    for idx, row in df_efectivo.iterrows():
        row_str = " ".join(row.astype(str))
        if "ID CAJERO" in row_str or "CAJERO" in row_str:
            df_efectivo.columns = df_efectivo.iloc[idx]
            df_efectivo = df_efectivo[idx+1:].reset_index(drop=True)
            break
    
    # Buscar columnas de cajero y monto
    col_cajero = None
    col_monto = None
    for col in df_efectivo.columns:
        if "cajero" in str(col).lower() or "id" in str(col).lower():
            col_cajero = col
        if "efectivo" in str(col).lower() or "monto" in str(col).lower():
            col_monto = col
    
    if col_cajero and col_monto:
        df_efectivo[col_monto] = pd.to_numeric(df_efectivo[col_monto], errors='coerce').fillna(0)
        df_efectivo = df_efectivo[~df_efectivo[col_cajero].astype(str).str.contains("Total", na=False)]
        efectivo_proc = df_efectivo[[col_cajero, col_monto]].copy()
        efectivo_proc.columns = ["Cajero", "Monto"]
        st.success(f"✅ Efectivo: {len(efectivo_proc)} filas procesadas")

# --- 4. Tarjetas ---
tarjetas_proc = pd.DataFrame()
if df_tarjetas is not None and len(df_tarjetas) > 2:
    for idx, row in df_tarjetas.iterrows():
        row_str = " ".join(row.astype(str))
        if "Columna 1" in row_str or "FECHA" in row_str:
            df_tarjetas.columns = df_tarjetas.iloc[idx]
            df_tarjetas = df_tarjetas[idx+1:].reset_index(drop=True)
            break
    
    # Buscar columna de fecha
    col_fecha = None
    for col in df_tarjetas.columns:
        if df_tarjetas[col].astype(str).str.contains("2026-05").any():
            col_fecha = col
            break
    
    if col_fecha:
        df_tarjetas["FECHA"] = pd.to_datetime(df_tarjetas[col_fecha], errors='coerce')
        df_tarjetas = df_tarjetas.dropna(subset=["FECHA"])
        
        # Buscar columna de monto (la primera numérica después de fecha)
        for col in df_tarjetas.columns:
            if col != col_fecha:
                df_tarjetas["MONTO"] = pd.to_numeric(df_tarjetas[col], errors='coerce').fillna(0)
                if df_tarjetas["MONTO"].sum() > 0:
                    break
        
        tarjetas_proc = df_tarjetas[["FECHA", "MONTO"]].copy()
        st.success(f"✅ Tarjetas: {len(tarjetas_proc)} filas procesadas")

# ============================================
# MÉTRICAS
# ============================================
st.markdown('<div class="section-title">📊 MÉTRICAS CLAVE</div>', unsafe_allow_html=True)

total_tarjetas = tarjetas_proc["MONTO"].sum() if not tarjetas_proc.empty else 0
total_efectivo = efectivo_proc["Monto"].sum() if not efectivo_proc.empty else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💳 Ventas con Tarjeta", f"")
with col2:
    st.metric("💵 Efectivo Rendido", f"")
with col3:
    st.metric("💰 Total General", f"")

# ============================================
# PESTAÑAS
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Control", "💳 Payway", "👥 Efectivo", "💵 Tarjetas", "🏦 Banco Macro"
])

with tab1:
    if not control_proc.empty:
        st.dataframe(control_proc, use_container_width=True)
    else:
        st.info("No hay datos de Control disponibles")

with tab2:
    if not payway_proc.empty:
        st.dataframe(payway_proc, use_container_width=True)
    else:
        st.info("No hay datos de Payway disponibles")

with tab3:
    if not efectivo_proc.empty:
        fig = px.bar(efectivo_proc, x="Monto", y="Cajero", orientation="h", text_auto=True)
        fig.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(efectivo_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de Efectivo disponibles")

with tab4:
    if not tarjetas_proc.empty:
        fig = px.line(tarjetas_proc, x="FECHA", y="MONTO", markers=True)
        fig.update_layout(height=450, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(tarjetas_proc, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de Tarjetas disponibles")

with tab5:
    if df_banco is not None and not df_banco.empty:
        st.dataframe(df_banco, use_container_width=True)
    else:
        st.info("No hay datos del Banco Macro disponibles")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: #999; font-size: 0.8rem; padding: 1rem;">
        📊 Dashboard | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
""", unsafe_allow_html=True)
