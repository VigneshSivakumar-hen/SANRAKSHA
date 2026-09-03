#ifndef SENSOR_CONFIG_H
#define SENSOR_CONFIG_H

// ---- WiFi ----
#define WIFI_SSID      "your-wifi-ssid"
#define WIFI_PASSWORD  "your-wifi-password"

// ---- MQTT broker (the IoT gateway's host, see iot/gateway/gateway.py) ----
#define MQTT_HOST      "192.168.1.10"   // gateway's local IP on-site
#define MQTT_PORT      1883
#define MQTT_CLIENT_ID "sanraksha-node-01"

// This node's location_id — MUST match a location_id already registered in
// the backend (see backend/data/sample/sample_readings.json or however you
// register real sites), since predictions are looked up by this id.
#define LOCATION_ID    "munnar-01"

// Published to: sanraksha/sensors/<LOCATION_ID>
#define MQTT_TOPIC_PREFIX "sanraksha/sensors/"

// ---- Pins ----
#define SOIL_MOISTURE_PIN   34   // ADC1 pin, capacitive soil moisture sensor
#define RAIN_SENSOR_PIN     35   // ADC1 pin, analog rain intensity sensor
#define DHT_PIN             4    // DHT22 temperature/humidity sensor
#define DHT_TYPE            DHT22

// ---- Calibration ----
// Raw ADC reading when the soil moisture probe is in DRY air / fully
// submerged in water. Recalibrate per sensor batch — cheap capacitive
// probes vary a lot unit to unit.
#define SOIL_ADC_DRY   3200
#define SOIL_ADC_WET   1200

// Rain sensor: raw ADC reading with a dry board vs. fully wet board.
#define RAIN_ADC_DRY   4095
#define RAIN_ADC_WET   1500

// ---- Timing ----
#define PUBLISH_INTERVAL_MS  60000   // publish a reading once a minute
#define DEEP_SLEEP_SECONDS   0       // set >0 to deep-sleep between readings (battery nodes)

#endif  // SENSOR_CONFIG_H
