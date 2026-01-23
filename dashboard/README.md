# Smart Home Controller (Python MCP + Arduino)

How to run:
- Install deps: `python -m venv .venv && .\.venv\Scripts\activate && pip install -r requirements.txt`.
- Flash arduino/smart_home.ino once (adjust pins if needed).
- Start server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000` and open `http://localhost:8000`. Choose the Arduino port, connect, and use the buttons. MCP clients can POST to /mcp/invoke with {"name": "<ACTION>"}.

Python FastAPI web app that exposes a minimal MCP-like endpoint and a simple UI to control an Arduino-powered servo door, DC fan, and LEDs. The Arduino listens on serial for commands:

- `OPEN_DOOR` / `CLOSE_DOOR`
- `TURN_ON_FAN` / `TURN_OFF_FAN`
- `TURN_ON_LIGHTS` / `TURN_OFF_LIGHTS`

## Quick start

1. **Install dependencies**
   ```bash
   cd D:\UCBL\Projects\domotic-mcp-ia-generated
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Flash the Arduino once**
   - Open `arduino/smart_home.ino` in the Arduino IDE.
   - Adjust `DOOR_PIN`, `FAN_PIN`, `LED_PIN` if your wiring differs.
   - Upload to the Arduino UNO.

3. **Run the server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Then open http://localhost:8000 in your browser.

## UI endpoints

- `/` — Web UI
- `/api/ports` — List serial ports
- `/api/connect` — `POST { "port": "COM3", "baudrate": 9600 }`
- `/api/command` — `POST { "action": "OPEN_DOOR" }`
- `/api/status` — Connection status

## MCP endpoint

- `/mcp/invoke` — `POST { "name": "<ACTION>" }`
  - Forwards directly to the Arduino (same actions as above).

## Notes

- If multiple Arduinos are connected, pick the right port in the UI before sending commands.
- The server keeps one active serial connection; reconnect via `/api/connect` to switch ports.
- The Arduino sketch sends `ACK:<ACTION>` back on serial for optional debugging.
