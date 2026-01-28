# IoT-SmartGestureHome

Système domotique intelligent avec contrôle par gestes utilisant la reconnaissance de la langue des signes.

## Aperçu

Ce projet permet de contrôler des appareils domestiques (porte, lumières, ventilateurs) par des gestes de la main capturés par une webcam. Un modèle de machine learning reconnaît les gestes de la langue des signes et déclenche les actions correspondantes via un contrôleur Arduino.

## Architecture

```
Webcam → MediaPipe → Modèle TFLite → FastAPI → Ollama LLM → Serveur MCP → Arduino → Matériel
```

### Composants

| Composant | Description |
|-----------|-------------|
| **Backend** (`/backend/`) | Application FastAPI avec détection de gestes, intégration LLM et contrôle des appareils |
| **Modèle Langue des Signes** (`/sign-language-modele/`) | Modèle MediaPipe + TFLite pour la reconnaissance de gestes |
| **Serveur MCP** (`/mcp_server/`) | Serveur Model Context Protocol pour la communication Arduino |
| **FastAPI Dashboard** (`/fastapi_dashboard/`) | Dashboard legacy pour le contrôle manuel |

## Gestes Supportés

| Geste | Action |
|-------|--------|
| `HELLO` | Ouvrir la porte |
| `CUT` | Fermer la porte |
| `OUI` | Allumer les lumières |
| `NON` | Éteindre les lumières |
| `BRAS` | Allumer le ventilateur |
| `SCISSORS` | Éteindre le ventilateur |

## Prérequis

### Matériel
- Arduino Uno
- Servomoteur (porte)
- Ventilateur DC avec relais/transistor
- LEDs
- Webcam

### Logiciel
- Python 3.10+
- Environnement Conda : `iot-smarthome`
- Ollama (serveur LLM local sur le port 11434)
- Arduino CLI

## Installation

### 1. Cloner et configurer l'environnement

```bash
git clone https://github.com/your-repo/IoT-SmartGestureHome.git
cd IoT-SmartGestureHome
conda create -n iot-smarthome python=3.10
conda activate iot-smarthome
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
cd backend && pip install -r requirements.txt
```

### 3. Flasher le firmware Arduino

```bash
arduino-cli compile --fqbn arduino:avr:uno fastapi_dashboard/arduino/smart_home.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno fastapi_dashboard/arduino/smart_home.ino
```

### 4. Démarrer Ollama

```bash
ollama serve
ollama pull llama3.1:8b
```

## Utilisation

### Démarrer le backend

```bash
cd backend
python3 backend_main.py
# ou
uvicorn backend_main:app --reload --host 0.0.0.0 --port 8000
```

Accéder au dashboard sur `http://localhost:8000`

### Démarrer le serveur MCP (standalone)

```bash
fastmcp run mcp_server/server.py:mcp
```

## Points d'API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Dashboard Vue.js |
| `/camera/video_feed` | GET | Flux vidéo MJPEG |
| `/camera/last_gesture` | GET | Dernier geste détecté |
| `/api/state` | GET | États actuels des appareils |
| `/api/gesture` | POST | Envoyer une commande de geste |
| `/health` | GET | Vérification de santé |

## Configuration

### Variables d'environnement

```bash
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
MCP_ENTRY=mcp_server/server.py:mcp
MCP_COMMAND=fastmcp
```

### Port Série

Modifier `mcp_server/arduino_utils.py` :
- Linux : `/dev/ttyUSB0` ou `/dev/ttyACM0`
- Windows : `COM7`
- Baud rate : 9600

## Protocole Série

Commandes envoyées à l'Arduino :
- `OPEN_DOOR` / `CLOSE_DOOR`
- `TURN_ON_FAN` / `TURN_OFF_FAN`
- `TURN_ON_LEDS` / `TURN_OFF_LEDS`

L'Arduino répond avec `ACK:<ACTION>` en cas de succès.

## Structure du Projet

```
IoT-SmartGestureHome/
├── backend/
│   ├── backend_main.py      # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── routers/
│   │   ├── camera.py        # Streaming vidéo + détection de gestes
│   │   └── devices.py       # Contrôle des appareils + intégration LLM
│   ├── services/
│   │   ├── llm_service.py   # Appels Ollama LLM
│   │   └── mcp_service.py   # Wrapper client FastMCP
│   └── static/
│       ├── dashboard.html   # Interface Vue.js
│       ├── dashboard.css    # Styles
│       └── dashboard.js     # Logique Vue.js
├── sign-language-modele/
│   └── src/
│       ├── backbone.py      # Inférence TFLite
│       └── landmarks_extraction.py
├── mcp_server/
│   ├── server.py            # Serveur FastMCP
│   └── arduino_utils.py     # Connexion série
├── fastapi_dashboard/
│   ├── arduino/
│   │   └── smart_home.ino   # Firmware Arduino
│   └── main.py              # Dashboard legacy
└── requirements.txt
```

## Licence

MIT
