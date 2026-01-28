import os
from typing import List, Optional

import serial
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from serial.tools import list_ports

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )
