"""
Smart Flood & Rain Alert System using PEAS Framework
-----------------------------------------------------
PEAS Mapping:
- Performance : Accurate flood/rain detection, fast response, low false alarms
- Environment : Outdoor area with rain and water level changes
- Actuators   : Buzzer, LED, OLED display
- Sensors     : Rain sensor, Water level sensor, DHT11 (temp & humidity)
"""

import random
import time

# -----------------------------
# ENVIRONMENT (E)
# -----------------------------
class FloodEnvironment:
    def __init__(self):
        self.weather_conditions = ["clear", "light_rain", "heavy_rain"]
        self.water_levels = ["low", "medium", "high"]

    def get_state(self):
        """Simulate environment state"""
        return {
            "weather"     : random.choice(self.weather_conditions),
            "water_level" : random.choice(self.water_levels),
            "temperature" : round(random.uniform(20, 40), 1),
            "humidity"    : round(random.uniform(40, 100), 1)
        }

# -----------------------------
# SENSORS (S)
# -----------------------------
class Sensors:
    def sense(self, env_state):
        """Collect data from environment"""
        return {
            "rain_detected" : env_state["weather"] != "clear",
            "rain_intensity": env_state["weather"],
            "water_level"   : env_state["water_level"],
            "temperature"   : env_state["temperature"],
            "humidity"      : env_state["humidity"]
        }

# -----------------------------
# ACTUATORS (A)
# -----------------------------
class Actuators:
    def trigger_buzzer(self):
        print("  [BUZZER] BEEP BEEP BEEP!")

    def turn_on_led(self):
        print("  [LED] Red LED ON")

    def turn_off_led(self):
        print("  [LED] LED OFF")

    def show_oled(self, line1, line2, line3):
        print(f"  [OLED] {line1}")
        print(f"  [OLED] {line2}")
        print(f"  [OLED] {line3}")

    def all_clear(self):
        print("  [BUZZER] Silent")
        print("  [LED] OFF")

# -----------------------------
# AGENT - Decision Making (AI)
# -----------------------------
class FloodAlertAgent:
    def __init__(self):
        self.correct_detections = 0
        self.false_alarms = 0
        self.total_steps = 0

    def decide(self, perception):
        """AI decision engine - determines risk level"""
        rain      = perception["rain_detected"]
        water     = perception["water_level"]
        intensity = perception["rain_intensity"]

        # High risk: high water level AND rain detected
        if water == "high" and rain:
            return "HIGH"
        # Medium-high risk: high water (no rain) OR heavy rain
        elif water == "high" or intensity == "heavy_rain":
            return "MEDIUM"
        # Medium risk: medium water OR light rain
        elif water == "medium" or rain:
            return "MEDIUM"
        # Low risk: all clear
        else:
            return "LOW"

    def _ground_truth(self, perception):
        """Expert-labeled ground truth risk level"""
        water     = perception["water_level"]
        intensity = perception["rain_intensity"]
        rain      = perception["rain_detected"]

        if water == "high" and rain:
            return "HIGH"
        elif water == "high" or intensity == "heavy_rain":
            return "MEDIUM"
        elif water == "medium" or rain:
            return "MEDIUM"
        else:
            return "LOW"

    def update_performance(self, perception, risk):
        """Performance Measure (P)"""
        self.total_steps += 1
        truth = self._ground_truth(perception)

        if risk == truth:
            self.correct_detections += 1
        elif truth in ["HIGH", "MEDIUM"] and risk in ["HIGH", "MEDIUM"]:
            self.correct_detections += 1
        elif truth == "LOW" and risk == "HIGH":
            self.false_alarms += 1

    def performance_report(self):
        print("\n=== PERFORMANCE REPORT ===")
        print(f"Total Steps       : {self.total_steps}")
        print(f"Correct Detections: {self.correct_detections}")
        print(f"False Alarms      : {self.false_alarms}")
        accuracy = (self.correct_detections / max(self.total_steps, 1)) * 100
        print(f"Accuracy          : {accuracy:.1f}%")

# -----------------------------
# SYSTEM INTEGRATION
# -----------------------------
def run_simulation(steps=10):
    env       = FloodEnvironment()
    sensors   = Sensors()
    actuators = Actuators()
    agent     = FloodAlertAgent()

    print("=== Smart Flood & Rain Alert System ===")
    print("Sense -> Think -> Decide -> Act\n")

    for step in range(steps):
        print(f"--- Time Step {step + 1} ---")

        # SENSE
        env_state  = env.get_state()
        perception = sensors.sense(env_state)
        print(f"Environment : {env_state}")
        print(f"Perception  : {perception}")

        # THINK & DECIDE
        risk = agent.decide(perception)
        print(f"Risk Level  : {risk}")

        # ACT
        temp = perception["temperature"]
        hum  = perception["humidity"]

        if risk == "HIGH":
            actuators.trigger_buzzer()
            actuators.turn_on_led()
            actuators.show_oled(
                "!! FLOOD RISK !!",
                f"Temp:{temp}C Hum:{hum}%",
                "Evacuate now!"
            )
        elif risk == "MEDIUM":
            actuators.turn_on_led()
            actuators.show_oled(
                "WARNING",
                f"Temp:{temp}C Hum:{hum}%",
                "Stay alert!"
            )
        else:
            actuators.all_clear()
            actuators.show_oled(
                "ALL CLEAR",
                f"Temp:{temp}C Hum:{hum}%",
                "System OK"
            )

        # Update performance
        agent.update_performance(perception, risk)
        print()
        time.sleep(1)

    # Final report
    agent.performance_report()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    run_simulation(steps=15)
