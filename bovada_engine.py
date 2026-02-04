import requests
import pandas as pd

# ---------------------------------------------------------
# PEGA TU API KEY AQUÍ (Dentro de las comillas)
API_KEY = "72503fba894cd3d0eb051071fce25d6c" 
# ---------------------------------------------------------

def get_bovada_odds():
    # URL para NBA
    sport_key = 'basketball_nba'
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'

    params = {
        'api_key': API_KEY,
        'regions': 'us',
        'markets': 'spreads', # Hándicaps
        'oddsFormat': 'decimal',
        'bookmakers': 'bovada'
    }

    try:
        r = requests.get(url, params=params)
        
        # --- DIAGNÓSTICO VISUAL (Para que lo veas en la pantalla) ---
        
        # Error de Clave (401)
        if r.status_code == 401:
            return pd.DataFrame([{
                "Periodo": "ERROR", "Estado": "CLAVE INVALIDA",
                "Local": "Revisa tu API Key", "Visita": "Copia y pega bien",
                "Hándicap Local": 0, "Cuota": 0
            }])

        # Error de Cuota (429) - Se acabaron las peticiones gratis
        if r.status_code == 429:
            return pd.DataFrame([{
                "Periodo": "ERROR", "Estado": "CUOTA LLENA",
                "Local": "Se acabaron los 500 requests", "Visita": "Usa otra cuenta/key",
                "Hándicap Local": 0, "Cuota": 0
            }])

        # Otros errores de conexión
        if r.status_code != 200:
            return pd.DataFrame([{
                "Periodo": "ERROR", "Estado": f"Status {r.status_code}",
                "Local": "Error de conexión", "Visita": r.text[:20],
                "Hándicap Local": 0, "Cuota": 0
            }])

        data = r.json()

    except Exception as e:
        return pd.DataFrame([{
            "Periodo": "ERROR", "Estado": "CRITICO",
            "Local": "Fallo Python", "Visita": str(e),
            "Hándicap Local": 0, "Cuota": 0
        }])

    # Si la lista está vacía (Bovada no tiene líneas publicadas en la API)
    if not data:
        return pd.DataFrame([{
            "Periodo": "INFO", "Estado": "SIN DATOS",
            "Local": "La API funciona", "Visita": "Pero Bovada no da líneas hoy",
            "Hándicap Local": 0, "Cuota": 0
        }])

    # Procesar datos si hay éxito
    all_odds = []
    for game in data:
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        
        for book in game.get('bookmakers', []):
            if book['key'] == 'bovada':
                for market in book['markets']:
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            team_name = outcome.get('name')
                            price = outcome.get('price')
                            point = outcome.get('point')

                            es_local = (team_name == home_team)
                            
                            if es_local:
                                all_odds.append({
                                    "Periodo": "Game Lines",
                                    "Estado": "✅ API OK",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(point),
                                    "Cuota": float(price)
                                })

    if not all_odds:
        return pd.DataFrame([{
            "Periodo": "INFO", "Estado": "VACIO",
            "Local": "Hay partidos", "Visita": "Pero no líneas de Bovada",
            "Hándicap Local": 0, "Cuota": 0
        }])

    return pd.DataFrame(all_odds)
