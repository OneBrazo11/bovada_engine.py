import requests
import pandas as pd
import time

# HEADERS: Clave para que no nos bloqueen
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.bovada.lv/sports/basketball/nba'
}

def get_bovada_odds():
    all_odds = []
    print("🚀 INICIANDO ESCANEO BOVADA...")

    # 1. Obtener Menú Principal
    main_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"
    try:
        r = requests.get(main_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"❌ Error conectando al menú principal: {r.status_code}")
            return pd.DataFrame()
        main_data = r.json()
    except Exception as e:
        print(f"🔥 Error crítico: {e}")
        return pd.DataFrame()

    # 2. Recorrer cada partido
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            # Datos básicos
            title = event.get('description', 'Desconocido')
            link = event.get('link')
            is_live = event.get('live', False)
            
            # Equipos
            try:
                teams = title.split(' @ ')
                if len(teams) == 2:
                    away_team, home_team = teams
                else:
                    continue
            except: continue

            print(f"🔎 Analizando: {title} ({'LIVE' if is_live else 'PRE'})")

            # --- ESTRATEGIA HÍBRIDA ---
            # Guardamos primero lo que hay en el menú (Suele ser solo Game Lines)
            events_to_process = [event]

            # Si hay link, INTENTAMOS entrar para buscar Cuartos/Mitades
            if link:
                try:
                    # Corrección de URL: Asegurar que el link empiece bien
                    if not link.startswith('/'): link = f"/{link}"
                    
                    deep_url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}"
                    
                    # Pausa de cortesía para evitar bloqueo
                    time.sleep(0.1) 
                    
                    r_deep = requests.get(deep_url, headers=HEADERS, timeout=5)
                    
                    if r_deep.status_code == 200:
                        deep_data = r_deep.json()
                        if deep_data and 'events' in deep_data[0]:
                            # ¡ÉXITO! Tenemos los datos profundos con cuartos
                            events_to_process = deep_data[0]['events']
                            # print(f"   ✅ Datos profundos descargados para {title}")
                    else:
                        print(f"   ⚠️ No se pudo entrar al link (Status {r_deep.status_code})")
                except Exception as e:
                    print(f"   ⚠️ Error en Deep Scan: {e}")

            # 3. Procesar Mercados (Ya sea del menú o del deep scan)
            for ev in events_to_process:
                if 'displayGroups' not in ev: continue
                
                for group in ev['displayGroups']:
                    raw_period = group.get('description', '')
                    
                    # FILTRO DE PERIODOS: Estandarización de nombres
                    clean_period = None
                    
                    # Game Lines
                    if "Game Lines" in raw_period: clean_period = "Game Lines"
                    
                    # Cuartos
                    elif "1st Quarter" in raw_period or "1Q" in raw_period: clean_period = "1st Quarter"
                    elif "2nd Quarter" in raw_period or "2Q" in raw_period: clean_period = "2nd Quarter"
                    elif "3rd Quarter" in raw_period or "3Q" in raw_period: clean_period = "3rd Quarter"
                    elif "4th Quarter" in raw_period or "4Q" in raw_period: clean_period = "4th Quarter"
                    
                    # Mitades
                    elif "1st Half" in raw_period or "1H" in raw_period: clean_period = "1st Half"
                    elif "2nd Half" in raw_period or "2H" in raw_period: clean_period = "2nd Half"

                    if not clean_period: continue

                    # Extraer Cuotas (Spread)
                    for market in group['markets']:
                        # Buscamos "Point Spread" o variantes
                        if "Point Spread" in market.get('description', ''):
                            for outcome in market['outcomes']:
                                price = outcome['price'].get('decimal')
                                handicap = outcome['price'].get('handicap')
                                desc = outcome['description'] # Home / Away
                                
                                # Filtro de calidad (Cuotas vacías o locas)
                                if not price or not handicap: continue
                                try:
                                    f_price = float(price)
                                    # Solo cuotas jugables (1.70 a 2.30)
                                    if not (1.70 <= f_price <= 2.30): continue
                                except: continue

                                # Asignar a Local (Bovada suele poner el nombre del equipo o "Home")
                                if desc == 'Home' or home_team in desc:
                                    all_odds.append({
                                        "Periodo": clean_period,
                                        "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                        "Local": home_team,
                                        "Visita": away_team,
                                        "Hándicap Local": float(handicap),
                                        "Cuota": f_price
                                    })

    df = pd.DataFrame(all_odds)
    print(f"🏁 Escaneo finalizado. Total líneas encontradas: {len(df)}")
    return df
