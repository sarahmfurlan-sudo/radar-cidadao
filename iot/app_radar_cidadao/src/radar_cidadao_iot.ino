/* ---- Includes ---- */
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "ESP32SensorsDistancia.hpp"
#include "ESP32SensorsChuva.hpp"

/* ---- Config Hardware (alinhado ao diagram.json) ---- */
const uint8_t TRIG_PIN = 19;
const uint8_t ECHO_PIN = 18;
const uint8_t CHUVA_PIN = 34;       // Potenciometro simulando intensidade de chuva (ADC1)
const uint8_t LED_ALERTA_PIN = 4;   // LED vermelho de alerta local

/* ---- Parametros do Bueiro / Limiares de Risco ---- */
const float ALTURA_BUEIRO_CM = 100.0f;   // Profundidade de referencia (sensor ate o fundo seco)
const float DIST_CRITICA_CM = 10.0f;     // Distancia minima ate a tampa (100% cheio)
const float LIMIAR_CHUVA_ATIVA = 20.0f;  // >= 20% indica chuva ativa
const float LIMIAR_CHUVA_FORTE = 50.0f;  // >= 50% indica chuva forte
const float LIMIAR_AGUA_ATENCAO = 40.0f; // >= 40% nivel de atencao
const float LIMIAR_AGUA_ALERTA = 70.0f;  // >= 70% + chuva forte (ou >= 85% isolado) = ALERTA

/* ---- Config Wi-Fi e MQTT ---- */
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";
#define MQTT_SERVER "host.wokwi.internal"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "RadarCidadao_Bueiro01"
#define REGIAO_PONTO "Pompeia - Ponto 01"
#define MQTT_PUB_TELEMETRIA "radarcidadao/bueiro01/telemetria"
#define MQTT_PUB_ALERTA "radarcidadao/bueiro01/alerta"

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

/* ---- Controle de intervalo ---- */
const unsigned long INTERVALO_COLETA = 1000;
const unsigned long INTERVALO_RECONEXAO = 5000;
const unsigned long INTERVALO_PISCA_LED = 500;
unsigned long tempoAnterior = 0;
unsigned long ultimaTentativaWiFi = 0;
unsigned long ultimaTentativaMQTT = 0;
unsigned long ultimoPiscaLed = 0;
bool estadoLed = false;

/* ---- Estado atual ---- */
float distanciaCm = NAN;
float nivelAguaPct = 0.0f;
float chuvaPct = 0.0f;
String nivelRisco = "NORMAL";
String riscoAnterior = "NORMAL";

/* ---- Prototipos ---- */
void conectarWiFi();
void conectarMQTT();
float calcularNivelAguaPct(float distCm);
String classificarRisco(float aguaPct, float chuva);
void atualizarLedAlerta();
bool publicarTelemetria();
void publicarAlertaSeNecessario();

void setup() {
  Serial.begin(115200);
  pinMode(LED_ALERTA_PIN, OUTPUT);
  digitalWrite(LED_ALERTA_PIN, LOW);

  ESP32Sensors::Distancia::inicializar(TRIG_PIN, ECHO_PIN);
  ESP32Sensors::Chuva::inicializar(CHUVA_PIN);

  delay(INTERVALO_RECONEXAO);
  conectarWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setBufferSize(768);
  mqttClient.setKeepAlive(120);

  Serial.println("distancia_cm,nivel_agua_pct,chuva_pct,nivel_risco");
}

void loop() {
  if (millis() - tempoAnterior >= INTERVALO_COLETA) {
    tempoAnterior = millis();

    distanciaCm = ESP32Sensors::Distancia::medirDistancia();
    nivelAguaPct = calcularNivelAguaPct(distanciaCm);
    chuvaPct = ESP32Sensors::Chuva::medirIntensidadePct();
    nivelRisco = classificarRisco(nivelAguaPct, chuvaPct);

    publicarTelemetria();
    publicarAlertaSeNecessario();
    riscoAnterior = nivelRisco;
  }

  atualizarLedAlerta();

  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  } else if (!mqttClient.connected()) {
    conectarMQTT();
  } else {
    mqttClient.loop();
  }
}

float calcularNivelAguaPct(float distCm) {
  if (isnan(distCm) || distCm >= ALTURA_BUEIRO_CM) {
    return 0.0f;
  }
  if (distCm <= DIST_CRITICA_CM) {
    return 100.0f;
  }
  float pct = ((ALTURA_BUEIRO_CM - distCm) / (ALTURA_BUEIRO_CM - DIST_CRITICA_CM)) * 100.0f;
  return constrain(pct, 0.0f, 100.0f);
}

