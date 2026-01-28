"""Smart Home MCP Server.

Provides MCP tools for home automation device control via Arduino.
Implements lazy initialization and robust error handling.
"""

from fastmcp import FastMCP
from arduino_utils import get_arduino, flash_arduino

# Initialize MCP server at module level (required for decorators)
mcp = FastMCP("SmartHouseMCP")


# ============================================================================
# MCP TOOLS - Home Automation Commands
# ============================================================================


@mcp.tool()
def control_door(action: str) -> str:
    """Control door lock mechanism.

    Args:
        action: Control action - "OPEN" or "CLOSE".

    Returns:
        Status message describing operation result.
    """
    try:
        arduino = get_arduino()
        if arduino is None:
            return "✗ Arduino not connected"

        command = action.strip().upper()

        if command == "OPEN":
            arduino.write(b"OPEN_DOOR\n")
            return "✓ Door opened successfully"
        elif command == "CLOSE":
            arduino.write(b"CLOSE_DOOR\n")
            return "✓ Door closed successfully"
        else:
            return "✗ Invalid command. Use: OPEN or CLOSE"

    except Exception as e:
        return f"✗ Error: {type(e).__name__}: {e}"


@mcp.tool()
def control_fans(action: str) -> str:
    """Control ventilation fans.

    Args:
        action: Control action - "ON" or "OFF".

    Returns:
        Status message describing operation result.
    """
    try:
        arduino = get_arduino()
        if arduino is None:
            return "✗ Arduino not connected"

        command = action.strip().upper()

        if command == "ON":
            arduino.write(b"TURN_ON_FAN\n")
            return "✓ Fans turned on"
        elif command == "OFF":
            arduino.write(b"TURN_OFF_FAN\n")
            return "✓ Fans turned off"
        else:
            return "✗ Invalid command. Use: ON or OFF"

    except Exception as e:
        return f"✗ Error: {type(e).__name__}: {e}"


@mcp.tool()
def control_leds(action: str) -> str:
    """Control LED lighting.

    Args:
        action: Control action - "ON" or "OFF".

    Returns:
        Status message describing operation result.
    """
    try:
        arduino = get_arduino()
        if arduino is None:
            return "✗ Arduino not connected"

        command = action.strip().upper()

        if command == "ON":
            arduino.write(b"TURN_ON_LEDS\n")
            return "✓ LEDs turned on"
        elif command == "OFF":
            arduino.write(b"TURN_OFF_LEDS\n")
            return "✓ LEDs turned off"
        else:
            return "✗ Invalid command. Use: ON or OFF"

    except Exception as e:
        return f"✗ Error: {type(e).__name__}: {e}"
