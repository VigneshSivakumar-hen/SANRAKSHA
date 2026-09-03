"""
Small wrapper around paho-mqtt so the simulator and gateway scripts don't
each reimplement connect/publish/subscribe boilerplate.

Topic convention: sanraksha/sensors/<location_id>
Payload: JSON — {"rainfall_mm_24h": float, "soil_moisture_pct": float,
                  "temperature_c": float, "ts": iso8601 string}
"""

import json
import logging

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttClient:
    def __init__(self, host: str, port: int = 1883, client_id: str = ""):
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    def connect(self):
        self.client.connect(self.host, self.port, keepalive=60)
        return self

    def publish(self, topic: str, payload: dict, qos: int = 1):
        self.client.publish(topic, json.dumps(payload), qos=qos)
        logger.info("Published to %s: %s", topic, payload)

    def subscribe(self, topic_filter: str, on_message):
        """on_message(topic: str, payload: dict) -> None"""

        def _on_connect(client, userdata, flags, reason_code, properties=None):
            logger.info("Connected to broker %s:%s (rc=%s)", self.host, self.port, reason_code)
            client.subscribe(topic_filter)
            logger.info("Subscribed to %s", topic_filter)

        def _on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                logger.warning("Dropping non-JSON message on %s", msg.topic)
                return
            on_message(msg.topic, payload)

        self.client.on_connect = _on_connect
        self.client.on_message = _on_message
        self.client.connect(self.host, self.port, keepalive=60)

    def loop_forever(self):
        self.client.loop_forever()

    def loop_start(self):
        self.client.loop_start()

    def disconnect(self):
        self.client.disconnect()
