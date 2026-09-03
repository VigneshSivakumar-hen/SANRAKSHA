/*
 * Rain sensor reading — same sketch as soil_moisture.ino (Arduino IDE
 * compiles every .ino in this folder together as one sketch). Kept in its
 * own file/tab so the rain-sensing logic can be swapped or unit-tested
 * independently of the main loop.
 *
 * This assumes a simple resistive/capacitive analog rain board (e.g. the
 * common "raindrop sensor" modules), which reports "how wet the board
 * currently is", not cumulative rainfall in mm. Converting that into a
 * genuine 24h rainfall total needs either:
 *   (a) a tipping-bucket rain gauge instead (each tip = a fixed mm
 *       increment, counted via interrupt), or
 *   (b) accumulating this board's wetness readings into an estimated
 *       total over a rolling 24h window on the ESP32 or gateway.
 *
 * For now this returns an instantaneous 0-100 "wetness" estimate scaled
 * into a plausible mm figure — good enough to exercise the pipeline, but
 * swap in a tipping-bucket gauge for a real deployment.
 */

#include "sensor_config.h"

float readRainfallMm() {
  int raw = analogRead(RAIN_SENSOR_PIN);

  float wetnessPct = 100.0 * (float)(RAIN_ADC_DRY - raw) / (float)(RAIN_ADC_DRY - RAIN_ADC_WET);
  if (wetnessPct < 0) wetnessPct = 0;
  if (wetnessPct > 100) wetnessPct = 100;

  // Rough placeholder scaling: treat 100% board wetness as ~250mm/24h
  // equivalent intensity. Replace with a tipping-bucket accumulator for
  // real rainfall totals.
  return wetnessPct * 2.5;
}
