import cloudscraper
import pandas as pd
import time
import random

def get_bovada_odds():
    all_odds = []
    print("🚀 INICIANDO ESCANEO DIAGNÓSTICO...")

    # Configuración anti-bloqueo estándar
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

    # URL que trae TODO (Vivo y Próximos)
    main_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"
    
    try:
        r = scraper.get(main_url, timeout=20)
        
        # --- DIAGNÓSTICO VISUAL ---
        # Si falla la conexión, devolvemos el error como si fuera un equipo para que lo veas en pantalla
        if r.status_code == 403:
            return pd.DataFrame([{
                "Periodo": "ERROR", "Estado": "BLOQUEADO", 
                "Local": "Bovada bloqueó la IP", "Visita": "Intenta más tarde", 
                "Hándicap Local": 0, "Cuota": 0
            }])
        if r.status_code != 200:
            return pd.DataFrame([{
                "Periodo": "ERROR", "Estado": f"Err {r.status_code}", 
                "Local": "Fallo de Conexión", "Visita": "Revisar URL", 
                "Hándicap Local": 0, "Cuota": 0
            }])
            
        main_data = r.json()
        
    except Exception as e:
        return pd.DataFrame([{
            "Periodo": "ERROR", "Estado": "CRITICO", 
            "Local": "Error de Script", "Visita": str(e)[:50], 
            "Hándicap Local": 0, "Cuota": 0
        }])

    # Si la conexión fue buena, buscamos los partidos
    events_found_count = 0
    
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            events_found_count += 1
            title = event.get('description', 'Desconocido')
            link = event.get('link')
            is_live = event.get('live', False)
            
            # Limpieza de nombres
            try:
                parts = title.split(' @ ')
                if len(parts) == 2:
                    away_team, home_team = parts
                else:
                    away_team, home_team = "Visitante", "Local"
            except:
                away_team, home_team = "Visitante", "Local"

            # --- ESTRATEGIA: SIEMPRE GUARDAR GAME LINES (Juego Completo) ---
            # Esto asegura que los partidos de mañana aparezcan
            
            # 1. Buscar en los grupos visuales directos (Lo más rápido)
            if 'displayGroups' in event:
                for group in event['displayGroups']:
                    raw_period = group.get('description', '')
                    
                    # Filtramos periodos
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
                        # Aceptamos Spread, Handicap, Run Line (beisbol/otros), etc.
                        desc = market.get('description', '')
                        if not any(x in desc for x in ["Spread", "Handicap", "Point Spread"]):
                            continue

                        for outcome in market['outcomes']:
                            price = outcome['price'].get('decimal')
                            handicap = outcome['price'].get('handicap')
                            outcome_type = outcome.get('type')
                            
                            if not price or not handicap: continue
                            
                            # Filtro de cuota amplio para detectar todo
                            try:
                                f_price = float(price)
                            except: continue

                            # Detectar Local
                            es_local = False
                            if outcome_type == 'H': es_local = True
                            elif home_team in outcome.get('description', ''): es_local = True
                            elif "Home" in outcome.get('description', ''): es_local = True

                            if es_local:
                                all_odds.append({
                                    "Periodo": clean_period,
                                    "Estado": "🔴 LIVE" if is_live else "📅 Futuro",
                                    "Local": home_team,
                                    "Visita": away_team,
                                    "Hándicap Local": float(handicap),
                                    "Cuota": f_price
                                })

    # Si no encontramos nada pero la conexión fue buena
    if len(all_odds) == 0:
        return pd.DataFrame([{
            "Periodo": "INFO", "Estado": "VACIO", 
            "Local": "Conectado OK", "Visita": f"0 juegos encontrados (Raw: {events_found_count})", 
            "Hándicap Local": 0, "Cuota": 0
        }])

    return pd.DataFrame(all_odds)
