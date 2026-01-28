# IoT-SmartGestureHome

Smart home automation system with gesture-based control using sign language recognition.

## Overview

This project enables controlling home devices (door, lights, fans) through hand gestures captured by a webcam. A machine learning model recognizes sign language gestures and triggers corresponding actions via an Arduino-based controller.

## Architecture

```
Webcam → MediaPipe → TFLite Model → FastAPI → Ollama LLM → MCP Server → Arduino → Hardware
```

### Components

| Component | Description |
|-----------|-------------|
| **Backend** (`/backend/`) | FastAPI application with gesture detection, LLM integration, and device control |
| **Sign Language Model** (`/sign-language-modele/`) | MediaPipe + TFLite model for gesture recognition |
| **MCP Server** (`/mcp_server/`) | Model Context Protocol server for Arduino communication |
| **FastAPI Dashboard** (`/fastapi_dashboard/`) | Legacy dashboard for manual control |

## Supported Gestures

| Gesture | Action |
|---------|--------|
| `HELLO` | Open door |
| `CUT` | Close door |
| `OUI` | Turn on lights |
| `NON` | Turn off lights |
| `BRAS` | Turn on fan |
| `SCISSORS` | Turn off fan |

## Requirements

### Hardware
- Arduino Uno
- Servo motor (door)
- DC fan with relay/transistor
- LEDs
- Webcam

### Software
- Python 3.10+
- Conda environment: `iot-smarthome`
- Ollama (local LLM server on port 11434)
- Arduino CLI

## Installation

### 1. Clone and setup environment

```bash
git clone https://github.com/your-repo/IoT-SmartGestureHome.git
cd IoT-SmartGestureHome
conda create -n iot-smarthome python=3.10
conda activate iot-smarthome
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
cd backend && pip install -r requirements.txt
```

### 3. Flash Arduino firmware

```bash
arduino-cli compile --fqbn arduino:avr:uno fastapi_dashboard/arduino/smart_home.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno fastapi_dashboard/arduino/smart_home.ino
```

### 4. Start Ollama

```bash
ollama serve
ollama pull llama3.1:8b
```

## Usage

### Start the backend

```bash
cd backend
python3 backend_main.py
# or
uvicorn backend_main:app --reload --host 0.0.0.0 --port 8000
```

Access the dashboard at `http://localhost:8000`

### Start MCP Server (standalone)

```bash
fastmcp run mcp_server/server.py:mcp
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Vue.js dashboard |
| `/camera/video_feed` | GET | MJPEG video stream |
| `/camera/last_gesture` | GET | Last detected gesture |
| `/api/state` | GET | Current device states |
| `/api/gesture` | POST | Send gesture command |
| `/health` | GET | Health check |

## Configuration

### Environment Variables

```bash
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
MCP_ENTRY=mcp_server/server.py:mcp
MCP_COMMAND=fastmcp
```

### Serial Port

Edit `mcp_server/arduino_utils.py`:
- Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
- Windows: `COM7`
- Baud rate: 9600

## Serial Protocol

Commands sent to Arduino:
- `OPEN_DOOR` / `CLOSE_DOOR`
- `TURN_ON_FAN` / `TURN_OFF_FAN`
- `TURN_ON_LEDS` / `TURN_OFF_LEDS`

Arduino responds with `ACK:<ACTION>` on success.

## Project Structure

```
IoT-SmartGestureHome/
├── backend/
│   ├── backend_main.py      # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── routers/
│   │   ├── camera.py        # Video streaming + gesture detection
│   │   └── devices.py       # Device control + LLM integration
│   ├── services/
│   │   ├── llm_service.py   # Ollama LLM calls
│   │   └── mcp_service.py   # FastMCP client wrapper
│   └── static/
│       ├── dashboard.html   # Vue.js UI
│       ├── dashboard.css    # Styles
│       └── dashboard.js     # Vue.js logic
├── sign-language-modele/
│   └── src/
│       ├── backbone.py      # TFLite inference
│       └── landmarks_extraction.py
├── mcp_server/
│   ├── server.py            # FastMCP server
│   └── arduino_utils.py     # Serial connection
├── fastapi_dashboard/
│   ├── arduino/
│   │   └── smart_home.ino   # Arduino firmware
│   └── main.py              # Legacy dashboard
└── requirements.txt
```

## License

MIT
