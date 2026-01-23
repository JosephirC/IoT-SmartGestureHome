import asyncio
import os
from typing import List, Optional

import serial
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from serial.tools import list_ports

from mcp_client import get_mcp_client, get_event_log, clear_event_log

AVAILABLE_ACTIONS = {
    "OPEN_DOOR",
    "CLOSE_DOOR",
    "TURN_ON_FAN",
    "TURN_OFF_FAN",
    "TURN_ON_LIGHTS",
    "TURN_OFF_LIGHTS",
}


class ConnectRequest(BaseModel):
    port: str = Field(..., description="Serial port path (e.g. COM3 or /dev/ttyACM0)")
    baudrate: int = Field(9600, description="Baud rate used by the Arduino sketch")


class CommandRequest(BaseModel):
    action: str = Field(..., description="One of the supported actions")


class MCPInvokeRequest(BaseModel):
    name: str = Field(..., description="Action name matching the Arduino command set")
    args: Optional[dict] = Field(default=None, description="Unused, reserved for future")


class MCPToolRequest(BaseModel):
    tool: str = Field(..., description="Tool name: control_door, control_fans, control_leds")
    action: str = Field(..., description="Action: OPEN/CLOSE for door, ON/OFF for fans/leds")


# ============================================================
# WebSocket Manager pour le live log
# ============================================================


class WebSocketManager:
    """Gère les connexions WebSocket pour le live log."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envoie un message à tous les clients connectés."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


ws_manager = WebSocketManager()


class SerialManager:
    """Keeps a single serial connection alive for the app."""

    def __init__(self) -> None:
        self._serial: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self.baudrate: int = 9600

    def list_ports(self) -> List[dict]:
        return [
            {"device": p.device, "description": p.description or ""}
            for p in list_ports.comports()
        ]

    def connect(self, port: str, baudrate: int = 9600) -> None:
        if self._serial and self._serial.is_open and self.port == port:
            self.baudrate = baudrate
            return

        self.close()
        try:
            self._serial = serial.Serial(port, baudrate=baudrate, timeout=1)
            self.port = port
            self.baudrate = baudrate
        except serial.SerialException as exc:
            self._serial = None
            self.port = None
            raise HTTPException(status_code=400, detail=f"Failed to open port: {exc}")

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self.port = None

    def send(self, action: str) -> None:
        if action not in AVAILABLE_ACTIONS:
            raise HTTPException(
                status_code=400, detail=f"Unsupported action '{action}'."
            )

        if not self._serial or not self._serial.is_open:
            raise HTTPException(status_code=400, detail="Serial port not connected.")

        try:
            payload = (action.strip().upper() + "\n").encode("utf-8")
            self._serial.write(payload)
            self._serial.flush()
        except serial.SerialException as exc:
            raise HTTPException(status_code=500, detail=f"Serial write failed: {exc}")

    def status(self) -> dict:
        return {
            "connected": bool(self._serial and self._serial.is_open),
            "port": self.port,
            "baudrate": self.baudrate,
        }


serial_manager = SerialManager()


# ============================================================
# Fonctions importables pour le LLM (contrôle direct Python)
# ============================================================


def control_leds(state: str) -> str:
    """
    Contrôle les LEDs.

    Args:
        state: 'ON' pour allumer, 'OFF' pour éteindre

    Returns:
        Message de confirmation

    Raises:
        ValueError: Si une erreur survient (connexion, envoi, etc.)
    """
    action = "TURN_ON_LIGHTS" if state.upper() == "ON" else "TURN_OFF_LIGHTS"
    try:
        serial_manager.send(action)
    except HTTPException as e:
        raise ValueError(e.detail) from e
    return f"LEDs {state.upper()}"


def control_door(action: str) -> str:
    """
    Contrôle la porte.

    Args:
        action: 'OPEN' pour ouvrir, 'CLOSE' pour fermer

    Returns:
        Message de confirmation

    Raises:
        ValueError: Si une erreur survient (connexion, envoi, etc.)
    """
    cmd = "OPEN_DOOR" if action.upper() == "OPEN" else "CLOSE_DOOR"
    try:
        serial_manager.send(cmd)
    except HTTPException as e:
        raise ValueError(e.detail) from e
    return f"Door {action.upper()}"


def control_fan(state: str) -> str:
    """
    Contrôle le ventilateur.

    Args:
        state: 'ON' pour allumer, 'OFF' pour éteindre

    Returns:
        Message de confirmation

    Raises:
        ValueError: Si une erreur survient (connexion, envoi, etc.)
    """
    cmd = "TURN_ON_FAN" if state.upper() == "ON" else "TURN_OFF_FAN"
    try:
        serial_manager.send(cmd)
    except HTTPException as e:
        raise ValueError(e.detail) from e
    return f"Fan {state.upper()}"


def get_available_tools() -> list:
    """
    Retourne la liste des outils disponibles pour le LLM.

    Returns:
        Liste des outils avec leurs paramètres
    """
    return [
        {
            "name": "control_leds",
            "description": "Contrôle les LEDs (lumières)",
            "params": ["state: ON|OFF"],
        },
        {
            "name": "control_door",
            "description": "Contrôle la porte (servo)",
            "params": ["action: OPEN|CLOSE"],
        },
        {
            "name": "control_fan",
            "description": "Contrôle le ventilateur",
            "params": ["state: ON|OFF"],
        },
    ]


# ============================================================
# Application FastAPI
# ============================================================

app = FastAPI(title="Smart Home Control + MCP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/ports")
async def get_ports() -> dict:
    return {"ports": serial_manager.list_ports()}


@app.post("/api/connect")
async def connect(request: ConnectRequest) -> dict:
    serial_manager.connect(request.port, request.baudrate)
    return {"status": "connected", **serial_manager.status()}


@app.post("/api/command")
async def send_command(request: CommandRequest) -> dict:
    action = request.action.strip().upper()
    serial_manager.send(action)
    return {"status": "ok", "action": action}


@app.get("/api/status")
async def status() -> dict:
    return serial_manager.status()


@app.post("/mcp/invoke")
async def mcp_invoke(request: MCPInvokeRequest) -> dict:
    """
    Minimal MCP-like endpoint: forward `name` to the Arduino command set.
    """
    action = request.name.strip().upper()
    serial_manager.send(action)
    return {"status": "ok", "action": action, "notes": "Forwarded via MCP endpoint"}


# ============================================================
# Endpoints MCP Tester
# ============================================================


@app.post("/mcp/connect")
async def mcp_connect() -> dict:
    """Connecte au serveur MCP."""
    client = await get_mcp_client()
    success = await client.connect()
    if success:
        await ws_manager.broadcast({"type": "system", "message": "MCP connecté"})
        return {"status": "connected"}
    raise HTTPException(status_code=500, detail="Échec de connexion au serveur MCP")


@app.post("/mcp/disconnect")
async def mcp_disconnect() -> dict:
    """Déconnecte du serveur MCP."""
    client = await get_mcp_client()
    await client.disconnect()
    await ws_manager.broadcast({"type": "system", "message": "MCP déconnecté"})
    return {"status": "disconnected"}


@app.get("/mcp/status")
async def mcp_status() -> dict:
    """Retourne l'état de la connexion MCP."""
    client = await get_mcp_client()
    return {"connected": client.is_connected}


