#include <LiquidCrystal.h>
#include <Servo.h>

// Pin assignments (adjust to your wiring)
const int DOOR_PIN = 8;   // Servo signal pin
const int FAN_PIN = 9;    // PWM pin for transistor/driver controlling DC fan
const int LED_PIN_1 = 13;    // Digital pin for LEDs via resistor
const int LED_PIN_2 = 6;    // Digital pin for LEDs via resistor
const int LED_PIN_3 = 7;    // Digital pin for LEDs via resistor

const int POTENTIOMETER_PIN = A1;
const int PHOTORESISTOR_PIN = A0;


Servo doorServo;

// LCD
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

int fan_speed_raw_value = 0; // Valeur du potentiomètre entre 0..1023
int fan_speed_value = 0; // Vitesse du moteur entre 0..255
bool fanIsOn = false;

String serialBuffer = "";

bool systemIsOn = true;
bool lastSystemState = true;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2); // set up the LCD's number of columns and rows (16x2)
  lcd.print("WAITING COMMAND"); 

  pinMode(FAN_PIN, OUTPUT); // Pour envoyer la vitesse du ventilateur au transistor et ajuster/réguler la vitesse du moteur
  pinMode(POTENTIOMETER_PIN, INPUT); // Pour controler la vitesse du ventilateur
  doorServo.attach(DOOR_PIN);

  pinMode(LED_PIN_1, OUTPUT);
  pinMode(LED_PIN_2, OUTPUT);
  pinMode(LED_PIN_3, OUTPUT);


  //doorServo.write(0);
}

void loop() {
  int photoresistor_value = analogRead(PHOTORESISTOR_PIN);
  //Serial.println(photoresistor_value);

  if(photoresistor_value > 50) {
    systemIsOn = true;
  }
  else {
    systemIsOn = false;
  }

  if (systemIsOn != lastSystemState) {
    lcd.clear();
    if (!systemIsOn) {
      lcd.setCursor(0, 0);
      lcd.print("SYSTEM OFF");
      analogWrite(FAN_PIN, 0);   // sécurité
    } else {
      lcd.setCursor(0, 0);
      lcd.print("SYSTEM ON");
    }
    lastSystemState = systemIsOn;
  }

  if(systemIsOn) {
    fan_speed_raw_value = analogRead(POTENTIOMETER_PIN); // Récupérer la valeur du potentiomètre
    fan_speed_value = map(fan_speed_raw_value, 0, 1023, 200, 255); // Transformer la valeur du potentiomètre en vitesse de rotation du moteur
    if (fanIsOn) {
      analogWrite(FAN_PIN, fan_speed_value); // Envoyer la vitesse du moteur au PIN correspondant
    }

    if (Serial.available()) {
      //String command = Serial.readStringUntil('\n');
      //command.trim();
      //handleCommand(command);

      char c = Serial.read();
      if (c == '\n') {          // fin de commande
        serialBuffer.trim();
        handleCommand(serialBuffer);
        serialBuffer = "";     // reset buffer
      } else {
        serialBuffer += c;     // accumuler
      }
    }
  }
  
}


void handleCommand(const String& command) {
  lcd.clear(); // Reset the LCD Screen before handling command
  if (command == "OPEN_DOOR") {
    openDoor();
  } else if (command == "CLOSE_DOOR") {
    closeDoor();
  } else if (command == "TURN_ON_FAN") {
    turnOnFan();
  } else if (command == "TURN_OFF_FAN") {
    turnOffFan();
  } else if (command == "TURN_ON_LIGHTS") {
    turnOnLights();
  } else if (command == "TURN_OFF_LIGHTS") {
    turnOffLights();
  } else if (command.startsWith("DOOR_CALIBRATION:")) {

    // Extraire la partie après le :
    String valueStr = command.substring(17);   // longueur de "CALIBRATION_DOOR:" = 17
    int angle = valueStr.toInt();               // convertir en int

    // Sécurité: limiter entre 0 et 180
    //angle = constrain(angle, 0, 90);

    doorServo.write(angle);

    lcd.print("Door calib:");
    lcd.print(angle);

    Serial.print("Door calibrated to ");
    Serial.println(angle);
  } else {
    lcd.print("UNKNOWN COMMAND");
  }

  Serial.print("ACK:");
  Serial.println(command);
}

void openDoor() {
  doorServo.write(90);
  lcd.print("OPEN DOOR");
}

void closeDoor() {
  doorServo.write(0);
  lcd.print("CLOSE DOOR");
}

void turnOnFan() {
  // Logique Activer ou Eteindre le ventilateur
  fanIsOn = true;
  lcd.print("TURN ON FAN :" + String(fan_speed_value));
}

void turnOffFan() {
  fanIsOn = false;
  analogWrite(FAN_PIN, 0);
  lcd.print("TURN OFF FAN");
}

void turnOnLights() {
  digitalWrite(LED_PIN_1, HIGH);
  digitalWrite(LED_PIN_2, HIGH);
  digitalWrite(LED_PIN_3, HIGH);

  lcd.print("TURN ON LED");
}

void turnOffLights() {
  digitalWrite(LED_PIN_1, LOW);
  digitalWrite(LED_PIN_2, LOW);
  digitalWrite(LED_PIN_3, LOW);

  lcd.print("TURN OFF LED");
}
