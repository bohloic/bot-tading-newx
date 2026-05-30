import os
import sys
import collections
import asyncio
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from stable_baselines3 import PPO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engines.risk_engine import RiskAndAuditEngine
from app.services.broker.factory import BrokerFactory

runtime_storage = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = os.path.join("models", "ppo_trading_policy")
    if os.path.exists(model_path + ".zip"):
        runtime_storage["ppo_agent"] = PPO.load(model_path)
        print(f"[PRODUCTION] IA active. Modèle chargé.")
    yield
    runtime_storage.clear()

app = FastAPI(title="Moteur de Trading Autonome Résilient", lifespan=lifespan)

# Autoriser votre interface Frontend à communiquer avec FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En production, remplacez "*" par l'URL de votre frontend (ex: ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

risk_engine = RiskAndAuditEngine(initial_capital=10000.0, max_drawdown_limit=0.30)
# Commutateur universel : Changez simplement ici par "CRYPTO", "FOREX" ou "DERIV"
broker = BrokerFactory.get_broker("DERIV")

market_window = collections.deque(maxlen=10)

# Un ensemble pour store les connexions des interfaces frontend ouvertes
connected_frontends = set()

async def network_reconnect_loop():
    """
    Tâche de fond autonome chargée de surveiller et rétablir 
    la connexion avec l'API du Broker en cas de coupure internet.
    """
    while True:
        try:
            print("[RÉSEAU] Vérification de la liaison avec le Broker...")
            await broker.connect()
            break # Si la connexion réussit, on sort de la boucle de reconnexion
        except Exception as e:
            print(f"[PANNE RÉSEAU] Impossible de joindre le Broker : {e}. Nouvelle tentative dans 5 secondes...")
            await asyncio.sleep(5) # Attente de sécurité avant de réessayer

@app.on_event("startup")
async def startup_event():
    # Lance la tentative de connexion initiale de manière sécurisée au démarrage
    asyncio.create_task(network_reconnect_loop())

# FONCTION UTILITAIRE DE DIFFUSION
async def broadcast_to_frontend(message: dict):
    """Envoie les données et les ordres à tous les écrans frontend ouverts."""
    if connected_frontends:
        # Création des tâches d'envoi asynchrones pour ne pas ralentir l'IA
        await asyncio.gather(*[fs.send_json(message) for fs in connected_frontends], return_exceptions=True)

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "kill_switch_status": risk_engine.kill_switch_activated,
        "model_loaded": "ppo_agent" in runtime_storage,
        "memory_buffer_size": len(market_window),
        "connected_dashboards": len(connected_frontends)
    }

@app.websocket("/ws/trading-feed")
async def trading_feed_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Flux de marché connecté en local.")
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception:
                # Si le client local qui envoie les données coupe, on intercepte proprement
                break
                
            price = float(data["Price_Close"])
            tdi_rsi = float(data["TDI_RSI_Line"])
            mbl = float(data["TDI_Market_Baseline"])
            volume = float(data["Volume"])
            
            feature_row = [price, tdi_rsi, tdi_rsi, tdi_rsi, mbl, volume]
            market_window.append(feature_row)
            
            # Diffusion des indicateurs TDI au frontend pour la mise à jour des graphiques en direct
            await broadcast_to_frontend({
                "type": "MARKET_UPDATE",
                "price": price,
                "tdi_rsi": tdi_rsi,
                "mbl": mbl,
                "volume": volume
            })
            
            if len(market_window) < 10:
                await websocket.send_json({"status": "buffering", "current_size": len(market_window)})
                continue
                
            obs_array = np.array(market_window, dtype=np.float32)
            mean = np.mean(obs_array, axis=0)
            std = np.std(obs_array, axis=0) + 1e-8
            normalized_obs = (obs_array - mean) / std
            
            if "ppo_agent" in runtime_storage:
                action, _ = runtime_storage["ppo_agent"].predict(np.expand_dims(normalized_obs, axis=0), deterministic=True)
                action = int(action[0])
            else:
                action = 0
                
            # Gestion résiliente des appels de balance
            try:
                balance = await broker.get_account_balance()
            except Exception:
                print("[ALERTE RISK] Broker injoignable pour vérification de la balance. HOLD forcé.")
                # Lancement asynchrone de la boucle de reconnexion sans bloquer le thread principal
                asyncio.create_task(network_reconnect_loop())
                action = 0 
                balance = 10000.0 # Valeur de secours
                
            is_allowed = risk_engine.process_risk_check(current_equity=balance, proposed_action=action)
            
            if is_allowed:
                qty = risk_engine.calculate_position_size(current_price=price, current_balance=balance)
                side = "BUY" if action == 1 else "SELL"
                
                # Exécution sécurisée avec bloc d'interception des pannes en cours de trade
                try:
                    order_result = await broker.execute_order(symbol="R_75", side=side, qty=qty)
                    risk_engine.audit_trade(order_result)
                    
                    response_payload = {
                        "status": "order_placed", 
                        "action": side, 
                        "quantity": qty, 
                        "order_id": order_result.get("order_id")
                    }
                    await websocket.send_json(response_payload)
                    
                    # Envoi de l'ordre exécuté au frontend pour l'historique et les notifications
                    await broadcast_to_frontend({
                        "type": "ORDER_EXECUTED",
                        "action": side,
                        "quantity": qty,
                        "price": price,
                        "order_id": order_result.get("order_id"),
                        "balance": balance
                    })
                    
                except Exception as e:
                    print(f"[ERREUR CRITIQUE TRANSACTION] Échec de l'envoi de l'ordre : {e}")
                    asyncio.create_task(network_reconnect_loop())
            else:
                # Notification de monitoring simple au flux et au frontend si l'action est HOLD (0)
                monitor_payload = {"status": "monitoring", "ai_action": action, "risk_validated": False}
                await websocket.send_json(monitor_payload)
                
                await broadcast_to_frontend({
                    "type": "AI_MONITORING",
                    "ai_action": action,
                    "price": price
                })
                
    except WebSocketDisconnect:
        print("[WS] Déconnexion du flux local.")

@app.websocket("/ws/frontend-dashboard")
async def frontend_websocket_endpoint(websocket: WebSocket):
    """Point d'accès auquel votre interface utilisateur va se connecter."""
    await websocket.accept()
    connected_frontends.add(websocket)
    print(f"[FRONTEND] Nouveau tableau de bord connecté. Total : {len(connected_frontends)}")
    try:
        while True:
            # On maintient la connexion vivante
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_frontends.remove(websocket)
        print("[FRONTEND] Tableau de bord déconnecté.")