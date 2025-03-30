from flask import Flask, render_template_string
import time
import threading
import board
import busio
from adafruit_seesaw.seesaw import Seesaw

app = Flask(__name__)

# Globale Variable zum Speichern der Sensordaten
sensor_data = {"moisture": None, "temperature": None, "timestamp": None}

# I²C-Bus und Sensor initialisieren (Standardadresse 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)

def read_sensor():
    """Liest periodisch den Sensor aus und speichert die Werte in sensor_data."""
    while True:
        try:
            moisture = ss.moisture_read()
        except Exception as e:
            moisture = None

        try:
            # Liest die Temperatur (in °C), sofern unterstützt
            temperature = ss.get_temp()
        except Exception as e:
            temperature = None

        sensor_data["moisture"] = moisture
        sensor_data["temperature"] = temperature
        sensor_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(5)  # alle 5 Sekunden aktualisieren

# Starte einen Hintergrundthread, um den Sensor auszulesen
sensor_thread = threading.Thread(target=read_sensor, daemon=True)
sensor_thread.start()

@app.route('/')
def home():
    html = """
    <html>
      <head>
        <title>Soil Sensor Data</title>
      </head>
      <body>
        <h1>Soil Sensor Data</h1>
        <ul>
          <li>Feuchtigkeit: {{ moisture }}</li>
          <li>Temperatur: {{ temperature }}</li>
          <li>Messzeitpunkt: {{ timestamp }}</li>
        </ul>
      </body>
    </html>
    """
    return render_template_string(
        html,
        moisture=sensor_data["moisture"],
        temperature=sensor_data["temperature"],
        timestamp=sensor_data["timestamp"]
    )

if __name__ == "__main__":
    # Starte den Server auf Port 80, sodass er im Netzwerk unter der IP des Pi erreichbar ist
    app.run(host='0.0.0.0', port=5000, debug=True)
