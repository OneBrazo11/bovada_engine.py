import requests
import pandas as pd

# URL Principal (Menú General)
BOVADA_MAIN_URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_specific_event_odds(link):
    """Función auxiliar que entra a la URL específica del partido para buscar cuartos"""
    try:
        # Construimos la URL del evento individual
        # El link suele venir como "/sports/basketball/nba/..."
        url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}"
        r = requests.get(url, headers=HEADERS, timeout=3)
        if r.status_code == 200:
            return r.json() # Devuelve lista con el evento detallado
    except:
        pass
    return []

def get_bovada_odds():
    all_odds = []
    
    # 1. Escanear el Menú Principal
    try:
        r = requests.get(BOVADA_MAIN_URL, headers=HEADERS, timeout=5)
        if r.status_code != 200: return pd.DataFrame()
        main_data = r.json()
    except:
        return pd.DataFrame()

    # 2. Procesar cada partido encontrado
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            # Extraer datos básicos
            description = event['description']
            teams = description.split(' @ ')
            if len(teams) != 2: continue
            away_team, home_team = teams
            is_live = event.get('live', False)
            link = event.get('link')

            # --- ESTRATEGIA DE CAZA ---
            # Si el partido está EN VIVO, los cuartos suelen estar ocultos.
            # Hacemos una llamada extra (Deep Dive) para traer todos los mercados.
            event_source = [event] # Por defecto usamos lo que ya tenemos
            
            if is_live and link:
                # ¡ENTRAMOS AL PARTIDO! (Esto tarda un poco más pero garantiza datos)
                detailed_data = get_specific_event_odds(link)
                if detailed_data and len(detailed_data) > 0:
                    # Usamos la info detallada en vez de la general
                    if 'events' in detailed_data[0]:
                        event_source = detailed_data[0]['events']

            # Procesar los mercados (ya sea del menú principal o del detallado)
            for ev in event_source:
                for group in ev['displayGroups']:
                    period_name = group.get('description', '')
                    
                    # FILTRO: Solo nos interesan estos periodos
                    valid_periods = ["Game Lines", "1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter", "1st Half", "2nd Half"]
                    if period_name not in valid_periods: continue

                    for market in group['markets']:
                        if market['description'] == "Point Spread":
                            line_home, price_home = None, None
                            
                            for outcome in market['outcomes']:
                                price = outcome['price'].get('decimal')
                                handicap = outcome['price'].get('handicap')
                                desc = outcome['description']
                                
                                # Filtro de calidad (Cuotas 1.75 - 2.25)
                                if not price: continue
                                try:
                                    if not (1.75 <= float(price) <= 2.25): continue
                                except: continue

                                if desc == 'Home' or home_team in desc:
                                    line_home = handicap
                                    price_home = price
                            
                            if line_home is not None:
                                all_odds.append({
                                    "Periodo": period_name,
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(line_home),
                                    "Cuota": float(price_home)
                                })

    return pd.DataFrame(all_odds)
