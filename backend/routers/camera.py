"""Router pour la caméra et le streaming vidéo avec détection de gestes"""

from mediapipe import solutions as mp_solutions
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import sys
import os
from datetime import datetime, timedelta
from mediapipe import solutions as mp_solutions

router = APIRouter(prefix="/camera", tags=["camera"])

# Global state
last_gesture = ""
last_gesture_time = None

# Charger les modèles
MODEL_AVAILABLE = False
tflite_keras_model = None
p2s_map = {}
SEQ_LEN = 30
THRESH_HOLD = 0.5
mp_holistic = mp_solutions.holistic

# Filtrer uniquement les 6 gestes attendus (en lower car p2s_map renvoie souvent en lower)
# ALLOWED_GESTURES = {"oui", "non", "bras", "hello", "cut", "animal"}


try:
    # Déterminer le chemin correct vers sign-language-modele
    current_dir = os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))  # backend/
    sign_lang_path = os.path.join(os.path.dirname(
        current_dir), "sign-language-modele")
    sys.path.insert(0, sign_lang_path)

    from src.backbone import TFLiteModel, get_model
    from src.landmarks_extraction import (
        mediapipe_detection,
        draw,
        extract_coordinates,
        load_json_file,
    )
    from src.config import SEQ_LEN as SEQ_LEN_CONFIG, THRESH_HOLD as THRESH_HOLD_CONFIG

    SEQ_LEN = SEQ_LEN_CONFIG
    THRESH_HOLD = THRESH_HOLD_CONFIG

    # Charger la map geste -> prédiction
    json_path = os.path.join(sign_lang_path, "src",
                             "sign_to_prediction_index_map.json")
    s2p_map = {k.lower(): v for k, v in load_json_file(json_path).items()}
    p2s_map = {v: k for k, v in load_json_file(json_path).items()}

    def decoder(x: int):
        return p2s_map.get(x)

    # Charger les modèles
    model_file = os.path.join(sign_lang_path, "models",
                              "islr-fp16-192-8-seed42-fold0-best.h5")
    models = [get_model()]
    models[0].load_weights(model_file)
    tflite_keras_model = TFLiteModel(islr_models=models)
    MODEL_AVAILABLE = True
    print("✓ Modèle de détection de gestes chargé")
except Exception as e:
    print(f"⚠️  Détection non disponible: {e}")
    MODEL_AVAILABLE = False


async def generate_frames():
    """Génère les frames vidéo avec détection"""
    global last_gesture, last_gesture_time

    sequence_data = []
    recognized_signs = []

    # Anti-spam / stabilité
    stable_needed = 2          # nb de détections consécutives identiques requises
    stable_count = 0
    last_candidate = None

    # ne pas republier le même geste trop vite
    cooldown = timedelta(seconds=1.5)
    last_publish_time = datetime.min

    cap = cv2.VideoCapture(0)

    try:
        if MODEL_AVAILABLE and tflite_keras_model is not None and mp_holistic is not None:
            with mp_holistic.Holistic(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as holistic:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame = cv2.flip(frame, 1)

                    image, results = mediapipe_detection(frame, holistic)
                    draw(image, results)

                    try:
                        landmarks = extract_coordinates(results)
                    except Exception:
                        landmarks = np.zeros((468 + 21 + 33 + 21, 3))

                    sequence_data.append(landmarks)

                    decoded_sign = None

                    if len(sequence_data) >= SEQ_LEN:
                        prediction = tflite_keras_model(
                            np.array(
                                sequence_data[-SEQ_LEN:], dtype=np.float32)
                        )["outputs"]

                        pred = prediction.numpy()
                        score = float(np.max(pred))

                        if score > float(THRESH_HOLD):
                            sign_idx = int(
                                np.argmax(pred, axis=-1).reshape(-1)[0])
                            decoded_sign = decoder(sign_idx)

                            # Filtrage sur tes 6 gestes (pour éviter le bruit)
                            # if decoded_sign:
                            #     d = decoded_sign.strip().lower()
                            #     if d not in ALLOWED_GESTURES:
                            #         decoded_sign = None

                        sequence_data = []

                    # Stabilisation + cooldown
                    now = datetime.now()
                    if decoded_sign:
                        if decoded_sign == last_candidate:
                            stable_count += 1
                        else:
                            last_candidate = decoded_sign
                            stable_count = 1

                        if stable_count >= stable_needed and (now - last_publish_time) >= cooldown:
                            recognized_signs.insert(0, decoded_sign)
                            recognized_signs = recognized_signs[:5]

                            last_gesture = decoded_sign
                            last_gesture_time = now
                            last_publish_time = now

                            print(f"✓ Geste détecté: {decoded_sign}")

                    # Bande blanche de statut
                    height, width = image.shape[0], image.shape[1]
                    white_band = np.ones(
                        (height // 4, width, 3), dtype="uint8") * 255

                    cv2.putText(
                        white_band,
                        f"Sequence: {len(sequence_data)}/{SEQ_LEN}",
                        (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )

                    signs_text = ", ".join(str(x)
                                           for x in recognized_signs[:5])
                    if signs_text:
                        cv2.putText(
                            white_band,
                            f"Signes reconnus: {signs_text}",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.2,
                            (0, 150, 0),
                            3,
                        )
                    else:
                        cv2.putText(
                            white_band,
                            "En attente de geste...",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (100, 100, 100),
                            2,
                        )

                    final_image = np.concatenate((white_band, image), axis=0)

                    ok, buffer = cv2.imencode(".jpg", final_image)
                    if not ok:
                        continue
                    frame_bytes = buffer.tobytes()

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
        else:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                ok, buffer = cv2.imencode(".jpg", frame)
                if not ok:
                    continue
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
    finally:
        cap.release()


@router.get("/video_feed")
async def video_feed():
    """Streaming vidéo"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/last_gesture")
async def get_last_gesture():
    """Retourne le dernier geste détecté"""
    return {
        "gesture": last_gesture,
        "timestamp": last_gesture_time.isoformat() if last_gesture_time else None,
    }
