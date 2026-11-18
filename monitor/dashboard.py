"""Dashboard en Streamlit: estado en tiempo real de las máquinas de la planta.


Ejecutar: python -m streamlit run monitor/dashboard.py
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from monitor import config

# Limites de alarma fijos (reglas). En la fase 3 los sustituirá el modelo de ML.
LIMITS = {
    "temperature": {"max": 75.0, "unit": "°C"},
    "vibration": {"max": 3.0, "unit": "mm/s"},
    "power": {"max": 20.0, "unit": "kW"},
    "rpm": {"min": 1400.0, "unit": "rpm"}
}
SENSORS = list(LIMITS)


def load_readings(minutes: int) -> pd.DataFrame:
    """Lee de la base de datos las lecturas delos últimos 'minutes' minutos."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    query = """
    SELECT timestamp, line, machine_id, temperature, vibration, power, rpm 
    FROM readings
    WHERE timestamp >= ?
    ORDER BY id
    """
    with sqlite3.connect(config.DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=(since,))
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    return df


def check_alarms(reading: pd.Series) -> list[str]:
    """Devuelve la lista de sensores fuera de límites en una lectura."""
    alarms = []
    for sensor, limit in LIMITS.items():
        value = reading[sensor]
        if "max" in limit and value > limit["max"]:
            alarms.append(f"{sensor} alta: {value:.1f} {limit['unit']}")
        if "min" in limit and value < limit["min"]:
            alarms.append(f"{sensor} baja: {value:.1f} {limit['unit']}")
    return alarms


def show_machine_cards(latest: pd.DataFrame) -> None:
    """Una tarjeta por máquina con su estado y sus últimos valores."""
    columns = st.columns(len(latest))
    for column, (machine_id, reading) in zip(columns, latest.iterrows()):
        alarms = check_alarms(reading)
        with column.container(border=True):
            icon = "🔴" if alarms else "🟢"
            st.markdown(f"**{icon} {machine_id}**")
            st.caption(reading["line"])
            st.metric("Temperatura", f"{reading['temperature']:.1f} ºC")
            st.metric("Vibración", f"{reading['vibration']:.1f} mm/s")
            st.metric("Potencia", f"{reading['power']:.1f} kW")
            st.metric("RPM", f"{reading['rpm']:.0f} rpm")
            for alarm in alarms:
                st.error(alarm, icon="⚠️")


def show_history(df: pd.DataFrame) -> None:
    """Gráficas de evolución de los sensores de una máquina."""
    machine = st.selectbox("Máquina", sorted(df["machine_id"].unique()))
    history = df[df["machine_id"] == machine].set_index("timestamp")

    left, right = st.columns(2)
    for i, sensor in enumerate(SENSORS):
        column = left if i % 2 == 0 else right
        with column:
            st.markdown(f"**{sensor}** ({LIMITS[sensor]['unit']})")
            st.line_chart(history[sensor], height=200)


# ---------------------------------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------------------------------
st.set_page_config(page_title="Industrial Monitor", page_icon="🏭", layout="wide")
st.title("Industrial Monitor 🏭")

minutes = st.sidebar.slider("Minutos de historial", 1, 30, 5)

if not Path(config.DB_PATH).exists():
    st.warning(f"No hay datos todavía en {config.DB_PATH}. ¿Está funcionando el colector de datos?")
    st.stop()

@st.fragment(run_every=2)
def live_view() -> None:
    df = load_readings(minutes)
    if df.empty:
        st.info("Esperando lecturas...")
        return

    latest = df.groupby("machine_id").last()
    in_alarm = sum(bool(check_alarms(r)) for _, r in latest.iterrows())

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Máquinas", len(latest))
    kpi2.metric("En alarma", in_alarm)
    kpi3.metric("Lecturas en pantalla", len(df))

    st.subheader("Estado actual de las máquinas")
    show_machine_cards(latest)

    st.subheader("Historial")
    show_history(df)


live_view()
