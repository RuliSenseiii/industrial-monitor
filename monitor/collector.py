"""Subscribes to every machine's telemetry topic and stores the readings in SQLite.

Run:  python -m monitor.collector
"""

import json
import logging
import time

import paho.mqtt.client as mqtt

from monitor import config, db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [collector] %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    conn = db.connect(config.DB_PATH)
    stored = 0

    def on_connect(client, userdata, flags, reason_code, properties):
        log.info("Connected (%s), subscribing to %s", reason_code, config.TELEMETRY_TOPIC)
        client.subscribe(config.TELEMETRY_TOPIC, qos=1)

    def on_message(client, userdata, msg):
        nonlocal stored
        try:
            reading = json.loads(msg.payload)
        except json.JSONDecodeError:
            log.warning("Invalid message on %s, ignored", msg.topic)
            return
        db.insert_reading(conn, reading)
        stored += 1
        if stored % 100 == 0:
            log.info("%d readings stored", stored)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="collector")
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(config.MQTT_HOST, config.MQTT_PORT)
            break
        except OSError:
            log.info("Broker not ready, retrying...")
            time.sleep(2)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()


if __name__ == "__main__":
    main()
