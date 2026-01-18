# ===============================
# SINGLE INSTANCE LOCK
# ===============================
import socket
import sys

lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    lock_socket.bind(("127.0.0.1", 65432))
except OSError:
    sys.exit(0)

# ===============================
# IMPORTS
# ===============================
import subprocess
import threading
import time
import webbrowser
import re
import json
import base64
import io
import hashlib
import asyncio
import os

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageGrab
import pyperclip
import websockets

# ===============================
# WINDOWS ASYNCIO FIX (CRITICAL)
# ===============================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ===============================
# CONFIG
# ===============================
IMAGE_NAME = "live-clipboard"
CONTAINER_NAME = "clipboard"
PORT = 9000
SERVER_WS = f"ws://localhost:{PORT}/ws"

CLOUDFLARED_PATH = r"C:\tools\cloudflared.exe"

# ===============================
# GLOBAL STATE
# ===============================
cloudflared_proc = None
public_url = None
running = True
last_clip_hash = None

# ===============================
# UTIL
# ===============================
def run(cmd):
    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False
    )

# ===============================
# DOCKER
# ===============================
def start_docker():
    run(["docker", "rm", "-f", CONTAINER_NAME])
    run([
        "docker", "run", "-d",
        "-p", f"{PORT}:{PORT}",
        "--name", CONTAINER_NAME,
        IMAGE_NAME
    ])

# ===============================
# CLOUDFLARE TUNNEL
# ===============================
def start_cloudflare():
    global cloudflared_proc, public_url

    if not os.path.exists(CLOUDFLARED_PATH):
        return

    cloudflared_proc = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    for line in cloudflared_proc.stdout:
        match = re.search(r"https://[^\s]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            break

# ===============================
# CLIPBOARD CLIENT
# ===============================
def hash_bytes(b: bytes):
    return hashlib.sha256(b).hexdigest()

def get_clipboard_image():
    try:
        img = ImageGrab.grabclipboard()
        if img:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except:
        pass
    return None

async def clipboard_loop():
    global last_clip_hash

    while running:
        try:
            async with websockets.connect(
                SERVER_WS,
                max_size=20 * 1024 * 1024
            ) as ws:

                while running:
                    # TEXT
                    text = pyperclip.paste()
                    if isinstance(text, str) and text.strip():
                        h = hash_bytes(text.encode())
                        if h != last_clip_hash:
                            await ws.send(json.dumps({
                                "type": "text",
                                "data": text
                            }))
                            last_clip_hash = h

                    # IMAGE
                    img_bytes = get_clipboard_image()
                    if img_bytes:
                        h = hash_bytes(img_bytes)
                        if h != last_clip_hash:
                            await ws.send(json.dumps({
                                "type": "image",
                                "name": "clipboard.png",
                                "data": base64.b64encode(img_bytes).decode()
                            }))
                            last_clip_hash = h

                    await asyncio.sleep(0.5)

        except:
            await asyncio.sleep(2)

def start_clipboard_client():
    threading.Thread(
        target=lambda: asyncio.run(clipboard_loop()),
        daemon=True
    ).start()

# ===============================
# STARTUP / SHUTDOWN
# ===============================
def startup():
    time.sleep(2)
    start_docker()
    time.sleep(3)
    start_clipboard_client()
    start_cloudflare()

def shutdown():
    global running
    running = False

    if cloudflared_proc:
        cloudflared_proc.terminate()

    run(["docker", "rm", "-f", CONTAINER_NAME])
    icon.stop()

# ===============================
# TRAY ACTIONS
# ===============================
def open_ui(icon, item):
    if public_url:
        webbrowser.open(public_url)

def copy_url(icon, item):
    if public_url:
        pyperclip.copy(public_url)

def restart(icon, item):
    shutdown()
    time.sleep(2)
    threading.Thread(target=startup, daemon=True).start()

def quit_app(icon, item):
    shutdown()

# ===============================
# TRAY ICON
# ===============================
def create_icon():
    img = Image.new("RGB", (64, 64), "#0f172a")
    d = ImageDraw.Draw(img)
    d.rectangle((12, 12, 52, 52), outline="#3b82f6", width=4)
    return img

menu = pystray.Menu(
    item("Open Web UI", open_ui),
    item("Copy Public URL", copy_url),
    item("Restart Services", restart),
    item("Quit", quit_app)
)

icon = pystray.Icon(
    "Live Clipboard",
    create_icon(),
    "Live Clipboard",
    menu
)

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    threading.Thread(target=startup, daemon=True).start()
    icon.run()
