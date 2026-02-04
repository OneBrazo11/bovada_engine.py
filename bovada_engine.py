import requests
import pandas as pd
import time

# URL "Secreta" de Bovada (API Pública JSON)
BOVADA_URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_bovada_odds():
    print("🎯 Conectando con servidores de Bovada...")
    try:
        r = requests.get(BOVADA_URL, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            return []

        data = r.json()
        clean_odds = []
        
        # Bovada devuelve una lista de "Coupons" (Grupos de eventos)
        for coupon in data:
            if 'events' not in coupon: continue
            
            for event in coupon['events']:
                # 1. Datos Básicos del Evento
                game_id = event['id']
                description = event['description'] # Ej: "Lakers @ Celtics"
                is_live = event.get('live', False)
                start_time = event['startTime']
                
                # Separar equipos (Bovada suele poner "Away @ Home")
                teams = description.split(' @ ')
                if len(teams) != 2: continue # Saltamos formatos raros
                away_team, home_team = teams
                
                # 2. Buscar Mercados (Display Groups)
                # Bovada agrupa por "Game Lines", "1st Quarter", etc.
                for group in event['displayGroups']:
                    
                    # FILTRO: Aquí decidimos qué periodo nos interesa.
                    # Por defecto buscamos 'Game Lines' (Partido Completo)
                    # Si quieres cuartos, busca '1st Quarter', '2nd Quarter', etc.
                    period_name = group.get('description', '')
                    
                    # Vamos a capturar SOLO líneas principales para probar
                    if period_name != "Game Lines": 
                        continue 

                    for market in group['markets']:
                        # 3. Extraer HÁNDICAP (Point Spread)
                        if market['description'] == "Point Spread":
                            # Bovada tiene outcomes: [Away, Home]
                            line_home = None
                            price_home = None
                            line_away = None
                            price_away = None
                            
                            # --- BLOQUE MEJORADO CON FILTRO DE CALIDAD ---
                            for outcome in market['outcomes']:
                                current_price = outcome['price'].get('decimal')
                                current_handicap = outcome['price'].get('handicap')
                                team_desc = outcome['description'] 
                                
                                # FILTRO ANTI-RUIDO: 
                                # Solo aceptamos líneas "estándar" (cuotas entre 1.80 y 2.10)
                                # Esto elimina las líneas alternativas de +28 puntos que ensucian tu tabla.
                                if not (1.80 <= float(current_price) <= 2.20):
                                    continue 

                                # Asignar a Local o Visita
                                if team_desc == 'Home' or home_team in team_desc:
                                    line_home = current_handicap
                                    price_home = current_price
                                elif team_desc == 'Away' or away_team in team_desc:
                                    line_away = current_handicap
                                    price_away = current_price
                            # ---------------------------------------------
                                
                                # Asignar a Local o Visita (Lógica simple de coincidencia)
                                if team_desc == 'Home' or home_team in team_desc:
                                    line_home = current_handicap
                                    price_home = current_price
                                elif team_desc == 'Away' or away_team in team_desc:
                                    line_away = current_handicap
                                    price_away = current_price
                            
                            # Guardamos la data si está completa
                            if line_home is not None:
                                clean_odds.append({
                                    "Casa": "Bovada",
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Periodo": "Full Time", # Cambiar si filtras cuartos
                                    "Hándicap Local": line_home,
                                    "Cuota Local": price_home,
                                    "Hándicap Visita": line_away,
                                    "Cuota Visita": price_away
                                })

        return pd.DataFrame(clean_odds)

    except Exception as e:
        print(f"🔥 Error en Bovada Engine: {e}")
        return []

# --- ZONA DE PRUEBAS (Solo se ejecuta si corres este archivo directo) ---
if __name__ == "__main__":
    df = get_bovada_odds()
    if not df.empty:
        print("\n✅ ¡DATOS EXTRAÍDOS DE BOVADA!")
        print(df.to_string(index=False))
    else:
        print("\n⚠️ No se encontraron líneas (o no hay partidos NBA activos).")
