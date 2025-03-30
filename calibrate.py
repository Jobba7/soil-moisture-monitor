import board
import busio
from adafruit_seesaw.seesaw import Seesaw
import time

# I²C-Schnittstelle initialisieren
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)

# Variablen für Max/Min-Werte
min_moisture = float("inf")  # Sehr hoher Startwert
max_moisture = float("-inf")  # Sehr niedriger Startwert

print("Starte Messungen. Drücke STRG+C zum Beenden.")

try:
    while True:
        moisture = ss.moisture_read()
        print(f"Aktueller Wert: {moisture}")

        # Max und Min Werte aktualisieren
        if moisture < min_moisture:
            min_moisture = moisture
        if moisture > max_moisture:
            max_moisture = moisture

        print(f"Min: {min_moisture} | Max: {max_moisture}")

        time.sleep(2)
except KeyboardInterrupt:
    print("\nMessung beendet.")
    print(f"Gespeicherte Min/Max-Werte: Min={min_moisture}, Max={max_moisture}")
