import sys
import subprocess
import time

def auto_instalar():
    print("🔧 MODO REPARACIÓN ACTIVADO")
    print("⏳ Instalando la herramienta 'cloudscraper'... Por favor espera...")
    
    try:
        # Esto obliga al Python actual a instalar la librería
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cloudscraper"])
        print("\n✅ ¡ÉXITO! La herramienta se instaló correctamente.")
        print("👉 AHORA: Borra este código y pega el código del BOT que te di antes.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error: {e}")
        print("Avísame qué dice este error.")
    
    time.sleep(10) # Pausa para que leas el mensaje

if __name__ == "__main__":
    auto_instalar()
