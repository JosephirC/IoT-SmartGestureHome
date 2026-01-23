"""
Client MCP pour le dashboard.
Se connecte au serveur MCP et permet d'appeler les tools.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

# Chemin vers le repertoire racine du projet
PROJECT_ROOT = Path(__file__).parent.parent
MCP_SERVER_PATH = str(PROJECT_ROOT / "mcp_server" / "server.py") + ":mcp"


class MCPClient:
    """Client pour communiquer avec le serveur MCP."""

    def __init__(self, on_event: Optional[Callable] = None):
        self._client: Optional[Client] = None
        self._transport: Optional[StdioTransport] = None
        self._connected = False
        self._on_event = on_event  # Callback pour logger les événements

    def _log_event(self, event_type: str, tool: str, args: dict, result: str):
        """Enregistre un événement pour le live log."""
        if self._on_event:
            self._on_event({
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "tool": tool,
                "args": args,
                "result": result,
            })

    async def connect(self) -> bool:
        """Connecte au serveur MCP."""
        if self._connected:
            return True

        try:
            self._transport = StdioTransport(
                command="fastmcp",
                args=["run", MCP_SERVER_PATH],
                cwd=str(PROJECT_ROOT),
            )
            self._client = Client(self._transport)
            await self._client.__aenter__()
            self._connected = True
            self._log_event("system", "connect", {}, "Connecté au serveur MCP")
            return True
        except Exception as e:
            self._log_event("error", "connect", {}, str(e))
            return False

    async def disconnect(self):
        """Déconnecte du serveur MCP."""
        if self._client and self._connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass
            self._connected = False
            self._log_event("system", "disconnect", {}, "Déconnecté du serveur MCP")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Appelle un tool MCP et retourne le résultat."""
        if not self._connected:
            return {"success": False, "error": "Non connecté au serveur MCP"}

        try:
            self._log_event("call", tool_name, args, "En cours...")
            result = await self._client.call_tool(tool_name, args)
            result_str = str(result)
            self._log_event("result", tool_name, args, result_str)
            return {"success": True, "result": result_str}
        except Exception as e:
            error_msg = str(e)
            self._log_event("error", tool_name, args, error_msg)
            return {"success": False, "error": error_msg}

    async def control_door(self, action: str) -> dict:
        """Contrôle la porte (OPEN/CLOSE)."""
        return await self.call_tool("control_door", {"action": action})

    async def control_fans(self, action: str) -> dict:
        """Contrôle le ventilateur (ON/OFF)."""
        return await self.call_tool("control_fans", {"action": action})

    async def control_leds(self, action: str) -> dict:
        """Contrôle les LEDs (ON/OFF)."""
        return await self.call_tool("control_leds", {"action": action})

    async def list_tools(self) -> list:
        """Liste les tools disponibles sur le serveur MCP."""
        if not self._connected:
            return []

        try:
            tools = await self._client.list_tools()
            return [{"name": t.name, "description": t.description} for t in tools]
        except Exception:
            return []


# Instance globale pour réutilisation
_mcp_client: Optional[MCPClient] = None
_event_log: list = []


def get_event_log() -> list:
    """Retourne le log des événements."""
    return _event_log


def clear_event_log():
    """Vide le log des événements."""
    global _event_log
    _event_log = []


def _on_event_callback(event: dict):
    """Callback appelé pour chaque événement MCP."""
    global _event_log
    _event_log.append(event)
    # Garder seulement les 100 derniers événements
    if len(_event_log) > 100:
        _event_log = _event_log[-100:]


async def get_mcp_client() -> MCPClient:
    """Retourne l'instance du client MCP (singleton)."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(on_event=_on_event_callback)
    return _mcp_client
