import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import os
import random
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestor de Finanzas CM v4.0",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS PERSONALIZADOS (DISEÑO PREMIUM + WATCHLIST REPLICA) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #fcfdfe;
    }

    /* Estilo de Tarjetas */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: white;
        padding: 30px !important;
        border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        border: 1px solid #f1f5f9;
        margin-bottom: 25px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f1f5f9;
        min-width: 320px !important;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    
    .category-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.2rem;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
    }

    /* Métricas Sidebar */
    .sidebar-metric-container {
        background: #ffffff;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #f1f5f9;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .sidebar-metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .sidebar-metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
    }

    /* Botones */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #0f172a !important;
        color: white !important;
        border: none !important;
    }

    /* Badges de Watchlist */
    .badge {
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-stock { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-etf { background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .badge-pos-blue { background: #dbeafe; color: #1e40af; }
    .badge-pos-red { background: #fee2e2; color: #b91c1c; }
    .badge-signal-red { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
    .badge-signal-blue { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-impact { background: #fff7ed; color: #c2410c; border: 1px solid #ffedd5; }
    .badge-attactive-yes { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-attactive-no { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }
    .badge-owned { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
    
    .rsi-low { color: #10b981; }
    .rsi-high { color: #ef4444; }
    
    .lc-progress-container {
        width: 100%;
        background-color: #f1f5f9;
        border-radius: 10px;
        height: 8px;
        margin-top: 10px;
    }
    .lc-progress-bar {
        height: 8px;
        border-radius: 10px;
    }
    .wl-header {
        font-weight: 700;
        color: #94a3b8;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES ---
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
FECHA_ACTUAL_STR = datetime.now().strftime('%d/%m/%Y')

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("No se pudo establecer conexión con Google Sheets. Revisa tus Secrets.")
    st.stop()

# --- FUNCIONES DE DATOS ---

def cargar_todo():
    """Carga todas las pestañas de la nube."""
    try:
        ef = conn.read(worksheet="Efectivo", ttl="0")
        pre = conn.read(worksheet="Presupuesto", ttl="0")
        inv = conn.read(worksheet="Inversiones", ttl="0")
        wl = conn.read(worksheet="Watchlist", ttl="0")
        return ef, pre, inv, wl
    except Exception:
        # Fallback en caso de error o hoja vacía
        return pd.DataFrame(columns=["label", "monto"]), \
               pd.DataFrame(columns=["Mes", "Tipo", "Concepto", "Monto"]), \
               pd.DataFrame(columns=["Fecha", "Ticker", "Cantidad", "Precio Compra", "Tipo"]), \
               pd.DataFrame(columns=["Ticker", "Tipo", "RSI", "Posicion", "Senal", "Atractivo", "Precio", "Cambio", "Nivel", "Impacto"])

def guardar_nube(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)

# --- ESTADO INICIAL ---
if 'init' not in st.session_state:
    ef, pre, inv, wl = cargar_todo()
    st.session_state.df_efectivo = ef
    st.session_state.df_presupuesto = pre
    st.session_state.df_inversiones = inv
    st.session_state.df_watchlist = wl
    st.session_state.init = True

# --- SIDEBAR (EFECTIVO) ---
with st.sidebar:
    st.markdown("<h2 style='color:#0f172a; margin-bottom: 25px; font-weight:800;'>🏢 CM Finanzas</h2>", unsafe_allow_html=True)
    menu = st.radio("Menu", ["📊 Presupuesto", "📈 Inversiones"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("<p style='font-weight:700; color:#94a3b8; font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase;'>Efectivo</p>", unsafe_allow_html=True)
    
    for idx, row in st.session_state.df_efectivo.iterrows():
        c_m, c_e = st.columns([5, 1])
        with c_m:
            st.markdown(f'<div class="sidebar-metric-container"><div class="sidebar-metric-label">{row["label"]}</div><div class="sidebar-metric-value">${row["monto"]:,.2f}</div></div>', unsafe_allow_html=True)
        with c_e:
            st.write("") # Alineación visual
            if st.button("✏️", key=f"edit_ef_{idx}"):
                st.info("Para editar, modifica directamente tu Google Sheet y presiona Sincronizar.")

    if st.button("🔄 Sincronizar con Nube"):
        st.session_state.clear()
        st.rerun()

# --- PÁGINA: PRESUPUESTO ---
if menu == "📊 Presupuesto":
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown('<p class="main-title">Flujo de Caja</p>', unsafe_allow_html=True)
    with col_h2:
        mes_sel = st.selectbox("Seleccionar Mes", options=MESES, index=datetime.now().month - 1)

    # Filtrar datos locales
    df_p = st.session_state.df_presupuesto
    df_mes = df_p[df_p['Mes'] == mes_sel]
    
    c1, c2, c3 = st.columns(3, gap="large")
    
    with c1:
        st.markdown('<p class="category-header">💰 Ingresos</p>', unsafe_allow_html=True)
        # Sumamos ingresos
        val_ing = df_mes[df_mes['Tipo'] == 'Ingreso']['Monto'].sum()
        st.metric("Total Ingresos", f"${val_ing:,.2f}")
        if st.button("+ Ingreso"):
            new_r = pd.DataFrame([{"Mes": mes_sel, "Tipo": "Ingreso", "Concepto": "Nuevo", "Monto": 0.0}])
            st.session_state.df_presupuesto = pd.concat([st.session_state.df_presupuesto, new_r], ignore_index=True)
            st.rerun()

    with c2:
        st.markdown('<p class="category-header">🏠 Fijos</p>', unsafe_allow_html=True)
        fijos_idx = df_p[(df_p['Mes'] == mes_sel) & (df_p['Tipo'] == 'Fijo')].index
        for i in fijos_idx:
            cl, cm = st.columns([2, 1])
            st.session_state.df_presupuesto.at[i, 'Concepto'] = cl.text_input("G", df_p.at[i, 'Concepto'], key=f"c_f_{i}", label_visibility="collapsed")
            st.session_state.df_presupuesto.at[i, 'Monto'] = cm.number_input("M", value=float(df_p.at[i, 'Monto']), key=f"m_f_{i}", label_visibility="collapsed")
        if st.button("+ Fijo"):
            new_r = pd.DataFrame([{"Mes": mes_sel, "Tipo": "Fijo", "Concepto": "Nuevo", "Monto": 0.0}])
            st.session_state.df_presupuesto = pd.concat([st.session_state.df_presupuesto, new_r], ignore_index=True)
            st.rerun()

    with c3:
        st.markdown('<p class="category-header">🛍️ Variables</p>', unsafe_allow_html=True)
        var_idx = df_p[(df_p['Mes'] == mes_sel) & (df_p['Tipo'] == 'Variable')].index
        for i in var_idx:
            cl, cm = st.columns([2, 1])
            st.session_state.df_presupuesto.at[i, 'Concepto'] = cl.text_input("G", df_p.at[i, 'Concepto'], key=f"c_v_{i}", label_visibility="collapsed")
            st.session_state.df_presupuesto.at[i, 'Monto'] = cm.number_input("M", value=float(df_p.at[i, 'Monto']), key=f"m_v_{i}", label_visibility="collapsed")
        if st.button("+ Variable"):
            new_r = pd.DataFrame([{"Mes": mes_sel, "Tipo": "Variable", "Concepto": "Nuevo", "Monto": 0.0}])
            st.session_state.df_presupuesto = pd.concat([st.session_state.df_presupuesto, new_r], ignore_index=True)
            st.rerun()

    if st.button("💾 GUARDAR CAMBIOS EN GOOGLE SHEETS", type="primary", use_container_width=True):
        guardar_nube(st.session_state.df_presupuesto, "Presupuesto")
        st.toast("Guardado en la nube", icon="☁️")

    # --- ANÁLISIS ---
    st.markdown("---")
    st.markdown('<p class="category-header">📊 Rendimiento</p>', unsafe_allow_html=True)
    # Re-cargar sumas
    df_mes_actual = st.session_state.df_presupuesto[st.session_state.df_presupuesto['Mes'] == mes_sel]
    t_ing = df_mes_actual[df_mes_actual['Tipo'] == 'Ingreso']['Monto'].sum()
    t_gas = df_mes_actual[df_mes_actual['Tipo'].isin(['Fijo', 'Variable'])]['Monto'].sum()
    st.columns(3)[0].metric("Capacidad de Ahorro", f"${t_ing - t_gas:,.2f}", delta=f"{((t_ing-t_gas)/t_ing*100 if t_ing>0 else 0):.1f}%")

# --- PÁGINA: INVERSIONES ---
else:
    st.markdown('<p class="main-title">Portafolio & Mercado</p>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📊 Mi Portafolio", "⚙️ Gestión", "🔭 Watchlist"])
    
    with t1:
        df_inv = st.session_state.df_inversiones.copy()
        if not df_inv.empty:
            df_inv['Precio Mercado'] = df_inv['Precio Compra'] * 1.05 # Simulación
            df_inv['Market Value'] = df_inv['Cantidad'] * df_inv['Precio Mercado']
            st.metric("Equity Total", f"${df_inv['Market Value'].sum():,.2f}")
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.info("Registra activos en 'Gestión'.")

    with t2:
        st.markdown("### Registrar Nueva Posición")
        with st.form("add_asset", clear_on_submit=True):
            tick = st.text_input("Ticker").upper()
            cant = st.number_input("Cantidad", min_value=0.0, format="%.6f")
            cost = st.number_input("Costo", min_value=0.0)
            if st.form_submit_button("Confirmar Compra", use_container_width=True):
                new_asset = pd.DataFrame([{"Fecha": FECHA_ACTUAL_STR, "Ticker": tick, "Cantidad": cant, "Precio Compra": cost, "Tipo": "Acción"}])
                st.session_state.df_inversiones = pd.concat([st.session_state.df_inversiones, new_asset], ignore_index=True)
                guardar_nube(st.session_state.df_inversiones, "Inversiones")
                st.rerun()

    with t3:
        st.markdown("### 🔭 Market Scanner / Watchlist")
        wl_data = st.session_state.df_watchlist
        tickers_propios = st.session_state.df_inversiones['Ticker'].unique()
        
        # Header Watchlist
        h_cols = st.columns([1, 1, 0.8, 1.2, 1.8, 1.1, 1, 1, 1, 1.2])
        headers = ["TICKER", "Tipo", "RSI", "Cartera", "Posicion", "Senal", "Atractivo", "PRECIO", "Nivel LC", ""]
        for i, h in enumerate(headers): h_cols[i].markdown(f"<div class='wl-header'>{h}</div>", unsafe_allow_html=True)
        
        for idx, item in wl_data.iterrows():
            r = st.columns([1, 1, 0.8, 1.2, 1.8, 1.1, 1, 1, 1, 1.2])
            r[0].markdown(f"**{item['Ticker']}**")
            
            # Tipo Badge
            t_class = "badge-stock" if item['Tipo'] == "Stock" else "badge-etf"
            r[1].markdown(f"<span class='badge {t_class}'>{item['Tipo']}</span>", unsafe_allow_html=True)
            
            # RSI
            rsi_val = float(item['RSI'])
            rsi_c = "rsi-low" if rsi_val < 45 else "rsi-high" if rsi_val > 65 else ""
            r[2].markdown(f"<span class='{rsi_c}'>{rsi_val}</span>", unsafe_allow_html=True)
            
            # En Cartera
            en_c = item['Ticker'] in tickers_propios
            c_icon = "💼 Sí" if en_c else "No"
            c_class = "badge-owned" if en_c else "badge-attactive-no"
            r[3].markdown(f"<span class='badge {c_class}'>{c_icon}</span>", unsafe_allow_html=True)
            
            # Posicion
            p_class = "badge-pos-red" if "Sobre" in str(item['Posicion']) else "badge-pos-blue"
            r[4].markdown(f"<span class='badge {p_class}'>{item['Posicion']}</span>", unsafe_allow_html=True)
            
            # Señal
            s_class = "badge-signal-blue" if item['Senal'] == "Interesante" else "badge-signal-red"
            r[5].markdown(f"<span class='badge {s_class}'>{item['Senal']}</span>", unsafe_allow_html=True)
            
            # Atractivo
            is_att = "Sí" if (rsi_val < 50 and item['Senal'] == "Interesante") else "No"
            a_class = "badge-attactive-yes" if is_att == "Sí" else "badge-attactive-no"
            r[6].markdown(f"<span class='badge {a_class}'>{'✅' if is_att=='Sí' else '⏳'} {is_att}</span>", unsafe_allow_html=True)
            
            r[7].markdown(f"**${item['Precio']}**")
            
            # Nivel LC
            nv = int(item['Nivel'])
            pr_c = "#f97316" if nv < 40 else "#10b981"
            r[8].markdown(f"<div class='lc-progress-container'><div class='lc-progress-bar' style='width:{nv}%; background-color:{pr_c};'></div></div>", unsafe_allow_html=True)
            
            if r[9].button("🗑️", key=f"del_wl_{idx}"):
                st.session_state.df_watchlist = st.session_state.df_watchlist.drop(idx)
                guardar_nube(st.session_state.df_watchlist, "Watchlist")
                st.rerun()
