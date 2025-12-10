#ifndef DEVICES_H
#define DEVICES_H

#include <Arduino.h>
#include <Servo.h>

class Led {
  int pin;
public:
  Led(int p);
  void begin();
  void on();
  void off();
};

class ServoMotor {
  int pin;
  Servo servo;
public:
  ServoMotor(int p);
  void begin();
  void setAngle(int angle);
};

// tu pourras ajouter moteur DC, relais, etc.

#endif
