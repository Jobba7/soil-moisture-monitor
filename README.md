# Soil Moisture Monitor

Dieses Projekt liest Sensordaten (Bodenfeuchtigkeit & Temperatur) von einem **Adafruit Seesaw**-Sensor über I²C aus und zeigt die Daten live auf einer Webseite mit **WebSockets** an.

- Gespeicherte Min/Max-Werte: Min=320, Max=820

## Voraussetzungen

- **Raspberry Pi** oder ein anderes Gerät mit I²C-Unterstützung
- **Python 3.7+**
- **I²C aktiviert** auf dem Raspberry Pi (`sudo raspi-config` → Interfacing Options → I2C → Enable)

## Installation & Einrichtung

### 1. Repository klonen
```bash
git clone https://github.com/Jobba7/soil-moisture-monitor.git
cd soil-moisture-monitor
```

### 2. Virtuelle Umgebung erstellen (empfohlen)
```bash
python -m venv venv
source venv/bin/activate  # Für Windows: venv\Scripts\activate
```

### 3. Abhängigkeiten installieren
Erstelle eine `requirements.txt`, falls sie nicht existiert:
```bash
pip freeze > requirements.txt
```
Dann installiere die Pakete:
```bash
pip install -r requirements.txt
```

### 4. Anwendung starten
```bash
python server.py
```

Die Anwendung läuft nun auf **http://<IP-Adresse>:5000** und zeigt die Sensordaten live an.

## Automatischer Start beim Booten
Falls das Programm automatisch beim Hochfahren gestartet werden soll, kann es als **Systemd-Service** eingerichtet werden.

Erstelle die Datei `/etc/systemd/system/flask_sensor.service` mit folgendem Inhalt:
```ini
[Unit]
Description=Flask WebSocket Sensor Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/flask-websocket-sensor
ExecStart=/home/pi/flask-websocket-sensor/venv/bin/python /home/pi/flask-websocket-sensor/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Dann aktiviere den Service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable flask_sensor
sudo systemctl start flask_sensor
```

## Fehlerbehebung
Falls der Sensor nicht erkannt wird, überprüfe die I²C-Verbindung mit:
```bash
sudo i2cdetect -y 1
```
Falls die Adresse `0x36` nicht angezeigt wird, prüfe die Kabelverbindungen.
