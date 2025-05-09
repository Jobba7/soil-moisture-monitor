import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

DB_FILE = "sensor_data.db"


# Daten aus der DB laden
def load_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT moisture_percent, temperature, timestamp FROM sensor_data ORDER BY timestamp")
    data = cursor.fetchall()
    conn.close()
    return data


# Daten vorbereiten
def prepare_data(data):
    moisture = []
    temperature = []
    timestamps = []

    for row in data:
        m, t, ts = row
        try:
            dt = datetime.fromisoformat(ts)
            timestamps.append(dt)
            moisture.append(m)
            temperature.append(t)
        except ValueError:
            print(f"Ungültiges Datum: {ts}")

    return timestamps, moisture, temperature


# Daten plotten
def plot_data(timestamps, moisture, temperature):
    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(timestamps, moisture, label="Feuchtigkeit (%)", color="blue")
    plt.ylabel("Feuchtigkeit (%)")
    plt.grid(True)
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(timestamps, temperature, label="Temperatur (°C)", color="red")
    plt.xlabel("Zeit")
    plt.ylabel("Temperatur (°C)")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()


# Hauptfunktion
if __name__ == "__main__":
    data = load_data()
    timestamps, moisture, temperature = prepare_data(data)
    plot_data(timestamps, moisture, temperature)
