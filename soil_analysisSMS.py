import serial
import time
import pandas as pd

# 1) Ask soil type
soil_type = input("Enter soil type (sand / loamy / clay): ").strip().lower()

# 2) Serial port - change to your port (e.g. COM3, COM6)
SERIAL_PORT = 'COM5'
BAUDRATE = 9600
TIMEOUT = 2

print(f"Opening serial port {SERIAL_PORT} ...")
arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT)
time.sleep(2)
print("Connected. Collecting 5 readings (5s interval)...\n")

# 3) Collect 5 readings from Arduino
data = []
samples_needed = 5
collected = 0

while collected < samples_needed:
    line = arduino.readline().decode('utf-8', errors='ignore').strip()
    if not line:
        time.sleep(0.5)
        continue

    # Expect CSV: soil,temperature,humidity
    parts = line.split(',')
    if len(parts) != 3:
        # not a CSV data line; skip
        # print("Skipping log:", line)
        continue

    try:
        soil = float(parts[0])
        temp = float(parts[1])
        hum = float(parts[2])
    except:
        # parsing failed, skip
        continue

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data.append({
        "Timestamp": timestamp,
        "Soil Moisture": soil,
        "Temperature": temp,
        "Humidity": hum
    })
    collected += 1
    print(f"Sample {collected}: Soil={soil}, Temp={temp} °C, Humidity={hum} %")
    # small wait buffer
    time.sleep(0.5)

# 4) Save readings to one Excel
df = pd.DataFrame(data)
readings_file = f"soil_readings_{soil_type}.xlsx"
df.to_excel(readings_file, index=False)
print(f"\nSaved readings -> {readings_file}")

# 5) Compute averages
avg_soil = df["Soil Moisture"].mean()
avg_temp = df["Temperature"].mean()
avg_hum = df["Humidity"].mean()

# 6) Crop suggestion logic (same as your code)
def suggest_crop(soil_type, moisture):
    if soil_type == "loamy":
        if 150 <= moisture <= 320:
            return "Millet (drought-resistant)"
        elif 321 <= moisture <= 380:
            return "Groundnut (moderate moisture)"
        elif 381 <= moisture <= 450:
            return "Watermelon (moist but not wet soil)"
        else:
            return "Moisture out of loamy soil ideal range (150–450)."
    elif soil_type == "sand":
        if 450 <= moisture <= 600:
            return "Barley (tolerates lower moisture levels)"
        elif 601 <= moisture <= 700:
            return "Wheat (requires moderate moisture)"
        elif 701 <= moisture <= 775:
            return "Maize (thrives in slightly wet sandy soil)"
        elif 776 <= moisture <= 800:
            return "Rice, Cotton (needs high moisture)"
        else:
            return "Moisture out of sandy soil ideal range (450-800)."
    elif soil_type == "clay":
        if 600 <= moisture <= 700:
            return "Paddy (high water requirement)"
        elif 701 <= moisture <= 800:
            return "Sugarcane (moderately high moisture)"
        elif 801 <= moisture <= 900:
            return "Jute (requires very high moisture)"
        else:
            return "Moisture out of clay soil ideal range (600–900)."
    else:
        return "Unknown soil type."

crop_suggestion = suggest_crop(soil_type, avg_soil)

def temp_adjustment_advice(temp, soil_type):
    if soil_type == "loamy" and temp < 25:
        return "Increase temperature slightly (use mulch or plastic cover)."
    elif soil_type == "sand" and temp > 32:
        return "Temperature high — provide shade or light irrigation."
    elif soil_type == "clay" and temp < 20:
        return "Temperature low — ensure sunlight exposure."
    else:
        return "Temperature suitable for your soil and crop type."

advice = temp_adjustment_advice(avg_temp, soil_type)

# 7) Create summary and save to separate Excel
summary = pd.DataFrame({
    "Parameter": [
        "Soil Type",
        "Average Soil Moisture",
        "Average Temperature",
        "Average Humidity",
        "Recommended Crop(s)",
        "Temperature Advice"
    ],
    "Value": [
        soil_type.capitalize(),
        f"{avg_soil:.2f}",
        f"{avg_temp:.2f} °C",
        f"{avg_hum:.2f} %",
        crop_suggestion,
        advice
    ]
})

summary_file = f"soil_suggestion_{soil_type}.xlsx"
summary.to_excel(summary_file, index=False)
print(f"Saved summary -> {summary_file}\n")

# 8) Print summary to console
print("--- Summary ---")
print(f"Avg Soil Moisture: {avg_soil:.2f}")
print(f"Avg Temperature: {avg_temp:.2f} °C")
print(f"Avg Humidity: {avg_hum:.2f} %")
print(f"Recommended Crop(s): {crop_suggestion}")
print(f"Temperature Advice: {advice}")

# 9) Build compact SMS text (single line)
sms_text = (
    f"Soil:{soil_type.capitalize()}, "
    f"Mois:{avg_soil:.1f}, "
    f"Temp:{avg_temp:.1f}C, "
    f"Hum:{avg_hum:.1f}%, "
    f"Crop:{crop_suggestion}, "
    f"Note:{advice}"
)

print("\nSending SMS to via Arduino...")
# Very important: prefix "SMS:" so Arduino recognizes it
arduino.write(("SMS:" + sms_text + "\n").encode("utf-8"))
time.sleep(2)   # give Arduino some time to read and send

arduino.close()
print("Done. SMS request sent to Arduino.")
