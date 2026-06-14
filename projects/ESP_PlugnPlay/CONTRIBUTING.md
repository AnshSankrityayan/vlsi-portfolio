# Contributing

Thanks for wanting to make this better. Contributions of all sizes are welcome — whether that's adding a new sensor to the library, fixing a bug, improving the docs, or making the UI nicer.

---

## The fastest thing you can do: add a sensor to the library

The sensor catalog lives entirely in [`data/app.js`](data/app.js). Adding a new sensor takes about 10 lines of JavaScript — no firmware knowledge required.

Open `data/app.js` and find the `CATALOG` array near the top. Add a new entry:

```js
{
  name: "Your Sensor Name",          // shown on the library card
  category: "Your Category",         // groups sensors in the picker (see below)
  label: "Dashboard Display Name",   // pre-filled in the Label field
  type: "analog",                    // firmware type — must match an existing type
  desc: "One-line description of what it measures and how",
  wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",  // wiring shorthand
  pin: 34,                           // suggested GPIO pin
  pin2: -1,                          // set to a number only for ultrasonic sensors
  warnHigh: 2000,                    // optional — amber threshold
  dangerHigh: 3500,                  // optional — red threshold
  warnLow: null,                     // optional — amber low threshold
  dangerLow: null,                   // optional — red low threshold
},
```

### Existing firmware types

Use one of these for `type` — these are the types the firmware already understands:

| Type | What the firmware does |
|---|---|
| `analog` | `analogRead(pin)`, returns raw 0–4095 |
| `temperature` | `analogRead(pin)`, returns raw 0–4095 |
| `humidity` | `analogRead(pin)`, returns raw 0–4095 |
| `gas` | `analogRead(pin)`, returns raw 0–4095 |
| `soil` | `analogRead(pin)`, inverts to 0–100% |
| `ldr` | `analogRead(pin)`, scales to 0–100% |
| `digital` | `digitalRead(pin)`, returns 0 or 1 |
| `pir` | `digitalRead(pin)`, returns 0 or 1 |
| `relay` | `digitalRead(pin)`, adds toggle button to card |
| `dht11` | DHT11 library, returns temp + humidity |
| `dht22` | DHT22 library, returns temp + humidity |
| `ultrasonic` | `pulseIn()`, returns distance in cm |

### Existing categories

To keep the library picker tidy, use an existing category if your sensor fits:

- `Temp / Humidity`
- `Gas / Air`
- `Distance`
- `Light`
- `Soil / Water`
- `Motion / Presence`
- `Sound`
- `Electrical`
- `Output`

Add a new category string if none of these fit — it will appear automatically.

### Then add the wiring to SENSORS.md

Add a section to [`docs/SENSORS.md`](docs/SENSORS.md) following the same format as the existing entries:
- What it measures
- Pinout table
- ASCII wiring diagram
- Any important notes (voltage levels, preheat, calibration)

---

## Adding a new sensor *type* to the firmware

If your sensor needs firmware support that doesn't exist yet (e.g. a new protocol, an I²C sensor, a pulse counter), you'll need to edit `src/main.cpp`.

### Steps

1. **Add to the enum** near the top of `main.cpp`:
   ```cpp
   enum SensorKind {
     KIND_ANALOG, KIND_DIGITAL, KIND_DHT11, KIND_DHT22,
     KIND_ULTRASONIC, KIND_RELAY,
     KIND_YOUR_NEW_SENSOR,   // ← add here
   };
   ```

2. **Map the type string** in `kindFromType()`:
   ```cpp
   if (type == "your_type") return KIND_YOUR_NEW_SENSOR;
   ```

3. **Set up the GPIO** in `applySensorPins()`:
   ```cpp
   } else if (s.kind == KIND_YOUR_NEW_SENSOR) {
     pinMode(s.pin, INPUT);
     // any initialisation your sensor needs
   }
   ```

4. **Read the sensor** in `readSensor()`:
   ```cpp
   } else if (cfg.kind == KIND_YOUR_NEW_SENSOR) {
     r.value = yourReadFunction(cfg.pin);
     r.healthy = isfinite(r.value);
   }
   ```

5. **Add a unit** in `unitForType()`:
   ```cpp
   if (t == "your_type") return "unit";
   ```

6. **Add analysis text** in `analysisFor()`:
   ```cpp
   if (cfg.type == "your_type") {
     if (value > HIGH_THRESHOLD) return "high";
     return "normal";
   }
   ```

7. **Add to the browser catalog** (see above)

8. **Add wiring to SENSORS.md**

---

## General code contributions

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/esp32-sensor-dashboard.git
cd esp32-sensor-dashboard
# Open in VS Code with PlatformIO installed
```

### Build

```bash
pio run               # compile firmware
pio run --target uploadfs   # upload web files
pio run --target upload     # upload firmware
pio device monitor --baud 115200  # open serial monitor
```

### Code style

- C++ (firmware): follow the style in `main.cpp` — static functions, minimal globals, clear variable names
- JavaScript (frontend): vanilla JS, no frameworks, no build step
- Keep the web files small — they live in the ESP32's limited LittleFS flash
- No comments that restate what the code obviously does — only comment the *why* when it's non-obvious

### Pull request checklist

- [ ] Firmware compiles without errors or warnings
- [ ] New sensor added to both the JS catalog AND `docs/SENSORS.md`
- [ ] New firmware sensor type handles the disabled/offline case gracefully
- [ ] Tested on actual hardware (or clearly marked as untested)
- [ ] PR description explains what the sensor is and what it measures

---

## Reporting bugs

Open an issue with:
- What you expected to happen
- What actually happened
- Your ESP32 board (DevKit v1, ESP32-WROOM, etc.)
- The sensor you're using
- Serial Monitor output if the issue is firmware-side

---

## Ideas that would be great to see

- **BMP280 / BME280** — I²C pressure + temperature + humidity (needs I²C reading in firmware)
- **BME680** — air quality with actual TVOC / eCO₂ readings
- **DS18B20** — 1-Wire temperature, multiple sensors on one pin
- **PZEM-004T** — AC power monitoring (voltage, current, power, energy)
- **OTA firmware updates** — update without USB
- **Grafana / InfluxDB export** — push data to a time-series database
- **Historical chart** — longer than 72 points, maybe stored in SPIFFS as a rolling file
- **Notifications** — WebPush or email when a threshold is crossed

If you build any of these, a PR would make a lot of people happy.
