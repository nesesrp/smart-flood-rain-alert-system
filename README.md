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
├── main.py          # MicroPython code — runs on ESP32-S3 hardware
├── simulation.py    # PC simulation — demonstrates PEAS class structure
└── README.md
```

---

## Hardware

| Component | Pin |
|-----------|-----|
| Rain sensor (analog) | GPIO 14 |
| Rain sensor (digital) | GPIO 15 |
| Water level sensor | GPIO 2 |
| Buzzer | GPIO 20 |
| LED | GPIO 9 |
| DHT11 (data) | GPIO 4 |
| OLED SDA | GPIO 37 |
| OLED SCL | GPIO 36 |

**Board:** ESP32-S3  
**Firmware:** MicroPython v1.28.0

---

## Risk Levels

| Risk | Condition | Buzzer | LED | OLED |
|------|-----------|--------|-----|------|
| HIGH | Rain detected + water level high | ON | ON | `!! FLOOD RISK !!` |
| MEDIUM | Rain detected OR water level medium | OFF | ON | `** WARNING **` |
| LOW | All clear | OFF | OFF | `** ALL CLEAR **` |

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

## Running the Simulation (PC)

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
Correct Detections: 15
False Alarms      : 0
Accuracy          : 100.0%
```

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
pip3 install esptool mpremote
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
