import { useEffect, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";
import "./App.css";

const TTL_MS = 60 * 1000;

function App() {
  const wsRef = useRef(null);
  const fileInputRef = useRef(null);

  const WS_URL =
    (window.location.protocol === "https:" ? "wss://" : "ws://") +
    window.location.host +
    "/ws";

  const pairingUrl = window.location.origin;

  const [status, setStatus] = useState("Disconnected");
  const [items, setItems] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [textInput, setTextInput] = useState("");

  // =========================
  // WEBSOCKET
  // =========================
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setStatus("Connected");

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);

      if (msg.type === "sync") {
        setItems(msg.items || []);
      }

      if (msg.type === "add") {
        setItems((prev) => [...prev, msg.item]);
      }
    };

    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    return () => ws.close();
  }, []);

  /* =====================
     CLIPBOARD PASTE LOGIC
     ===================== */
  const pasteFromClipboard = async () => {
    try {
      const clipboardItems = await navigator.clipboard.read();

      for (const item of clipboardItems) {
        if (item.types.includes("image/png")) {
          const blob = await item.getType("image/png");
          const reader = new FileReader();

          reader.onload = () => {
            wsRef.current.send(
              JSON.stringify({
                type: "image",
                name: "clipboard.png",
                data: reader.result.split(",")[1],
              })
            );
          };

          reader.readAsDataURL(blob);
          return;
        }
      }

      const text = await navigator.clipboard.readText();
      if (text.trim()) {
        wsRef.current.send(
          JSON.stringify({
            type: "text",
            data: text,
          })
        );
      }
    } catch {
      alert(
        "Clipboard access denied.\n\n" +
          "• Click Paste button\n" +
          "• Use Chrome / Edge\n" +
          "• Allow clipboard permissions"
      );
    }
  };

  const processFile = (file) => {
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert("File too large (max 10MB)");
      return;
    }

    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = () => {
        wsRef.current.send(
          JSON.stringify({
            type: "image",
            name: file.name,
            data: reader.result.split(",")[1],
          })
        );
      };
      reader.readAsDataURL(file);
      return;
    }

    if (file.type.startsWith("text/")) {
      const reader = new FileReader();
      reader.onload = () => {
        wsRef.current.send(
          JSON.stringify({
            type: "text",
            name: file.name,
            data: reader.result,
          })
        );
      };
      reader.readAsText(file);
      return;
    }

    wsRef.current.send(
      JSON.stringify({
        type: "file",
        name: file.name,
        size: file.size,
        mime: file.type,
      })
    );
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    processFile(e.dataTransfer.files[0]);
  };

  const sendText = () => {
    if (!textInput.trim()) return;

    wsRef.current.send(
      JSON.stringify({
        type: "text",
        data: textInput,
      })
    );
    setTextInput("");
  };

  return (
    <div className="app">
      <header>
        <h1>Live Clipboard</h1>
        <span className={`status ${status.toLowerCase()}`}>
          {status}
        </span>
      </header>

      {/* QR PAIRING */}
      <div className="pairing">
        <div className="pairing-text">Scan to open on another device</div>
        <QRCodeCanvas
          value={pairingUrl}
          size={140}
          bgColor="#020617"
          fgColor="#e5e7eb"
        />
        <div className="pairing-url">{pairingUrl}</div>
      </div>

      {/* ACTION BAR */}
      <div className="action-bar">
        <button className="paste-btn" onClick={pasteFromClipboard}>
          📋 Paste from Clipboard
        </button>
      </div>

      {/* TEXT INPUT */}
      <div className="text-box">
        <textarea
          placeholder="Paste or type text here…"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.ctrlKey && e.key === "Enter") sendText();
          }}
        />
        <button onClick={sendText}>Send Text</button>
      </div>

      {/* DROP ZONE */}
      <div
        className={`dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <div className="drop-content">
          <div className="icon">📁</div>
          <p>Drag & drop or click to browse</p>
          <span className="hint">Images, text, files</span>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        hidden
        onChange={(e) => processFile(e.target.files[0])}
      />

      {/* PREVIEW GRID */}
      <div className="preview-grid">
        {items.map((item) => (
          <PreviewItem key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

/* =========================
   PREVIEW ITEM
   ========================= */
function PreviewItem({ item }) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const i = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(i);
  }, []);

  const created = item.created_at * 1000;
  const remaining = Math.max(0, TTL_MS - (now - created));
  const progress = remaining / TTL_MS;

  return (
    <div
      className="preview-item"
      style={{
        opacity: Math.max(0.4, progress),
        transform: `scale(${0.95 + progress * 0.05})`,
      }}
    >
      {item.type === "image" && (
        <img src={`data:image/*;base64,${item.data}`} />
      )}

      {item.type === "text" && <pre>{item.data}</pre>}

      <div className="ttl-bar">
        <div
          className="ttl-progress"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      <div className="ttl-label">
        {Math.ceil(remaining / 1000)}s left
      </div>
    </div>
  );
}

export default App;
