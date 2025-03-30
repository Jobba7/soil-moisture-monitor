import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from config_loader import save_config, config
from logger_config import logger

# Initialize I2C bus and sensor (default address 0x36)
i2c_bus = busio.I2C(board.SCL, board.SDA)
moisture_sensor = Seesaw(i2c_bus, addr=0x36)

# Load initial min/max values from config
MIN_MOISTURE = config["sensor"]["min_moisture"]
MAX_MOISTURE = config["sensor"]["max_moisture"]


def normalize_moisture(value):
    """Scales raw moisture value to a percentage (0-100%)."""
    if value is None:
        return None
    return max(0, min(100, int((value - MIN_MOISTURE) / (MAX_MOISTURE - MIN_MOISTURE) * 100)))


def read_sensor():
    """
    Takes 10 measurements to produce a more accurate reading.
    Averages the 10 values for both moisture and temperature.
    Updates the min/max configuration if new extremes are detected.
    Returns a sensor_data dictionary with averaged values.
    """
    global MIN_MOISTURE, MAX_MOISTURE

    moisture_values = []
    temperature_values = []

    # Take 10 measurements
    for _ in range(10):
        try:
            raw_moisture = moisture_sensor.moisture_read()
            moisture_values.append(raw_moisture)
        except Exception as e:
            logger.error(f"Moisture read failed: {e}")
        try:
            temp = moisture_sensor.get_temp()
            temperature_values.append(temp)
        except Exception as e:
            logger.error(f"Temperature read failed: {e}")
        time.sleep(0.1)  # Short delay between measurements

    # Compute averages if values were collected
    if moisture_values:
        avg_moisture = sum(moisture_values) / len(moisture_values)
        moisture_percent = normalize_moisture(avg_moisture)

        # Update min/max values if any measurement is out of bounds
        updated = False
        for value in moisture_values:
            if value < MIN_MOISTURE:
                MIN_MOISTURE = value
                updated = True
            if value > MAX_MOISTURE:
                MAX_MOISTURE = value
                updated = True
        if updated:
            save_config(MIN_MOISTURE, MAX_MOISTURE)
    else:
        avg_moisture = None
        moisture_percent = None

    # Average temperature if values were collected
    if temperature_values:
        avg_temperature = sum(temperature_values) / len(temperature_values)
    else:
        avg_temperature = None

    sensor_data = {
        "moisture_raw": avg_moisture,
        "moisture_percent": moisture_percent,
        "temperature": avg_temperature,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "min_moisture": MIN_MOISTURE,
        "max_moisture": MAX_MOISTURE,
    }

    logger.info(f"Sensor Read: moisture={avg_moisture} ({moisture_percent}%), temp={avg_temperature}°C")
    return sensor_data
