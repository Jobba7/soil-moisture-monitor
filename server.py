import yaml
import time
import threading
import board
import busio
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from adafruit_seesaw.seesaw import Seesaw

# Flask-Anwendung mit WebSocket-Unterstützung initialisieren
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# I²C-Bus und Sensor initialisieren (Standardadresse 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)

# Standardwerte für Min-/Max-Feuchtigkeit (falls config.yml fehlt)
DEFAULT_MIN_MOISTURE = 200
DEFAULT_MAX_MOISTURE = 800


def load_config():
    """Lädt die Konfigurationswerte aus der Datei config.yml oder setzt Standardwerte."""
    try:
        with open("config.yml", "r") as file:
            config = yaml.safe_load(file)
            return config["sensor"].get("min_moisture", DEFAULT_MIN_MOISTURE), config["sensor"].get(
                "max_moisture", DEFAULT_MAX_MOISTURE
            )
    except (FileNotFoundError, KeyError):
        print("⚠️  Warnung: config.yml nicht gefunden oder fehlerhaft. Standardwerte werden verwendet.")
        return DEFAULT_MIN_MOISTURE, DEFAULT_MAX_MOISTURE


def save_config(min_moisture, max_moisture):
    """Speichert die aktuellen Min-/Max-Werte in der config.yml."""
    config_data = {"sensor": {"min_moisture": min_moisture, "max_moisture": max_moisture}}
    with open("config.yml", "w") as file:
        yaml.safe_dump(config_data, file)
    print(f"✅ Neue Werte gespeichert: min={min_moisture}, max={max_moisture}")


# Min-/Max-Werte aus der Config-Datei laden
MIN_MOISTURE, MAX_MOISTURE = load_config()


def normalize_moisture(value):
    """Skaliert den Feuchtigkeitswert auf eine Skala von 0-100%."""
    if value is None:
        return None
    return max(0, min(100, int((value - MIN_MOISTURE) / (MAX_MOISTURE - MIN_MOISTURE) * 100)))


def read_sensor():
    """Liest periodisch den Sensor aus, aktualisiert Min-/Max-Werte und sendet die Daten per WebSocket."""
    global MIN_MOISTURE, MAX_MOISTURE

    while True:
        try:
            raw_moisture = ss.moisture_read()
            moisture_percent = normalize_moisture(raw_moisture)

            # Prüfen, ob neuer Min-/Max-Wert auftritt
            updated = False
            if raw_moisture < MIN_MOISTURE:
                MIN_MOISTURE = raw_moisture
                updated = True
            if raw_moisture > MAX_MOISTURE:
                MAX_MOISTURE = raw_moisture
                updated = True

            # Falls sich die Min-/Max-Werte geändert haben, speichern
            if updated:
                save_config(MIN_MOISTURE, MAX_MOISTURE)

        except Exception:
            raw_moisture = None
            moisture_percent = None

        try:
            temperature = ss.get_temp()
        except Exception:
            temperature = None

        sensor_data = {
            "moisture_raw": raw_moisture,
            "moisture_percent": moisture_percent,
            "temperature": temperature,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "min_moisture": MIN_MOISTURE,
            "max_moisture": MAX_MOISTURE,
        }

        # Senden der aktuellen Sensordaten an alle verbundenen Clients
        socketio.emit("sensor_update", sensor_data)
        time.sleep(5)  # Alle 5 Sekunden aktualisieren


# Starte einen Hintergrundthread für das kontinuierliche Auslesen des Sensors
sensor_thread = threading.Thread(target=read_sensor, daemon=True)
sensor_thread.start()


@app.route("/")
def home():
    """Rendert die HTML-Seite mit WebSocket-Unterstützung."""
    html = """
    <html>
      <head>
        <title>Soil Sensor Data</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.js"></script>
        <script>
          var socket = io();
          socket.on('sensor_update', function(data) {
            document.getElementById('moisture').innerText = data.moisture_raw + " (" + data.moisture_percent + "%)";
            document.getElementById('temperature').innerText = data.temperature + " °C";
            document.getElementById('timestamp').innerText = data.timestamp;
            document.getElementById('min_moisture').innerText = data.min_moisture;
            document.getElementById('max_moisture').innerText = data.max_moisture;
          });
        </script>
      </head>
      <body>
        <h1>Soil Sensor Data (Live)</h1>
        <ul>
          <li>Feuchtigkeit: <span id="moisture">Laden...</span></li>
          <li>Temperatur: <span id="temperature">Laden...</span></li>
          <li>Messzeitpunkt: <span id="timestamp">Laden...</span></li>
          <li>Minimale Feuchtigkeit: <span id="min_moisture">Laden...</span></li>
          <li>Maximale Feuchtigkeit: <span id="max_moisture">Laden...</span></li>
        </ul>
      </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    # Flask-App mit WebSockets starten
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
