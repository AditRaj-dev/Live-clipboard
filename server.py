from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import time
import asyncio
import uuid

app = FastAPI()

clients = set()
items = []
TTL_SECONDS = 60


# =========================
# WEBSOCKET (MUST BE FIRST)
# =========================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)

    try:
        # Send initial sync
        await ws.send_json({
            "type": "sync",
            "items": items
        })

        while True:
            data = await ws.receive_json()

            item = {
                "id": str(uuid.uuid4()),
                "type": data.get("type"),
                "data": data.get("data"),
                "name": data.get("name"),
                "created_at": time.time(),
            }

            items.append(item)

            # Broadcast add
            for c in list(clients):
                try:
                    await c.send_json({
                        "type": "add",
                        "item": item
                    })
                except:
                    clients.discard(c)

    except WebSocketDisconnect:
        clients.discard(ws)


# =========================
# TTL CLEANUP TASK
# =========================
async def cleanup_task():
    while True:
        await asyncio.sleep(5)
        now = time.time()

        new_items = [
            i for i in items
            if now - i["created_at"] < TTL_SECONDS
        ]

        if len(new_items) != len(items):
            items.clear()
            items.extend(new_items)

            for c in list(clients):
                try:
                    await c.send_json({
                        "type": "sync",
                        "items": items
                    })
                except:
                    clients.discard(c)


@app.on_event("startup")
async def startup():
    asyncio.create_task(cleanup_task())


# =========================
# STATIC FILES (LAST)
# =========================
app.mount("/", StaticFiles(directory="dist", html=True), name="static")
