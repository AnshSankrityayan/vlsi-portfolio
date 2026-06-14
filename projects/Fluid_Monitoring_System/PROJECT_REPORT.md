# Fluid Monitoring System - File-wise Project Report

Date: 2026-06-14

## 1. Project Overview

This project is a bare-metal STM32-based fluid monitoring and control system built with PlatformIO. It runs on the STM32 Nucleo-F401RE board and monitors distance using an HC-SR04 ultrasonic sensor. The measured distance is treated as the fluid level reference, compared against a user-set threshold from a potentiometer, and reported over UART as JSON.

The firmware also drives:

- A relay output for critical-state control.
- A status LED for safe, warning, and critical state feedback.
- A MAX7219-driven 8x8 LED matrix used as a distance bargraph.

## 2. Hardware Summary

| Device | STM32 Pin | Purpose |
| --- | --- | --- |
| HC-SR04 Trigger | PA0 | Sends 10 us trigger pulse |
| HC-SR04 Echo | PA1 | Measures return pulse width |
| UART2 TX | PA2 | Sends JSON data to USB serial monitor |
| Relay | PA3 | Turns on in CRITICAL state |
| Potentiometer | PA4 / ADC1 CH4 | Adjustable distance threshold |
| MAX7219 CLK | PA5 | Bit-banged display clock |
| MAX7219 CS | PA6 | Display chip select |
| MAX7219 DIN | PA7 | Display data input |
| Status LED | PB0 | Shows SAFE/WARNING/CRITICAL state |

## 3. File-wise Report

### `platformio.ini`

This is the PlatformIO project configuration file.

Responsibilities:

- Selects the `nucleo_f401re` board.
- Uses the `ststm32` platform.
- Uses the `stm32cube` framework.
- Sets the serial monitor speed to `115200`.
- Defines `USE_HAL_DRIVER` and `STM32F401xE` for STM32F4 headers and build configuration.

Current configuration:

```ini
[env:nucleo_f401re]
platform     = ststm32
board        = nucleo_f401re
framework    = stm32cube
monitor_speed = 115200
build_flags  = -DUSE_HAL_DRIVER -DSTM32F401xE
```

GitHub relevance:

- This file must be committed because it allows anyone with PlatformIO to build the project.
- It is small, portable, and contains no local secrets.

### `src/main.c`

This is the main firmware application.

Responsibilities:

- Initializes the STM32 system clock to 84 MHz using HSI and PLL.
- Enables the DWT cycle counter for accurate microsecond timing.
- Configures SysTick for millisecond delays.
- Configures GPIO pins for the sensor, relay, LED, UART, ADC, and display.
- Reads the HC-SR04 ultrasonic sensor.
- Reads the potentiometer through ADC1 channel 4.
- Smooths distance measurements using a 5-sample moving average.
- Classifies the system state as `SAFE`, `WARNING`, or `CRITICAL`.
- Calculates level trend as `RISING`, `FALLING`, or `STABLE`.
- Sends telemetry over UART as JSON.
- Controls the relay, LED, and MAX7219 bargraph.

Important implementation details:

- `clock_init()` configures the MCU for 84 MHz operation.
- `dwt_init()` enables cycle-accurate timing.
- `delay_us()` uses `DWT->CYCCNT` for precise ultrasonic trigger and echo measurement.
- `gpio_init()` maps all external modules to GPIO pins.
- `uart_init()` configures USART2 TX at 115200 baud.
- `adc_init()` prepares ADC1 for potentiometer reading.
- `hcsr04_measure_cm()` performs ultrasonic measurement and converts pulse time to centimeters.
- The main loop emits JSON once per second.

UART output format:

```json
{"dist":42,"limit":70,"status":"CRITICAL","trend":"RISING","rate":3}
```

State logic:

- `CRITICAL`: measured distance is more than 5 cm below the selected threshold.
- `WARNING`: measured distance is within the 5 cm threshold band.
- `SAFE`: measured distance is above the threshold band.

Recent cleanup:

- The distance averaging now only averages filled history samples during startup, so the first readings are not pulled down by empty zero values.
- The threshold comparison now uses signed difference math to avoid unsigned underflow when the threshold is below the margin.

GitHub relevance:

- This is the core project file and should definitely be committed.
- The top comment documents wiring and test behavior, which makes the project easier for others to reproduce.

### `src/max7219.c`

This file contains the MAX7219 display driver.

Responsibilities:

- Implements a simple bit-banged serial protocol using GPIOA pins PA5, PA6, and PA7.
- Sends register/data pairs to the MAX7219.
- Initializes the MAX7219 for 8x8 matrix operation.
- Displays a bargraph based on measured distance.
- Clears the display when distance is out of the display range.

Important functions:

- `max7219_write_reg(uint8_t reg, uint8_t data)`: writes one MAX7219 register.
- `max7219_init(void)`: configures display test, scan limit, decode mode, brightness, and shutdown mode.
- `max7219_display_bargraph(uint32_t cm)`: displays a distance bargraph from 0 to 80 cm.
- `max7219_clear(void)`: clears all eight display rows.

Display behavior:

- `0 cm`: all columns lit.
- `10 cm`: seven columns lit.
- `20 cm`: six columns lit.
- `80 cm` or above: display cleared.

