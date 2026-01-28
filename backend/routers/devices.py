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


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        # Retire best-effort
        if websocket in self.active_connections:
            try:
                self.active_connections.remove(websocket)
            except Exception:
                pass

        # Ferme best-effort (même si déjà fermé / déjà retiré)
        try:
            await websocket.close()
        except Exception:
            pass

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)

        # Nettoyage après coup
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
    try:
        gesture_text = input.gesture
        print("[API] reçu gesture:", gesture_text)

        # Traduit le geste en commande
        tool, args = await translate_gesture(gesture_text)
        print("[API] LLM ->", tool, args)

        if tool is None:
            return {"status": "error", "message": "Geste non reconnu"}

        # IMPORTANT: valider args AVANT d'accéder à args["action"]
        if not isinstance(args, dict) or "action" not in args:
            return {
                "status": "error",
                "message": "Réponse LLM invalide (args.action manquant)",
                "tool": tool,
                "args": args
            }

        action = args["action"]

        # Vérifie les redondances
        if tool == "control_leds" and STATE["leds"] == action:
            return {"status": "skipped", "message": f"LEDs déjà {action}"}
        if tool == "control_fans" and STATE["fans"] == action:
            return {"status": "skipped", "message": f"Fans déjà {action}"}
        if tool == "control_door" and STATE["door"] == action:
            return {"status": "skipped", "message": f"Door déjà {action}"}

        # Exécute via MCP
        result = await execute_mcp_tool(tool, args)
        print("[API] MCP ->", result)

        # Met à jour l'état
        if tool == "control_leds":
            STATE["leds"] = action
        elif tool == "control_fans":
            STATE["fans"] = action
        elif tool == "control_door":
            STATE["door"] = action

        # Log l'action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "gesture": gesture_text,
            "tool": tool,
            "action": action,
            "result": result.get("message", "OK") if isinstance(result, dict) else str(result),
        }
        ACTION_LOG.append(log_entry)

        # Broadcast
        await manager.broadcast({
            "type": "action_executed",
            "gesture": gesture_text,
            "tool": tool,
            "action": action,
            "state": STATE,
            "log_entry": log_entry
        })

        return {
            "status": "success",
            "tool": tool,
            "action": action,
            "state": STATE
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour temps réel"""
    await manager.connect(websocket)

    try:
        # Envoie l'état initial
        try:
            await websocket.send_json({
                "type": "initial_state",
                "state": STATE,
                "action_log": ACTION_LOG[-20:]
            })
        except Exception:
            # client a déjà fermé (souvent lors d'un F5)
            await manager.disconnect(websocket)
            return

        while True:
            _ = await websocket.receive_text()
            # À développer si besoin

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
