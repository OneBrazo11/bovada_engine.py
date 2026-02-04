import streamlit as st
import pandas as pd
import requests
import bovada_quarters # Importamos el motor nuevo

st.set_page_config(layout="wide", page_title="NBA QUARTERS SNIPER", page_icon="🧩")

# --- CONFIGURACIÓN ---
with st.sidebar:
    st.header("🧩 Configuración Cuartos")
    api_key = st.text_input("API Key (The-Odds-API)", type="password")
    
    # SELECTOR DE PERIODO CRÍTICO
    # Mapeamos lo que devuelve Bovada vs lo que pide la API de Pinnacle
    period_map = {
        "1er Cuarto (1Q)": {"bovada": "1st Quarter", "api": "spreads_q1"},
        "2do Cuarto (2Q)": {"bovada": "2nd Quarter", "api": "spreads_q2"}, # Ojo: API a veces no tiene Q2 live
        "1ra Mitad (1H)":  {"bovada": "1st Half",    "api": "spreads_h1"},
        "2da Mitad (2H)":  {"bovada": "2nd Half",    "api": "spreads_h2"}
    }
    
    selected_label = st.selectbox("¿Qué periodo analizamos?", list(period_map.keys()))
    config = period_map[selected_label]
    
    min_diff = st.slider("Diferencia Mínima", 1.0, 5.0, 1.5)
    btn_scan = st.button("ESCANEAR PERIODO 🔫", type="primary")

# --- FUNCIONES ---
def normalize_name(name):
    if not isinstance(name, str): return ""
    return name.replace("L.A.", "LA").replace("Utd", "United").strip().lower()

def get_pinnacle_period(api_key, market_key):
    # Pedimos a Pinnacle solo el mercado específico (ej. spreads_q1)
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        'apiKey': api_key,
        'regions': 'eu',
        'markets': market_key, # Aquí viaja la clave dinámica (spreads_q1, etc)
        'oddsFormat': 'decimal',
        'bookmakers': 'pinnacle'
    }
    try:
        return requests.get(url, params=params).json()
    except: return []

# --- APP PRINCIPAL ---
st.title(f"🧩 NBA SNIPER: {selected_label}")

if btn_scan and api_key:
    with st.status(f"Buscando líneas de {config['bovada']}...", expanded=True):
        
        # 1. Obtener Pinnacle
        st.write("Leyendo Pinnacle...")
        pin_data = get_pinnacle_period(api_key, config['api'])
        
        # 2. Obtener Bovada
        st.write("Leyendo Bovada...")
        bov_df = bovada_quarters.get_bovada_quarters()
        
        # 3. Filtrar Bovada por el periodo seleccionado
        if not bov_df.empty:
            # Filtramos solo las filas que coincidan con "1st Quarter" (o lo que hayas elegido)
            bov_target = bov_df[bov_df['Periodo'] == config['bovada']]
        else:
            bov_target = pd.DataFrame()

        # Chequeo de seguridad
        if bov_target.empty:
            st.warning(f"Bovada no tiene líneas activas para '{config['bovada']}' en este momento.")
            st.stop()
            
    # --- MOTOR DE COMPARACIÓN ---
    opportunities = []
    
    # Mapa de Bovada
    bov_map = {}
    for _, row in bov_target.iterrows():
        name = normalize_name(row['Local'])
        bov_map[name] = row

    # Cruzar con Pinnacle
    if isinstance(pin_data, list):
        for event in pin_data:
            home = event['home_team']
            
            # Buscar línea Pinnacle
            pin_line = None
            for book in event['bookmakers']:
                if book['key'] == 'pinnacle':
                    if book['markets']: # Si existe el mercado q1/h1
                        for out in book['markets'][0]['outcomes']:
                            if out['name'] == home:
                                pin_line = out.get('point')
            
            if pin_line is None: continue
            
            # Comparar
            norm_home = normalize_name(home)
            if norm_home in bov_map:
                bov_row = bov_map[norm_home]
                bov_line = bov_row['Hándicap Local']
                
                try:
                    diff = abs(float(pin_line) - float(bov_line))
                    if diff >= min_diff:
                        opportunities.append({
                            "Partido": f"{home} vs {bov_row['Visita']}",
                            "Periodo": config['bovada'],
                            "Local": home,
                            "🏛️ Pinnacle": float(pin_line),
                            "🎯 Bovada": float(bov_line),
                            "💰 DIFERENCIA": round(diff, 2)
                        })
                except: continue

    if opportunities:
        st.success(f"¡{len(opportunities)} Oportunidades en {config['bovada']}!")
        st.dataframe(pd.DataFrame(opportunities))
    else:
        st.info(f"No hay diferencias en {config['bovada']} o Pinnacle no tiene cuotas para este periodo.")
