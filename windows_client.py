import asyncio
import base64
import hashlib
import io
import json
import time

import pyperclip
import websockets
from PIL import ImageGrab

# =========================
# CONFIG
# =========================
SERVER_URL = "ws://localhost:9000/ws"  # change if needed
POLL_INTERVAL = 0.5  # seconds

# =========================
# HELPERS
# =========================
def hash_data(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def get_clipboard_image():
    try:
        img = ImageGrab.grabclipboard()
        if img:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
    except Exception:
        pass
    return None

# =========================
# MAIN LOOP
# =========================
async def clipboard_watcher():
    last_hash = None

    async with websockets.connect(SERVER_URL, max_size=20 * 1024 * 1024) as ws:
        print("✅ Connected to clipboard server")

        while True:
            # ----- TEXT -----
            try:
                text = pyperclip.paste()
                if isinstance(text, str) and text.strip():
                    data = text.encode()
                    h = hash_data(data)

                    if h != last_hash:
                        await ws.send(json.dumps({
                            "type": "text",
                            "data": text
                        }))
                        last_hash = h
                        print("📋 Text pushed")
            except Exception:
                pass

            # ----- IMAGE -----
            img_bytes = get_clipboard_image()
            if img_bytes:
                h = hash_data(img_bytes)
                if h != last_hash:
                    await ws.send(json.dumps({
                        "type": "image",
                        "name": "clipboard.png",
                        "data": base64.b64encode(img_bytes).decode()
                    }))
                    last_hash = h
                    print("🖼️ Image pushed")

            await asyncio.sleep(POLL_INTERVAL)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    print("🔄 Clipboard watcher started")
    asyncio.run(clipboard_watcher())
