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

# SQLite database file
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
    """
    Continuously reads sensor values, stores them in the database,
    and sends data via WebSocket.
    """
    while True:
        sensor_data = read_sensor()
        # Insert data into the database
        insert_sensor_data(sensor_data)
        # Emit data via WebSocket
        socketio.emit("sensor_update", sensor_data)
        time.sleep(5)  # Update every 5 seconds


@app.route("/")
def home():
    """
    Renders the HTML page with WebSocket support and a Chart.js graph.
    The page will display live sensor updates along with all data from the last 30 days.
    """
    html = """
    <html>
      <head>
        <title>Soil Sensor Data</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        <canvas id="moistureChart" width="800" height="400"></canvas>

        <script>
          window.onload = function () {
            var socket = io();
            var moistureData = [];
            var timeLabels = [];

            // Create chart with historical data (x-axis as category)
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
                    title: {
                      display: true,
                      text: 'Timestamp'
                    }
                  },
                  y: {
                    min: 0,
                    max: 100,
                    title: {
                      display: true,
                      text: 'Moisture (%)'
                    }
                  }
                }
              }
            });

            // Fetch historical data for the last 30 days
            fetch('/historical_data')
              .then(response => response.json())
              .then(data => {
                // Data arrays come sorted by timestamp ascending
                timeLabels.push(...data.timestamps);
                moistureData.push(...data.moisture_percent);
                chart.update();
              })
              .catch(error => console.error("Error fetching historical data:", error));

            // Listen for live sensor updates via WebSocket
            socket.on('sensor_update', function (data) {
              console.log('Received live update:', data);
              // Update HTML elements
              document.getElementById('moisture').innerText = data.moisture_raw + " (" + data.moisture_percent + "%)";
              document.getElementById('temperature').innerText = data.temperature + " °C";
              document.getElementById('timestamp').innerText = data.timestamp;
              document.getElementById('min_moisture').innerText = data.min_moisture;
              document.getElementById('max_moisture').innerText = data.max_moisture;

              // Append new data to the chart
              moistureData.push(data.moisture_percent);
              timeLabels.push(data.timestamp);

              // Optionally, remove old data outside the 30-day window
              // Here we simply keep the last 100 entries for performance.
              if (moistureData.length > 100) {
                moistureData.shift();
                timeLabels.shift();
              }
              chart.update();
            });
          };
        </script>
      </body>
    </html>
    """
    return render_template_string(html)


@app.route("/historical_data")
def historical_data():
    """
    Fetches all sensor data from the database from the last 30 days.
    Returns JSON containing arrays of timestamps and moisture_percent values.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Filter for entries from the last 30 days
    query = """
        SELECT timestamp, moisture_percent 
        FROM sensor_data 
        WHERE timestamp >= datetime('now', '-30 days')
        ORDER BY timestamp ASC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Separate the data into two arrays for the chart
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
