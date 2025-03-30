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
cd soil-moisture-monitor/website
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

1. **Service-Datei erstellen**

Erstelle die Datei `/etc/systemd/system/soil_moisture_monitor.service` mit folgendem Inhalt:
```ini
[Unit]
Description=Soil Moisture Monitor WebSocket Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/website
ExecStart=/home/pi/website/venv/bin/python /home/pi/website/server.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

2. **Systemd-Service aktivieren und starten**

Aktualisiere den Systemd-Daemon und aktiviere den Service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable soil_moisture_monitor
sudo systemctl start soil_moisture_monitor
```

Nun wird das Projekt automatisch im Hintergrund beim Booten gestartet.

3. **Überprüfen des Service-Status**
   Um sicherzustellen, dass der Service läuft, kannst du den Status mit folgendem Befehl überprüfen:
   ```bash
   sudo systemctl status soil_moisture_monitor
   ```

4. **Service stoppen**
   Falls du den Service anhalten möchtest, verwende:
   ```bash
   sudo systemctl stop soil_moisture_monitor
   ```

## Fehlerbehebung
Falls der Sensor nicht erkannt wird, überprüfe die I²C-Verbindung mit:
```bash
sudo i2cdetect -y 1
```
Falls die Adresse `0x36` nicht angezeigt wird, prüfe die Kabelverbindungen.
