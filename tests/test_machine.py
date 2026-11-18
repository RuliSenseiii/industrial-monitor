import random

from monitor.machine import BASELINE, Machine


def make_machine(prob: float, seed: int = 42) -> Machine:
    return Machine("test-01", "line1", fault_probability=prob, rng=random.Random(seed))


def test_healthy_machine_stays_near_baseline():
    m = make_machine(prob=0.0)
    for _ in range(200):
        r = m.step()
        assert r["fault"] is None
        for sensor, (mean, std) in BASELINE.items():
            assert abs(r[sensor] - mean) < 5 * std


def test_reading_has_all_fields():
    r = make_machine(prob=0.0).step()
    for key in ("machine_id", "line", "timestamp", "fault", *BASELINE):
        assert key in r


def test_fault_makes_sensor_drift_and_then_gets_repaired():
    m = make_machine(prob=1.0)  # starts a fault on the first tick
    m.step()
    assert m.fault is not None
    fault = m.fault

    readings = []
    while m.fault == fault:
        readings.append(m.step())

    # The last reading of the fault must be clearly away from the baseline
    # in at least one sensor
    last = readings[-2]
    drifted = any(abs(last[s] - mean) > 5 * std for s, (mean, std) in BASELINE.items())
    assert drifted
