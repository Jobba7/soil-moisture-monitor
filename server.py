import threading
import time
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from sensor import read_sensor
from logger_config import logger

# Flask application with WebSocket support
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


def update_data():
    """Continuously reads sensor values, updates min/max moisture if needed, and sends data via WebSocket."""
    while True:
        sensor_data = read_sensor()
        socketio.emit("sensor_update", sensor_data)
        time.sleep(5)  # Update every 5 seconds


@app.route("/")
def home():
    """Renders the HTML page with WebSocket support (German interface)."""
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
    logger.info("Starting Flask server...")
    # Start sensor reading in a background thread
    sensor_thread = threading.Thread(target=update_data, daemon=True)
    sensor_thread.start()

    # Start the Flask app with WebSockets
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
