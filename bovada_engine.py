import requests
import pandas as pd

# URL API Pública de Bovada
BOVADA_URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_bovada_odds():
    try:
        r = requests.get(BOVADA_URL, headers=HEADERS, timeout=10)
        if r.status_code != 200: return pd.DataFrame()
        
        data = r.json()
        clean_odds = []
        
        # Periodos válidos que nos interesan
        valid_periods = ["Game Lines", "1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter", "1st Half", "2nd Half"]
        
        for coupon in data:
            if 'events' not in coupon: continue
            
            for event in coupon['events']:
                description = event['description'] 
                teams = description.split(' @ ')
                if len(teams) != 2: continue
                away_team, home_team = teams # Bovada suele poner Away @ Home
                is_live = event.get('live', False)
                
                # Recorremos TODOS los grupos de apuestas
                for group in event['displayGroups']:
                    period_name = group.get('description', '')
                    
                    # FILTRO: Solo guardamos si es uno de los periodos válidos
                    if period_name not in valid_periods:
                        continue
                        
                    for market in group['markets']:
                        # Buscamos SOLO Hándicaps (Point Spread)
                        if market['description'] == "Point Spread":
                            line_home, price_home = None, None
                            
                            for outcome in market['outcomes']:
                                current_price = outcome['price'].get('decimal')
                                current_handicap = outcome['price'].get('handicap')
                                team_desc = outcome['description']
                                
                                # FILTRO DE CALIDAD: Ignorar cuotas basura (menores a 1.80 o mayores a 2.20)
                                if not current_price: continue
                                try:
                                    if not (1.75 <= float(current_price) <= 2.25): continue
                                except: continue
                                
                                # Asignar a Local
                                if team_desc == 'Home' or home_team in team_desc:
                                    line_home = current_handicap
                                    price_home = current_price
                            
                            # Guardamos si encontramos línea válida
                            if line_home is not None:
                                clean_odds.append({
                                    "Periodo": period_name, # Aquí guardamos si es "Game Lines" o "1st Quarter"
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(line_home),
                                    "Cuota": float(price_home)
                                })
                                
        return pd.DataFrame(clean_odds)

    except Exception as e:
        return pd.DataFrame()
