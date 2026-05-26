"""
Smart Flood & Rain Alert System — GUI Simulation
Simulates the PEAS agent with a Tkinter interface.
Run: python3 simulation_gui.py
"""

import tkinter as tk
import random

# ── PEAS Classes ──────────────────────────────────────────────────────

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
        if risk == truth or (truth in ("HIGH","MEDIUM") and risk in ("HIGH","MEDIUM")):
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

# ── Colours ───────────────────────────────────────────────────────────

BG      = "#1a1a2e"
CARD    = "#16213e"
HIGH    = "#e63946"
MEDIUM  = "#f4a261"
LOW     = "#2a9d8f"
TEXT    = "#ffffff"
SUBTEXT = "#aaaaaa"

RISK_COLOR    = {"HIGH": HIGH, "MEDIUM": MEDIUM, "LOW": LOW}
WEATHER_LABEL = {"clear": "☀️  Clear", "light_rain": "🌦  Light Rain", "heavy_rain": "⛈  Heavy Rain"}
WATER_LABEL   = {"low": "💧  Low",    "medium": "🌊  Medium",      "high": "🚨  High"}

# ── GUI ───────────────────────────────────────────────────────────────

class SimulationGUI:
    def __init__(self, root):
        self.root    = root
        self.root.title("Flood Alert — GUI Simulation")
        self.root.geometry("680x640")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.env     = FloodEnvironment()
        self.sens    = Sensors()
        self.agent   = FloodAlertAgent()
        self.step    = 0
        self.running = False
        self._job    = None

        self._build()

    # ── Layout ────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self.root, text="Smart Flood & Rain Alert System",
                 font=("Helvetica", 17, "bold"), bg=BG, fg=TEXT).pack(pady=(14, 2))
        tk.Label(self.root, text="GUI Simulation — PEAS Framework",
                 font=("Helvetica", 10), bg=BG, fg=SUBTEXT).pack()

        # Risk banner
        self.risk_lbl = tk.Label(
            self.root, text="Press  ▶ Start  to begin",
            font=("Helvetica", 22, "bold"),
            bg=CARD, fg=TEXT, height=2, relief="flat"
        )
        self.risk_lbl.pack(fill="x", padx=20, pady=10)

        # Environment & Perception
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=20, pady=4)

        env_card  = self._card(row, "Environment (E)")
        perc_card = self._card(row, "Perception (Sensors)")
        env_card.pack(side="left",  expand=True, fill="both", padx=(0,6))
        perc_card.pack(side="left", expand=True, fill="both")

        self.weather_lbl = self._row_label(env_card,  "Weather",      "—")
        self.wlevel_lbl  = self._row_label(env_card,  "Water Level",  "—")
        self.temp_lbl    = self._row_label(env_card,  "Temperature",  "—")
        self.hum_lbl     = self._row_label(env_card,  "Humidity",     "—")

        self.rain_lbl    = self._row_label(perc_card, "Rain Detected","—")
        self.intens_lbl  = self._row_label(perc_card, "Intensity",    "—")
        self.pw_lbl      = self._row_label(perc_card, "Water Level",  "—")
        self.pt_lbl      = self._row_label(perc_card, "Temp / Hum",   "—")

        # Actuators
        act_card = self._card(self.root, "Actuators (A)")
        act_card.pack(fill="x", padx=20, pady=6)
        act_row  = tk.Frame(act_card, bg=CARD)
        act_row.pack(fill="x")
        self.buzzer_lbl = self._act_box(act_row, "🔔  BUZZER", SUBTEXT)
        self.led_lbl    = self._act_box(act_row, "💡  LED",    SUBTEXT)
        self.oled_lbl   = self._act_box(act_row, "🖥  OLED",   SUBTEXT)

        # Performance
        perf_card = self._card(self.root, "Performance Measure (P)")
        perf_card.pack(fill="x", padx=20, pady=4)
        prow = tk.Frame(perf_card, bg=CARD)
        prow.pack(fill="x")
        self.step_lbl    = self._perf_box(prow, "Steps",       "0")
        self.correct_lbl = self._perf_box(prow, "Correct",     "0")
        self.false_lbl   = self._perf_box(prow, "False Alarms","0")
        self.acc_lbl     = self._perf_box(prow, "Accuracy",    "—")

        # Start / Stop buttons
        btn_row = tk.Frame(self.root, bg=BG)
        btn_row.pack(pady=12)

        self.start_btn = tk.Button(
            btn_row, text="▶  Start",
            font=("Helvetica", 13, "bold"),
            bg=LOW, fg=TEXT, activebackground="#1f7a70",
            relief="flat", padx=24, pady=8,
            command=self._start
        )
        self.start_btn.pack(side="left", padx=8)

        self.stop_btn = tk.Button(
            btn_row, text="⏹  Stop",
            font=("Helvetica", 13, "bold"),
            bg="#555566", fg=TEXT, activebackground="#444455",
            relief="flat", padx=24, pady=8,
            command=self._stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=8)

        self.step_info = tk.Label(self.root, text="Step: 0  |  Interval: 2 sec",
                                  font=("Helvetica", 10), bg=BG, fg=SUBTEXT)
        self.step_info.pack()

    # ── Helpers ───────────────────────────────────────────────────────

    def _card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, padx=12, pady=10)
        tk.Label(frame, text=title, font=("Helvetica", 10, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0,6))
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

    # ── Control ───────────────────────────────────────────────────────

    def _start(self):
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal", bg=HIGH)
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
        self._run_step()
        self._job = self.root.after(2000, self._loop)

    # ── Step ──────────────────────────────────────────────────────────

    def _run_step(self):
        self.step += 1
        env_state  = self.env.get_state()
        perception = self.sens.sense(env_state)
        risk       = self.agent.decide(perception)
        self.agent.update(perception, risk)

        # Risk banner
        self.risk_lbl.config(text=f"RISK: {risk}", bg=RISK_COLOR[risk])

        # Environment
        self.weather_lbl.config(text=WEATHER_LABEL.get(env_state["weather"], env_state["weather"]))
        self.wlevel_lbl.config(text=WATER_LABEL.get(env_state["water_level"], env_state["water_level"]))
        self.temp_lbl.config(text=f"{env_state['temperature']} °C")
        self.hum_lbl.config(text=f"{env_state['humidity']} %")

        # Perception
        rain = perception["rain_detected"]
        self.rain_lbl.config(text="YES 🌧" if rain else "No ☀️",
                             fg=HIGH if rain else TEXT)
        self.intens_lbl.config(text=perception["rain_intensity"].replace("_"," ").title())
        wl = perception["water_level"]
        self.pw_lbl.config(text=wl.title(),
                           fg=HIGH if wl=="high" else MEDIUM if wl=="medium" else TEXT)
        self.pt_lbl.config(text=f"{perception['temperature']}°C / {perception['humidity']}%")

        # Actuators
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

        # Performance
        self.step_lbl.config(text=str(self.agent.total))
        self.correct_lbl.config(text=str(self.agent.correct))
        self.false_lbl.config(text=str(self.agent.false_alarms))
        self.acc_lbl.config(text=f"{self.agent.accuracy():.1f}%")
        self.step_info.config(text=f"Step: {self.step}  |  Interval: 2 sec")

# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    SimulationGUI(root)
    root.mainloop()
