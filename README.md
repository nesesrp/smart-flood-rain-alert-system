# Smart Flood & Rain Alert System

An intelligent flood and rain detection system built with ESP32-S3 and MicroPython, designed using the **PEAS framework** (Performance, Environment, Actuators, Sensors).

---

## PEAS Framework

| Component | Description |
|-----------|-------------|
| **Performance** | Accurate flood/rain detection, fast response time, minimal false alarms |
| **Environment** | Outdoor area subject to rain and rising water levels |
| **Actuators** | Buzzer, LED, 128×64 OLED display (SSD1306) |
| **Sensors** | Rain sensor (analog + digital), Water level sensor, DHT11 (temperature & humidity) |

---

## Project Structure

```
.
├── main.py             # MicroPython code — runs on ESP32-S3 hardware
├── simulation.py       # Terminal simulation — demonstrates PEAS class structure
├── simulation_gui.py   # GUI simulation — Tkinter interface with Start/Stop control
├── dashboard.py        # PC dashboard — reads live data from ESP32 via serial port
└── README.md
```

---

## Hardware

| Component | Pin |
|-----------|-----|
| Rain sensor (analog AO) | GPIO 15 |
| Rain sensor (digital DO) | GPIO 14 |
| Water level sensor | GPIO 2 |
| Buzzer | GPIO 21 |
| LED | GPIO 9 |
| Green LED (LOW) | GPIO 40 |
| Yellow LED (MEDIUM) | GPIO 45 |
| Red LED (HIGH) | GPIO 41 |
| DHT11 (data) | GPIO 4 |
| OLED SDA | GPIO 37 |
| OLED SCL | GPIO 36 |

**Board:** ESP32-S3  
**Firmware:** MicroPython v1.28.0

---

## Risk Levels

| Risk | Condition | Buzzer | LED (GPIO 9) | Green (GPIO 40) | Yellow (GPIO 45) | Red (GPIO 41) | OLED |
|------|-----------|--------|--------------|-----------------|------------------|---------------|------|
| HIGH | Water level high (> 3000) | ON | ON | OFF | OFF | ON | `!! FLOOD RISK !!` |
| MEDIUM | Water level medium (> 550) OR rain detected | OFF | ON | OFF | ON | OFF | `** WARNING **` |
| LOW | All clear | OFF | OFF | ON | OFF | OFF | `** ALL CLEAR **` |

OLED display layout (128×64):
```
** ALL CLEAR **
────────────────
Risk  : LOW
Rain  : No
Temp  : 25 C
Humid : 53 %
```

---

## Running the Terminal Simulation (PC)

No hardware required. Runs on standard Python 3.

**Step 1 — Open a terminal in VS Code:**
> Terminal → New Terminal

**Step 2 — Run:**
```bash
python3 simulation.py
```

**Step 3 — Stop:** `Ctrl + C`

### Example Output

```
=== Smart Flood & Rain Alert System ===
Sense -> Think -> Decide -> Act

--- Time Step 1 ---
Environment : {'weather': 'heavy_rain', 'water_level': 'high', ...}
Perception  : {'rain_detected': True, 'rain_intensity': 'heavy_rain', ...}
Risk Level  : HIGH
  [BUZZER] BEEP BEEP BEEP!
  [LED] Red LED ON
  [OLED] !! FLOOD RISK !!
  [OLED] Temp:28.3C Hum:54.7%
  [OLED] Evacuate now!

=== PERFORMANCE REPORT ===
Total Steps       : 15
Correct Detections: 13
False Alarms      : 1
```

---

## Running the GUI Simulation (PC)

A Tkinter-based graphical simulation of the PEAS agent. No hardware required.

**Requirements:**
```bash
brew install python-tk@3.14   # macOS only, if tkinter is missing
```

**Run:**
```bash
python3 simulation_gui.py
```

**How to use:**
- Press **▶ Start** — sensor values update automatically every 2 seconds
- Press **⏹ Stop** — pauses the simulation
- The risk banner changes color: red (HIGH), orange (MEDIUM), green (LOW)
- Performance panel tracks Steps, Correct detections, and False Alarms in real time

---

## Running the PC Dashboard (Live Hardware)

Reads real sensor data from the ESP32-S3 via USB serial and displays it on a graphical dashboard.

**Requirements:**
```bash
pip3 install pyserial
```

**Run:**
```bash
python3 dashboard.py
```

> Make sure the ESP32-S3 is connected and running `main.py` before launching the dashboard.  
> Default port: `/dev/cu.usbserial-14420` — edit `PORT` in `dashboard.py` if your port is different.

---

## Running on ESP32-S3 (Hardware)

**Step 1 — Open a terminal in VS Code:**
> Terminal → New Terminal

**Step 2 — Connect ESP32-S3 via USB**, then find the port:
```bash
ls /dev/cu.*
```
Look for something like `/dev/cu.usbserial-XXXX`.

**Step 3 — Upload the code to the board:**
```bash
python3 -m mpremote connect /dev/cu.usbserial-14420 cp main.py :main.py
```

**Step 4 — Run:**
```bash
python3 -m mpremote connect /dev/cu.usbserial-14420 run main.py
```

**Step 5 — Stop:** `Ctrl + C`

> **Tip:** To make the code run automatically every time the board powers on, upload it as `boot.py`:
> ```bash
> python3 -m mpremote connect /dev/cu.usbserial-14420 cp main.py :boot.py
> ```

---

## First-Time Setup

### 1. Install tools
```bash
pip3 install esptool mpremote pyserial
```

### 2. Flash MicroPython firmware to ESP32-S3
```bash
# Erase flash
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-XXXX erase-flash

# Write firmware
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-XXXX write-flash 0x0 firmware.bin
```
Download firmware from: https://micropython.org/download/ESP32_GENERIC_S3/

### 3. Install MicroPython libraries (run once on the board)
```bash
python3 -m mpremote connect /dev/cu.usbserial-XXXX exec "import mip; mip.install('ssd1306'); mip.install('dht')"
```
