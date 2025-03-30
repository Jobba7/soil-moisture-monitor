import yaml
from logger_config import logger

CONFIG_FILE = "config.yml"


def load_config():
    """Loads configuration from config.yml."""
    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)
        logger.debug(f"Config loaded")
        return config


def save_config(min_moisture, max_moisture):
    """Saves updated min/max moisture values to config.yml."""
    config_data = {"sensor": {"min_moisture": min_moisture, "max_moisture": max_moisture}}
    with open(CONFIG_FILE, "w") as file:
        yaml.safe_dump(config_data, file)
    logger.info(f"New config saved: min_moisture={min_moisture}, max_moisture={max_moisture}")


config = load_config()
