#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <LittleFS.h>
#include <Preferences.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <DHT.h>

static const char *WIFI_SSID = "";   // leave blank to use AP only, or set your 2.4GHz SSID
static const char *WIFI_PASS = "";   // your WiFi password
static const char *AP_SSID  = "ESP32-Dashboard";
static const char *AP_PASS  = "esp32setup";

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");
Preferences prefs;

enum SensorKind { KIND_ANALOG, KIND_DIGITAL, KIND_DHT11, KIND_DHT22, KIND_ULTRASONIC, KIND_RELAY };

struct SensorConfig {
  String id, label, type;
  SensorKind kind;
  int pin, pin2;
  float warnLow, warnHigh, dangerLow, dangerHigh;
  bool enabled;
};

struct SensorReading {
  String id, label, type, unit, unit2, status, analysis;
  float value, value2;
  bool healthy;
};

static SensorConfig sensors[12];
static size_t sensorCount = 0;
static DHT *dhtObjects[12] = {};
static unsigned long lastBroadcastMs = 0;
static unsigned long lastDeviceBroadcastMs = 0;
static String csvLog = "time_ms,id,label,type,value,unit,status,analysis\n";

// ─── Sensor helpers ──────────────────────────────────────────────────────────

static SensorKind kindFromType(const String &t) {
  if (t == "dht11")      return KIND_DHT11;
  if (t == "dht22")      return KIND_DHT22;
  if (t == "ultrasonic") return KIND_ULTRASONIC;
  if (t == "digital")    return KIND_DIGITAL;
  if (t == "relay")      return KIND_RELAY;
  return KIND_ANALOG;
}

static String defaultLabel(const String &t) {
  if (t == "temperature") return "Temperature";
  if (t == "humidity")    return "Humidity";
  if (t == "gas")         return "Gas";
  if (t == "soil")        return "Soil Moisture";
  if (t == "ldr")         return "Light";
  if (t == "pir")         return "Motion";
  if (t == "dht11")       return "DHT11";
  if (t == "dht22")       return "DHT22";
  if (t == "ultrasonic")  return "Distance";
  if (t == "relay")       return "Relay";
  return "Sensor";
}

static String unitForType(const String &t) {
  if (t == "temperature") return "C";
  if (t == "humidity")    return "%";
  if (t == "gas")         return "ppm";
  if (t == "soil")        return "%";
  if (t == "ldr")         return "%";
  if (t == "ultrasonic")  return "cm";
  if (t == "pir" || t == "digital" || t == "relay") return "";
  return "raw";
}

static String statusFromThresholds(float value, const SensorConfig &cfg) {
  if (!isfinite(value)) return "offline";
  if ((cfg.dangerLow  != -99999 && value <= cfg.dangerLow)  ||
      (cfg.dangerHigh !=  99999 && value >= cfg.dangerHigh)) return "danger";
  if ((cfg.warnLow    != -99999 && value <= cfg.warnLow)    ||
      (cfg.warnHigh   !=  99999 && value >= cfg.warnHigh))   return "warning";
  return "ok";
}

static String analysisFor(const SensorConfig &cfg, float value, const String &status) {
  if (status == "offline") return "Sensor not responding";
  if (cfg.kind == KIND_DHT11 || cfg.kind == KIND_DHT22 || cfg.type == "temperature") {
    if (value >= 40) return "unsafe heat level";
    if (value >= 32) return "high";
    if (value <= 15) return "cold";
    return "normal";
  }
  if (cfg.type == "humidity") {
    if (value < 35) return "dry";
    if (value > 70) return "humid";
    return "comfortable";
  }
  if (cfg.type == "gas")  { return status == "ok" ? "safe" : status; }
  if (cfg.type == "soil") {
    if (value < 35) return "dry";
    if (value > 75) return "saturated";
    return "good";
  }
  if (cfg.type == "ldr") {
    if (value < 20) return "dark";
    if (value > 80) return "bright";
    return "normal";
  }
  if (cfg.type == "pir")       return value > 0.5 ? "motion detected" : "clear";
  if (cfg.type == "ultrasonic") return value < 15  ? "object very close" : "clear range";
  if (cfg.type == "relay")      return value > 0.5 ? "ON" : "OFF";
  return status == "ok" ? "normal" : status;
}

