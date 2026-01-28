"""Pydantic models pour validation des données"""

from pydantic import BaseModel
from typing import Optional


class GestureDetected(BaseModel):
    gesture: str
    confidence: Optional[float] = None


class DeviceCommand(BaseModel):
    device: str  # "leds", "fans", "door"
    action: str  # "ON", "OFF", "OPEN", "CLOSE"


class ActionLog(BaseModel):
    timestamp: str
    gesture: str
    tool: str
    action: str
    result: str


class StateResponse(BaseModel):
    leds: str
    fans: str
    door: str
