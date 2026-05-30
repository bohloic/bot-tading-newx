from fastapi import APIRouter
from app.core.decision import get_signal

router = APIRouter()

@router.post("/webhook")
async def webhook(data: dict):

    """
    Data from TradingView:
    {
        "price": 0.652,
        "tdi_rsi": 0.58,
        "volume": 0.45
    }
    """

    signal = get_signal(data)

    return {
        "action": signal["action"],
        "confidence": signal["confidence"]
    }