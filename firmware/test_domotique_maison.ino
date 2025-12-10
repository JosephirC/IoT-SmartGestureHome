#include "devices.h"
#include "mcp_link.h"

// === Instances des périphériques ===
Led ledSalon(5);
ServoMotor servoVolet(6);

// Contexte pour le module MCP
DevicesContext devicesCtx;

void setup() {
  // init devices
  ledSalon.begin();
  servoVolet.begin();

  // relier le contexte au matériel réel
  devicesCtx.led1 = &ledSalon;
  devicesCtx.servo1 = &servoVolet;

  // init lien serveur MCP
  mcp_init();
}

void loop() {
  // écouter les commandes venant du serveur MCP
  mcp_poll(devicesCtx);

  // ici tu peux ajouter des comportements locaux (scènes, sécurité, etc.)
}
