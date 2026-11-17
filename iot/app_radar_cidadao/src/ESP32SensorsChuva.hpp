#pragma once
#include <Arduino.h>

namespace ESP32Sensors {
  namespace Chuva {
    static uint8_t pino = 0;

    void inicializar(uint8_t adcPin) {
      pino = adcPin;
      pinMode(pino, INPUT);
    }

    // Converte a leitura ADC (0..4095) em intensidade simulada de chuva (0..100%).
    float medirIntensidadePct() {
      int leitura = analogRead(pino);
      return (leitura / 4095.0f) * 100.0f;
    }
  }
}

