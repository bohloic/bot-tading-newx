from fastapi import FastAPI
from app.api.webhook import router as webhook_router
from app.api.ws import router as ws_router

app = FastAPI(title="AI Trading Engine")

app.include_router(webhook_router)
app.include_router(ws_router)


@app.get("/")
def health():
    return {"status": "running"}