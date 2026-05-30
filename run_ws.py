import asyncio

from app.websocket.bybit_ws import BybitWebSocket


async def main():

    ws = BybitWebSocket()

    await ws.connect()


if __name__ == "__main__":

    asyncio.run(main())