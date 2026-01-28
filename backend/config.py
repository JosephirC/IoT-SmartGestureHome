"""Configuration centralisée pour le backend"""

import os
from dotenv import load_dotenv

load_dotenv()

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Paths
SIGN_LANGUAGE_MODEL_PATH = "../sign-language-modele"
GESTURE_MODEL_PATH = os.path.join(
    SIGN_LANGUAGE_MODEL_PATH, "models/islr-fp16-192-8-seed42-fold0-best.h5")
SIGN_MAP_PATH = os.path.join(
    SIGN_LANGUAGE_MODEL_PATH, "src/sign_to_prediction_index_map.json")

# Detection
SEQ_LEN = 30
THRESH_HOLD = 0.5
