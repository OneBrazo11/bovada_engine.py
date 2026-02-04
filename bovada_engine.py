import cloudscraper
import pandas as pd
import time
import random

def get_bovada_odds():
    all_odds = []
    print("🚀 INICIANDO ESCANEO BOVADA (MODO CLOUD)...")

    # Creamos el navegador falso
    scraper = cloudscraper.create_scraper()

    # 1. Obtener Menú Principal
    main_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"
    
    try:
        # Usamos scraper en lugar de requests
        r = scraper.get(main_url, timeout=15)
        if r.status_code != 200:
            print(f"❌ Error conexión menú principal: {r.status_code}")
            return pd.DataFrame()
        main_data = r.json()
    except Exception as e:
        print(f"🔥 Error crítico: {e}")
        return pd.DataFrame()

    # 2. Recorrer partidos
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            title = event.get('description', 'Desconocido')
            link = event.get('link')
            is_live = event.get('live', False)
            
            # Limpieza básica de nombres
            try:
                parts = title.split(' @ ')
                if len(parts) == 2:
                    away_team, home_team = parts
                else:
                    away_team, home_team = "Visitante", "Local"
            except:
                away_team, home_team = "Visitante", "Local"

            events_to_process = [event]

            # --- DEEP SCAN (Para cuartos y mitades) ---
            if link:
                try:
                    if not link.startswith('/'): link = f"/{link}"
                    deep_url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}"
                    time.sleep(random.uniform(0.1, 0.3)) # Pequeña pausa
                    r_deep = scraper.get(deep_url, timeout=10)
                    if r_deep.status_code == 200:
                        deep_data = r_deep.json()
                        if deep_data and isinstance(deep_data, list) and 'events' in deep_data[0]:
                            events_to_process = deep_data[0]['events']
                except:
                    pass 

            # 3. Extraer cuotas
            for ev in events_to_process:
                if 'displayGroups' not in ev: continue
                
                for group in ev['displayGroups']:
                    raw_period = group.get('description', '')
                    
                    # Normalizar periodos
                    clean_period = None
                    if any(x in raw_period for x in ["1st Half", "1H"]): clean_period = "1st Half"
                    elif any(x in raw_period for x in ["2nd Half", "2H"]): clean_period = "2nd Half"
                    elif any(x in raw_period for x in ["1st Quarter", "1Q"]): clean_period = "1st Quarter"
                    elif any(x in raw_period for x in ["2nd Quarter", "2Q"]): clean_period = "2nd Quarter"
                    elif any(x in raw_period for x in ["3rd Quarter", "3Q"]): clean_period = "3rd Quarter"
                    elif any(x in raw_period for x in ["4th Quarter", "4Q"]): clean_period = "4th Quarter"
                    elif "Game Lines" in raw_period: clean_period = "Game Lines"
                    
                    if not clean_period: continue

                    for market in group['markets']:
                        # Buscamos Spread o Handicap
                        desc = market.get('description', '')
                        if not any(x in desc for x in ["Spread", "Handicap", "Point Spread"]):
                            continue

                        for outcome in market['outcomes']:
                            price = outcome['price'].get('decimal')
                            handicap = outcome['price'].get('handicap')
                            outcome_type = outcome.get('type') # 'H' o 'A'
                            
                            if not price or not handicap: continue
                            
                            try:
                                f_price = float(price)
                                # Filtro cuota jugable
                                if not (1.70 <= f_price <= 2.30): continue
                            except: continue

                            # Detectar si es LOCAL
                            es_local = False
                            if outcome_type == 'H': es_local = True
                            elif home_team in outcome.get('description', ''): es_local = True
                            elif "Home" in outcome.get('description', ''): es_local = True

                            if es_local:
                                all_odds.append({
                                    "Periodo": clean_period,
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(handicap),
                                    "Cuota": f_price
                                })

    df = pd.DataFrame(all_odds)
    return df
