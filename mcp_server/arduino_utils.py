import time
import serial
import subprocess

SERIAL_PORT = 'COM7'
BAUD_RATE = 9600
SKETCH_NAME = "arduino:avr:uno"
SKETCH_NAME = "firmware\test_domotique_maison.ino"
CORE_TYPE = "arduino:avr:uno"


def get_arduino():
    """Établit la connexion série permanente."""
    global _arduino
    if _arduino is None:
        try:
            print(f"Connexion au port {SERIAL_PORT}...")
            _arduino = serial.Serial(
                SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            return _arduino
        except Exception as e:
            print(f"Erreur de connexion : {e}")
            return None


def flash_arduino():
    """Compile et téléverse le code sans ouvrir l'IDE."""
    print("[AUTO-SETUP] Compilation et Téléversement en cours...")

    # Commande pour compiler
    compile_cmd = f"arduino-cli compile --fqbn {CORE_TYPE} {SKETCH_NAME}"
    # Commande pour téléverser
    upload_cmd = f"arduino-cli upload -p {SERIAL_PORT} --fqbn {CORE_TYPE} {SKETCH_NAME}"

    try:
        # 1. Compilation
        print("   -> Compilation...")
        subprocess.run(compile_cmd, shell=True, check=True)

        # 2. Téléversement
        print(f"   -> Téléversement sur {SERIAL_PORT}...")
        subprocess.run(upload_cmd, shell=True, check=True)

        print("[AUTO-SETUP] Arduino prêt et flashé avec succès !")
        return True
    except subprocess.CalledProcessError:
        print("ERREUR CRITIQUE : Échec du téléversement automatique.")
        print(
            "   Assure-toi que 'arduino-cli' est installé ou que le port n'est pas utilisé.")
        return False
