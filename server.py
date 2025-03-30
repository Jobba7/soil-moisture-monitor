import threading
import time
import sqlite3
from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO
from sensor import read_sensor
from logger_config import logger

# Flask application with WebSocket support
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# SQLite database setup
DB_FILE = "sensor_data.db"


def create_db():
    """Creates the SQLite database and table if not already present."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moisture_raw INTEGER,
            moisture_percent INTEGER,
            temperature REAL,
            timestamp TEXT,
            min_moisture INTEGER,
            max_moisture INTEGER
        )
    """
    )
    conn.commit()
    conn.close()


def insert_sensor_data(sensor_data):
    """Inserts sensor data into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sensor_data (
            moisture_raw, moisture_percent, temperature, timestamp, min_moisture, max_moisture
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            sensor_data["moisture_raw"],
            sensor_data["moisture_percent"],
            sensor_data["temperature"],
            sensor_data["timestamp"],
            sensor_data["min_moisture"],
            sensor_data["max_moisture"],
        ),
    )
    conn.commit()
    conn.close()


def update_data():
    """Continuously reads sensor values, stores them in the database, and sends data via WebSocket."""
    while True:
        sensor_data = read_sensor()

        # Insert data into the database
        insert_sensor_data(sensor_data)

        # Send data via WebSocket
        socketio.emit("sensor_update", sensor_data)

        time.sleep(5)  # Update every 5 seconds


@app.route("/")
def home():
    """Renders the HTML page with WebSocket support and chart (German interface)."""
    html = """
    <html>
      <head>
        <title>Soil Sensor Data</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
          var socket = io();
          var moistureData = [];
          var timeLabels = [];

          // Function to update the chart with new data
          socket.on('sensor_update', function(data) {
            // Add new data to arrays
            moistureData.push(data.moisture_percent);
            timeLabels.push(data.timestamp);

            // Keep the last 50 entries for the graph
            if (moistureData.length > 50) {
              moistureData.shift();
              timeLabels.shift();
            }

            // Update the chart
            chart.update();
          });

          // Create chart
          var ctx = document.getElementById('moistureChart').getContext('2d');
          var chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: timeLabels,
              datasets: [{
                label: 'Moisture (%)',
                data: moistureData,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              scales: {
                x: {
                  type: 'linear',
                  position: 'bottom'
                },
                y: {
                  min: 0,
                  max: 100
                }
              }
            }
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
        <canvas id="moistureChart" width="400" height="200"></canvas>
      </body>
    </html>
    """
    return render_template_string(html)


@app.route("/historical_data")
def historical_data():
    """Fetches historical data from the database and sends it as JSON."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, moisture_percent FROM sensor_data ORDER BY id DESC LIMIT 50")
    data = cursor.fetchall()
    conn.close()

    # Prepare data for the chart
    timestamps = [entry[0] for entry in data]
    moisture_percent = [entry[1] for entry in data]

    return jsonify({"timestamps": timestamps, "moisture_percent": moisture_percent})


if __name__ == "__main__":
    # Initialize the database
    create_db()

    logger.info("Starting App...")

    # Start sensor reading in a background thread
    sensor_thread = threading.Thread(target=update_data, daemon=True)
    sensor_thread.start()

    # Start the Flask app with WebSockets
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
