import requests
import pandas as pd

# ---------------------------------------------------------
# 🔴 PEGA TU API KEY AQUÍ (Dentro de las comillas)
API_KEY = "df28f2f3c24ae0bbc3b76cfc79296683" 
# ---------------------------------------------------------

def get_bovada_odds():
    print("🚀 CONSULTANDO API (FULL: H2H, SPREAD, TOTALES, MITADES, CUARTOS)...")
    
    sport_key = 'basketball_nba'
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'

    # SOLICITAMOS LA LISTA COMPLETA DE MERCADOS
    markets_list = (
        "h2h,spreads,totals,"               # Juego Completo
        "h2h_h1,spreads_h1,totals_h1,"      # 1ra Mitad
        "h2h_h2,spreads_h2,totals_h2,"      # 2da Mitad
        "h2h_q1,spreads_q1,totals_q1,"      # 1er Cuarto
        "h2h_q2,spreads_q2,totals_q2,"      # 2do Cuarto
        "h2h_q3,spreads_q3,totals_q3,"      # 3er Cuarto
        "h2h_q4,spreads_q4,totals_q4"       # 4to Cuarto
    )

    params = {
        'api_key': API_KEY,
        'regions': 'us',
        'markets': markets_list, 
        'oddsFormat': 'decimal',
        'bookmakers': 'bovada'
    }

    try:
        r = requests.get(url, params=params)
        
        # --- DIAGNÓSTICO DE ERRORES ---
        if r.status_code == 401:
            return pd.DataFrame([{"Periodo": "ERROR", "Tipo": "KEY", "Local": "Tu API Key", "Visita": "no es válida", "Dato": 0, "Cuota": 0}])
        if r.status_code == 429:
            return pd.DataFrame([{"Periodo": "ERROR", "Tipo": "QUOTA", "Local": "Se acabaron los créditos", "Visita": "Crea otra cuenta", "Dato": 0, "Cuota": 0}])
        if r.status_code != 200:
            return pd.DataFrame([{"Periodo": "ERROR", "Tipo": f"HTTP {r.status_code}", "Local": "Fallo Conexión", "Visita": "...", "Dato": 0, "Cuota": 0}])

        data = r.json()

    except Exception as e:
        return pd.DataFrame([{"Periodo": "ERROR", "Tipo": "CRITICO", "Local": "Error Script", "Visita": str(e), "Dato": 0, "Cuota": 0}])

    # Procesar los datos
    all_odds = []
    
    if not data:
        return pd.DataFrame([{"Periodo": "INFO", "Tipo": "VACIO", "Local": "API Conectada", "Visita": "Sin líneas publicadas", "Dato": 0, "Cuota": 0}])

    for game in data:
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for book in game.get('bookmakers', []):
            if book['key'] == 'bovada':
                for market in book['markets']:
                    
                    key = market['key']
                    
                    # 1. IDENTIFICAR PERIODO
                    period_name = "Full Time"
                    if "h1" in key: period_name = "1st Half"
                    elif "h2" in key: period_name = "2nd Half"
                    elif "q1" in key: period_name = "1st Quarter"
                    elif "q2" in key: period_name = "2nd Quarter"
                    elif "q3" in key: period_name = "3rd Quarter"
                    elif "q4" in key: period_name = "4th Quarter"

                    # 2. IDENTIFICAR TIPO DE APUE
