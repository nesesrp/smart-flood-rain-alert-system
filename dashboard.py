"""
Smart Flood & Rain Alert System — PC Dashboard
Reads live sensor data from ESP32-S3 via serial port and displays it.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import threading
import re

PORT = "/dev/cu.usbserial-14420"
BAUD = 115200

COLORS = {
    "bg":       "#1a1a2e",
    "card":     "#16213e",
    "HIGH":     "#e63946",
    "MEDIUM":   "#f4a261",
    "LOW":      "#2a9d8f",
    "text":     "#ffffff",
    "subtext":  "#aaaaaa",
    "log_bg":   "#0f0f23",
    "log_text": "#00ff88",
}


class FloodDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Flood & Rain Alert System")
        self.root.geometry("660x560")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)

        self.serial_conn = None
        self.running = False

        self._build_ui()
        self._connect_serial()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Title
        tk.Label(
            self.root, text="Smart Flood & Rain Alert System",
            font=("Helvetica", 17, "bold"),
            bg=COLORS["bg"], fg=COLORS["text"]
        ).pack(pady=(14, 4))

        # ── Risk banner ──────────────────────────────────────────────
        self.risk_label = tk.Label(
            self.root, text="RISK: LOW",
            font=("Helvetica", 30, "bold"),
            bg=COLORS["LOW"], fg=COLORS["text"],
            height=2, relief="flat"
        )
        self.risk_label.pack(fill="x", padx=20, pady=(4, 10))

        # ── Water level ──────────────────────────────────────────────
        water_card = tk.Frame(self.root, bg=COLORS["card"], padx=12, pady=10)
        water_card.pack(fill="x", padx=20, pady=4)

        tk.Label(
            water_card, text="Water Level",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["card"], fg=COLORS["subtext"]
        ).pack(anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "flood.Horizontal.TProgressbar",
            troughcolor=COLORS["bg"],
            background=COLORS["LOW"],
            thickness=22
        )
        self.water_bar = ttk.Progressbar(
            water_card, style="flood.Horizontal.TProgressbar",
            length=600, maximum=4095, mode="determinate"
        )
        self.water_bar.pack(fill="x", pady=(6, 2))

        self.water_val_label = tk.Label(
            water_card, text="0 / 4095",
            font=("Helvetica", 10),
            bg=COLORS["card"], fg=COLORS["subtext"]
        )
        self.water_val_label.pack(anchor="e")

        # ── Sensor cards (Rain / Temp / Humidity) ────────────────────
        info_row = tk.Frame(self.root, bg=COLORS["bg"])
        info_row.pack(fill="x", padx=20, pady=6)

        self.rain_box  = self._sensor_card(info_row, "Rain",     "No")
        self.temp_box  = self._sensor_card(info_row, "Temp",     "--°C")
        self.hum_box   = self._sensor_card(info_row, "Humidity", "--%")

        # ── Serial log ───────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg=COLORS["bg"])
        log_frame.pack(fill="both", expand=True, padx=20, pady=(4, 0))

        tk.Label(
            log_frame, text="Serial Log",
            font=("Helvetica", 10),
            bg=COLORS["bg"], fg=COLORS["subtext"]
        ).pack(anchor="w")

        self.log = scrolledtext.ScrolledText(
            log_frame, height=8,
            bg=COLORS["log_bg"], fg=COLORS["log_text"],
            font=("Courier", 9), state="disabled",
            relief="flat", bd=0
        )
        self.log.pack(fill="both", expand=True)

        # ── Status bar ───────────────────────────────────────────────
        self.status_label = tk.Label(
            self.root, text="Connecting...",
            font=("Helvetica", 9),
            bg=COLORS["bg"], fg=COLORS["subtext"]
        )
        self.status_label.pack(pady=6)

    def _sensor_card(self, parent, title, initial):
        frame = tk.Frame(parent, bg=COLORS["card"], padx=10, pady=10)
        frame.pack(side="left", expand=True, fill="both", padx=4)
        tk.Label(
            frame, text=title,
            font=("Helvetica", 10),
            bg=COLORS["card"], fg=COLORS["subtext"]
        ).pack()
        value_lbl = tk.Label(
            frame, text=initial,
            font=("Helvetica", 18, "bold"),
            bg=COLORS["card"], fg=COLORS["text"]
        )
        value_lbl.pack()
        return value_lbl

    # ------------------------------------------------------------------
    # Serial
    # ------------------------------------------------------------------
    def _connect_serial(self):
        try:
            self.serial_conn = serial.Serial(PORT, BAUD, timeout=1)
            self.running = True
            self.status_label.config(text=f"Connected  ·  {PORT}  ·  {BAUD} baud")
            threading.Thread(target=self._read_serial, daemon=True).start()
        except Exception as e:
            self.status_label.config(
                text=f"Connection failed: {e}",
                fg=COLORS["HIGH"]
            )

    def _read_serial(self):
        while self.running:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self.root.after(0, self._process_line, line)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Data parsing
    # ------------------------------------------------------------------
    def _process_line(self, line):
        self._log(line)

        if "Water level" in line:
            m = re.search(r":\s*(\d+)", line)
            if m:
                val = int(m.group(1))
                self.water_bar["value"] = val
                self.water_val_label.config(text=f"{val} / 4095")

        elif line.startswith("Rain"):
            m = re.search(r":\s*(\w+)", line)
            if m:
                rain = m.group(1) == "YES"
                self.rain_box.config(
                    text="YES" if rain else "No",
                    fg=COLORS["HIGH"] if rain else COLORS["text"]
                )

        elif "Temperature" in line:
            t = re.search(r"Temperature\s*:\s*(\d+)", line)
            h = re.search(r"Humidity:\s*(\d+)", line)
            if t:
                self.temp_box.config(text=f"{t.group(1)}°C")
            if h:
                self.hum_box.config(text=f"{h.group(1)}%")

        elif line.startswith("Risk"):
            m = re.search(r":\s*(\w+)", line)
            if m:
                risk = m.group(1)
                color = COLORS.get(risk, COLORS["LOW"])
                self.risk_label.config(text=f"RISK: {risk}", bg=color)
                style = ttk.Style()
                style.configure("flood.Horizontal.TProgressbar", background=color)

    def _log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def on_close(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.root.destroy()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FloodDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
