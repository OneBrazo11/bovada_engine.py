import requests
import pandas as pd
import time
import random

# HEADERS: Rotamos User-Agent para parecer más humanos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.bovada.lv/sports/basketball/nba',
    'Origin': 'https://www.bovada.lv'
}

def get_bovada_odds():
    all_odds = []
    print("🚀 INICIANDO ESCANEO BOVADA (MODO DEBUG)...")

    # 1. Obtener Menú Principal
    main_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"
    try:
        r = requests.get(main_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"❌ Error conectando al menú principal: {r.status_code}")
            return pd.DataFrame()
        main_data = r.json()
    except Exception as e:
        print(f"🔥 Error crítico de conexión: {e}")
        return pd.DataFrame()

    # 2. Recorrer cada partido
    for coupon in main_data:
        if 'events' not in coupon: continue
        
        for event in coupon['events']:
            title = event.get('description', 'Desconocido')
            link = event.get('link')
            is_live = event.get('live', False)
            
            # Intentar obtener nombres de equipos, pero no bloquear si falla
            try:
                teams = title.split(' @ ')
                if len(teams) == 2:
                    away_team_name, home_team_name = teams
                else:
                    away_team_name, home_team_name = "Visitante", "Local"
            except:
                away_team_name, home_team_name = "Visitante", "Local"

            print(f"🔎 Analizando: {title}")

            events_to_process = [event] # Por defecto, lo que tenemos a mano

            # --- DEEP SCAN (Para cuartos y mitades) ---
            if link:
                try:
                    if not link.startswith('/'): link = f"/{link}"
                    deep_url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}"
                    
                    # Aumentamos el tiempo de espera para evitar bloqueos (0.5 a 1.5 seg)
                    time.sleep(random.uniform(0.5, 1.2)) 
                    
                    r_deep = requests.get(deep_url, headers=HEADERS, timeout=8)
                    
                    if r_deep.status_code == 200:
                        deep_data = r_deep.json()
                        if deep_data and isinstance(deep_data, list) and 'events' in deep_data[0]:
                            events_to_process = deep_data[0]['events']
                        else:
                            print(f"   ⚠️ JSON profundo vacío o formato inesperado para {title}")
                    else:
                        print(f"   ⚠️ Falló Deep Scan (Status {r_deep.status_code}) - Usando datos básicos")
                except Exception as e:
                    print(f"   ⚠️ Error conexión Deep Scan: {e}")

            # 3. Procesar Mercados
            found_markets = False
            for ev in events_to_process:
                if 'displayGroups' not in ev: continue
                
                for group in ev['displayGroups']:
                    raw_period = group.get('description', '')
                    
                    # FILTRO DE PERIODOS
                    clean_period = None
                    if "Game Lines" in raw_period: clean_period = "Game Lines"
                    elif any(x in raw_period for x in ["1st Quarter", "1Q"]): clean_period = "1st Quarter"
                    elif any(x in raw_period for x in ["2nd Quarter", "2Q"]): clean_period = "2nd Quarter"
                    elif any(x in raw_period for x in ["3rd Quarter", "3Q"]): clean_period = "3rd Quarter"
                    elif any(x in raw_period for x in ["4th Quarter", "4Q"]): clean_period = "4th Quarter"
                    elif any(x in raw_period for x in ["1st Half", "1H"]): clean_period = "1st Half"
                    elif any(x in raw_period for x in ["2nd Half", "2H"]): clean_period = "2nd Half"

                    if not clean_period: continue

                    for market in group['markets']:
                        # Filtro de mercado más flexible (Busca "Spread" O "Handicap")
                        market_desc = market.get('description', '')
                        if not any(x in market_desc for x in ["Point Spread", "Spread", "Handicap"]):
                            continue

                        for outcome in market['outcomes']:
                            price = outcome['price'].get('decimal')
                            handicap = outcome['price'].get('handicap')
                            outcome_type = outcome.get('type') # 'H' = Home, 'A' = Away
                            outcome_desc = outcome.get('description', '')

                            if not price or not handicap: continue
                            
                            try:
                                f_price = float(price)
                                # Filtro de cuota (1.70 - 2.30)
                                if not (1.70 <= f_price <= 2.30): 
                                    continue 
                            except: continue

                            # LOGICA DE EQUIPOS MEJORADA (Usamos 'type' si existe)
                            team_type = "Desconocido"
                            
                            if outcome_type == 'H':
                                team_type = "Local"
                            elif outcome_type == 'A':
                                team_type = "Visita"
                            else:
                                # Fallback a comparación de texto si 'type' no existe
                                if home_team_name in outcome_desc or "Home" in outcome_desc:
                                    team_type = "Local"
                                elif away_team_name in outcome_desc or "Away" in outcome_desc:
                                    team_type = "Visita"

                            # Solo guardamos si es Local (para mantener tu lógica original)
                            if team_type == "Local":
                                found_markets = True
                                all_odds.append({
                                    "Periodo": clean_period,
                                    "Estado": "🔴 LIVE" if is_live else "🕒 Pre",
                                    "Local": home_team_name,
                                    "Visita": away_team_name,
                                    "Hándicap Local": float(handicap),
                                    "Cuota": f_price
                                })

            if not found_markets:
                print(f"   ⚠️ No se encontraron líneas válidas para {title} (Verifica filtros de cuota/mercado)")

    df = pd.DataFrame(all_odds)
    print(f"🏁 Escaneo finalizado. Total líneas encontradas: {len(df)}")
    if not df.empty:
        print(df.head()) # Muestra las primeras líneas encontradas
    return df

# Ejecutar para probar
if __name__ == "__main__":
    df = get_bovada_odds()
