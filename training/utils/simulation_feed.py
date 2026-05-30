import asyncio
import json
import websockets
import random

async def simulate_market_feed():
    uri = "ws://127.0.0.1:8000/ws/trading-feed"
    print(f"[SIMULATEUR] Tentative de connexion au serveur FastAPI sur {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[SIMULATEUR] Connecté au serveur ! Envoi du flux TDI en cours...")
            
            # Simulation d'une tendance de prix de départ
            price = 0.6500
            
            # Boucle d'envoi de 50 ticks (ajustable)
            for tick in range(1, 51):
                # Simulation d'une micro-évolution du prix et des indicateurs TDI
                price += random.uniform(-0.002, 0.002)
                tdi_rsi = random.uniform(0.30, 0.70)  # RSI entre 30 et 70
                mbl = random.uniform(0.45, 0.55)      # Baseline stable autour de 50
                volume = random.uniform(0.10, 0.90)
                
                payload = {
                    "Price_Close": round(price, 4),
                    "TDI_RSI_Line": round(tdi_rsi, 3),
                    "TDI_Market_Baseline": round(mbl, 3),
                    "Volume": round(volume, 3)
                }
                
                print(f"\n[TICK #{tick}] Envoi des données : Price={payload['Price_Close']} | TDI_RSI={payload['TDI_RSI_Line']}")
                await websocket.send(json.dumps(payload))
                
                # Attente de la réponse de l'API FastAPI (Inférence de l'IA et décision du Risk Engine)
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"[REPONSE API] : {response_data}")
                
                # Temporisation pour simuler des bougies de scalping ultra-rapides (1 seconde)
                await asyncio.sleep(1)
                
            print("\n[SIMULATEUR] Fin du flux de simulation.")
            
    except Exception as e:
        print(f"[ERREUR SIMULATEUR] Impossible de communiquer avec l'API : {e}")

if __name__ == "__main__":
    # Lancement de la boucle asynchrone
    asyncio.run(simulate_market_feed())