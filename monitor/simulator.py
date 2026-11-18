"""Publishes the readings of a small simulated plant to an MQTT broker.

Run:  python -m monitor.simulator
"""

import json
import logging
import time

import paho.mqtt.client as mqtt

from monitor import config
from monitor.machine import Machine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [simulator] %(message)s")
log = logging.getLogger(__name__)

# The simulated plant: two production lines with a few machines each
PLANT = {
    "line1": ["press-01", "press-02", "cnc-01"],
    "line2": ["pump-01", "conveyor-01"],
}


def build_machines() -> list[Machine]:
    return [
        Machine(machine_id=m, line=line, fault_probability=config.FAULT_PROBABILITY)
        for line, machines in PLANT.items()
        for m in machines
    ]


def connect() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulator")
    while True:  # the broker may not be ready yet when running with Docker
        try:
            client.connect(config.MQTT_HOST, config.MQTT_PORT)
            break
        except OSError:
            log.info("Broker %s:%s not ready, retrying...", config.MQTT_HOST, config.MQTT_PORT)
            time.sleep(2)
    client.loop_start()
    log.info("Connected to %s:%s", config.MQTT_HOST, config.MQTT_PORT)
    return client


def main() -> None:
    machines = build_machines()
    client = connect()
    try:
        while True:
            for machine in machines:
                reading = machine.step()
                topic = f"{config.TOPIC_PREFIX}/{machine.line}/{machine.machine_id}/telemetry"
                client.publish(topic, json.dumps(reading), qos=1)
                if reading["fault"]:
                    log.info("%s -> %s (tick %d)", machine.machine_id, machine.fault, machine.fault_age)
            time.sleep(config.INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
