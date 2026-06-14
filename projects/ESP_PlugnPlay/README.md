# ESP32 Sensor Dashboard

**Connect a sensor. Pick it from a list. Watch the data live. That's it.**

A plug-and-play web dashboard that runs entirely on your ESP32 — no cloud, no mobile app, no complicated setup. Wire up any sensor, open a browser on your phone or laptop, pick the sensor from the built-in library, and a live graph appears on screen.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-ESP32-red.svg)
![Framework](https://img.shields.io/badge/framework-Arduino-teal.svg)
![Built with](https://img.shields.io/badge/built%20with-PlatformIO-orange.svg)

---

```
┌─────────────────────────────────────────────────────────────────┐
│  ESP32 Dashboard                  ● Live      [Dark]  [Setup]  │
├──────────┬───────────┬────────────┬────────────────────────────┤
│ IP       │ Uptime    │ Free heap  │ Clients                    │
│ 192.168… │ 4m 12s    │ 218 KB     │ 2                          │
├──────────┴───────────┴────────────┴────────────────────────────┤
│  Connected Sensors                                              │
│  [GPIO 34 · Soil Moisture · soil]  [GPIO 4 · DHT22 · dht22]   │
├───────────────────────────┬─────────────────────────────────────┤
│  Soil Moisture            │  DHT22 Temp+Humidity               │
│  soil · GPIO 34      ● OK │  dht22 · GPIO 4               ● OK │
│                           │                                     │
│          62.4 %           │         28.3 °C                     │
│  good                     │  normal    /   54.1 %               │
│  ▁▂▄▅▆▅▄▃▂▃▄▅▆▅          │  ▃▄▄▅▅▄▄▅▅▄▃▃▄▅▄                   │
└───────────────────────────┴─────────────────────────────────────┘
```

---

## Why does this exist?

Most ESP32 sensor projects look like this:

1. Copy-paste code from a forum post
2. Hard-code the sensor type and pin number
3. Flash, open Serial Monitor, squint at raw numbers
4. Want to add a second sensor → rewrite everything

This project flips that loop entirely. The ESP32 serves a web dashboard over WiFi. You add sensors from a menu in the browser, assign GPIO pins, hit Save — the dashboard builds itself from that config and starts streaming live data immediately. Add, remove, or swap sensors at any time without touching the firmware.

---

## Features

- **Live data over WebSocket** — readings update every second, no page refresh
- **Sensor library** — 25+ pre-built templates (DHT11/22, MQ gas sensors, HC-SR04, LDR, soil moisture, PIR, relay, and more). Pick one, confirm the pin, done
- **Pin Probe** — not sure which GPIO your sensor landed on? Hit *Probe Pins* and the ESP32 reads every safe GPIO at once and highlights the ones with a signal
- **I²C Scanner** — finds I²C devices (BMP280, OLED, MPU6050…) by address with a name hint
- **Warn / Danger thresholds** — set high/low limits per sensor; cards turn amber or red automatically
- **Relay control** — toggle relay outputs directly from the dashboard button
- **Sparkline charts** — 60-point rolling history graph on every sensor card
- **Dark mode** — because it looks better at 2am when your plant-watering project is still going
- **CSV + JSON export** — download your entire sensor log at any time
- **Offline-first** — everything runs on the ESP32. No internet required
- **Fallback AP** — if your WiFi isn't available the ESP32 spins up its own hotspot so you can always reach the dashboard
- **Config survives reboots** — saved to non-volatile flash. Wire it once and forget it

---

## What you need

| Thing | Notes |
|---|---|
| ESP32 development board | Any standard 30-pin or 38-pin ESP32 DevKit |
| Sensors | Whatever you have — see [Supported Sensors](docs/SENSORS.md) |
| USB cable | For flashing |
| [PlatformIO](https://platformio.org/install/ide?install=vscode) | Free VS Code extension — handles libraries and flashing |
| A browser | Chrome, Firefox, Safari — anything modern |

That's genuinely the whole list.

---

## Quick start

### 1 — Get the code

```bash
git clone https://github.com/YOUR_USERNAME/esp32-sensor-dashboard.git
cd esp32-sensor-dashboard
```

Open the folder in VS Code. PlatformIO will automatically install all dependencies.

### 2 — (Optional) Set your WiFi credentials

Open [`src/main.cpp`](src/main.cpp) and update lines 8–9:

```cpp
static const char *WIFI_SSID = "YourNetworkName";
static const char *WIFI_PASS = "YourPassword";
```

> **You can skip this entirely.** The ESP32 always starts a fallback hotspot called `ESP32-Dashboard` (password: `esp32setup`) that works without any router.

### 3 — Flash

```bash
# Step 1: Upload the web files (HTML/CSS/JS → ESP32 flash filesystem)
pio run --target uploadfs

# Step 2: Upload the firmware
pio run --target upload

# Step 3: Open Serial Monitor to see the boot output
pio device monitor --baud 115200
```

Or use the PlatformIO sidebar: click **Upload Filesystem Image**, then **Upload**.

### 4 — Open the dashboard

Connect to one of these:

| Option | How |
|---|---|
| **Your router** | Join your normal WiFi → open the IP shown in the Serial Monitor |
| **ESP32 hotspot** | Join `ESP32-Dashboard` (password: `esp32setup`) → open `http://192.168.4.1` |

The dashboard loads. It's empty. Let's fix that.

---

## Adding your first sensor

### The fast way — Sensor Library

1. Click **Setup** (top-right corner of the dashboard)
2. Click **+ From library**
3. Search for your sensor or browse by category
4. Click the sensor card
5. A config row appears — **pre-filled** with the right type, label, and thresholds
6. Change the **GPIO pin** to match where you actually wired your sensor
7. Click **Save config**

Your sensor card appears immediately and starts streaming live data.

### Not sure which pin your sensor is on?

Click **Probe Pins** inside the Setup panel. The ESP32 reads every safe GPIO simultaneously and shows:

- **Green / ACTIVE** — this pin has a signal. Your sensor is probably here
- Raw analog value (0–4095) and percentage for analog pins
- HIGH / LOW for digital pins
- A Δ (delta) value — if it's high, the signal is fluctuating, which is a great sign of a live sensor

### Adding something not in the library

Click **+ Blank** and fill in the fields manually:

| Field | What to put |
|---|---|
| Label | Whatever you want to call it |
| Type | Pick the closest match from the dropdown |
| Data / Trig pin | The GPIO number on your board |
| Echo pin | HC-SR04 ultrasonic only (the ECHO wire) |
| Warn high | Value above which the card turns amber |
| Danger high | Value above which the card turns red |

---

## Supported sensors

Full wiring diagrams and connection notes: **[docs/SENSORS.md](docs/SENSORS.md)**

| Sensor | Library type | Signal | What it measures |
|---|---|---|---|
| DHT11 | `dht11` | Digital | Temperature °C + Humidity % |
| DHT22 / AM2302 | `dht22` | Digital | Temperature °C + Humidity % (more accurate) |
| LM35 | `temperature` | Analog | Temperature (10mV/°C) |
| NTC Thermistor | `analog` | Analog | Temperature via resistance |
| MQ-2 | `gas` | Analog | LPG, propane, smoke |
| MQ-3 | `gas` | Analog | Alcohol, ethanol |
| MQ-4 | `gas` | Analog | Methane, natural gas |
| MQ-5 | `gas` | Analog | LPG, natural gas |
| MQ-7 | `gas` | Analog | Carbon monoxide |
| MQ-9 | `gas` | Analog | CO + combustible gases |
| MQ-135 | `gas` | Analog | Air quality (CO₂, ammonia, benzene) |
| HC-SR04 | `ultrasonic` | Digital | Distance in cm (needs 2 pins) |
| LDR | `ldr` | Analog | Light level 0–100% |
| Capacitive soil moisture | `soil` | Analog | Soil moisture 0–100% |
| Resistive soil moisture | `soil` | Analog | Soil moisture 0–100% |
| Water level sensor | `analog` | Analog | Water depth / level |
| Rain sensor | `analog` | Analog | Rainfall / moisture on plate |
| PIR HC-SR501 | `pir` | Digital | Motion detection |
| IR obstacle sensor | `digital` | Digital | Obstacle in front of sensor |
| TTP223 touch sensor | `digital` | Digital | Capacitive touch |
| Sound sensor KY-037 | `analog` | Analog | Ambient sound level |
| Voltage divider | `analog` | Analog | Voltage monitoring |
| ACS712 current sensor | `analog` | Analog | AC/DC current (5A/20A/30A) |
| Relay module | `relay` | Digital | Switch control from dashboard |

---

## Serial Monitor pin map

Every boot and after every config save, the ESP32 prints a pin map table to Serial so you can instantly verify what's connected where:

```
  ╔══════════════════════════════════════════╗
  ║        ESP32 Sensor Dashboard            ║
  ╠══════════════════════════════════════════╣
  ║  GPIO  │ Type        │ Label             ║
  ║────────┼─────────────┼───────────────────║
  ║  34    │ soil        │ Soil Moisture     ║
  ║  4     │ dht22       │ DHT22             ║
  ║  5/18  │ ultrasonic  │ Distance          ║
  ╠══════════════════════════════════════════╣
  ║  AP: ESP32-Dashboard                     ║
  ║  URL: http://192.168.4.1                 ║
  ╚══════════════════════════════════════════╝
```

---

## REST API endpoints

The ESP32 also exposes HTTP endpoints if you want to pull data into other tools:

| Endpoint | Returns |
|---|---|
| `GET /api/readings` | Latest sensor values as JSON |
| `GET /api/config` | Current sensor config |
| `GET /api/device` | Uptime, heap, IP, client count |
| `GET /api/i2c-scan` | I²C devices found on the bus |
| `GET /api/pin-probe` | All GPIO readings (analog + digital) |
| `GET /api/export.json` | Full readings snapshot |
| `GET /api/export.csv` | Log as CSV (downloadable) |

WebSocket is at `ws://[ip]/ws` — see [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) for the message format.

---

## Important ESP32 pin notes

Not all GPIO pins are the same. Before wiring:

| Pin range | What to know |
|---|---|
| **GPIO 32–39** | Best for analog sensors (ADC1 — works with WiFi active) |
| **GPIO 34–39** | Input only — cannot be OUTPUT |
| **GPIO 6–11** | ⚠️ Do not use — connected to internal SPI flash |
| **GPIO 1, 3** | UART TX/RX — used by Serial Monitor |
| **GPIO 0, 2, 12, 15** | Boot-sensitive — avoid for sensors if possible |
| **ADC2 pins (0,2,4,12–15,25–27)** | ⚠️ Conflict with WiFi — use ADC1 (32–39) for all analog sensors |

**Best analog pins:** 32, 33, 34, 35, 36, 39
**Best digital pins:** 4, 5, 13, 14, 16, 17, 18, 19, 21, 22, 23, 26, 27

---

## Project structure

```
esp32-sensor-dashboard/
│
├── src/
│   └── main.cpp              ← All ESP32 firmware: sensor reading, WebSocket server, HTTP API
│
├── data/                     ← Web files uploaded to LittleFS (the ESP32's flash filesystem)
│   ├── index.html            ← Dashboard layout and templates
│   ├── style.css             ← All styling: light theme, dark theme, responsive
│   └── app.js                ← WebSocket client, sensor catalog, live card rendering
│
├── docs/
│   ├── SENSORS.md            ← Full wiring guide for every supported sensor
│   └── HOW_IT_WORKS.md       ← Technical architecture for the curious
│
├── platformio.ini            ← PlatformIO build config (board, framework, libraries)
├── CONTRIBUTING.md           ← How to add a sensor to the library or contribute code
├── LICENSE                   ← MIT
└── README.md                 ← You are here
```

---

## Troubleshooting

**Dashboard doesn't load at all**
- Make sure you ran *both* `uploadfs` and `upload` — the filesystem and the firmware are separate
- Open Serial Monitor to see the IP address
- Try `http://192.168.4.1` (the fallback AP always works)

**Sensor card shows "offline"**
- Check wiring against [docs/SENSORS.md](docs/SENSORS.md)
- DHT sensors: add a 10kΩ pull-up resistor between VCC and DATA pin
- Analog sensors: only use GPIO 32–39. ADC2 pins conflict with WiFi and give garbage readings
- HC-SR04: ECHO pin outputs 5V — use a voltage divider (1kΩ + 2kΩ) before the ESP32 GPIO

**Pin Probe shows nothing active**
- Digital pins read LOW by default (floating, no pull-up) — this is normal when nothing is connected
- For analog sensors: make sure VCC is connected; an unconnected ADC pin floats near zero

**WiFi not connecting**
- ESP32 supports **2.4GHz only** — check your router isn't 5GHz-only
- The fallback AP always works regardless — join `ESP32-Dashboard` → `http://192.168.4.1`
- Check SSID/password in `src/main.cpp` lines 8–9

**Compile error**
- Run `pio lib update` to refresh library versions
- Make sure you're using PlatformIO (VS Code extension), not the Arduino IDE

---

## Contributing

Want to add a sensor to the library? Found a bug? Want to make the UI even prettier?

Read [CONTRIBUTING.md](CONTRIBUTING.md) — adding a new sensor to the catalog is literally 10 lines of JavaScript, no firmware knowledge required.

---

## License

MIT — do whatever you want with it. Build something weird, sell a product, use it in a school project. If you make something cool, open an issue and show us.

---

*Built with an ESP32, too much coffee, and a genuine frustration with having to re-flash firmware every time you want to try a new sensor.*