// ─── DHT lifecycle ───────────────────────────────────────────────────────────

static void clearDhtObjects() {
  for (size_t i = 0; i < 12; i++) { delete dhtObjects[i]; dhtObjects[i] = nullptr; }
}

static void applySensorPins() {
  clearDhtObjects();
  for (size_t i = 0; i < sensorCount; i++) {
    SensorConfig &s = sensors[i];
    if (!s.enabled) continue;
    if (s.kind == KIND_RELAY)       pinMode(s.pin, OUTPUT);
    else if (s.kind == KIND_DIGITAL) pinMode(s.pin, INPUT);
    else if (s.kind == KIND_ULTRASONIC) {
      pinMode(s.pin,  OUTPUT);
      pinMode(s.pin2, INPUT);
    } else if (s.kind == KIND_DHT11 || s.kind == KIND_DHT22) {
      dhtObjects[i] = new DHT(s.pin, s.kind == KIND_DHT11 ? DHT11 : DHT22);
      dhtObjects[i]->begin();
    }
  }
}

// ─── Config persistence ──────────────────────────────────────────────────────

static bool parseConfig(const String &json) {
  JsonDocument doc;
  if (deserializeJson(doc, json) || !doc["sensors"].is<JsonArray>()) return false;
  sensorCount = 0;
  for (JsonObject item : doc["sensors"].as<JsonArray>()) {
    if (sensorCount >= 12) break;
    SensorConfig &s = sensors[sensorCount++];
    s.type      = item["type"]    | "analog";
    s.kind      = kindFromType(s.type);
    String fid  = "sensor_" + String(sensorCount);
    s.id        = item["id"]      | fid;
    s.label     = item["label"]   | defaultLabel(s.type);
    s.pin       = item["pin"]     | 34;
    s.pin2      = item["pin2"]    | -1;
    s.enabled   = item["enabled"] | true;
    s.warnLow   = item["warnLow"]   | -99999.0f;
    s.warnHigh  = item["warnHigh"]  |  99999.0f;
    s.dangerLow = item["dangerLow"] | -99999.0f;
    s.dangerHigh= item["dangerHigh"]|  99999.0f;
  }
  applySensorPins();
  return true;
}

static String configToJson() {
  JsonDocument doc;
  JsonArray arr = doc["sensors"].to<JsonArray>();
  for (size_t i = 0; i < sensorCount; i++) {
    JsonObject item = arr.add<JsonObject>();
    item["id"]      = sensors[i].id;
    item["label"]   = sensors[i].label;
    item["type"]    = sensors[i].type;
    item["pin"]     = sensors[i].pin;
    item["pin2"]    = sensors[i].pin2;
    item["enabled"] = sensors[i].enabled;
    if (sensors[i].warnLow   != -99999) item["warnLow"]   = sensors[i].warnLow;
    if (sensors[i].warnHigh  !=  99999) item["warnHigh"]  = sensors[i].warnHigh;
    if (sensors[i].dangerLow != -99999) item["dangerLow"] = sensors[i].dangerLow;
    if (sensors[i].dangerHigh!=  99999) item["dangerHigh"]= sensors[i].dangerHigh;
  }
  String out; serializeJson(doc, out); return out;
}

static void saveConfig(const String &json) {
  prefs.begin("dashboard", false);
  prefs.putString("config", json);
  prefs.end();
}

static void loadConfig() {
  prefs.begin("dashboard", true);
  String saved = prefs.getString("config", "");
  prefs.end();
  if (!saved.length() || !parseConfig(saved)) sensorCount = 0;
}

// ─── Serial pin map ───────────────────────────────────────────────────────────

