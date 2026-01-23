// ============================================================
// Elements DOM
// ============================================================

// Connexion serie
const portSelect = document.getElementById("portSelect");
const refreshBtn = document.getElementById("refreshPorts");
const connectBtn = document.getElementById("connectBtn");
const baudInput = document.getElementById("baudInput");
const statusEl = document.getElementById("status");
const lastActionEl = document.getElementById("lastAction");

// MCP
const mcpConnectBtn = document.getElementById("mcpConnectBtn");
const mcpDisconnectBtn = document.getElementById("mcpDisconnectBtn");
const mcpStatusEl = document.getElementById("mcpStatus");

// Log
const logContainer = document.getElementById("logContainer");
const clearLogBtn = document.getElementById("clearLogBtn");

// WebSocket
let ws = null;

// ============================================================
// Utilitaires
// ============================================================

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || res.statusText);
  }
  return res.json();
}

function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// ============================================================
// Connexion Serie
// ============================================================

async function loadPorts() {
  statusEl.textContent = "Scan des ports...";
  try {
    const data = await fetchJSON("/api/ports");
    portSelect.innerHTML = "";
    if (!data.ports || data.ports.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "Aucun port trouve";
      opt.disabled = true;
      portSelect.appendChild(opt);
      statusEl.textContent = "Branchez l'Arduino et actualisez.";
      return;
    }
    data.ports.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.device;
      opt.textContent = `${p.device} - ${p.description}`;
      portSelect.appendChild(opt);
    });
    statusEl.textContent = "Selectionnez un port et connectez.";
  } catch (err) {
    statusEl.textContent = `Erreur: ${err.message}`;
  }
}

async function connect() {
  const port = portSelect.value;
  const baudrate = Number(baudInput.value) || 9600;
  statusEl.textContent = "Connexion...";
  try {
    const res = await fetchJSON("/api/connect", {
      method: "POST",
      body: JSON.stringify({ port, baudrate }),
    });
    statusEl.textContent = `Connecte a ${res.port} @ ${res.baudrate} baud`;
    statusEl.classList.add("connected");
  } catch (err) {
    statusEl.textContent = `Echec: ${err.message}`;
    statusEl.classList.remove("connected");
  }
}

