import time
import board
from adafruit_seesaw.seesaw import Seesaw

# I2C-Bus initialisieren
i2c_bus = board.I2C()

# Sensor-Objekt erstellen (Standardadresse 0x36)
sensor = Seesaw(i2c_bus, addr=0x36)

while True:
    # Feuchtigkeitswert auslesen
    moisture = sensor.moisture_read()

    # Temperatur auslesen (optional, aber nicht sehr genau)
    temperature = sensor.get_temp()

    # Werte ausgeben
    print(f"Bodenfeuchte: {moisture}")
    print(f"Temperatur: {temperature:.2f} °C")
    
    time.sleep(2)  # 2 Sekunden warten
