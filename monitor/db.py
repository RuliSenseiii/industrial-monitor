"""SQLite storage for sensor readings."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    line        TEXT    NOT NULL,
    machine_id  TEXT    NOT NULL,
    temperature REAL,
    vibration   REAL,
    power       REAL,
    rpm         REAL,
    fault       TEXT
);
CREATE INDEX IF NOT EXISTS idx_machine_time ON readings (machine_id, timestamp);
"""

COLUMNS = ("timestamp", "line", "machine_id", "temperature", "vibration", "power", "rpm", "fault")


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")  # lets the dashboard read while we write
    conn.executescript(SCHEMA)
    return conn


def insert_reading(conn: sqlite3.Connection, reading: dict) -> None:
    placeholders = ", ".join("?" for _ in COLUMNS)
    conn.execute(
        f"INSERT INTO readings ({', '.join(COLUMNS)}) VALUES ({placeholders})",
        tuple(reading.get(c) for c in COLUMNS),
    )
    conn.commit()
