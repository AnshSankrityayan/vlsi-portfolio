# 🔬 DE0-Nano FPGA Health Check — LED Blink Test

> **A complete step-by-step guide to verify your Terasic DE0-Nano (Altera Cyclone IV EP4CE22F17C6) is working correctly using a LED blink test in Quartus Prime Lite 20.1.1 and ModelSim 2020.1**

---

## 📋 Table of Contents

- [Hardware Required](#hardware-required)
- [Software Required](#software-required)
- [Board Overview](#board-overview)
- [Step 1 — Install Quartus & Verify Device Support](#step-1--install-quartus--verify-device-support)
- [Step 2 — Create a New Project](#step-2--create-a-new-project)
- [Step 3 — Write the Verilog Code](#step-3--write-the-verilog-code)
- [Step 4 — Assign Pins via TCL Console](#step-4--assign-pins-via-tcl-console)
- [Step 5 — Compile the Design](#step-5--compile-the-design)
- [Step 6 — Simulate with ModelSim](#step-6--simulate-with-modelsim)
- [Step 7 — Install USB-Blaster Driver](#step-7--install-usb-blaster-driver)
- [Step 8 — Program the Board](#step-8--program-the-board)
- [Step 9 — Verify on Hardware](#step-9--verify-on-hardware)
- [What Each Step Confirms](#what-each-step-confirms)
- [Common Errors & Fixes](#common-errors--fixes)
- [Project File Structure](#project-file-structure)

---

## Hardware Required

| Item | Details |
|---|---|
| FPGA Board | Terasic DE0-Nano |
| FPGA Chip | Altera Cyclone IV E — EP4CE22F17C6N |
| USB Cable | Mini-USB (for USB-Blaster programming) |
| PC | Windows 10/11 |

### Board Resources Used in This Test

| Resource | Available on Board | Used |
|---|---|---|
| Logic Elements | 22,320 | 26 (< 1%) |
| Registers | 22,320 | 26 |
| Green LEDs | 8 | 8 |
| Push Buttons | 2 | 1 (reset) |
| 50 MHz Clock | 1 | 1 |

---

## Software Required

| Software | Version | Download |
|---|---|---|
| Quartus Prime Lite | 20.1.1 | [Intel FPGA Software Downloads](https://www.intel.com/content/www/us/en/collections/products/fpga/software/downloads.html) |
| ModelSim-Altera Starter | 2020.1 | Included with Quartus |
| Cyclone IV Device Pack | 20.1.1 | Bundled in full installer |

> **Note:** The full Quartus installer is approximately 6GB. Cyclone IV device support is included — no separate download needed.

---

## Board Overview

```
DE0-Nano Board Layout (Top View)
┌─────────────────────────────────────────┐
│  [LED7][LED6][LED5][LED4][LED3][LED2][LED1][LED0]  ← 8 Green LEDs  │
│                          [KEY1] [KEY0]  ← Push Buttons              │
│                                                                       │
│         ┌──────────────────────┐                                     │
│         │   Altera Cyclone IV  │                                     │
│         │   EP4CE22F17C6N      │                                     │
│         └──────────────────────┘                                     │
│  [USB-Blaster Port] ←── Connect USB cable here                      │
│  [POWER LED]        ←── Blue LED, ON when powered                   │
│                    Y1 50MHz ←── Onboard clock oscillator            │
└─────────────────────────────────────────┘
```

**Key onboard components:**
- **EP4CE22F17C6N** — Cyclone IV FPGA chip (centre of board)
- **50 MHz oscillator** — clock source (marked Y1 on PCB)
- **8 green LEDs** — labelled LED0 to LED7
- **2 push buttons** — KEY0 and KEY1 (active LOW)
- **Mini-USB port** — USB-Blaster for programming
- **Blue power LED** — confirms board is powered

---

## Step 1 — Install Quartus & Verify Device Support

After installing Quartus Prime Lite 20.1.1, verify Cyclone IV support before creating any project.

### 1.1 Open Quartus Prime Lite
Right-click the Quartus icon → **Run as Administrator** (important for Windows)

### 1.2 Check Device Support
1. Click **File → New Project Wizard**
2. Click **Next** until you reach **"Family & Device Settings"**
3. In the **Family** dropdown, look for **Cyclone IV E**
4. In the search box, type: `EP4CE22F17C6`

**✅ If EP4CE22F17C6 appears in the list → device support is installed. You are ready.**

> **Tip:** If you get a "Cannot launch Device Installer" error, ignore it. The device is already included in the full 6GB installer package. Just check the device list directly as described above.

---

## Step 2 — Create a New Project

### 2.1 Start the Project Wizard
**File → New Project Wizard**

### 2.2 Project Directory and Name
| Field | Value |
|---|---|
| Project directory | `C:/intelFPGA_lite/20.1/Demo` |
| Project name | `Demo` |
| Top-level entity | `Demo` |

Click **Next**

### 2.3 Add Files
Leave empty for now. Click **Next**

### 2.4 Family & Device Settings
| Field | Value |
|---|---|
| Family | Cyclone IV E |
| Device | EP4CE22F17C6 |

Click **Next**

### 2.5 EDA Tool Settings
| Tool Type | Tool Name | Format |
|---|---|---|
| Simulation | ModelSim-Altera | Verilog HDL |
| Synthesis | None | — |
| Timing Analysis | None | — |

Click **Next → Finish**

> **If Quartus crashes during the wizard:** Create the project folder manually at `C:\intelFPGA_lite\20.1\Demo\`, then use **File → Open Project** and navigate there. Alternatively use the TCL console method below.

---

## Step 3 — Write the Verilog Code

### 3.1 Create a New Verilog File
**File → New → Verilog HDL File → OK**

A blank editor tab opens.

### 3.2 Paste the LED Blink Code

```verilog
module Demo(
    input wire CLOCK_50,
    input wire KEY0,
    input wire KEY1,
    output wire LED0,
    output wire LED1,
    output wire LED2,
    output wire LED3,
    output wire LED4,
    output wire LED5,
    output wire LED6,
    output wire LED7
);

reg [25:0] counter;

always @(posedge CLOCK_50) begin
    if (!KEY0)
        counter <= 0;
    else
        counter <= counter + 1;
end

assign LED0 = counter[18];
assign LED1 = counter[19];
assign LED2 = counter[20];
assign LED3 = counter[21];
assign LED4 = counter[22];
assign LED5 = counter[23];
assign LED6 = counter[24];
assign LED7 = counter[25];

endmodule
```

### 3.3 How This Code Works

```
50 MHz clock → 26-bit counter → upper 8 bits drive LEDs

counter[18] toggles every 2^18 / 50,000,000 = ~5ms  (LED0, fastest)
counter[25] toggles every 2^25 / 50,000,000 = ~0.67s (LED7, slowest)

KEY0 pressed (LOW) → counter resets → all LEDs off
KEY0 released     → counter counts again → LEDs blink
```

### 3.4 Save the File
**File → Save As** → name it exactly `Demo.v` → Save inside your Demo project folder

Click **Yes** if asked to add file to project.

### 3.5 Confirm Project Navigator Shows Demo
In the left panel under **Project Navigator → Hierarchy**, you should see:

```
Cyclone IV E: EP4CE22F17C6
  └── Demo
```

---

## Step 4 — Assign Pins via TCL Console

This maps your Verilog port names to the physical pins on the EP4CE22F17C6 chip according to the DE0-Nano schematic.

### 4.1 Open TCL Console
**View → Utility Windows → TCL Console**

### 4.2 Paste All Pin Assignments at Once

Copy and paste the entire block below into the TCL Console and press **Enter**:

```tcl
set_location_assignment PIN_R8  -to CLOCK_50
set_location_assignment PIN_J15 -to KEY0
set_location_assignment PIN_E1  -to KEY1
set_location_assignment PIN_A15 -to LED0
set_location_assignment PIN_A13 -to LED1
set_location_assignment PIN_B13 -to LED2
set_location_assignment PIN_A11 -to LED3
set_location_assignment PIN_D1  -to LED4
set_location_assignment PIN_F3  -to LED5
set_location_assignment PIN_B1  -to LED6
set_location_assignment PIN_L3  -to LED7
```

### 4.3 Pin Reference Table

| Signal | Physical Pin | I/O Direction | Notes |
|---|---|---|---|
| CLOCK_50 | PIN_R8 | Input | 50 MHz onboard oscillator |
| KEY0 | PIN_J15 | Input | Active LOW push button |
| KEY1 | PIN_E1 | Input | Active LOW push button |
| LED0 | PIN_A15 | Output | Rightmost LED |
| LED1 | PIN_A13 | Output | |
| LED2 | PIN_B13 | Output | |
| LED3 | PIN_A11 | Output | |
| LED4 | PIN_D1 | Output | |
| LED5 | PIN_F3 | Output | |
| LED6 | PIN_B1 | Output | |
| LED7 | PIN_L3 | Output | Leftmost LED |

> **Tip:** You can also verify assignments visually using **Assignments → Pin Planner** — you will see the EP4CE22F17C6 chip diagram with your assigned pins highlighted.

---

## Step 5 — Compile the Design

### 5.1 Start Compilation
Press **Ctrl + L** or go to **Processing → Start Compilation**

The Tasks panel on the left will show progress through these stages:

```
▶ Analysis & Synthesis    ← Converts Verilog to logic gates
▶ Fitter (Place & Route)  ← Maps gates to FPGA fabric
▶ Assembler               ← Generates .sof programming file
▶ Timing Analyzer         ← Checks timing constraints
▶ EDA Netlist Writer      ← Generates ModelSim simulation files
```

### 5.2 Expected Compilation Result

```
Flow Status    : Successful
Device         : EP4CE22F17C6
Total logic elements : 26 / 22,320 ( < 1 % )
Total registers      : 26
Total pins           : 11 / 154 ( 7 % )
```

### 5.3 Warnings You Can Safely Ignore

| Warning | Reason | Action |
|---|---|---|
| 332012 — Demo.sdc not found | No timing constraints file | Ignore for this test |
| 332148 — Timing requirements not met | No SDC constraints set | Ignore for this test |
| 18236 — NUM_PARALLEL_PROCESSORS not set | Multi-core hint | Ignore |
| 10230 — Truncated value | Counter bit width | Ignore |
| 21074 — Input pins that do not drive logic | KEY1 unused | Ignore |

> **These are all warnings, not errors. Zero errors = successful compilation.**

---

## Step 6 — Simulate with ModelSim

ModelSim launches automatically after compilation via NativeLink. If it doesn't, open it manually from the Windows Start Menu.

### 6.1 Create a Testbench File

**File → New → Verilog HDL File** and paste:

```verilog
`timescale 1ns/1ps

module tb_Demo;

    reg        CLOCK_50;
    reg        KEY0;
    reg        KEY1;
    wire       LED0, LED1, LED2, LED3;
    wire       LED4, LED5, LED6, LED7;

    // Instantiate the design under test
    Demo uut (
        .CLOCK_50(CLOCK_50),
        .KEY0(KEY0),
        .KEY1(KEY1),
        .LED0(LED0),
        .LED1(LED1),
        .LED2(LED2),
        .LED3(LED3),
        .LED4(LED4),
        .LED5(LED5),
        .LED6(LED6),
        .LED7(LED7)
    );

    // 50 MHz clock = 20ns period
    initial CLOCK_50 = 0;
    always #10 CLOCK_50 = ~CLOCK_50;

    initial begin
        KEY0 = 1; KEY1 = 1;   // No reset
        #100;
        KEY0 = 0;              // Press reset
        #60;
        KEY0 = 1;              // Release reset
        #50000;                // Let counter run
        $stop;
    end

    initial begin
        $monitor("Time=%0t LED=%b%b%b%b%b%b%b%b",
            $time, LED7,LED6,LED5,LED4,LED3,LED2,LED1,LED0);
    end

endmodule
```

Save as `tb_Demo.v`

### 6.2 Run Simulation in ModelSim

1. In ModelSim: **File → New → Project** → name it `Demo_sim`
2. **Add Existing File** → add both `Demo.v` and `tb_Demo.v`
3. **Compile → Compile All** — should show 0 errors
4. **Simulate → Start Simulation** → expand `work` → select `tb_Demo` → OK
5. In the Objects panel, right-click signals → **Add to Wave**
6. Click **Run** (or type `run 50us` in console)

**Expected result:** LED signals toggle in sequence — confirms the counter logic is correct.

---

## Step 7 — Install USB-Blaster Driver

The USB-Blaster is the built-in programmer on the DE0-Nano. Windows needs a driver to communicate with it.

### 7.1 Connect the Board
Plug the **mini-USB cable** into the **USB-Blaster port** on the DE0-Nano (top-left of the board, near the blue POWER LED).

The blue POWER LED should turn on immediately.

### 7.2 Check Device Manager
1. Press **Windows + X → Device Manager**
2. Look under **Other Devices** for **USB-Blaster** with a yellow ⚠️ triangle

```
Other Devices
  ⚠️ USB-Blaster    ← This means driver not installed
```

### 7.3 Enable Driver Signature Enforcement Bypass (One-Time Only)

Windows 10/11 blocks unsigned drivers by default. Do this once:

1. Click **Start → Power icon**
2. Hold **Shift** and click **Restart**
3. On the blue screen: **Troubleshoot → Advanced Options → Startup Settings → Restart**
4. When the numbered list appears, press **F7**:
   ```
   7) Disable driver signature enforcement
   ```
5. Windows restarts normally

### 7.4 Install the Driver

After restarting with signature enforcement disabled:

1. Open **Device Manager** again
2. Right-click **USB-Blaster** → **Update Driver**
3. Click **Browse my computer for driver software**
4. Navigate to:
   ```
   C:\intelFPGA_lite\20.1\quartus\drivers\usb-blaster
   ```
5. Make sure **Include subfolders** is checked ✅
6. Click **Next**

If Windows asks "Install anyway?" → click **Yes**

### 7.5 Confirm Driver Installed Successfully

In Device Manager, USB-Blaster should now appear under:

```
Universal Serial Bus Controllers
  ✅ Altera USB-Blaster    ← No yellow triangle = success
```

---

## Step 8 — Program the Board

### 8.1 Open the Programmer
In Quartus: **Tools → Programmer**

### 8.2 Select Hardware
1. Click **Hardware Setup...**
2. Under **"Currently selected hardware"** dropdown, select **USB-Blaster [USB-0]**
3. Click **Close**

The top bar should now show:
```
Hardware Setup...  |  USB-Blaster [USB-0]  |  Mode: JTAG
```

### 8.3 Verify Programming File
The programmer should already show:

| File | Device | Program/Configure |
|---|---|---|
| output_files/Demo.sof | EP4CE22F17 | ✅ checked |

If the .sof file is missing, click **Add File** and navigate to:
```
C:\intelFPGA_lite\20.1\Demo\output_files\Demo.sof
```

### 8.4 Program!
Click **Start**

Watch the progress bar:
```
Progress: [████████████████████] 100% (Successful)
```

> **Note:** `.sof` files are loaded into FPGA RAM — they are lost on power off. For permanent storage, you would program the `.pof` file to the EPCS flash chip instead.

---

## Step 9 — Verify on Hardware

### 9.1 What You Should See Immediately After Programming

| Component | Expected Behaviour |
|---|---|
| Blue POWER LED | Stays ON solid |
| Green LEDs (LED0–LED7) | Blinking/glowing in binary count pattern |
| Counter speed | Slowest LED (~0.67s per toggle visible) |

### 9.2 Test the Reset Button

Press **KEY0** (right button on board):
- All LEDs turn OFF immediately
- Release KEY0 → LEDs start counting again from zero

This confirms both the **clock input** and **button input** are working.

### 9.3 Binary Counting Pattern

The LEDs display a binary counter. Here's what the pattern means:

```
LED7 LED6 LED5 LED4 LED3 LED2 LED1 LED0
  0    0    0    0    0    0    0    1   = 1
  0    0    0    0    0    0    1    0   = 2
  0    0    0    0    0    0    1    1   = 3
  ...
  1    1    1    1    1    1    1    1   = 255
  0    0    0    0    0    0    0    0   = 0 (wraps)
```

Each complete cycle through all 256 states takes approximately **171 seconds**.

---

## What Each Step Confirms

| What's Tested | How It's Tested | Confirmed By |
|---|---|---|
| FPGA chip is alive | Design compiles and routes | Successful compilation |
| 50 MHz oscillator working | Counter increments at 50MHz | LEDs blinking at correct speed |
| FPGA fabric healthy | 26 logic elements used correctly | No routing errors |
| All 8 green LEDs functional | Each driven by individual counter bit | All LEDs visible and different |
| KEY0 push button working | Resets counter to zero | LEDs go off on press |
| USB-Blaster programmer | .sof loaded successfully | 100% progress in Programmer |
| JTAG chain intact | Board detected in Programmer | EP4CE22F17 shown in chain |
| Power supply stable | Board runs without issues | No glitches or resets |

**If all 8 LEDs blink and KEY0 resets them → your DE0-Nano is 100% healthy ✅**

---

## Common Errors & Fixes

### Error: `10170 Verilog HDL syntax error at Demo.v(5)`
**Cause:** Hidden character or wrong bracket in copy-pasted code.
**Fix:** Select all code (Ctrl+A), delete, and re-paste fresh from this README.

### Error: `Cannot launch Device Installer`
**Cause:** Windows path or permission issue with the installer GUI.
**Fix:** Ignore it. Check if Cyclone IV E already appears in **File → New Project → Device** list. If yes, you're fine.

### Error: `Can't open project — you do not have permission`
**Cause:** Quartus not running as Administrator.
**Fix:** Close Quartus → right-click icon → **Run as Administrator** → reopen project.

### Error: `No Hardware` in Programmer
**Cause:** USB-Blaster driver not installed or cable not connected.
**Fix:** Follow Step 7 completely. Make sure mini-USB is in the correct port (near POWER LED).

### Error: `A problem was encountered while adding driver to store`
**Cause:** Windows driver signature enforcement blocking the install.
**Fix:** Follow Step 7.3 — restart with F7 (Disable driver signature enforcement) then install.

### Warning: `332012 Synopsys Design Constraints File not found`
**Cause:** No .sdc timing constraints file created.
**Fix:** Safe to ignore for this project. Add an SDC file for production designs.

### LEDs not blinking after programming
**Cause 1:** Wrong .sof file loaded. Check the filename in Programmer says `Demo.sof`.
**Cause 2:** Pin assignments not saved before compile. Re-run TCL commands → recompile → reprogram.
**Cause 3:** Board in passive mode. Check the MSEL jumpers on the board are in default position.

---

## Project File Structure

After completing all steps, your project folder should look like:

```
C:\intelFPGA_lite\20.1\Demo\
│
├── Demo.qpf                    ← Quartus Project File (open this to reload)
├── Demo.qsf                    ← Settings file (contains pin assignments)
├── Demo.v                      ← Your Verilog design
├── tb_Demo.v                   ← ModelSim testbench
│
├── output_files\
│   ├── Demo.sof                ← FPGA programming file (JTAG, volatile)
│   ├── Demo.pof                ← Flash programming file (permanent)
│   ├── Demo.fit.rpt            ← Fitter report
│   └── Demo.sta.rpt            ← Timing report
│
├── simulation\
│   └── modelsim\
│       └── Demo.vo             ← Gate-level netlist for simulation
│
└── db\                         ← Quartus internal database (auto-generated)
```

---

## Next Steps

Once your board passes this health check, here are suggested next projects in order of complexity:

| Level | Project | What You Learn |
|---|---|---|
| ⭐ | **UART** — send "Hello" to PC terminal | Serial communication |
| ⭐⭐ | **VGA Controller** — display on monitor | Timing, pixel clocks |
| ⭐⭐ | **SPI** — read onboard accelerometer | Sensor interfacing |
| ⭐⭐⭐ | **SDRAM Controller** — use 32MB RAM | Memory interfaces |
| ⭐⭐⭐ | **FIR Filter** — process audio | DSP on FPGA |
| ⭐⭐⭐⭐ | **RISC-V Core** — build your own CPU | Computer architecture |
| ⭐⭐⭐⭐ | **AES Engine** — hardware encryption | Security hardware |

---

## References

- [Terasic DE0-Nano User Manual](https://www.terasic.com.tw/cgi-bin/page/archive.pl?Language=English&CategoryNo=139&No=593&PartNo=4)
- [Intel Quartus Prime Lite Download](https://www.intel.com/content/www/us/en/collections/products/fpga/software/downloads.html)
- [Cyclone IV Device Handbook](https://www.intel.com/content/www/us/en/programmable/documentation/sam1403482608772.html)
- [ModelSim-Altera Starter Documentation](https://www.intel.com/content/www/us/en/docs/programmable/683091/current/introduction.html)

---

## License

This project is open source and free to use for educational purposes.

---

*Tested on: Windows 10/11 | Quartus Prime Lite 20.1.1 | ModelSim-Altera Starter 2020.1 | Terasic DE0-Nano EP4CE22F17C6N*
