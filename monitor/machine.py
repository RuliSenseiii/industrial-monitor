"""Simulated industrial machine.

Each machine produces sensor readings around a healthy baseline with some
Gaussian noise. From time to time it starts developing a fault: the
affected sensor drifts away from normal values, a little more every tick,
until the fault is "repaired" and the machine goes back to normal.

Each reading includes the fault that is active (or None). The anomaly
detector never uses this label to make decisions; it is the ground truth
we use later to measure how well the model works.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Healthy baseline: (mean, standard deviation) for each sensor
BASELINE = {
    "temperature": (65.0, 1.5),   # °C
    "vibration": (2.0, 0.2),      # mm/s RMS
    "power": (15.0, 0.8),         # kW
    "rpm": (1450.0, 10.0),        # revolutions per minute
}

# Fault type -> per-tick drift applied to each sensor while the fault grows
FAULTS = {
    "overheating": {"temperature": 0.6, "power": 0.05},
    "bearing_wear": {"vibration": 0.08, "temperature": 0.1, "rpm": -0.5},
    "overload": {"power": 0.4, "temperature": 0.2, "rpm": -2.0},
}

FAULT_DURATION = (30, 90)  # ticks a fault lasts before it is repaired


@dataclass
class Machine:
    machine_id: str
    line: str
    fault_probability: float = 0.01
    rng: random.Random = field(default_factory=random.Random)

    fault: str | None = None
    fault_age: int = 0
    fault_duration: int = 0

    def step(self) -> dict:
        """Advance one tick and return a new reading."""
        self._update_fault_state()

        reading = {
            "machine_id": self.machine_id,
            "line": self.line,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fault": self.fault,
        }
        for sensor, (mean, std) in BASELINE.items():
            value = self.rng.gauss(mean, std) + self._drift(sensor)
            reading[sensor] = round(value, 2)
        return reading

    def _update_fault_state(self) -> None:
        if self.fault is None:
            if self.rng.random() < self.fault_probability:
                self.fault = self.rng.choice(list(FAULTS))
                self.fault_age = 0
                self.fault_duration = self.rng.randint(*FAULT_DURATION)
        else:
            self.fault_age += 1
            if self.fault_age >= self.fault_duration:
                self.fault = None  # machine repaired
                self.fault_age = 0

    def _drift(self, sensor: str) -> float:
        """How far the sensor is from its baseline because of the active fault."""
        if self.fault is None:
            return 0.0
        return FAULTS[self.fault].get(sensor, 0.0) * self.fault_age
