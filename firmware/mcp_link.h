#ifndef MCP_LINK_H
#define MCP_LINK_H

#include <Arduino.h>
#include "devices.h"

// simple structure pour partager les objets
struct DevicesContext {
  Led* led1;
  ServoMotor* servo1;
};

void mcp_init();
void mcp_poll(DevicesContext& ctx);

#endif
