import streamlit as st
import pandas as pd
import requests
import bovada_engine  # Tu motor actualizado

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="NBA LIVE HUNTER", page_icon="🏀")

st.markdown("""
    <style>
    .big-money { font-size: 24px; font-weight: bold; color: #00FF00; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CENTRO DE MANDO ---
with st.sidebar:
    st.header("🏀 NBA LIVE HUNTER")
    api_key = st.text_input("API Key (The-Odds-API)", type="password")
    
    st.divider()
    
    # --- EL SELECTOR MÁGICO ---
    # Mapea lo que ve Bovada vs lo que pide la API de Pinnacle
    modo = st.selectbox("🎯 ¿Qué cazamos hoy?", [
        "Partido Completo (Full Game)",
        "1er Cuarto (1Q)",
        "2do Cuarto (2Q)",
        "1ra Mitad (1H)",
        "2da Mitad (2H)"
    ])
    
    # Configuración interna según la elección
    config_map = {
        "Partido Completo (Full Game)": {"bovada": "Game Lines", "api": "spreads"},
        "1er Cuarto (1Q)":             {"bovada": "1st Quarter", "api": "spreads_q1"},
        "2do Cuarto (2Q)":             {"bovada": "2nd Quarter", "api": "spreads_q2"},
        "1ra Mitad (1H)":              {"bovada": "1st Half",    "api": "spreads_h1"},
        "2da Mitad (2H)":              {"bovada": "2nd Half",    "api": "spreads_h2"}
    }
    
    seleccion = config_map[modo]
    
    st.divider()
    min_diff = st.slider("Diferencia Mínima (Puntos)", 1.0, 5.0, 1.5)
    btn_scan = st.button("ESCANEAR AHORA 🔫", type="primary")

# --- FUNCIONES ---
def normalize_name(name):
    if not isinstance(name, str): return ""
    return name.replace("L.A.", "LA").replace("Utd", "United").strip().lower()

def get_pinnacle_data(api_key, market_key):
    """Pide a Pinnacle solo el mercado que seleccionaste"""
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        'apiKey': api_key,
        'regions': 'eu',
        'markets': market_key, # Dinámico: spreads, spreads_q1, etc.
        'oddsFormat': 'decimal',
        'bookmakers': 'pinnacle'
    }
    try:
        return requests.get(url, params=params).json()
    except: return []

# --- MOTOR PRINCIPAL ---
st.title(f"📡 RADAR: {modo}")

if btn_scan and api_key:
    # 1. OBTENCIÓN DE DATOS
    with st.status(f"Escaneando {modo}...", expanded=True) as status:
        
        st.write(f"1. Consultando a Pinnacle ({seleccion['api']})...")
        pin_data = get_pinnacle_data(api_key, seleccion['api'])
        
        st.write("2. Infiltrando Bovada (Todos los periodos)...")
        bov_all_df = bovada_engine.get_bovada_odds()
        
        # FILTRADO INTELIGENTE
        # De todo lo que trajo Bovada, nos quedamos solo con el periodo seleccionado
        if not bov_all_df.empty:
            bov_target = bov_all_df[bov_all_df['Periodo'] == seleccion['bovada']]
        else:
            bov_target = pd.DataFrame()
            
        if bov_target.empty:
            st.warning(f"Bovada no tiene líneas activas para '{seleccion['bovada']}' ahora mismo.")
            st.stop()
            
        status.update(label="✅ Datos recibidos. Comparando...", state="complete")

    # 2. COMPARACIÓN
    opportunities = []
    
    # Mapa rápido de Bovada
    bov_map = {}
    for _, row in bov_target.iterrows():
        name = normalize_name(row['Local'])
        bov_map[name] = row

    # Recorrer Pinnacle
    if isinstance(pin_data, list):
        for event in pin_data:
            home = event['home_team']
            
            # Buscar línea Pinnacle
            pin_line = None
            for book in event['bookmakers']:
                if book['key'] == 'pinnacle':
                    if book['markets']:
                        for out in book['markets'][0]['outcomes']:
                            if out['name'] == home:
                                pin_line = out.get('point')
            
            if pin_line is None: continue
            
            # Cruzar con Bovada
            norm_home = normalize_name(home)
            if norm_home in bov_map:
                bov_row = bov_map[norm_home]
                bov_line = bov_row['Hándicap Local']
                
                try:
                    diff = abs(float(pin_line) - float(bov_line))
                    if diff >= min_diff:
                        opportunities.append({
                            "Partido": f"{home} vs {bov_row['Visita']}",
                            "Periodo": seleccion['bovada'], # Muestra qué cuarto es
                            "Local": home,
                            "🏛️ Pin": float(pin_line),
                            "🎯 Bov": float(bov_line),
                            "💰 DIFF": round(diff, 2)
                        })
                except: continue

    # 3. RESULTADOS
    if opportunities:
        st.markdown(f"### 🔥 {len(opportunities)} OPORTUNIDADES ENCONTRADAS")
        
        # Tabla simple (Sin colores para evitar errores de matplotlib)
        st.dataframe(pd.DataFrame(opportunities), use_container_width=True)
        
        for op in opportunities:
            st.error(f"🚨 **{op['Local']}**: Pinnacle **{op['🏛️ Pin']}** vs Bovada **{op['🎯 Bov']}** (Diff: {op['💰 DIFF']})")
    else:
        st.info(f"Mercado eficiente. No hay errores en {modo}.")
        with st.expander("Ver datos crudos de Bovada (Debug)"):
            st.dataframe(bov_target)
