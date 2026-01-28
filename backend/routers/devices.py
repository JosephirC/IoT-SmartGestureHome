"""Router pour les commandes des appareils"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.schemas import GestureDetected, StateResponse
from services.llm_service import translate_gesture
from services.mcp_service import execute_mcp_tool
from datetime import datetime
from typing import Dict

router = APIRouter(prefix="/api", tags=["devices"])

# État global
STATE: Dict = {
    "leds": "OFF",
    "fans": "OFF",
    "door": "CLOSED"
}

ACTION_LOG = []

# Websocket connections


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            try:
                self.active_connections.remove(websocket)
            except Exception:
                print("Erreur lors de la déconnexion websocket")

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)

        # nettoyer après
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()


@router.get("/state")
async def get_state() -> StateResponse:
    """Retourne l'état actuel des appareils"""
    return StateResponse(**STATE)


@router.post("/gesture")
async def process_gesture(input: GestureDetected):
    """Traite un geste détecté"""
    gesture_text = input.gesture

    # Traduit le geste en commande
    tool, args = await translate_gesture(gesture_text)

    if tool is None:
        return {"status": "error", "message": "Geste non reconnu"}

    # Vérifie les redondances
    if tool == "control_leds" and STATE["leds"] == args["action"]:
        return {"status": "skipped", "message": f"LEDs déjà {args['action']}"}
    if tool == "control_fans" and STATE["fans"] == args["action"]:
        return {"status": "skipped", "message": f"Fans déjà {args['action']}"}
    if tool == "control_door" and STATE["door"] == args["action"]:
        return {"status": "skipped", "message": f"Door déjà {args['action']}"}

    # Exécute via MCP
    result = await execute_mcp_tool(tool, args)

    # Met à jour l'état
    if tool == "control_leds":
        STATE["leds"] = args["action"]
    elif tool == "control_fans":
        STATE["fans"] = args["action"]
    elif tool == "control_door":
        STATE["door"] = args["action"]

    # Log l'action
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "gesture": gesture_text,
        "tool": tool,
        "action": args.get("action"),
        "result": result.get("message", "OK")
    }
    ACTION_LOG.append(log_entry)

    # Broadcast
    await manager.broadcast({
        "type": "action_executed",
        "gesture": gesture_text,
        "tool": tool,
        "action": args.get("action"),
        "state": STATE,
        "log_entry": log_entry
    })

    return {
        "status": "success",
        "tool": tool,
        "action": args.get("action"),
        "state": STATE
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour temps réel"""
    await manager.connect(websocket)

    try:
        # Envoie l'état initial
        await websocket.send_json({
            "type": "initial_state",
            "state": STATE,
            "action_log": ACTION_LOG[-20:]
        })

        while True:
            data = await websocket.receive_text()
            # À développer si besoin

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