static void printPinMap() {
  Serial.println();
  Serial.println("  ╔══════════════════════════════════════════╗");
  Serial.println("  ║        ESP32 Sensor Dashboard            ║");
  Serial.println("  ╠══════════════════════════════════════════╣");

  if (sensorCount == 0) {
    Serial.println("  ║  No sensors configured.                  ║");
    Serial.println("  ║  Open the dashboard → Setup to add them. ║");
  } else {
    Serial.println("  ║  GPIO  │ Type        │ Label             ║");
    Serial.println("  ║────────┼─────────────┼───────────────────║");
    for (size_t i = 0; i < sensorCount; i++) {
      SensorConfig &s = sensors[i];
      char pinStr[10];
      if (s.kind == KIND_ULTRASONIC)
        snprintf(pinStr, sizeof(pinStr), "%2d/%-2d", s.pin, s.pin2);
      else
        snprintf(pinStr, sizeof(pinStr), "%-5d", s.pin);

      char line[46];
      snprintf(line, sizeof(line), "  ║  %-5s │ %-11s │ %-17s║",
               pinStr, s.type.c_str(), s.label.c_str());
      Serial.println(line);
    }
  }

  Serial.println("  ╠══════════════════════════════════════════╣");
  char apLine[46];
  snprintf(apLine, sizeof(apLine), "  ║  AP: %-36s║", AP_SSID);
  Serial.println(apLine);
  Serial.println("  ║  URL: http://192.168.4.1                 ║");
  Serial.println("  ╚══════════════════════════════════════════╝");
  Serial.println();
}

// ─── Sensor reading ──────────────────────────────────────────────────────────

static float readUltrasonicCm(int trig, int echo) {
  digitalWrite(trig, LOW);  delayMicroseconds(3);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long dur = pulseIn(echo, HIGH, 30000);
  return dur == 0 ? NAN : dur / 58.0f;
}

// ─── Pin probe ────────────────────────────────────────────────────────────────
// Reads every safe GPIO once and reports analog + digital values.
// ADC1 pins only for analog (ADC2 shares WiFi and gives garbage while connected).
static String pinProbeJson() {
  // ADC1-capable pins (safe with WiFi active)
  static const uint8_t analogPins[] = { 32, 33, 34, 35, 36, 39 };
  // Digital-readable pins (skips flash 6-11, UART 1/3, input-only 34-39 covered above)
  static const uint8_t digitalPins[] = { 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19,
                                         21, 22, 23, 25, 26, 27, 32, 33 };

  JsonDocument doc;
  doc["type"] = "pin_probe";
  JsonArray arr = doc["pins"].to<JsonArray>();

  // Analog pins — set INPUT, read multiple samples, report average + range
  for (uint8_t pin : analogPins) {
    pinMode(pin, INPUT);
    int s1 = analogRead(pin); delay(5);
    int s2 = analogRead(pin); delay(5);
    int s3 = analogRead(pin);
    int avg = (s1 + s2 + s3) / 3;
    int rng = max(s1, max(s2, s3)) - min(s1, min(s2, s3));
    bool active = avg > 50 || rng > 30;

    JsonObject p = arr.add<JsonObject>();
    p["pin"]     = pin;
    p["mode"]    = "analog";
    p["analog"]  = avg;
    p["range"]   = rng;          // noise/variation — high range = signal changing
    p["digital"] = avg > 2047 ? 1 : 0;
    p["active"]  = active;
  }

  // Digital-only scan
  for (uint8_t pin : digitalPins) {
    // skip pins already covered by analog list
    bool skip = false;
    for (uint8_t ap : analogPins) if (ap == pin) { skip = true; break; }
    if (skip) continue;

    pinMode(pin, INPUT);
    delay(1);
    int d = digitalRead(pin);

    JsonObject p = arr.add<JsonObject>();
    p["pin"]     = pin;
    p["mode"]    = "digital";
    p["analog"]  = -1;
    p["range"]   = 0;
    p["digital"] = d;
    p["active"]  = d == HIGH;
  }

  String out; serializeJson(doc, out); return out;
}

static float scaleAnalog(const SensorConfig &cfg, int raw) {
  if (cfg.type == "soil") return 100.0f - (raw / 4095.0f) * 100.0f;
  if (cfg.type == "ldr")  return (raw / 4095.0f) * 100.0f;
  return (float)raw;
}

