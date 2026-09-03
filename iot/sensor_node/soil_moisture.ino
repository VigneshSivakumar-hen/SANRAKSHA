/*
 * Sanraksha sensor node — main sketch.
 *
 * Arduino IDE combines every .ino file in this folder into one sketch, so
 * this file owns setup()/loop() and calls readRainfallMm(), which is
 * defined in rain_sensor.ino (same folder, separate tab).
 *
 * Hardware: ESP32 + capacitive soil moisture probe + analog rain sensor +
 * DHT22 temperature/humidity sensor. Reads all three, publishes one JSON
 * reading per location to MQTT for the gateway (../gateway/gateway.py) to
 * forward to the backend.
 *
 * Libraries required (Arduino Library Manager):
 *   - PubSubClient   (MQTT client)
 *   - DHT sensor library (Adafruit)
 *   - ArduinoJson
 *
 * NOT tested against real hardware in this repo — reference firmware for
 * you to flash and calibrate once nodes are deployed. See sensor_config.h
 * for WiFi/MQTT/pin/calibration constants.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "sensor_config.h"

WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastPublish = 0;

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected");
  Serial.println(WiFi.localIP());
}

void connectMqtt() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");
    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" connected");
    } else {
      Serial.print(" failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 3s");
      delay(3000);
    }
  }
}

float readSoilMoisturePct() {
  int raw = analogRead(SOIL_MOISTURE_PIN);
  // Lower raw ADC = wetter, for typical capacitive probes.
  float pct = 100.0 * (float)(SOIL_ADC_DRY - raw) / (float)(SOIL_ADC_DRY - SOIL_ADC_WET);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

void publishReading() {
  float soilPct = readSoilMoisturePct();
  float rainfallMm = readRainfallMm();  // defined in rain_sensor.ino
  float tempC = dht.readTemperature();
  if (isnan(tempC)) tempC = 20.0;  // sensor read failure fallback

  StaticJsonDocument<256> doc;
  doc["rainfall_mm_24h"] = rainfallMm;
  doc["soil_moisture_pct"] = soilPct;
  doc["temperature_c"] = tempC;

  char payload[256];
  size_t len = serializeJson(doc, payload);

  char topic[128];
  snprintf(topic, sizeof(topic), "%s%s", MQTT_TOPIC_PREFIX, LOCATION_ID);

  mqttClient.publish(topic, payload, len);

  Serial.print("Published to ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payload);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);  // ESP32: 0-4095
  dht.begin();

  connectWifi();
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  if (!mqttClient.connected()) {
    connectMqtt();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;
    publishReading();
  }

#if DEEP_SLEEP_SECONDS > 0
  esp_sleep_enable_timer_wakeup((uint64_t)DEEP_SLEEP_SECONDS * 1000000ULL);
  esp_deep_sleep_start();
#endif
}
