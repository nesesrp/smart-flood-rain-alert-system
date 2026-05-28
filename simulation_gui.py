"""
Smart Flood & Rain Alert System — GUI Application
Two modes:
  [1] Simulation  — random PEAS data, no hardware needed
  [2] Live Serial — reads real data from ESP32-S3 via USB
Run: python3 simulation_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import random
import threading
import re
import glob
import sys

# ── PEAS Classes (Simulation Mode) ────────────────────────────────────

class FloodEnvironment:
    def get_state(self):
        return {
            "weather"     : random.choice(["clear", "light_rain", "heavy_rain"]),
            "water_level" : random.choice(["low", "medium", "high"]),
            "temperature" : round(random.uniform(20, 40), 1),
            "humidity"    : round(random.uniform(40, 100), 1),
        }

class Sensors:
    def sense(self, env):
        return {
            "rain_detected" : env["weather"] != "clear",
            "rain_intensity": env["weather"],
            "water_level"   : env["water_level"],
            "temperature"   : env["temperature"],
            "humidity"      : env["humidity"],
        }

class FloodAlertAgent:
    def __init__(self):
        self.total        = 0
        self.correct      = 0
        self.false_alarms = 0

    def decide(self, p):
        rain      = p["rain_detected"]
        water     = p["water_level"]
        intensity = p["rain_intensity"]
        if water == "high" and rain:
            return "HIGH"
        elif water == "high" or intensity == "heavy_rain":
            return "MEDIUM"
        elif water == "medium" or rain:
            return "MEDIUM"
        else:
            return "LOW"

    def update(self, p, risk):
        self.total += 1
        truth = self._truth(p)
        if risk == truth or (truth in ("HIGH", "MEDIUM") and risk in ("HIGH", "MEDIUM")):
            self.correct += 1
        elif truth == "LOW" and risk == "HIGH":
            self.false_alarms += 1

    def _truth(self, p):
        w = p["water_level"]
        i = p["rain_intensity"]
        if w == "high":
            return "HIGH"
        elif w == "medium" and i == "heavy_rain":
            return "HIGH"
        elif w == "medium" or i == "heavy_rain":
            return "MEDIUM"
        else:
            return "LOW"

    def accuracy(self):
        return (self.correct / max(self.total, 1)) * 100

# ── Colors ────────────────────────────────────────────────────────────

BG      = "#1a1a2e"
CARD    = "#16213e"
HIGH    = "#e63946"
MEDIUM  = "#f4a261"
LOW     = "#2a9d8f"
TEXT    = "#ffffff"
SUBTEXT = "#aaaaaa"

RISK_COLOR    = {"HIGH": HIGH, "MEDIUM": MEDIUM, "LOW": LOW}
WEATHER_LABEL = {"clear": "☀️  Clear", "light_rain": "🌦  Light Rain", "heavy_rain": "⛈  Heavy Rain"}
WATER_LABEL   = {"low": "💧  Low", "medium": "🌊  Medium", "high": "🚨  High"}

# ── Mode Selection Dialog ─────────────────────────────────────────────

class ModeDialog:
    def __init__(self, root):
        self.root = root
        self.mode = None
        self.port = None

        root.title("Smart Flood & Rain Alert System")
        root.geometry("440x300")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(root, text="Smart Flood & Rain Alert System",
                 font=("Helvetica", 14, "bold"), bg=BG, fg=TEXT).pack(pady=(24, 4))
        tk.Label(root, text="Select operating mode",
                 font=("Helvetica", 10), bg=BG, fg=SUBTEXT).pack(pady=(0, 20))

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack()

        tk.Button(
            btn_frame, text="[1]   Simulation Mode",
            font=("Helvetica", 12, "bold"),
            bg=LOW, fg=BG, activebackground="#1f7a70", activeforeground=BG,
            relief="flat", padx=20, pady=12, width=24,
            command=self._sim_mode
        ).pack(pady=5)

        tk.Button(
            btn_frame, text="[2]   Live Serial Mode  (ESP32)",
            font=("Helvetica", 12, "bold"),
            bg=MEDIUM, fg=BG, activebackground="#c47a3a", activeforeground=BG,
            relief="flat", padx=20, pady=12, width=24,
            command=self._live_mode
        ).pack(pady=5)

        tk.Label(root,
                 text="Simulation: no hardware needed   ·   Live: ESP32 must be connected via USB",
                 font=("Helvetica", 9), bg=BG, fg=SUBTEXT).pack(pady=(16, 0))

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _sim_mode(self):
        self.mode = "simulation"
        self.root.destroy()

    def _live_mode(self):
        self.mode = "live"
        ports = (glob.glob("/dev/cu.usbserial-*") +
                 glob.glob("/dev/ttyUSB*") +
                 glob.glob("/dev/ttyACM*"))
        self.port = ports[0] if ports else "/dev/cu.usbserial-14420"
        self.root.destroy()

    def _on_close(self):
        self.root.destroy()

# ── Main GUI ──────────────────────────────────────────────────────────

class FloodAlertGUI:
    def __init__(self, root, mode, port=None):
        self.root  = root
        self.mode  = mode
        self.port  = port

        title_suffix = "Simulation Mode" if mode == "simulation" else f"Live  ·  {port}"
        self.root.title(f"Flood Alert — {title_suffix}")
        self.root.geometry("700x760")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Shared agent (tracks performance in both modes)
        self.env   = FloodEnvironment()
        self.sens  = Sensors()
        self.agent = FloodAlertAgent()
        self.step  = 0

        # Simulation state
        self.running = False
        self._job    = None

        # Live serial state
        self.serial_conn   = None
        self._live_running = False
        self._buf          = {}   # accumulates partial line data between "---" separators

        self._build()

        if mode == "live":
            self._connect_serial()

    # ── Layout ────────────────────────────────────────────────────────

    def _build(self):
        if self.mode == "simulation":
            self._build_simulation()
        else:
            self._build_live()

    # Simulation layout — full PEAS panels
    def _build_simulation(self):
        self.root.geometry("700x760")
        tk.Label(self.root, text="Smart Flood & Rain Alert System",
                 font=("Helvetica", 17, "bold"), bg=BG, fg=TEXT).pack(pady=(14, 2))
        tk.Label(self.root, text="Simulation Mode — PEAS Framework",
                 font=("Helvetica", 10), bg=BG, fg=SUBTEXT).pack()

        self.risk_lbl = tk.Label(self.root, text="Press  ▶ Start  to begin",
                                 font=("Helvetica", 22, "bold"),
                                 bg=CARD, fg=TEXT, height=2, relief="flat")
        self.risk_lbl.pack(fill="x", padx=20, pady=10)

        self._build_water_bar()

        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=20, pady=4)
        env_card  = self._card(row, "Environment (E)")
        perc_card = self._card(row, "Perception — Sensors (S)")
        env_card.pack(side="left",  expand=True, fill="both", padx=(0, 6))
        perc_card.pack(side="left", expand=True, fill="both")

        self.weather_lbl = self._row_label(env_card,  "Weather",      "—")
        self.wlevel_lbl  = self._row_label(env_card,  "Water Level",  "—")
        self.temp_lbl    = self._row_label(env_card,  "Temperature",  "—")
        self.hum_lbl     = self._row_label(env_card,  "Humidity",     "—")

        self.rain_lbl   = self._row_label(perc_card, "Rain Detected", "—")
        self.intens_lbl = self._row_label(perc_card, "Intensity",     "—")
        self.pw_lbl     = self._row_label(perc_card, "Water Level",   "—")
        self.pt_lbl     = self._row_label(perc_card, "Temp / Hum",    "—")

        act_card = self._card(self.root, "Actuators (A)")
        act_card.pack(fill="x", padx=20, pady=6)
        act_row = tk.Frame(act_card, bg=CARD)
        act_row.pack(fill="x")
        self.buzzer_lbl = self._act_box(act_row, "🔔  BUZZER", SUBTEXT)
        self.led_lbl    = self._act_box(act_row, "💡  LED",    SUBTEXT)
        self.oled_lbl   = self._act_box(act_row, "🖥  OLED",   SUBTEXT)

        perf_card = self._card(self.root, "Performance Measure (P)")
        perf_card.pack(fill="x", padx=20, pady=4)
        prow = tk.Frame(perf_card, bg=CARD)
        prow.pack(fill="x")
        self.step_lbl    = self._perf_box(prow, "Steps",        "0")
        self.correct_lbl = self._perf_box(prow, "Correct",      "0")
        self.false_lbl   = self._perf_box(prow, "False Alarms", "0")
        self.acc_lbl     = self._perf_box(prow, "Accuracy",     "—")

        btn_row = tk.Frame(self.root, bg=BG)
        btn_row.pack(pady=10)
        self.start_btn = tk.Button(
            btn_row, text="▶  Start",
            font=("Helvetica", 13, "bold"),
            bg=LOW, fg=BG, activebackground="#1f7a70", activeforeground=BG,
            relief="flat", padx=24, pady=8, command=self._start
        )
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = tk.Button(
            btn_row, text="⏹  Stop",
            font=("Helvetica", 13, "bold"),
            bg="#555566", fg=BG, activebackground="#444455", activeforeground=BG,
            relief="flat", padx=24, pady=8,
            command=self._stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=8)
        self.step_info = tk.Label(self.root, text="Step: 0  |  Interval: 2 sec",
                                  font=("Helvetica", 10), bg=BG, fg=SUBTEXT)
        self.step_info.pack()

        tk.Button(
            self.root, text="← Back to Menu",
            font=("Helvetica", 10),
            bg="#000000", fg=BG, activebackground="#222222", activeforeground=BG,
            relief="flat", padx=16, pady=6,
            command=self._back
        ).pack(pady=(4, 10))

    # Live layout — matches dashboard.py
    def _build_live(self):
        self.root.geometry("660x560")
        tk.Label(self.root, text="Smart Flood & Rain Alert System",
                 font=("Helvetica", 17, "bold"), bg=BG, fg=TEXT).pack(pady=(14, 4))

        self.risk_lbl = tk.Label(self.root, text="RISK: —",
                                 font=("Helvetica", 30, "bold"),
                                 bg=LOW, fg=TEXT, height=2, relief="flat")
        self.risk_lbl.pack(fill="x", padx=20, pady=(4, 10))

        self._build_water_bar()

        info_row = tk.Frame(self.root, bg=BG)
        info_row.pack(fill="x", padx=20, pady=6)
        self.rain_box = self._sensor_card(info_row, "Rain",     "—")
        self.temp_box = self._sensor_card(info_row, "Temp",     "--°C")
        self.hum_box  = self._sensor_card(info_row, "Humidity", "--%")

        self._build_log("Serial Log")

        self.status_lbl = tk.Label(self.root, text="Connecting…",
                                   font=("Helvetica", 9), bg=BG, fg=SUBTEXT)
        self.status_lbl.pack(pady=(6, 2))

        tk.Button(
            self.root, text="← Back to Menu",
            font=("Helvetica", 10),
            bg="#000000", fg=BG, activebackground="#222222", activeforeground=BG,
            relief="flat", padx=16, pady=6,
            command=self._back
        ).pack(pady=(0, 8))

    # ── Shared Layout Helpers ─────────────────────────────────────────

    def _build_water_bar(self):
        water_card = tk.Frame(self.root, bg=CARD, padx=12, pady=8)
        water_card.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(water_card, text="Water Level  (ADC 0 – 4095)",
                 font=("Helvetica", 9, "bold"), bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0, 4))
        style = ttk.Style()
        style.theme_use("default")
        style.configure("flood.Horizontal.TProgressbar",
                        troughcolor=BG, background=LOW, thickness=18)
        self.water_bar = ttk.Progressbar(
            water_card, style="flood.Horizontal.TProgressbar",
            length=600, maximum=4095, mode="determinate"
        )
        self.water_bar.pack(fill="x")
        self.water_val_lbl = tk.Label(water_card, text="0 / 4095",
                                      font=("Helvetica", 9), bg=CARD, fg=SUBTEXT)
        self.water_val_lbl.pack(anchor="e")

    def _build_log(self, label):
        log_frame = tk.Frame(self.root, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(4, 0))
        tk.Label(log_frame, text=label, font=("Helvetica", 9),
                 bg=BG, fg=SUBTEXT).pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            log_frame, height=8,
            bg="#0f0f23", fg="#00ff88",
            font=("Courier", 9), state="disabled",
            relief="flat", bd=0
        )
        self.log.pack(fill="both", expand=True)

    def _sensor_card(self, parent, title, initial):
        frame = tk.Frame(parent, bg=CARD, padx=10, pady=10)
        frame.pack(side="left", expand=True, fill="both", padx=4)
        tk.Label(frame, text=title, font=("Helvetica", 10),
                 bg=CARD, fg=SUBTEXT).pack()
        lbl = tk.Label(frame, text=initial,
                       font=("Helvetica", 18, "bold"), bg=CARD, fg=TEXT)
        lbl.pack()
        return lbl

    # ── Widget Helpers ────────────────────────────────────────────────

    def _card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, padx=12, pady=10)
        tk.Label(frame, text=title, font=("Helvetica", 10, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0, 6))
        return frame

    def _row_label(self, parent, key, val):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=key+":", font=("Helvetica", 10),
                 bg=CARD, fg=SUBTEXT, width=14, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=val, font=("Helvetica", 10, "bold"),
                       bg=CARD, fg=TEXT, anchor="w")
        lbl.pack(side="left")
        return lbl

    def _act_box(self, parent, title, color):
        f = tk.Frame(parent, bg=CARD)
        f.pack(side="left", expand=True, fill="both", padx=4, pady=2)
        lbl = tk.Label(f, text=title, font=("Helvetica", 12, "bold"),
                       bg=CARD, fg=color, pady=8)
        lbl.pack(fill="x")
        return lbl

    def _perf_box(self, parent, title, val):
        f = tk.Frame(parent, bg=CARD)
        f.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        tk.Label(f, text=title, font=("Helvetica", 9), bg=CARD, fg=SUBTEXT).pack()
        lbl = tk.Label(f, text=val, font=("Helvetica", 16, "bold"), bg=CARD, fg=TEXT)
        lbl.pack()
        return lbl

    def _log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    # ── Simulation Control ────────────────────────────────────────────

    def _start(self):
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal", bg=HIGH, fg=BG)
        self._loop()

    def _stop(self):
        self.running = False
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled", bg="#555566")

    def _loop(self):
        if not self.running:
            return
        self._run_sim_step()
        self._job = self.root.after(2000, self._loop)

    def _run_sim_step(self):
        self.step += 1
        env_state  = self.env.get_state()
        perception = self.sens.sense(env_state)
        risk       = self.agent.decide(perception)
        self.agent.update(perception, risk)

        # Map categorical water level to an approximate ADC value for the bar
        wl_adc = {"low": 300, "medium": 1200, "high": 3500}[env_state["water_level"]]
        self._update_water_bar(wl_adc)
        self._update_risk(risk)

        # Environment panel
        self.weather_lbl.config(text=WEATHER_LABEL.get(env_state["weather"], env_state["weather"]))
        self.wlevel_lbl.config(text=WATER_LABEL.get(env_state["water_level"], env_state["water_level"]))
        self.temp_lbl.config(text=f"{env_state['temperature']} °C")
        self.hum_lbl.config(text=f"{env_state['humidity']} %")

        # Perception panel
        rain = perception["rain_detected"]
        self.rain_lbl.config(text="YES 🌧" if rain else "No ☀️", fg=HIGH if rain else TEXT)
        self.intens_lbl.config(text=perception["rain_intensity"].replace("_", " ").title())
        wl = perception["water_level"]
        self.pw_lbl.config(text=wl.title(),
                           fg=HIGH if wl == "high" else MEDIUM if wl == "medium" else TEXT)
        self.pt_lbl.config(text=f"{perception['temperature']}°C / {perception['humidity']}%")

        self._update_actuators(risk)
        self._update_perf()
        self.step_info.config(text=f"Step: {self.step}  |  Interval: 2 sec")

    # ── Live Serial ───────────────────────────────────────────────────

    def _connect_serial(self):
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, 115200, timeout=1)
            self._live_running = True
            self.status_lbl.config(text=f"Connected  ·  {self.port}  ·  115200 baud")
            threading.Thread(target=self._read_serial, daemon=True).start()
        except ImportError:
            self.status_lbl.config(
                text="pyserial not found — run: pip install pyserial", fg=HIGH)
        except Exception as e:
            self.status_lbl.config(text=f"Connection failed: {e}", fg=HIGH)

    def _read_serial(self):
        while self._live_running:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self.root.after(0, self._process_line, line)
            except Exception:
                pass

    def _process_line(self, line):
        self._log(line)

        if "Water level" in line:
            m = re.search(r":\s*(\d+)", line)
            if m:
                val = int(m.group(1))
                self._buf["water_val"] = val
                self._update_water_bar(val)

        elif line.startswith("Rain"):
            m = re.search(r":\s*(\w+)", line)
            if m:
                rain = m.group(1) == "YES"
                self._buf["rain"] = rain
                self.rain_box.config(text="YES 🌧" if rain else "No ☀️",
                                     fg=HIGH if rain else TEXT)

        elif "Temperature" in line:
            t = re.search(r"Temperature\s*:\s*([\d.]+)", line)
            h = re.search(r"Humidity:\s*([\d.]+)", line)
            if t:
                self._buf["temp"] = t.group(1)
                self.temp_box.config(text=f"{t.group(1)}°C")
            if h:
                self._buf["hum"] = h.group(1)
                self.hum_box.config(text=f"{h.group(1)}%")

        elif line.startswith("Risk"):
            m = re.search(r":\s*(\w+)", line)
            if m:
                risk = m.group(1)
                self._buf["risk"] = risk
                self._update_risk(risk)
                self._live_update_perf(risk)

        elif line == "---":
            self.step += 1

    def _live_update_perf(self, risk):
        water_val = self._buf.get("water_val", 0)
        rain      = self._buf.get("rain", False)
        wl = "high" if water_val > 3000 else "medium" if water_val > 550 else "low"
        truth = "HIGH" if wl == "high" else ("MEDIUM" if wl == "medium" or rain else "LOW")

        self.agent.total += 1
        if risk == truth or (truth in ("HIGH", "MEDIUM") and risk in ("HIGH", "MEDIUM")):
            self.agent.correct += 1
        elif truth == "LOW" and risk == "HIGH":
            self.agent.false_alarms += 1

    # ── Shared UI Updates ─────────────────────────────────────────────

    def _update_risk(self, risk):
        self.risk_lbl.config(text=f"RISK: {risk}", bg=RISK_COLOR.get(risk, CARD))

    def _update_water_bar(self, val):
        self.water_bar["value"] = val
        self.water_val_lbl.config(text=f"{val} / 4095")
        color = HIGH if val > 3000 else MEDIUM if val > 550 else LOW
        ttk.Style().configure("flood.Horizontal.TProgressbar", background=color)

    def _update_actuators(self, risk):
        if risk == "HIGH":
            self.buzzer_lbl.config(text="🔔  BEEP BEEP!", fg=HIGH)
            self.led_lbl.config(text="💡  LED ON",       fg=HIGH)
            self.oled_lbl.config(text="🖥  FLOOD RISK!", fg=HIGH)
        elif risk == "MEDIUM":
            self.buzzer_lbl.config(text="🔔  Silent",    fg=SUBTEXT)
            self.led_lbl.config(text="💡  LED ON",       fg=MEDIUM)
            self.oled_lbl.config(text="🖥  WARNING",     fg=MEDIUM)
        else:
            self.buzzer_lbl.config(text="🔔  Silent",    fg=SUBTEXT)
            self.led_lbl.config(text="💡  LED OFF",      fg=SUBTEXT)
            self.oled_lbl.config(text="🖥  ALL CLEAR",   fg=LOW)

    def _update_perf(self):
        self.step_lbl.config(text=str(self.agent.total))
        self.correct_lbl.config(text=str(self.agent.correct))
        self.false_lbl.config(text=str(self.agent.false_alarms))
        self.acc_lbl.config(text=f"{self.agent.accuracy():.1f}%")

    def _back(self):
        self._stop() if self.mode == "simulation" else None
        self._live_running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("440x300")
        sel = tk.Toplevel(self.root)
        dialog = ModeDialog(sel)
        self.root.wait_window(sel)
        if dialog.mode is None:
            self.root.destroy()
            return
        self.__init__(self.root, mode=dialog.mode, port=dialog.port)

    def on_close(self):
        self.running       = False
        self._live_running = False
        if self._job:
            self.root.after_cancel(self._job)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.root.destroy()


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()   # hide until mode is chosen

    sel = tk.Toplevel(root)
    dialog = ModeDialog(sel)
    root.wait_window(sel)   # block until selection window closes

    if dialog.mode is None:
        root.destroy()
        sys.exit(0)

    root.deiconify()
    app = FloodAlertGUI(root, mode=dialog.mode, port=dialog.port)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
