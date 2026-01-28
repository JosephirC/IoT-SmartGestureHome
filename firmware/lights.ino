// --- bridge.ino ---
// Code propre sans erreurs de compilation

// Constante pour la LED intégrée (pin 13 sur Arduino Uno)
const int LED_PIN = 13;

void setup()
{
    // Initialise la communication USB à 9600 bauds
    Serial.begin(9600);

    // Configure la PIN 13 comme une sortie (pour envoyer du courant)
    pinMode(LED_PIN, OUTPUT);

    // Éteint la LED au démarrage
    digitalWrite(LED_PIN, LOW);

    Serial.println("Arduino Pret !");
}

void loop()
{
    // Vérifie si des données arrivent par le câble USB
    if (Serial.available() > 0)
    {
        // Lit le texte reçu jusqu'au caractère "saut de ligne"
        String input = Serial.readStringUntil('\n');
        input.trim(); // Nettoie les espaces (enlève \r ou \n à la fin)

        // Logique de contrôle
        if (input == "TURN_ON_LEDS")
        {
            digitalWrite(LED_PIN, HIGH); // Allume la LED
            Serial.println("LED Allumée");
        }
        else if (input == "TURN_OFF_LEDS")
        {
            digitalWrite(LED_PIN, LOW); // Éteint la LED
            Serial.println("LED Éteinte");
        }
    }
}