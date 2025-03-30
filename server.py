import yaml
import time
import threading
import board
import busio
from loguru import logger
from flask import Flask, render_template_string
from flask_socketio import SocketIO
from adafruit_seesaw.seesaw import Seesaw

# Flask application with WebSocket support
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize I²C bus and sensor (default address 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)

# Default min/max values (used if config.yml is missing)
DEFAULT_MIN_MOISTURE = 200
DEFAULT_MAX_MOISTURE = 800
CONFIG_FILE = "config.yml"

# Configure logging with loguru
logger.remove()
logger.add("sensor.log", rotation="1 MB", retention="7 days", level="INFO")


def load_config():
    """Loads sensor configuration (min/max moisture) from config.yml."""
    try:
        with open(CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)
            min_moisture = config["sensor"].get("min_moisture", DEFAULT_MIN_MOISTURE)
            max_moisture = config["sensor"].get("max_moisture", DEFAULT_MAX_MOISTURE)
            logger.info(f"Config loaded: min_moisture={min_moisture}, max_moisture={max_moisture}")
            return min_moisture, max_moisture
    except (FileNotFoundError, KeyError) as e:
        logger.warning(f"Could not load config.yml: {e}. Using default values.")
        return DEFAULT_MIN_MOISTURE, DEFAULT_MAX_MOISTURE


def save_config(min_moisture, max_moisture):
    """Saves updated min/max moisture values to config.yml."""
    config_data = {"sensor": {"min_moisture": min_moisture, "max_moisture": max_moisture}}
    with open(CONFIG_FILE, "w") as file:
        yaml.safe_dump(config_data, file)
    logger.info(f"New config saved: min_moisture={min_moisture}, max_moisture={max_moisture}")


# Load min/max values from config
MIN_MOISTURE, MAX_MOISTURE = load_config()


def normalize_moisture(value):
    """Scales raw moisture value to a percentage (0-100%)."""
    if value is None:
        return None
    return max(0, min(100, int((value - MIN_MOISTURE) / (MAX_MOISTURE - MIN_MOISTURE) * 100)))


def read_sensor():
    """Continuously reads sensor values, updates min/max moisture if needed, and sends data via WebSocket."""
    global MIN_MOISTURE, MAX_MOISTURE

    while True:
        try:
            raw_moisture = ss.moisture_read()
            moisture_percent = normalize_moisture(raw_moisture)

            # Update min/max values if new extremes are detected
            updated = False
            if raw_moisture < MIN_MOISTURE:
                MIN_MOISTURE = raw_moisture
                updated = True
            if raw_moisture > MAX_MOISTURE:
                MAX_MOISTURE = raw_moisture
                updated = True

            if updated:
                save_config(MIN_MOISTURE, MAX_MOISTURE)

            logger.info(f"Sensor Read: moisture={raw_moisture} ({moisture_percent}%), temp={ss.get_temp()}°C")

        except Exception as e:
            logger.error(f"Sensor read failed: {e}")
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

        # Send data to WebSocket clients
        socketio.emit("sensor_update", sensor_data)
        time.sleep(5)  # Update every 5 seconds


# Start sensor reading in a background thread
sensor_thread = threading.Thread(target=read_sensor, daemon=True)
sensor_thread.start()


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
    # Start the Flask app with WebSockets
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
