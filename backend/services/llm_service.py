"""Service Ollama - Traduit les gestes en commandes via LLM"""

import httpx
from config import OLLAMA_HOST, OLLAMA_MODEL

OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"


async def translate_gesture(gesture: str) -> tuple[str, dict]:
    """Traduit un geste en commande via Llama 3.1 8B"""

    prompt = f"""You are a home automation router.
You will receive a detected gesture label from a fixed set.

Allowed gesture labels (case-insensitive):
- OUI
- NON
- BRAS
- HELLO
- CUT
- ANIMAL

Map gestures to actions EXACTLY as follows:
- HELLO  -> control_door OPEN
- CUT    -> control_door CLOSE
- OUI    -> control_leds ON
- NON    -> control_leds OFF
- BRAS   -> control_fans ON
- ANIMAL -> control_fans OFF

Rules:
- Output ONLY ONE LINE.
- Output must be exactly one of:
  control_door OPEN | control_door CLOSE | control_fans ON | control_fans OFF | control_leds ON | control_leds OFF | none
- If the input is not one of the allowed labels, output: none

Gesture: "{gesture}"
Response:"""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 16,
                    },
                },
            )
            resp.raise_for_status()
            completion = resp.json().get("response", "").strip().upper()
            print(f"[LLM] Gesture: {gesture} → Response: {completion}")

            # Parse
            lines = completion.split('\n')
            first_line = lines[0].strip()

            if "CONTROL_DOOR" in first_line:
                action = "OPEN" if " OPEN" in first_line else "CLOSE"
                return "control_door", {"action": action}
            if "CONTROL_FANS" in first_line:
                action = "ON" if " ON" in first_line else "OFF"
                return "control_fans", {"action": action}
            if "CONTROL_LEDS" in first_line:
                action = "ON" if " ON" in first_line else "OFF"
                return "control_leds", {"action": action}
            return None, None
    except Exception as e:
        print(f"[ERROR] LLM failed: {e}")
        return None, None