Recent cleanup:

- The MAX7219 is now configured with no-decode mode and all eight rows enabled, matching the 8x8 matrix bargraph behavior.

GitHub relevance:

- This file is reusable as a small MAX7219 matrix driver.
- It should be committed with `include/max7219.h`.

### `include/max7219.h`

This is the public header for the MAX7219 driver.

Responsibilities:

- Provides register address definitions for the MAX7219.
- Documents the GPIO mapping for DIN, CLK, and CS.
- Declares the functions implemented in `src/max7219.c`.

Important declarations:

```c
void max7219_init(void);
void max7219_write_reg(uint8_t reg, uint8_t data);
void max7219_display_bargraph(uint32_t cm);
void max7219_clear(void);
```

Recent cleanup:

- Removed stale declarations for number/error display functions that were not implemented.
- Added declarations for the actual bargraph and clear functions used by `main.c`.

GitHub relevance:

- Required for clean compilation and for understanding the display driver's public interface.

### `.gitignore`

This file tells Git which generated files should not be committed.

Current ignored paths:

- `.pio`
- `.vscode/.browse.c_cpp.db*`
- `.vscode/c_cpp_properties.json`
- `.vscode/launch.json`
- `.vscode/ipch`

Why this matters:

- `.pio` contains build outputs, package state, and generated firmware artifacts.
- Some `.vscode` files are generated locally and contain absolute machine-specific paths.
- Ignoring these keeps the GitHub repository clean and portable.

Recommended:

- Keep `.vscode/extensions.json` committed because it recommends the PlatformIO extension.
- Keep ignoring `.vscode/c_cpp_properties.json` and `.vscode/launch.json` because they contain local absolute paths.

### `.vscode/extensions.json`

This VS Code helper file recommends the PlatformIO IDE extension.

Responsibilities:

- Helps someone opening the repo in VS Code install the right embedded development extension.

GitHub relevance:

- This file is useful and safe to commit.

### `.vscode/c_cpp_properties.json`

This file is generated by PlatformIO and contains local include paths and toolchain paths.

GitHub relevance:

- It should not be committed.
- It contains absolute paths from the current machine.
- It is already ignored by `.gitignore`.

### `.vscode/launch.json`

This file is generated by PlatformIO for debugging.

GitHub relevance:

- It should not be committed in its current form.
- It contains absolute paths from the current machine.
- It is already ignored by `.gitignore`.

### `.pio/`

This is PlatformIO's generated build directory.

GitHub relevance:

- It should not be committed.
- It is already ignored.
- Anyone can regenerate it with `pio run`.

## 4. System Flow

1. The board boots and sets the clock to 84 MHz.
2. GPIO, UART, ADC, SysTick, DWT, and MAX7219 are initialized.
3. PA3 relay output flashes three times as a startup test.
4. The main loop runs once per second.
5. The ultrasonic sensor measures distance.
6. The potentiometer sets the threshold from 0 to 200 cm.
7. The firmware smooths the distance value.
8. The firmware classifies the state as SAFE, WARNING, or CRITICAL.
9. JSON telemetry is sent through UART2.
10. Relay, status LED, and display are updated.

## 5. Build Verification

Verified command:

```bash
pio run
```

Result:

```text
SUCCESS
RAM:   0.2% (used 152 bytes from 98304 bytes)
Flash: 0.8% (used 4196 bytes from 524288 bytes)
```

The project builds successfully for the `nucleo_f401re` environment.

## 6. GitHub Push Review

The current folder is not initialized as a Git repository yet. Running `git status` returned:

```text
fatal: not a git repository (or any of the parent directories): .git
```

There is no separate GitHub-pushing app or script in this project folder. The project can still be pushed normally with Git commands after initializing the repository.

Recommended first push workflow:

```bash
git init
git add platformio.ini src include .gitignore .vscode/extensions.json PROJECT_REPORT.md
git commit -m "Add fluid monitoring firmware"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Before pushing, avoid adding:

- `.pio/`
- `.vscode/c_cpp_properties.json`
- `.vscode/launch.json`
- `.vscode/ipch`

These are already covered by `.gitignore`.

## 7. Strengths

- Clean bare-metal register-level STM32 implementation.
- Uses DWT for accurate ultrasonic timing.
- JSON serial output is ready for downstream devices such as ESP32, dashboard software, or a logging tool.
- Threshold is adjustable in hardware using a potentiometer.
- Relay and LED outputs provide immediate local control and feedback.
- MAX7219 bargraph gives a simple visual indication of measured distance.
- Project builds successfully with PlatformIO.

## 8. Notes and Future Improvements

- Add a `README.md` with setup instructions, wiring diagram, build steps, and sample serial output.
- Add a simple schematic image or pinout table for GitHub visitors.
- Consider replacing `sprintf` with `snprintf` for extra buffer safety.
- Consider adding a voltage divider on HC-SR04 Echo if the sensor outputs 5V.
- Consider documenting whether smaller distance means higher fluid level or lower fluid level, depending on sensor mounting.
- Add upload instructions using `pio run --target upload`.
- Add serial monitor instructions using `pio device monitor --baud 115200`.