static SensorReading readSensor(size_t i) {
  SensorConfig &cfg = sensors[i];
  SensorReading r;
  r.id = cfg.id; r.label = cfg.label; r.type = cfg.type;
  r.value = NAN; r.value2 = NAN;
  r.unit = unitForType(cfg.type); r.unit2 = "";
  r.healthy = cfg.enabled;

  if (!cfg.enabled) { r.status = "offline"; r.analysis = "disabled"; r.healthy = false; return r; }

  if (cfg.kind == KIND_DHT11 || cfg.kind == KIND_DHT22) {
    r.value  = dhtObjects[i] ? dhtObjects[i]->readTemperature() : NAN;
    r.value2 = dhtObjects[i] ? dhtObjects[i]->readHumidity()    : NAN;
    r.unit = "°C"; r.unit2 = "%";
    r.healthy = isfinite(r.value) && isfinite(r.value2);
  } else if (cfg.kind == KIND_ULTRASONIC) {
    r.value = readUltrasonicCm(cfg.pin, cfg.pin2);
    r.healthy = isfinite(r.value);
  } else if (cfg.kind == KIND_DIGITAL || cfg.kind == KIND_RELAY) {
    r.value = digitalRead(cfg.pin); r.healthy = true;
  } else {
    r.value = scaleAnalog(cfg, analogRead(cfg.pin)); r.healthy = true;
  }

  r.status   = statusFromThresholds(r.value, cfg);
  r.analysis = analysisFor(cfg, r.value, r.status);
  return r;
}

// ─── JSON payloads ────────────────────────────────────────────────────────────

static String deviceInfoJson() {
  JsonDocument doc;
  doc["type"]         = "device";
  doc["uptimeMs"]     = millis();
  doc["freeHeap"]     = ESP.getFreeHeap();
  doc["ip"]           = WiFi.status() == WL_CONNECTED
                          ? WiFi.localIP().toString()
                          : WiFi.softAPIP().toString();
  doc["clients"]      = ws.count();
  doc["wifiConnected"]= WiFi.status() == WL_CONNECTED;
  String out; serializeJson(doc, out); return out;
}

static String readingsJson() {
  JsonDocument doc;
  doc["type"]   = "sensor_update";
  doc["timeMs"] = millis();
  JsonArray arr = doc["sensors"].to<JsonArray>();

  for (size_t i = 0; i < sensorCount; i++) {
    SensorReading r = readSensor(i);
    JsonObject item = arr.add<JsonObject>();
    item["id"]      = r.id;
    item["label"]   = r.label;
    item["type"]    = r.type;
    if (isfinite(r.value))  item["value"]  = serialized(String(r.value,  2));
    else                    item["value"]  = nullptr;
    if (isfinite(r.value2)) item["value2"] = serialized(String(r.value2, 2));
    else                    item["value2"] = nullptr;
    item["unit"]    = r.unit;
    item["unit2"]   = r.unit2;
    item["status"]  = r.status;
    item["analysis"]= r.analysis;
    item["healthy"] = r.healthy;

    if (csvLog.length() < 32000) {
      csvLog += String(millis()) + "," + r.id + "," + r.label + "," + r.type + ",";
      csvLog += (isfinite(r.value) ? String(r.value, 2) : "") + "," + r.unit + ",";
      csvLog += r.status + "," + r.analysis + "\n";
    }
  }
  String out; serializeJson(doc, out); return out;
}

static String i2cScanJson() {
  JsonDocument doc;
  doc["type"] = "i2c_scan";
  JsonArray devices = doc["devices"].to<JsonArray>();
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      JsonObject d = devices.add<JsonObject>();
      char hex[8]; snprintf(hex, sizeof(hex), "0x%02X", addr);
      d["address"] = hex;
      if (addr == 0x76 || addr == 0x77)  d["hint"] = "BMP280 / BME280 / BME680";
      else if (addr == 0x3C || addr == 0x3D) d["hint"] = "OLED display";
      else if (addr == 0x68)              d["hint"] = "MPU6050 / DS3231 RTC";
      else if (addr == 0x40)              d["hint"] = "INA219 / SHT20";
      else if (addr == 0x48)              d["hint"] = "ADS1115 / TMP102";
      else                                d["hint"] = "Unknown I²C device";
    }
    delay(2);
  }
  String out; serializeJson(doc, out); return out;
}

