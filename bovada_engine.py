import requests
import pandas as pd

# ---------------------------------------------------------
# CONFIGURACIÓN: PEGA TU API KEY ABAJO DENTRO DE LAS COMILLAS
API_KEY = "TU_API_KEY_AQUI"
# ---------------------------------------------------------

def get_bovada_odds():
    all_odds = []
    print("🚀 CONSULTANDO THE ODDS API (VÍA OFICIAL)...")

    # 1. Configurar la petición a la API
    # Pedimos NBA, casa 'bovada', y mercados de spreads (hándicap)
    # Nota: El plan gratis permite consultar mercados principales.
    sport_key = 'basketball_nba'
    
    # URL oficial
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'

    params = {
        'api_key': API_KEY,
        'regions': 'us',          # Región US para Bovada
        'markets': 'spreads',     # Pedimos Hándicaps (Game Lines)
        'oddsFormat': 'decimal',
        'bookmakers': 'bovada'    # Solo queremos datos de Bovada
    }

    try:
        r = requests.get(url, params=params)
        
        # --- DIAGNÓSTICO DE ERRORES ---
        if r.status_code == 401:
            print("❌ ERROR: La API Key es incorrecta o no se ha activado aún.")
            return pd.DataFrame()
        if r.status_code == 429:
            print("❌ ERROR: Se acabó tu cuota mensual gratuita de la API.")
            return pd.DataFrame()
        if r.status_code != 200:
            print(f"❌ Error de conexión con API: {r.status_code}")
            return pd.DataFrame()

        data = r.json()

    except Exception as e:
        print(f"🔥 Error crítico: {e}")
        return pd.DataFrame()

    # 2. Procesar los datos limpios
    print(f"✅ Datos recibidos. Procesando {len(data)} partidos...")

    for game in data:
        # Datos del partido
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        commence_time = game.get('commence_time') # Fecha/Hora inicio
        
        # Buscar las cuotas de Bovada dentro del partido
        bookmakers = game.get('bookmakers', [])
        for book in bookmakers:
            if book['key'] == 'bovada':
                for market in book['markets']:
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            # outcome['name'] es el nombre del equipo
                            # outcome['price'] es la cuota (ej. 1.90)
                            # outcome['point'] es el hándicap (ej. -5.5)
                            
                            team_name = outcome.get('name')
                            price = outcome.get('price')
                            point = outcome.get('point')

                            # Identificar si es el Local
                            es_local = False
                            if team_name == home_team:
                                es_local = True

                            if es_local:
                                all_odds.append({
                                    "Periodo": "Game Lines", # La API básica da juego completo
                                    "Estado": "✅ ACTIVO",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(point),
                                    "Cuota": float(price)
                                })

    df = pd.DataFrame(all_odds)
    
    if df.empty:
        print("⚠️ La API respondió bien, pero no hay líneas de Bovada ahora mismo.")
    else:
        print(f"🏁 ÉXITO: {len(df)} líneas encontradas.")

    return df
