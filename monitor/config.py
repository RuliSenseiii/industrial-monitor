"""Central configuration, read from environment variables.

Every value has a sensible default so the project runs locally without
setting anything; Docker Compose overrides them (e.g. MQTT_HOST=mosquitto).
"""

import os

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Topic layout: factory/<line>/<machine_id>/telemetry
TOPIC_PREFIX = os.getenv("TOPIC_PREFIX", "factory")
TELEMETRY_TOPIC = f"{TOPIC_PREFIX}/+/+/telemetry"

DB_PATH = os.getenv("DB_PATH", "data/readings.db")

# Seconds between two readings of the same machine
INTERVAL = float(os.getenv("INTERVAL", "1.0"))

# Probability per tick that a healthy machine starts developing a fault
FAULT_PROBABILITY = float(os.getenv("FAULT_PROBABILITY", "0.01"))
