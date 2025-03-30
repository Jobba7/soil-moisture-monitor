import time
import threading
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from config_loader import save_config, config
from logger_config import logger

# Initialize I2C bus and sensor (default address 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
moisture_sensor = Seesaw(i2c_bus, addr=0x36)

MIN_MOISTURE = config["sensor"]["min_moisture"]
MAX_MOISTURE = config["sensor"]["max_moisture"]


def normalize_moisture(value):
    """Scales raw moisture value to a percentage (0-100%)."""
    if value is None:
        return None
    return max(0, min(100, int((value - MIN_MOISTURE) / (MAX_MOISTURE - MIN_MOISTURE) * 100)))


def read_sensor():
    """Continuously reads sensor values, updates min/max moisture if needed, and sends data via WebSocket."""
    global MIN_MOISTURE, MAX_MOISTURE

    try:
        raw_moisture = moisture_sensor.moisture_read()
        moisture_percent = normalize_moisture(raw_moisture)

        logger.info(f"Sensor Read: moisture={raw_moisture} ({moisture_percent}%), temp={moisture_sensor.get_temp()}°C")

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

    except Exception as e:
        logger.error(f"Sensor read failed: {e}")
        raw_moisture = None
        moisture_percent = None

    try:
        temperature = moisture_sensor.get_temp()
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

    return sensor_data