static void sendConfig(AsyncWebSocketClient *client = nullptr) {
  JsonDocument doc;
  doc["type"] = "config";
  JsonDocument cfg; deserializeJson(cfg, configToJson());
  doc["config"] = cfg.as<JsonObject>();
  String out; serializeJson(doc, out);
  if (client) client->text(out); else ws.textAll(out);
}

// ─── WebSocket handler ────────────────────────────────────────────────────────

static void handleWsMessage(AsyncWebSocketClient *client, uint8_t *data, size_t len) {
  String msg; msg.reserve(len + 1);
  for (size_t i = 0; i < len; i++) msg += (char)data[i];

  JsonDocument doc;
  if (deserializeJson(doc, msg)) return;
  String type = doc["type"] | "";

  if (type == "get_config") {
    sendConfig(client);

  } else if (type == "save_config") {
    String cfgJson; serializeJson(doc["config"], cfgJson);
    if (parseConfig(cfgJson)) {
      saveConfig(cfgJson);
      sendConfig();
      ws.textAll(readingsJson());
      printPinMap();
    }

  } else if (type == "relay") {
    String id = doc["id"] | "";
    bool state = doc["state"] | false;
    for (size_t i = 0; i < sensorCount; i++) {
      if (sensors[i].id == id && sensors[i].kind == KIND_RELAY)
        digitalWrite(sensors[i].pin, state ? HIGH : LOW);
    }

  } else if (type == "clear_log") {
    csvLog = "time_ms,id,label,type,value,unit,status,analysis\n";

  } else if (type == "i2c_scan") {
    client->text(i2cScanJson());
  } else if (type == "pin_probe") {
    client->text(pinProbeJson());
  }
}

static void onWsEvent(AsyncWebSocket *, AsyncWebSocketClient *client,
                      AwsEventType type, void *arg, uint8_t *data, size_t len) {
  if (type == WS_EVT_CONNECT) {
    sendConfig(client);
    client->text(deviceInfoJson());
    client->text(readingsJson());
  } else if (type == WS_EVT_DATA) {
    auto *info = (AwsFrameInfo *)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT)
      handleWsMessage(client, data, len);
  }
}

// ─── WiFi ────────────────────────────────────────────────────────────────────

static void setupWiFi() {
  WiFi.persistent(false);
  WiFi.setSleep(false);
  WiFi.mode(WIFI_AP_STA);

  if (strlen(WIFI_SSID)) {
    Serial.printf("  Connecting to %s ...\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    unsigned long t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 12000) {
      Serial.print(".");
      delay(400);
    }
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("  Station IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
      Serial.println("  WiFi not connected (wrong creds or out of range).");
    }
  }

  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.printf("  Fallback AP: %s  →  http://%s\n",
                AP_SSID, WiFi.softAPIP().toString().c_str());
}

// ─── HTTP routes ──────────────────────────────────────────────────────────────

static void setupServer() {
  ws.onEvent(onWsEvent);
  server.addHandler(&ws);

  server.on("/api/config",     HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", configToJson()); });
  server.on("/api/readings",   HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", readingsJson()); });
  server.on("/api/device",     HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", deviceInfoJson()); });
  server.on("/api/i2c-scan",   HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", i2cScanJson()); });
  server.on("/api/pin-probe",  HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", pinProbeJson()); });
  server.on("/api/export.json",HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "application/json", readingsJson()); });
  server.on("/api/export.csv", HTTP_GET, [](AsyncWebServerRequest *r){ r->send(200, "text/csv", csvLog); });

  server.serveStatic("/", LittleFS, "/").setDefaultFile("index.html");
  server.onNotFound([](AsyncWebServerRequest *r){ r->send(404, "text/plain", "Not found"); });
  server.begin();
}

// ─── Arduino entry points ─────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(200);
  Wire.begin();
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  if (!LittleFS.begin(true)) Serial.println("LittleFS failed.");

  loadConfig();
  setupWiFi();
  setupServer();
  printPinMap();
}

void loop() {
  const unsigned long now = millis();

  if (now - lastBroadcastMs >= 1000) {
    lastBroadcastMs = now;
    ws.textAll(readingsJson());
    ws.cleanupClients();
  }

  if (now - lastDeviceBroadcastMs >= 3000) {
    lastDeviceBroadcastMs = now;
    ws.textAll(deviceInfoJson());
  }
}
