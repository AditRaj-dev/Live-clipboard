docker run -p 5000:5000 live-clipboard
📋 **Live Clipboard**

A self-hosted, real-time, cross-device clipboard that syncs text, images, and files instantly across devices using WebSockets, with:

⏱️ Automatic expiry (TTL)

🧩 Multiple clipboard items

🌐 Cloudflare Tunnel for public access

🖥️ Windows tray app (single EXE)

🐳 Dockerized backend

⚡ React frontend (no refresh needed)

---

## ✨ Features

✅ Real-time clipboard sync (text & images)

✅ Multiple clipboard items in a grid

✅ Auto-expire items after 1 minute

✅ Live TTL progress animation

✅ Drag & drop + paste support

✅ QR pairing for other devices

✅ WebSocket-based (instant updates)

✅ Self-hosted (no third-party clipboard services)

✅ Works across different networks via Cloudflare

✅ Windows system-tray app (no terminal windows)

✅ Single-instance protection

---

## 🏗️ Architecture

```
Windows Tray App (EXE)
 ├─ Starts Docker container
 ├─ Pushes local clipboard → server
 ├─ Starts Cloudflare tunnel
 └─ Lives in system tray

Docker Container
 ├─ FastAPI backend
 ├─ WebSocket server (/ws)
 └─ Serves React build (dist/)

React Client
 ├─ Drag & drop / paste
 ├─ Live grid of clipboard items
 └─ TTL animation
```

---

## 📁 Project Structure

```
clipboard-server/
│
├─ server.py              # FastAPI + WebSocket server
├─ Dockerfile             # Docker image for server
├─ requirements.txt       # Python dependencies
│
├─ tray_app.py            # Windows tray app (Python)
├─ cloudflared.exe        # Cloudflare tunnel binary
│
├─ client/                # React app source
│   ├─ src/App.jsx
│   └─ ...
│
├─ dist/                  # Built React app (served by FastAPI)
│
└─ README.md
```

---

## 🚀 Running Locally (Without Cloudflare)

**1️⃣ Build the React client**

```bash
cd client
npm install
npm run build
```

Copy the generated `dist/` folder into `clipboard-server/dist`.

**2️⃣ Build & run the Docker server**

```bash
docker build -t live-clipboard .
docker rm -f clipboard
docker run -d -p 9000:9000 --name clipboard live-clipboard
```

**3️⃣ Open in browser**

http://localhost:9000

Status should show **Connected**.

---

## 🌐 Exposing Publicly with Cloudflare Tunnel

**Quick tunnel (no account required):**

```bash
cloudflared tunnel --url http://localhost:9000
```

You’ll get a URL like:

`https://something.trycloudflare.com`

Open it on any device — WebSockets work automatically.

---

## 🖥️ Windows Tray App (EXE)

The tray app:

- Starts Docker container
- Pushes Windows clipboard automatically
- Starts Cloudflare tunnel
- Runs silently in the system tray

**Build the EXE:**

```bash
C:\Users\study\AppData\Roaming\Python\Python313\Scripts\pyinstaller.exe \
  --onefile \
  --noconsole \
  --name LiveClipboard \
  --hidden-import=pystray._win32 \
  tray_app.py
```

**Output:**

`dist/LiveClipboard.exe`

Double-click to run.

---

## ⏱️ Clipboard Expiry (TTL)

- Each clipboard item lives for 60 seconds
- Progress bar shows remaining time
- Items auto-remove and sync across all clients
- TTL logic is handled server-side and reflected live on clients.

---

## 🔌 WebSocket Endpoint

`ws://<host>/ws`

**Message types:**

- `sync` → full state sync
- `add` → new clipboard item

---

## 🛡️ Notes & Limitations

- Clipboard auto-push works only on Windows (tray app)
- Clipboard permissions required in browsers for paste
- Cloudflare quick tunnels are temporary (URL changes)
- For permanent URLs, use a named Cloudflare tunnel + domain

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, WebSockets, Python
- **Frontend:** React, Vite
- **Packaging:** Docker, PyInstaller
- **Networking:** Cloudflare Tunnel
- **OS Integration:** pystray, pyperclip, Pillow

---

## 📌 Future Improvements

🔐 End-to-end encryption

📥 File download support

📌 Pin clipboard items (ignore TTL)

👥 Multi-user rooms

📱 Native Android client

⚙️ Configurable TTL

---

## 📄 License

MIT — use, modify, and self-host freely.

---

If you want, I can also:

- Add badges (Docker, WebSocket, Windows)
- Write a short project description for GitHub
- Create a demo GIF
- Help you publish this as an open-source project

Just say the word 👍