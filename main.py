from machine import Pin, ADC, I2C  # type: ignore
import time
import ssd1306  # type: ignore
import dht  # type: ignore

# --- PIN DEFINITIONS ---
rain_analog  = ADC(Pin(15))   # AO → Pin 15
rain_analog.atten(ADC.ATTN_11DB)
rain_digital = Pin(14, Pin.IN)  # DO → Pin 14

water_sensor = ADC(Pin(2))
water_sensor.atten(ADC.ATTN_11DB)

buzzer  = Pin(21, Pin.OUT, value=0)  # init LOW = silent
led_yellow = Pin(45, Pin.OUT, value=0)  # MEDIUM → sarı LED
led_green  = Pin(40, Pin.OUT, value=0)  # LOW    → yeşil LED
led_high   = Pin(41, Pin.OUT, value=0)  # HIGH   → LED
dht_sen = dht.DHT11(Pin(4))

i2c  = I2C(0, sda=Pin(37), scl=Pin(36), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# --- AI DECISION ENGINE ---
def ai_decision(rain_val, rain_det, water_val):
    rain = (rain_det == 0) or (rain_val < 1000)
    # High risk: water level is high regardless of rain
    if water_val > 3000:
        return "HIGH"
    # Medium risk: water level is medium OR rain detected
    elif water_val > 550 or rain:
        return "MEDIUM"
    # Low risk: everything normal
    else:
        return "LOW"

# --- ACTUATORS ---
def act(risk, temp, hum, rain_det, rain_val):
    oled.fill(0)
    rain_detected = (rain_det == 0) or (rain_val < 1000)
    rain_str = "YES" if rain_detected else "No"

    if risk == "HIGH":
        buzzer.value(1)
        led_high.value(1)
        led_yellow.value(0)
        led_green.value(0)
        oled.text("!! FLOOD RISK !!", 0, 0)
    elif risk == "MEDIUM":
        buzzer.value(0)
        led_yellow.value(1)
        led_high.value(0)
        led_green.value(0)
        oled.text("** WARNING **", 12, 0)
    else:
        buzzer.value(0)
        led_green.value(1)
        led_yellow.value(0)
        led_high.value(0)
        oled.text("** ALL CLEAR **", 4, 0)

    oled.hline(0, 11, 128, 1)
    oled.text("Risk  : " + risk, 0, 14)
    oled.text("Rain  : " + rain_str, 0, 26)
    oled.text("Temp  : " + str(temp) + " C", 0, 38)
    oled.text("Humid : " + str(hum) + " %", 0, 50)
    oled.show()

# --- MAIN LOOP ---
print("Smart Flood & Rain Alert System starting...")

while True:
    # SENSE
    rain_val  = rain_analog.read()
    rain_det  = rain_digital.value()
    water_val = water_sensor.read()

    try:
        dht_sen.measure()
        temp = dht_sen.temperature()
        hum  = dht_sen.humidity()
    except:
        temp = 0
        hum  = 0

    # THINK
    risk = ai_decision(rain_val, rain_det, water_val)

    # ACT
    act(risk, temp, hum, rain_det, rain_val)

    # Log
    rain_status = "YES" if (rain_det == 0 or rain_val < 1000) else "No"
    print("Rain        :", rain_status)
    print("Water level :", water_val)
    print("Temperature :", temp, "C  Humidity:", hum, "%")
    print("Risk        :", risk)
    print("---")

    time.sleep(2)