@app.get("/mcp/tools")
async def mcp_list_tools() -> dict:
    """Liste les tools disponibles sur le serveur MCP."""
    client = await get_mcp_client()
    if not client.is_connected:
        raise HTTPException(status_code=400, detail="Non connecté au serveur MCP")
    tools = await client.list_tools()
    return {"tools": tools}


@app.post("/mcp/call")
async def mcp_call_tool(request: MCPToolRequest) -> dict:
    """Appelle un tool MCP."""
    client = await get_mcp_client()
    if not client.is_connected:
        raise HTTPException(status_code=400, detail="Non connecté au serveur MCP")

    tool = request.tool.lower()
    action = request.action.upper()

    if tool == "control_door":
        result = await client.control_door(action)
    elif tool == "control_fans":
        result = await client.control_fans(action)
    elif tool == "control_leds":
        result = await client.control_leds(action)
    else:
        raise HTTPException(status_code=400, detail=f"Tool inconnu: {tool}")

    # Broadcast l'événement aux clients WebSocket
    await ws_manager.broadcast({
        "type": "mcp_call",
        "tool": tool,
        "action": action,
        "result": result,
    })

    return result


@app.get("/mcp/log")
async def mcp_get_log() -> dict:
    """Retourne le log des événements MCP."""
    return {"events": get_event_log()}


@app.delete("/mcp/log")
async def mcp_clear_log() -> dict:
    """Vide le log des événements MCP."""
    clear_event_log()
    return {"status": "cleared"}


# ============================================================
# WebSocket pour le live log
# ============================================================


@app.websocket("/ws/log")
async def websocket_log(websocket: WebSocket):
    """WebSocket pour recevoir les événements en temps réel."""
    await ws_manager.connect(websocket)
    try:
        # Envoyer les événements existants
        events = get_event_log()
        if events:
            await websocket.send_json({"type": "history", "events": events})

        # Garder la connexion ouverte et attendre les messages
        while True:
            # On attend juste pour garder la connexion active
            data = await websocket.receive_text()
            # Optionnel: traiter les messages du client si nécessaire
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )
