import streamlit as st
import pandas as pd
import requests
import time
import bovada_engine  # <--- IMPORTAMOS TU MOTOR BOVADA

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="NBA SNIPER: BOVADA vs PINNACLE", page_icon="🏀")

st.markdown("""
    <style>
    .big-money { font-size: 24px; font-weight: bold; color: #00FF00; }
    .alert-box { background-color: #4a1c1c; padding: 15px; border-radius: 5px; border: 1px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Configuración Sniper")
    api_key = st.text_input("Tu API Key (The-Odds-API)", type="password")
    min_diff = st.slider("Diferencia Mínima (Puntos)", 1.0, 5.0, 1.5)
    auto_refresh = st.checkbox("Auto-Refresh (Experimental)", value=False)
    btn_scan = st.button("ESCANEAR AHORA 🔫", type="primary")

# --- FUNCIONES ---
def get_pinnacle_reference(api_key):
    """Obtiene la línea 'verdadera' de Pinnacle vía API"""
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        'apiKey': api_key,
        'regions': 'eu', # Pinnacle suele estar en zona EU en esta API
        'markets': 'spreads', # Hándicap partido completo
        'oddsFormat': 'decimal',
        'bookmakers': 'pinnacle'
    }
    try:
        r = requests.get(url, params=params)
        return r.json()
    except:
        return []

def normalize_name(name):
    """Limpia nombres para asegurar coincidencia"""
    if not isinstance(name, str): return ""
    return name.replace("L.A.", "LA").replace("Utd", "United").strip().lower()

# --- LÓGICA PRINCIPAL ---
st.title("🏀 NBA LIVE SNIPER: CAZANDO A BOVADA")
st.caption("Comparando Pinnacle (La Verdad) vs Bovada
