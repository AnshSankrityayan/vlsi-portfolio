# How to Make an FPGA Remember Your Code

By default, your DE0-Nano forgets everything when you unplug it. Here's why, and how to fix it.

---

## Why does the FPGA forget?

A **microcontroller** has flash memory built in — it stores your program permanently. Power off, power on, program is still there.

An **FPGA is different**. The Cyclone IV on your DE0-Nano stores its configuration in SRAM — which is volatile.

```
Power off → SRAM clears → FPGA is blank again
```

So every time you power on, the FPGA needs to be configured from scratch.

---

## The fix — program the flash chip, not the FPGA

Your DE0-Nano has a separate **serial flash chip** (EPCS64) sitting next to the FPGA. When you power on, this chip automatically loads the saved configuration into the FPGA.

You need to program this chip instead of the FPGA directly.

The difference comes down to which file you use:

| File | What it does |
|------|-------------|
| `.sof` | Programs the FPGA directly — **lost on power off** |
| `.pof` | Programs the flash chip — **survives power off ✓** |

---

## Step by step

### Step 1 — Open the Programmer
Go to **Tools → Programmer**

### Step 2 — Change the mode
Top left of the Programmer window you'll see a dropdown that says **JTAG**.  
Change it to **Active Serial Programming**.

### Step 3 — Add the .pof file
The file list will clear. Click **Add File** and navigate to:
```
output_files/Button_Debouncer.pof
```

### Step 4 — Tick the right boxes
Make sure these are checked:
```
☑ Program/Configure
☑ Verify
```

### Step 5 — Program it
Click **Start**. Takes 30–60 seconds (flash is slower than SRAM).  
Wait for: **100% (Programming Successful)**

### Step 6 — Test it
- Unplug the USB completely
- Wait 5 seconds
- Plug back in

Your design should load on its own immediately — no Quartus needed.

---

## Don't see a .pof file?

Quartus didn't generate it. Fix:

1. **Assignments → Device**
2. Click **Device and Pin Options**
3. Go to the **Programming Files** tab
4. Tick **Programmer Object File (.pof)**
5. Click OK
6. Recompile with **Ctrl+L**

The `.pof` file will now appear in `output_files/` after compilation.

---

## Quick reference

```
At your desk, USB connected   →  use .sof  (fast to program, temporary)
Standalone / power bank       →  use .pof  (permanent, survives power off)
```

Always use `.pof` when you want the board to work without a computer.
