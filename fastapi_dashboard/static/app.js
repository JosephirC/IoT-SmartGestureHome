const portSelect = document.getElementById("portSelect");
const refreshBtn = document.getElementById("refreshPorts");
const connectBtn = document.getElementById("connectBtn");
const baudInput = document.getElementById("baudInput");
const statusEl = document.getElementById("status");
const lastActionEl = document.getElementById("lastAction");

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

async function loadPorts() {
  statusEl.textContent = "Scanning ports...";
  try {
    const data = await fetchJSON("/api/ports");
    portSelect.innerHTML = "";
    if (!data.ports || data.ports.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No ports found";
      opt.disabled = true;
      portSelect.appendChild(opt);
      statusEl.textContent = "Plug in your Arduino and refresh.";
      return;
    }
    data.ports.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.device;
      opt.textContent = `${p.device} – ${p.description}`;
      portSelect.appendChild(opt);
    });
    statusEl.textContent = "Select a port and connect.";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}

async function connect() {
  const port = portSelect.value;
  const baudrate = Number(baudInput.value) || 9600;
  statusEl.textContent = "Connecting...";
  try {
    const res = await fetchJSON("/api/connect", {
      method: "POST",
      body: JSON.stringify({ port, baudrate }),
    });
    statusEl.textContent = `Connected to ${res.port} @ ${res.baudrate} baud`;
  } catch (err) {
    statusEl.textContent = `Connect failed: ${err.message}`;
  }
}

async function sendAction(action) {
  try {
    const res = await fetchJSON("/api/command", {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    lastActionEl.textContent = `Sent ${res.action}`;
  } catch (err) {
    lastActionEl.textContent = `Error: ${err.message}`;
  }
}

refreshBtn.addEventListener("click", loadPorts);
connectBtn.addEventListener("click", connect);

document.querySelectorAll("[data-action]").forEach((btn) => {
  btn.addEventListener("click", () => sendAction(btn.dataset.action));
});

loadPorts();
