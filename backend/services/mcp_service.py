import os
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

# Chemin absolu vers le serveur MCP (racine du projet)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MCP_SERVER_PATH = os.path.join(_PROJECT_ROOT, "mcp_server", "server.py")
MCP_ENTRY = os.getenv("MCP_ENTRY", f"{_MCP_SERVER_PATH}:mcp")
MCP_COMMAND = os.getenv("MCP_COMMAND", "fastmcp")

_client: Client | None = None
_client_lock = asyncio.Lock()


async def _ensure_client() -> Client:
    global _client
    async with _client_lock:
        if _client is not None:
            return _client

        transport = StdioTransport(
            command=MCP_COMMAND,
            args=["run", MCP_ENTRY],
        )
        _client = Client(transport)
        await _client.__aenter__()
        return _client


async def shutdown_mcp():
    global _client
    async with _client_lock:
        if _client is not None:
            await _client.__aexit__(None, None, None)
            _client = None


async def execute_mcp_tool(tool: str, args: dict) -> dict:
    client = await _ensure_client()
    result = await client.call_tool(tool, args)

    # Normalise résultat
    if getattr(result, "content", None):
        txt = result.content[0].text if result.content else str(result)
        return {"message": txt}
    return {"message": str(result)}
