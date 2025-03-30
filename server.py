from flask import Flask, render_template_string
from flask_socketio import SocketIO
import time
import threading
import board
import busio
from adafruit_seesaw.seesaw import Seesaw

# Flask-Anwendung mit WebSocket-Unterstützung initialisieren
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# I²C-Bus und Sensor initialisieren (Standardadresse 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)


def read_sensor():
    """Liest periodisch den Sensor aus und sendet die Daten per WebSocket."""
    while True:
        try:
            moisture = ss.moisture_read()
        except Exception:
            moisture = None

        try:
            temperature = ss.get_temp()
        except Exception:
            temperature = None

        sensor_data = {
            "moisture": moisture,
            "temperature": temperature,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
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
            document.getElementById('moisture').innerText = data.moisture;
            document.getElementById('temperature').innerText = data.temperature;
            document.getElementById('timestamp').innerText = data.timestamp;
          });
        </script>
      </head>
      <body>
        <h1>Soil Sensor Data (Live)</h1>
        <ul>
          <li>Feuchtigkeit: <span id="moisture">Laden...</span></li>
          <li>Temperatur: <span id="temperature">Laden...</span></li>
          <li>Messzeitpunkt: <span id="timestamp">Laden...</span></li>
        </ul>
      </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    # Flask-App mit WebSockets starten
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
