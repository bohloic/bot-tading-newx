from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/market")
async def market_socket(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_json()

        # ici tu peux :
        # - update features
        # - push vers PPO
        # - store buffer

        await websocket.send_json({
            "status": "received",
            "price": data["price"]
        })