String classificarRisco(float aguaPct, float chuva) {
  if ((aguaPct >= LIMIAR_AGUA_ALERTA && chuva >= LIMIAR_CHUVA_FORTE) || aguaPct >= 85.0f) {
    return "ALERTA";
  }
  if (aguaPct >= LIMIAR_AGUA_ATENCAO || chuva >= LIMIAR_CHUVA_FORTE) {
    return "ATENCAO";
  }
  return "NORMAL";
}

void atualizarLedAlerta() {
  if (nivelRisco == "ALERTA") {
    digitalWrite(LED_ALERTA_PIN, HIGH);
  } else if (nivelRisco == "ATENCAO") {
    if (millis() - ultimoPiscaLed >= INTERVALO_PISCA_LED) {
      ultimoPiscaLed = millis();
      estadoLed = !estadoLed;
      digitalWrite(LED_ALERTA_PIN, estadoLed ? HIGH : LOW);
    }
  } else {
    estadoLed = false;
    digitalWrite(LED_ALERTA_PIN, LOW);
  }
}

void conectarWiFi() {
  if (millis() - ultimaTentativaWiFi < INTERVALO_RECONEXAO) {
    return;
  }
  ultimaTentativaWiFi = millis();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);
}

void conectarMQTT() {
  if (millis() - ultimaTentativaMQTT < INTERVALO_RECONEXAO) {
    return;
  }
  ultimaTentativaMQTT = millis();

  if (mqttClient.connect(MQTT_CLIENT_ID)) {
    Serial.println("[MQTT] Conectado ao broker");
  } else {
    Serial.printf("[MQTT] Falha na conexao: %d\r\n", mqttClient.state());
  }
}

bool publicarTelemetria() {
  Serial.printf("%.1f,%.1f,%.1f,%s\r\n",
                isnan(distanciaCm) ? -1.0f : distanciaCm,
                nivelAguaPct,
                chuvaPct,
                nivelRisco.c_str());

  JsonDocument doc;
  doc["device"] = MQTT_CLIENT_ID;
  doc["regiao"] = REGIAO_PONTO;
  doc["distancia_cm"] = isnan(distanciaCm) ? -1.0f : roundf(distanciaCm * 10.0f) / 10.0f;
  doc["nivel_agua_pct"] = roundf(nivelAguaPct * 10.0f) / 10.0f;
  doc["chuva_pct"] = roundf(chuvaPct * 10.0f) / 10.0f;
  doc["chuva_ativa"] = (chuvaPct >= LIMIAR_CHUVA_ATIVA);
  doc["nivel_risco"] = nivelRisco;
  doc["alerta_ativo"] = (nivelRisco == "ALERTA");

  String payload;
  serializeJson(doc, payload);
  if (!mqttClient.connected()) {
    return false;
  }
  bool ok = mqttClient.publish(MQTT_PUB_TELEMETRIA, payload.c_str());
  Serial.println(ok ? "[MQTT] Telemetria publicada" : "[MQTT] Falha ao publicar telemetria");
  return ok;
}

void publicarAlertaSeNecessario() {
  if (!mqttClient.connected()) {
    return;
  }
  // Publica evento no topico dedicado quando entra em ALERTA ou muda de estado para ATENCAO/NORMAL
  if (nivelRisco == "ALERTA" || nivelRisco != riscoAnterior) {
    JsonDocument doc;
    doc["device"] = MQTT_CLIENT_ID;
    doc["regiao"] = REGIAO_PONTO;
    doc["nivel_risco"] = nivelRisco;
    doc["nivel_agua_pct"] = roundf(nivelAguaPct * 10.0f) / 10.0f;
    doc["chuva_pct"] = roundf(chuvaPct * 10.0f) / 10.0f;
    doc["mensagem"] = (nivelRisco == "ALERTA")
      ? "Risco de alagamento confirmado por sensores. Evite a via e acione 199 (Defesa Civil) ou 193 em emergencia."
      : (nivelRisco == "ATENCAO"
        ? "Chuva forte ou elevacao do nivel de agua detectada no bueiro."
        : "Nivel normalizado no ponto monitorado.");

    String payload;
    serializeJson(doc, payload);
    mqttClient.publish(MQTT_PUB_ALERTA, payload.c_str());
  }
}

