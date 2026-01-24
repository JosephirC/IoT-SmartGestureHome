from flask import Flask, Response, render_template

from src.backbone import TFLiteModel, get_model
from src.landmarks_extraction import mediapipe_detection, draw, extract_coordinates, load_json_file
from src.config import SEQ_LEN, THRESH_HOLD
import numpy as np
import cv2
import mediapipe as mp


app = Flask(__name__)


mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils


s2p_map = {k.lower():v for k,v in load_json_file("src/sign_to_prediction_index_map.json").items()}
p2s_map = {v:k for k,v in load_json_file("src/sign_to_prediction_index_map.json").items()}
decoder = lambda x: p2s_map.get(x)


models_path = ['./models/islr-fp16-192-8-seed42-fold0-best.h5']
models = [get_model() for _ in models_path]

for model, path in zip(models, models_path):
    model.load_weights(path)

tflite_keras_model = TFLiteModel(islr_models=models)

#fonction qui génère les frames envoyé a flask
def generate_frames(videoSource=0):


    # Variables pour stocker les données
    sequence_data = []
    recognized_signs = []

    cap = cv2.VideoCapture(videoSource)

    with mp_holistic.Holistic(min_detection_confidence=0.5,
                              min_tracking_confidence=0.5) as holistic:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # same code que dans le main ===
            image, results = mediapipe_detection(frame, holistic)
            draw(image, results)

            try:
                landmarks = extract_coordinates(results)
            except:
                landmarks = np.zeros((468 + 21 + 33 + 21, 3))

            sequence_data.append(landmarks)

            # Prédiction
            if len(sequence_data) % SEQ_LEN == 0:
                prediction = tflite_keras_model(np.array(sequence_data, dtype=np.float32))["outputs"]

                if np.max(prediction.numpy(), axis=-1) > THRESH_HOLD:
                    sign = np.argmax(prediction.numpy(), axis=-1)
                    decoded_sign = decoder(sign)
                    if decoded_sign:
                        recognized_signs.insert(0, decoded_sign)
                        print(f"Signe reconnu : {decoded_sign}")

                sequence_data = []

            # Préparer l'image
            image = cv2.flip(image, 1)
            height, width = image.shape[0], image.shape[1]
            white_band = np.ones((height // 4, width, 3), dtype='uint8') * 255

            cv2.putText(white_band, f"Sequence: {len(sequence_data)}/{SEQ_LEN}",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            signs_text = ', '.join(str(x) for x in recognized_signs[:5])
            if signs_text:
                cv2.putText(white_band, f"Signes: {signs_text}",
                            (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 150, 0), 2, cv2.LINE_AA)

            final_image = np.concatenate((white_band, image), axis=0)

            # === PARTIE FLASK : Encoder et envoyer ===
            #encodage en jpg de l'image obtenue
            ret, buffer = cv2.imencode('.jpg', final_image)
            # Conversion en bytes pour l'envoie de donnée par yield
            frame_bytes = buffer.tobytes()

            # Yield au lieu de cv2.imshow()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   frame_bytes + b'\r\n')



@app.route('/')
def index():
    #Route principale - Affiche la page web
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    #Route pour le streaming vidéo
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print("=" * 60)
    print("Serveur Flask démarré !")
    print("Ouvrez le navigateur à : http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)