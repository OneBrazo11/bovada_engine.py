import requests
import pandas as pd
import time

# Headers para parecer un navegador real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.bovada.lv/sports/basketball/nba'
}

def get_event_details(link):
    """
    Entra a la URL específica del partido para sacar TODOS los mercados (Cuartos, Mitades, etc.)
    """
    try:
        # El link suele venir como "/sports/basketball/nba/..."
        # La API necesita: .../events/A/description/sports/basketball/nba/...
        base_api = "https://www.bovada.lv/services/sports/event/coupon/events/A/description"
        url = f"{base_api}{link}"
        
        # Damos un poco más de tiempo (timeout=5) porque estos JSON son grandes
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def get_bovada_odds():
    all_odds = []
    print("Iniciando escaneo agresivo de Bovada...")

    # 1. Obtener lista de partidos (Menú Principal)
    main_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"
    try:
        r = requests.get(main_url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return pd.DataFrame()
        main_data = r.json()
    except:
        return pd.DataFrame()

    # 2. Recorrer cada partido encontrado
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            link = event.get('link')
            
            # --- CAMBIO CRÍTICO: DEEP SCAN SIEMPRE ---
            # No importa si es live o pre-match. Si hay link, entramos a buscar cuartos.
            event_data = [event] # Por defecto usamos lo básico
            
            if link:
                # Hacemos la llamada profunda
                detailed = get_event_details(link)
                if detailed and len(detailed) > 0:
                    if 'events' in detailed[0]:
                        event_data = detailed[0]['events']
            
            # 3. Procesar los mercados encontrados
            for ev in event_data:
                # Datos básicos del evento
                teams = ev['description'].split(' @ ')
                if len(teams) != 2: continue
                away_team, home_team = teams
                is_live = ev.get('live', False)
                state_label = "🔴 LIVE" if is_live else "🕒 Pre"

                # Buscar en los grupos (Game Lines, Quarter Lines, Half Lines, etc.)
                for group in ev['displayGroups']:
                    period_name = group.get('description', '')
                    
                    # FILTRO DE PERIODOS (Lo que nos interesa)
                    # A veces Bovada llama a los cuartos "1Q", "2Q" o "1st Quarter"
                    # Usamos palabras clave para atrapar todo
                    clean_period = None
                    if "Game Lines" in period_name: clean_period = "Game Lines"
                    elif "1st Quarter" in period_name: clean_period = "1st Quarter"
                    elif "2nd Quarter" in period_name: clean_period = "2nd Quarter"
                    elif "3rd Quarter" in period_name: clean_period = "3rd Quarter"
                    elif "4th Quarter" in period_name: clean_period = "4th Quarter"
                    elif "1st Half" in period_name: clean_period = "1st Half"
                    elif "2nd Half" in period_name: clean_period = "2nd Half"
                    
                    if not clean_period: continue

                    # Extraer cuotas
                    for market in group['markets']:
                        if market['description'] == "Point Spread":
                            for outcome in market['outcomes']:
                                price = outcome['price'].get('decimal')
                                handicap = outcome['price'].get('handicap')
                                desc = outcome['description']
                                
                                # Filtro anti-basura (Cuotas deben ser competitivas)
                                if not price: continue
                                try:
                                    f_price = float(price)
                                    if not (1.75 <= f_price <= 2.25): continue
                                except: continue

                                # Asignar a Local
                                if desc == 'Home' or home_team in desc:
                                    all_odds.append({
                                        "Periodo": clean_period,
                                        "Estado": state_label,
                                        "Local": home_team,
                                        "Visita": away_team,
                                        "Hándicap Local": float(handicap),
                                        "Cuota": f_price
                                    })

    return pd.DataFrame(all_odds)
