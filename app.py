import streamlit as st
import pandas as pd
import requests
import time
import bovada_engine  # <--- IMPORTAMOS TU NUEVO MOTOR

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
        'markets': 'spreads', # Hándicap partido completo (para comparar con Bovada)
        'oddsFormat': 'decimal',
        'bookmakers': 'pinnacle'
    }
    try:
        r = requests.get(url, params=params)
        return r.json()
    except:
        return []

def normalize_name(name):
    """Limpia nombres para asegurar coincidencia (Ej. 'LA Clippers' vs 'L.A. Clippers')"""
    return name.replace("L.A.", "LA").replace("Utd", "United").strip().lower()

# --- LÓGICA PRINCIPAL ---
st.title("🏀 NBA LIVE SNIPER: CAZANDO A BOVADA")
st.caption("Comparando Pinnacle (La Verdad) vs Bovada (El Objetivo)")

if btn_scan or auto_refresh:
    if not api_key:
        st.error("❌ Falta la API Key de The-Odds-API para leer Pinnacle.")
        st.stop()

    # 1. OBTENER DATOS (En paralelo sería ideal, secuencial por ahora)
    with st.status("📡 Conectando satélites...", expanded=True) as status:
        
        st.write("1. Leyendo Pinnacle (The-Odds-API)...")
        pinnacle_data = get_pinnacle_reference(api_key)
        
        st.write("2. Infiltrando servidores de Bovada...")
        bovada_df = bovada_engine.get_bovada_odds() # <--- TU SCRIPT EN ACCIÓN
        
        if bovada_df.empty:
            st.error("⚠️ Bovada no respondió o no hay partidos en vivo.")
            st.stop()
            
        status.update(label="✅ ¡Datos Recibidos! Procesando...", state="complete")

    # 2. PROCESAR Y CRUZAR
    opportunities = []
    
    # Convertir Bovada a diccionario para búsqueda rápida
    # Clave: Nombre del equipo local normalizado
    bovada_map = {}
    for index, row in bovada_df.iterrows():
        norm_home = normalize_name(row['Local'])
        bovada_map[norm_home] = row

    # Recorrer Pinnacle (Referencia)
    if isinstance(pinnacle_data, list):
        for event in pinnacle_data:
            home_team = event['home_team']
            away_team = event['away_team']
            
            # Buscar línea de Pinnacle
            pin_line = None
            for book in event['bookmakers']:
                if book['key'] == 'pinnacle':
                    # Asumimos que la primera línea es la principal
                    if book['markets']:
                        # Buscamos la línea del equipo LOCAL
                        for outcome in book['markets'][0]['outcomes']:
                            if outcome['name'] == home_team:
                                pin_line = outcome['point']
                                break
            
            if pin_line is None: continue # Si Pinnacle no tiene línea, saltamos
            
            # 3. COMPARAR CON BOVADA
            norm_ref_home = normalize_name(home_team)
            
            # Buscamos si este partido existe en Bovada
            if norm_ref_home in bovada_map:
                bov_row = bovada_map[norm_ref_home]
                bov_line = bov_row['Hándicap Local']
                
                # CÁLCULO DEL GAP (Diferencia)
                diff = abs(pin_line - bov_line)
                
                if diff >= min_diff:
                    # ¡OPORTUNIDAD DETECTADA!
                    opportunities.append({
                        "Partido": f"{home_team} vs {away_team}",
                        "Estado": bov_row['Estado'],
                        "Equipo": home_team, # La comparación se basa en el Local
                        "🏛️ Pinnacle": pin_line,
                        "🎯 Bovada": bov_line,
                        "💰 DIFERENCIA": diff,
                        "Acción": f"Apuesta en Bovada al {'Local' if pin_line > bov_line else 'Visita'} (Verifica lógica)"
                    })

    # 4. MOSTRAR RESULTADOS
    if opportunities:
        st.markdown("### 🔥 OPORTUNIDADES ACTIVAS")
        df_ops = pd.DataFrame(opportunities)
        
        # Estilizar tabla
        st.dataframe(
            df_ops.style.background_gradient(subset=['💰 DIFERENCIA'], cmap='Reds'),
            use_container_width=True
        )
        
        for op in opportunities:
            st.warning(f"🚨 **ALERTA:** En {op['Partido']} hay **{op['💰 DIFERENCIA']} puntos** de diferencia. Pinnacle: {op['🏛️ Pinnacle']} | Bovada: {op['🎯 Bovada']}")
            
    else:
        st.info("✅ Mercado Eficiente. No hay diferencias grandes entre Pinnacle y Bovada ahora mismo.")
        st.write(f"Partidos analizados: {len(bovada_df)}")
        with st.expander("Ver datos crudos de Bovada"):
            st.dataframe(bovada_df)
