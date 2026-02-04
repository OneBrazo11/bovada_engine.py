import requests
import pandas as pd

# URL API Pública de Bovada
BOVADA_URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_bovada_quarters():
    try:
        r = requests.get(BOVADA_URL, headers=HEADERS, timeout=10)
        if r.status_code != 200: return []
        
        data = r.json()
        clean_odds = []
        
        for coupon in data:
            if 'events' not in coupon: continue
            
            for event in coupon['events']:
                description = event['description'] 
                teams = description.split(' @ ')
                if len(teams) != 2: continue
                away_team, home_team = teams
                is_live = event.get('live', False)
                
                # --- AQUÍ ESTÁ LA MAGIA: Buscamos en TODOS los grupos ---
                for group in event['displayGroups']:
                    period_name = group.get('description', '')
                    
                    # FILTRO: Solo queremos Cuartos o Mitades
                    # Aceptamos: "1st Quarter", "2nd Quarter", "1st Half", etc.
                    if "Quarter" not in period_name and "Half" not in period_name:
                        continue
                        
                    # Entramos a los mercados del periodo
                    for market in group['markets']:
                        # Buscamos Hándicaps (Point Spread)
                        if market['description'] == "Point Spread":
                            line_home, price_home = None, None
                            
                            for outcome in market['outcomes']:
                                current_price = outcome['price'].get('decimal')
                                current_handicap = outcome['price'].get('handicap')
                                team_desc = outcome['description']
                                
                                # FILTRO DE CALIDAD (Evitar líneas basura)
                                if not current_price or not (1.80 <= float(current_price) <= 2.20):
                                    continue
                                
                                # Asignar a Local
                                if team_desc == 'Home' or home_team in team_desc:
                                    line_home = current_handicap
                                    price_home = current_price
                            
                            # Si encontramos línea para el local, la guardamos
                            if line_home is not None:
                                clean_odds.append({
                                    "Periodo": period_name, # Ej: "1st Quarter"
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(line_home),
                                    "Cuota": float(price_home)
                                })
                                
        return pd.DataFrame(clean_odds)

    except Exception as e:
        return []
      
