#include "devices.h"

// === Led ===
Led::Led(int p) : pin(p) {}

void Led::begin() {
  pinMode(pin, OUTPUT);
  off();
}

void Led::on() {
  digitalWrite(pin, HIGH);
}

void Led::off() {
  digitalWrite(pin, LOW);
}

// === ServoMotor ===
ServoMotor::ServoMotor(int p) : pin(p) {}

void ServoMotor::begin() {
  servo.attach(pin);
  setAngle(0);
}

void ServoMotor::setAngle(int angle) {
  angle = constrain(angle, 0, 180);
  servo.write(angle);
}
