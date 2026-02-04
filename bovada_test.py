import requests
import json

# Headers "Humanos"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.bovada.lv/',
}

URL = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba"

print(f"--- PROBANDO CONEXIÓN A: {URL} ---")

try:
    r = requests.get(URL, headers=HEADERS, timeout=10)
    
    print(f"ESTADO HTTP: {r.status_code}")
    
    if r.status_code == 403:
        print("🔴 BLOQUEADO. Bovada detectó que eres un script (Cloudflare/Incapsula).")
        print("SOLUCIÓN: Necesitas usar 'cloudscraper' o Selenium, 'requests' ya no sirve solo.")
    
    elif r.status_code == 200:
        data = r.json()
        print("🟢 CONEXIÓN EXITOSA. Analizando datos recibidos...")
        
        # Verificar si hay eventos dentro
        event_count = 0
        if isinstance(data, list):
            for coupon in data:
                events = coupon.get('events', [])
                event_count += len(events)
                if len(events) > 0:
                    print(f"   -> Encontrado evento: {events[0].get('description')}")
        
        print(f"TOTAL EVENTOS EN RAW: {event_count}")
        
        if event_count == 0:
            print("⚠️ EL JSON ESTÁ VACÍO. Entraste, pero Bovada dice que no hay partidos en esta URL.")
    
    else:
        print(f"⚠️ ERROR RARO: {r.text[:200]}")

except Exception as e:
    print(f"❌ ERROR DE EJECUCIÓN: {e}")