async function sendAction(action) {
  try {
    const res = await fetchJSON("/api/command", {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    lastActionEl.textContent = `Envoye: ${res.action}`;
  } catch (err) {
    lastActionEl.textContent = `Erreur: ${err.message}`;
  }
}

// ============================================================
// MCP
// ============================================================

async function mcpConnect() {
  mcpStatusEl.textContent = "Connexion MCP...";
  mcpConnectBtn.disabled = true;
  try {
    await fetchJSON("/mcp/connect", { method: "POST" });
    mcpStatusEl.textContent = "MCP connecte";
    mcpStatusEl.classList.add("connected");
    mcpConnectBtn.disabled = true;
    mcpDisconnectBtn.disabled = false;
    enableMcpTools(true);
  } catch (err) {
    mcpStatusEl.textContent = `Echec MCP: ${err.message}`;
    mcpStatusEl.classList.remove("connected");
    mcpConnectBtn.disabled = false;
  }
}

async function mcpDisconnect() {
  try {
    await fetchJSON("/mcp/disconnect", { method: "POST" });
    mcpStatusEl.textContent = "MCP deconnecte";
    mcpStatusEl.classList.remove("connected");
    mcpConnectBtn.disabled = false;
    mcpDisconnectBtn.disabled = true;
    enableMcpTools(false);
  } catch (err) {
    mcpStatusEl.textContent = `Erreur: ${err.message}`;
  }
}

async function mcpCallTool(tool, action) {
  try {
    const res = await fetchJSON("/mcp/call", {
      method: "POST",
      body: JSON.stringify({ tool, action }),
    });
    if (res.success) {
      addLogEntry({
        type: "success",
        tool,
        action,
        result: res.result,
        timestamp: new Date().toISOString(),
      });
    } else {
      addLogEntry({
        type: "error",
        tool,
        action,
        result: res.error,
        timestamp: new Date().toISOString(),
      });
    }
  } catch (err) {
    addLogEntry({
      type: "error",
      tool,
      action,
      result: err.message,
      timestamp: new Date().toISOString(),
    });
  }
}

function enableMcpTools(enabled) {
  document.querySelectorAll("[data-mcp-tool]").forEach((btn) => {
    btn.disabled = !enabled;
  });
}

async function checkMcpStatus() {
  try {
    const res = await fetchJSON("/mcp/status");
    if (res.connected) {
      mcpStatusEl.textContent = "MCP connecte";
      mcpStatusEl.classList.add("connected");
      mcpConnectBtn.disabled = true;
      mcpDisconnectBtn.disabled = false;
      enableMcpTools(true);
    } else {
      mcpStatusEl.textContent = "MCP non connecte";
      mcpStatusEl.classList.remove("connected");
      mcpConnectBtn.disabled = false;
      mcpDisconnectBtn.disabled = true;
      enableMcpTools(false);
    }
  } catch (err) {
    mcpStatusEl.textContent = "Erreur verification MCP";
  }
}

// ============================================================
// Live Log
// ============================================================

function addLogEntry(event) {
  // Supprimer le message "aucun evenement" si present
  const emptyMsg = logContainer.querySelector(".log-empty");
  if (emptyMsg) {
    emptyMsg.remove();
  }

  const entry = document.createElement("div");
  entry.className = `log-entry ${event.type || "info"}`;

  const time = document.createElement("span");
  time.className = "log-time";
  time.textContent = formatTime(event.timestamp);

  const content = document.createElement("span");
  content.className = "log-content";

  if (event.tool) {
    content.innerHTML = `<strong>${event.tool}</strong>(${event.action || ""}) → ${event.result || ""}`;
  } else if (event.message) {
    content.textContent = event.message;
  } else {
    content.textContent = JSON.stringify(event);
  }

  entry.appendChild(time);
  entry.appendChild(content);

  // Ajouter en haut du log
  logContainer.insertBefore(entry, logContainer.firstChild);

  // Limiter a 50 entrees
  while (logContainer.children.length > 50) {
    logContainer.removeChild(logContainer.lastChild);
  }
}

function clearLog() {
  logContainer.innerHTML = '<div class="log-empty">Log efface.</div>';
  fetchJSON("/mcp/log", { method: "DELETE" }).catch(() => {});
}

async function loadLogHistory() {
  try {
    const res = await fetchJSON("/mcp/log");
    if (res.events && res.events.length > 0) {
      // Vider le log
      logContainer.innerHTML = "";
      // Ajouter les evenements (les plus recents d'abord)
      res.events.reverse().forEach((event) => {
        addLogEntry(event);
      });
    }
  } catch (err) {
    console.error("Erreur chargement historique:", err);
  }
}

// ============================================================
// WebSocket
// ============================================================

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/log`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connecte");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === "history") {
        // Historique recu a la connexion
        logContainer.innerHTML = "";
        data.events.reverse().forEach((e) => addLogEntry(e));
      } else if (data.type === "mcp_call") {
        // Nouvel appel MCP
        addLogEntry({
          type: data.result?.success ? "success" : "error",
          tool: data.tool,
          action: data.action,
          result: data.result?.result || data.result?.error,
          timestamp: new Date().toISOString(),
        });
      } else if (data.type === "system") {
        // Message systeme
        addLogEntry({
          type: "system",
          message: data.message,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error("Erreur parsing WebSocket:", err);
    }
  };

  ws.onclose = () => {
    console.log("WebSocket deconnecte, reconnexion...");
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error("Erreur WebSocket:", err);
  };
}

// ============================================================
// Event Listeners
// ============================================================

refreshBtn.addEventListener("click", loadPorts);
connectBtn.addEventListener("click", connect);

document.querySelectorAll("[data-action]").forEach((btn) => {
  btn.addEventListener("click", () => sendAction(btn.dataset.action));
});

mcpConnectBtn.addEventListener("click", mcpConnect);
mcpDisconnectBtn.addEventListener("click", mcpDisconnect);

document.querySelectorAll("[data-mcp-tool]").forEach((btn) => {
  btn.addEventListener("click", () => {
    mcpCallTool(btn.dataset.mcpTool, btn.dataset.mcpAction);
  });
});

clearLogBtn.addEventListener("click", clearLog);

// ============================================================
// Initialisation
// ============================================================

loadPorts();
checkMcpStatus();
loadLogHistory();
connectWebSocket();
