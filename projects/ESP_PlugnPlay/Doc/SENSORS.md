# Sensor Wiring Guide

Complete wiring reference for every sensor supported by the ESP32 Sensor Dashboard.

**Quick rule before you start:**
- Use **GPIO 32–39** for all analog sensors (ADC1 — safe with WiFi active)
- Never use **GPIO 6–11** (internal flash)
- Never use analog pins on ADC2 (GPIO 0, 2, 4, 12–15, 25–27) with WiFi — they read garbage
- GPIO 34–39 are **input only** — they cannot drive anything

---

## Table of contents

- [DHT11 — Temperature + Humidity](#dht11--temperature--humidity)
- [DHT22 / AM2302 — Temperature + Humidity](#dht22--am2302--temperature--humidity)
- [LM35 — Analog Temperature](#lm35--analog-temperature)
- [NTC Thermistor](#ntc-thermistor)
- [MQ Gas Sensors (MQ-2, 3, 4, 5, 7, 9, 135)](#mq-gas-sensors)
- [HC-SR04 — Ultrasonic Distance](#hc-sr04--ultrasonic-distance)
- [LDR — Light Level](#ldr--light-level)
- [Capacitive Soil Moisture Sensor](#capacitive-soil-moisture-sensor)
- [Resistive Soil Moisture Sensor](#resistive-soil-moisture-sensor)
- [Water Level Sensor](#water-level-sensor)
- [Rain Sensor](#rain-sensor)
- [PIR HC-SR501 — Motion Detection](#pir-hc-sr501--motion-detection)
- [IR Obstacle Sensor](#ir-obstacle-sensor)
- [TTP223 — Touch Sensor](#ttp223--touch-sensor)
- [Sound Sensor KY-037](#sound-sensor-ky-037)
- [Voltage Divider (Voltage Monitor)](#voltage-divider-voltage-monitor)
- [ACS712 — Current Sensor](#acs712--current-sensor)
- [Relay Module](#relay-module)

---

## DHT11 — Temperature + Humidity

**What it reads:** Temperature in °C and Humidity in %
**Dashboard type:** `dht11`

### Wiring

```
DHT11 pin        ESP32 pin
─────────────────────────────
VCC          →   3.3V
GND          →   GND
DATA         →   Any digital GPIO (e.g. GPIO 4)
```

```
3.3V ──┬──────── VCC (DHT11)
       │
      10kΩ           ← pull-up resistor (required!)
       │
       ├──────── DATA (DHT11)  ──→  GPIO 4
       
GND ──────────── GND (DHT11)
```

> **Important:** The 10kΩ pull-up resistor between VCC and DATA is required. Without it, the sensor will read "offline" intermittently.

### Dashboard config

| Field | Value |
|---|---|
| Type | `dht11` |
| Pin | Your DATA GPIO (e.g. `4`) |
| Warn high | `35` (°C) |
| Danger high | `42` (°C) |

### Notes
- Reads temperature AND humidity in one go — both values appear on the same card
- Minimum read interval is ~1 second; faster reads return NaN
- Accuracy: ±2°C, ±5% RH
- Range: 0–50°C, 20–90% RH

---

## DHT22 / AM2302 — Temperature + Humidity

**What it reads:** Temperature in °C and Humidity in %
**Dashboard type:** `dht22`

Identical wiring to DHT11. Just pick `dht22` as the type.

```
DHT22 pin        ESP32 pin
─────────────────────────────
VCC (pin 1)  →   3.3V
DATA (pin 2) →   Any digital GPIO  +  10kΩ pull-up to 3.3V
(pin 3)          not connected
GND (pin 4)  →   GND
```

### Notes
- More accurate than DHT11: ±0.5°C, ±2–5% RH
- Wider range: -40 to +80°C, 0–100% RH
- Same 10kΩ pull-up rule applies
- If you see `-999` or NaN readings, check the pull-up resistor first

---

## LM35 — Analog Temperature

**What it reads:** Temperature in °C
**Dashboard type:** `temperature`

The LM35 outputs 10mV per °C directly. At 25°C it outputs 250mV.

### Wiring

```
LM35 pin         ESP32 pin
─────────────────────────────
VCC          →   5V (or 3.3V — lower range)
GND          →   GND
VOUT         →   GPIO 36 (or any ADC1 pin 32-39)
```

> The ESP32 ADC reads 0–3.3V as 0–4095. LM35 at 3.3V tops out around 33°C. Power from 5V via a diode for wider range, or use the DHT22 for a better temperature sensor.

---

## NTC Thermistor

**What it reads:** Temperature (inverted resistance — higher temp = lower resistance)
**Dashboard type:** `analog`

### Wiring (voltage divider)

```
3.3V ──── 10kΩ (fixed resistor) ──┬──── GPIO 34 (ADC)
                                   │
                               NTC thermistor
                                   │
GND ───────────────────────────────┘
```

### Notes
- Raw ADC value (0–4095) is inversely proportional to temperature
- For actual °C you'd need a Steinhart-Hart equation in the firmware — currently shows raw value
- Useful as a relative temperature indicator without calibration

---

## MQ Gas Sensors

**Covers:** MQ-2, MQ-3, MQ-4, MQ-5, MQ-7, MQ-9, MQ-135
**Dashboard type:** `gas`

All MQ sensors have the same pinout and wiring. The difference is what gas they're sensitive to.

### What each one detects

| Sensor | Primary target | Good for |
|---|---|---|
| MQ-2 | LPG, propane | Kitchen gas leak detection |
| MQ-3 | Alcohol, ethanol | Breathalyser projects |
| MQ-4 | Methane, natural gas | Gas pipeline monitoring |
| MQ-5 | LPG, natural gas | Another gas leak option |
| MQ-7 | Carbon monoxide | CO alarm |
| MQ-9 | CO + combustible gas | Combination detector |
| MQ-135 | CO₂, ammonia, benzene, smoke | Air quality index |

### Wiring

```
MQ sensor pin    ESP32 pin
─────────────────────────────
VCC          →   5V  ← must be 5V, not 3.3V
GND          →   GND
AO (analog)  →   GPIO 34 (or any ADC1 pin 32-39)
DO (digital) →   not needed (use AO for more data)
```

```
5V ─────────── VCC (MQ sensor)
GND ────────── GND (MQ sensor)
AO ─────────── GPIO 34
```

> ⚠️ MQ sensors **need 5V** on VCC to heat the sensing element correctly. The analog output (AO) is still safe to connect directly to an ESP32 GPIO because AO output voltage doesn't exceed 3.3V under normal conditions. If you want to be safe, add a 10kΩ + 20kΩ voltage divider between AO and GND and connect the middle to GPIO.

### Preheat

MQ sensors need **warm-up time** after power-on:
- MQ-2, MQ-3, MQ-4, MQ-5, MQ-9, MQ-135: ~20 seconds for stable readings
- MQ-7: 60–90 seconds for accurate CO readings

The dashboard will show low/erratic values during preheat — this is normal.

### Dashboard config

| Field | Suggested value |
|---|---|
| Type | `gas` |
| Pin | Your AO GPIO (e.g. `34`) |
| Warn high | `1000`–`1500` (raw ADC) |
| Danger high | `2500`–`3500` (raw ADC) |

Calibrate these thresholds to your specific environment — clean air baseline varies by sensor and location.

---

## HC-SR04 — Ultrasonic Distance

**What it reads:** Distance in cm (range: 2–400 cm)
**Dashboard type:** `ultrasonic`

This sensor needs **two GPIO pins** — one to trigger a pulse and one to listen for the echo.

### Wiring

```
HC-SR04 pin      ESP32 pin
─────────────────────────────
VCC          →   5V
GND          →   GND
TRIG         →   Any digital GPIO (e.g. GPIO 5)
ECHO         →   GPIO via voltage divider (see below!)
```

```
5V ────────── VCC
GND ───────── GND
GPIO 5 ─────── TRIG

ECHO ──── 1kΩ ──┬──── GPIO 18
                │
               2kΩ
                │
               GND
```

> ⚠️ **ECHO outputs 5V.** The ESP32 is a 3.3V device. A direct connection will damage it over time. Use the 1kΩ + 2kΩ voltage divider shown above to bring ECHO down to ~3.3V.

### Dashboard config

| Field | Value |
|---|---|
| Type | `ultrasonic` |
| Data/Trig pin | Your TRIG GPIO (e.g. `5`) |
| Echo pin | Your ECHO GPIO (e.g. `18`) |
| Warn high | `100` (cm) |
| Danger high | `10` (cm — too close) |

### Notes
- Avoid obstacles or walls within 2cm — the sensor has a blind spot below that
- Works best aimed at flat surfaces perpendicular to the beam
- Soft/angled surfaces absorb or deflect the ultrasound — readings may be unreliable

---

## LDR — Light Level

**What it reads:** Light intensity 0–100% (0 = dark, 100 = bright)
**Dashboard type:** `ldr`

### Wiring (voltage divider)

```
3.3V ──── LDR (any orientation) ──┬──── GPIO 35 (ADC)
                                   │
                                  10kΩ
                                   │
GND ───────────────────────────────┘
```

The LDR resistance drops as light increases. Combined with the 10kΩ fixed resistor, it forms a voltage divider that produces higher voltage in bright light.

### Notes
- The dashboard automatically scales the raw ADC value to 0–100%
- Bright sunlight typically reads 85–100%
- Indoor room light: 20–60%
- Dark room: 0–10%

---

## Capacitive Soil Moisture Sensor

**What it reads:** Soil moisture 0–100% (0 = bone dry, 100 = saturated)
**Dashboard type:** `soil`

Capacitive sensors measure dielectric permittivity rather than conductivity. They last much longer than resistive sensors and don't corrode.

### Wiring

```
Sensor pin       ESP32 pin
─────────────────────────────
VCC          →   3.3V
GND          →   GND
AOUT         →   GPIO 32 (or any ADC1 pin)
```

### Notes
- Insert the sensor in soil up to the marked line — not deeper
- The output is **inverted**: dry soil = high ADC value, wet soil = low ADC value
- The dashboard firmware inverts this automatically: `100 - (raw/4095 * 100)`
- Calibrate your thresholds: take a dry reading and a fully-submerged reading, use those as your Danger Low / Warn Low

### Dashboard config

| Field | Value |
|---|---|
| Type | `soil` |
| Warn high | `70` (%) — getting wet |
| Warn low | `30` (%) — getting dry |
| Danger low | `15` (%) — needs water now |

---

## Resistive Soil Moisture Sensor

**What it reads:** Soil moisture 0–100%
**Dashboard type:** `soil`

Same wiring and config as capacitive. The probe just uses two exposed metal prongs instead of a PCB.

> ⚠️ Resistive probes corrode over months of continuous use in moist soil because they pass a small current through the soil. Use capacitive sensors for long-term deployments.

```
Sensor pin       ESP32 pin
─────────────────────────────
VCC          →   3.3V
GND          →   GND
AO           →   GPIO 32 (ADC1)
```

---

## Water Level Sensor

**What it reads:** Water depth / level as a raw analog value
**Dashboard type:** `analog`

### Wiring

```
Sensor pin       ESP32 pin
─────────────────────────────
+  (VCC)     →   5V
-  (GND)     →   GND
S  (signal)  →   GPIO 33 (ADC1)
```

> Only power the sensor when taking readings if you want to extend its life — the exposed traces corrode faster when constantly powered in water.

---

## Rain Sensor

**What it reads:** Rain / moisture on the sensor plate as analog value
**Dashboard type:** `analog`

### Wiring

```
Sensor pin       ESP32 pin
─────────────────────────────
VCC          →   5V
GND          →   GND
AO           →   GPIO 35 (ADC1)
DO           →   (optional — threshold digital output)
```

### Notes
- AO gives you the full analog range: dry = low value, wet = high value
- DO is a simple HIGH/LOW threshold output — useful as a simple alarm but less data
- This dashboard uses AO for the analog reading

---

## PIR HC-SR501 — Motion Detection

**What it reads:** Motion present (HIGH) or not (LOW)
**Dashboard type:** `pir`

### Wiring

```
HC-SR501 pin     ESP32 pin
─────────────────────────────
VCC          →   5V
GND          →   GND
OUT          →   Any digital GPIO (e.g. GPIO 13)
```

### Notes
- Has two potentiometers on the back: sensitivity (Sx) and delay time (Tx)
- Delay time sets how long OUT stays HIGH after motion is last detected (3s–300s)
- Warm-up time: ~30–60 seconds after power-on before reliable detection
- Detection angle: ~120°, range: 3–7m depending on sensitivity setting

---

## IR Obstacle Sensor

**What it reads:** Obstacle present (LOW) or clear (HIGH)
**Dashboard type:** `digital`

### Wiring

```
Sensor pin       ESP32 pin
─────────────────────────────
VCC          →   3.3V (or 5V)
GND          →   GND
OUT          →   Any digital GPIO (e.g. GPIO 14)
```

### Notes
- Output is **active LOW** — the pin goes LOW when an obstacle is detected
- Has a potentiometer for detection range (usually 2–30cm)
- Sunlight or other IR sources can interfere with readings

---

## TTP223 — Touch Sensor

**What it reads:** Touch detected (HIGH) or not (LOW)
**Dashboard type:** `digital`

### Wiring

```
TTP223 pin       ESP32 pin
─────────────────────────────
VCC          →   3.3V
GND          →   GND
SIG / I/O    →   Any digital GPIO (e.g. GPIO 15)
```

### Notes
- No physical press required — capacitive touch through plastic or glass works
- Can be placed behind non-metallic surfaces for hidden touch buttons
- Output stays HIGH while touching, returns LOW when released (default mode)

---

## Sound Sensor KY-037

**What it reads:** Ambient sound level as analog value
**Dashboard type:** `analog`

### Wiring

```
KY-037 pin       ESP32 pin
─────────────────────────────
VCC (+)      →   5V
GND (-)      →   GND
AO           →   GPIO 34 (ADC1)
DO           →   (not used)
```

### Notes
- AO gives a continuous analog reading proportional to sound pressure
- The reading spikes on loud sounds and drops back in silence
- Not calibrated in dB — use relative thresholds (quiet room ≈ 100–300, loud clap ≈ 2000+)
- Has a potentiometer for DO threshold sensitivity (unused here)

---

## Voltage Divider (Voltage Monitor)

**What it reads:** Voltage at a GPIO pin (scaled by resistor ratio)
**Dashboard type:** `analog`

Use two resistors to scale any voltage down to the ESP32's 3.3V ADC range.

### Wiring

```
V_input ──── R1 ──┬──── GPIO 39 (ADC)
                  │
                  R2
                  │
                 GND
```

**Formula:** `V_gpio = V_input × R2 / (R1 + R2)`

For **12V input** with R1=30kΩ and R2=10kΩ:
`V_gpio = 12 × 10k / 40k = 3.0V` ✓ (safe for ESP32)

### Notes
- Maximum input voltage depends on your resistor values — calculate before connecting
- ADC on ESP32 is non-linear near 0V and near 3.3V — readings are most accurate in the middle third
- The dashboard shows raw ADC (0–4095); conversion to actual voltage needs post-processing

---

## ACS712 — Current Sensor

**What it reads:** AC or DC current through the load (analog output)
**Dashboard type:** `analog`

### Wiring

```
ACS712 pin       ESP32 pin
─────────────────────────────
VCC          →   5V
GND          →   GND
VIOUT        →   GPIO 36 (ADC1)
```

The load current flows through the IP+ and IP- terminals on the sensor — the ESP32 is only connected to the VCC, GND, and VIOUT signal pins.

### Variants

| Module | Current range | Sensitivity |
|---|---|---|
| ACS712-05B | ±5A | 185 mV/A |
| ACS712-20A | ±20A | 100 mV/A |
| ACS712-30A | ±30A | 66 mV/A |

### Notes
- At zero current, VIOUT = 2.5V (mid-rail)
- Current in one direction raises VIOUT above 2.5V; opposite direction lowers it
- Dashboard shows raw ADC — convert to amperes using the sensitivity formula

---

## Relay Module

**What it does:** Switches an external circuit on or off from the dashboard
**Dashboard type:** `relay`

### Wiring

```
Relay module pin ESP32 pin
─────────────────────────────
VCC          →   5V
GND          →   GND
IN           →   Any digital GPIO (e.g. GPIO 26)
```

The relay itself has three screw terminals for your external circuit:
- **COM** — common (always connected)
- **NO** — normally open (circuit open when relay is off, closed when on)
- **NC** — normally closed (circuit closed when relay is off, open when on)

### Notes
- Most relay modules are **active LOW** — the relay triggers when IN goes LOW, releases on HIGH
- The dashboard relay button sends the opposite of the current state each click
- Never switch mains voltage (AC 220V/110V) unless you know what you're doing and your relay module is rated for it
- For inductive loads (motors, solenoids) add a flyback diode across the load

---

## Adding a sensor not on this list

If your sensor outputs an analog voltage: use type `analog` and GPIO 32–39.
If it outputs a digital HIGH/LOW: use type `digital` and any safe GPIO.

Then use **Probe Pins** in the dashboard to confirm which pin has a signal, adjust thresholds to match your sensor's output range, and you're done.

Want to add it to the library so others can use it too? See [CONTRIBUTING.md](../CONTRIBUTING.md).
