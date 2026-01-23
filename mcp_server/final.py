import time
import serial
import serial.tools.list_ports
import asyncio
from fastmcp import FastMCP

SERIAL_PORT = "COM7"
BAUD_RATE = 9600

mcp = FastMCP("ArduinoMCP")

arduino = None


def get_arduino():
    """Lazy initialization of Arduino connection"""
    global arduino
    if arduino is None or not arduino.is_open:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)
    return arduino


@mcp.tool()
def control_leds(state: str) -> str:
    try:
        arduino = get_arduino()

        if state.upper() == "ON":
            arduino.write(b"TURN_ON_LEDS\n")
        elif state.upper() == "OFF":
            arduino.write(b"TURN_OFF_LEDS\n")
        else:
            return "Erreur: ON ou OFF attendu"
        return "OK - LEDs command sent"
    except serial.SerialException as e:
        return f"Error connecting to Arduino on {SERIAL_PORT}: {e}"
    except Exception as e:
        return f"Error sending command: {e}"


@mcp.tool()
def list_ports() -> str:
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        return "No serial ports found"

    result = "Available ports:\n"
    for port in ports:
        result += f"- {port.device}: {port.description}\n"
    return result
