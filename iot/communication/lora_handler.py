"""
LoRa handler — reference stub.

For sensor nodes too far from WiFi to use MQTT directly (common in hilly,
low-connectivity terrain — exactly where landslide monitoring matters
most), the usual pattern is: sensor nodes talk LoRa to a LoRa-to-MQTT
bridge (e.g. a Raspberry Pi with a LoRa HAT running something like
ChirpStack, or a simple pyLoRa-based bridge script), which then republishes
onto the same local MQTT broker the gateway already subscribes to
(see ../gateway/gateway.py) — so no changes are needed downstream.

Not implemented here since it depends on your specific LoRa radio/module
(SX127x-based boards are common) and this sandbox has no LoRa hardware to
test against. This stub documents the intended shape so a real
implementation drops in without touching the rest of the pipeline.
"""

import json
import logging

logger = logging.getLogger(__name__)


class LoRaBridge:
    """Intended usage once implemented against real hardware:

        bridge = LoRaBridge(port="/dev/ttyUSB0", frequency=865e6)  # IN865 band
        bridge.on_packet(lambda location_id, payload: mqtt_client.publish(
            f"sanraksha/sensors/{location_id}", payload
        ))
        bridge.listen_forever()
    """

    def __init__(self, port: str, frequency: float):
        self.port = port
        self.frequency = frequency
        self._callback = None
        raise NotImplementedError(
            "Implement against your LoRa radio's library (e.g. pySX127x, RadioLib "
            "over serial). This stub only documents the intended interface."
        )

    def on_packet(self, callback):
        """callback(location_id: str, payload: dict) -> None"""
        self._callback = callback

    def listen_forever(self):
        raise NotImplementedError

    def _decode_packet(self, raw_bytes: bytes) -> tuple[str, dict]:
        """Expected on-air format: b"<location_id>|<json payload>" — keep
        packets small, LoRa payloads are typically capped around 51-222
        bytes depending on spreading factor."""
        location_id, _, json_part = raw_bytes.decode().partition("|")
        return location_id, json.loads(json_part)
