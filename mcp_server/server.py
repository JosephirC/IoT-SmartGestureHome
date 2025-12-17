import time
from fastmcp import FastMCP
from arduino_utils import get_arduino, flash_arduino


class MCPServer:
    def __init__(self):
        self.arduino = get_arduino()
        flash_arduino()

        global mcp
        mcp = FastMCP("SmartHouseMCP")

    @mcp.tool()
    def control_door(self, action: str) -> str:
        clean_action = action.strip().upper()
        if clean_action == "OPEN":
            self.arduino.write(b"OPEN_DOOR\n")
        elif clean_action == "CLOSE":
            self.arduino.write(b"CLOSE_DOOR\n")
        else:
            return "Erreur : Action inconnue. Utilisez OPEN ou CLOSE."

    @mcp.tool()
    def control_fans(self, action: str) -> str:
        clean_action = action.strip().upper()
        if clean_action == "ON":
            self.arduino.write(b"TURN_ON_FAN\n")
        elif clean_action == "OFF":
            self.arduino.write(b"TURN_OFF_FAN\n")
        else:
            return "Erreur : Action inconnue. Utilisez ON ou OFF."
        return "Blinds opened"

    @mcp.tool()
    def control_leds(self, action: str) -> str:
        clean_action = action.strip().upper()
        if clean_action == "ON":
            self.arduino.write(b"TURN_ON_LEDS\n")
        elif clean_action == "OFF":
            self.arduino.write(b"TURN_OFF_LEDS\n")
        else:
            return "Erreur : Action inconnue. Utilisez ON ou OFF."
        return "Blinds opened"
