#include "mcp_link.h"

static String inputLine;

void mcp_init() {
  Serial.begin(115200);  // lien avec ton serveur MCP
  inputLine.reserve(64);
}

// à appeler régulièrement dans loop()
void mcp_poll(DevicesContext& ctx) {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      // une ligne complète reçue -> on la traite
      inputLine.trim();
      if (inputLine.length() > 0) {

        // Parsing très simple, à améliorer si besoin
        if (inputLine.startsWith("LED 1 ")) {
          if (inputLine.endsWith("ON")) {
            ctx.led1->on();
          } else if (inputLine.endsWith("OFF")) {
            ctx.led1->off();
          }
        }
        else if (inputLine.startsWith("SERVO 1 ")) {
          int spaceIndex = inputLine.lastIndexOf(' ');
          if (spaceIndex > 0) {
            int angle = inputLine.substring(spaceIndex + 1).toInt();
            ctx.servo1->setAngle(angle);
          }
        }
      }
      inputLine = "";
    } else {
      inputLine += c;
    }
  }
}
