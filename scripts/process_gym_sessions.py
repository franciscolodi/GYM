#!/usr/bin/env python3
"""
process_gym_sessions.py

Lee todos los archivos JSON en gym_events/ (generados por los Atajos de
iPhone al llegar/salir del gimnasio), los empareja en sesiones
(entrada -> salida) y regenera data/gym_sessions.csv.

Formato esperado de cada evento (gym_events/AAAA-MM-DD_HHMMSS_tipo.json):
{
    "type": "entry" | "exit",
    "timestamp": "2026-09-11T09:15:32"
}

El nombre del archivo es solo para que sea legible/ordenable; el contenido
del JSON es la fuente de verdad.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = ROOT / "gym_events"
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "gym_sessions.csv"

CSV_HEADERS = [
    "date",
    "entry_time",
    "exit_time",
    "duration_minutes",
    "status",
]


def load_events():
    """Lee y parsea todos los .json de gym_events/, ordenados por timestamp."""
    events = []
    if not EVENTS_DIR.exists():
        return events

    for path in sorted(EVENTS_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            event_type = data.get("type")
            ts_raw = data.get("timestamp")
            if event_type not in ("entry", "exit") or not ts_raw:
                print(f"⚠️  Saltando {path.name}: falta 'type' o 'timestamp' válido")
                continue
            ts = datetime.fromisoformat(ts_raw)
            events.append({"type": event_type, "timestamp": ts, "file": path.name})
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️  Error leyendo {path.name}: {e}")
            continue

    events.sort(key=lambda e: e["timestamp"])
    return events


def pair_sessions(events):
    """Empareja eventos entry/exit consecutivos en sesiones."""
    sessions = []
    pending_entry = None

    for ev in events:
        if ev["type"] == "entry":
            if pending_entry is not None:
                # Había una entrada sin salida registrada: se cierra como abierta
                sessions.append(
                    {
                        "date": pending_entry["timestamp"].date().isoformat(),
                        "entry_time": pending_entry["timestamp"].strftime("%H:%M:%S"),
                        "exit_time": "",
                        "duration_minutes": "",
                        "status": "sin_salida",
                    }
                )
            pending_entry = ev
        elif ev["type"] == "exit":
            if pending_entry is None:
                # Salida sin entrada previa registrada
                sessions.append(
                    {
                        "date": ev["timestamp"].date().isoformat(),
                        "entry_time": "",
                        "exit_time": ev["timestamp"].strftime("%H:%M:%S"),
                        "duration_minutes": "",
                        "status": "sin_entrada",
                    }
                )
                continue
            duration = (ev["timestamp"] - pending_entry["timestamp"]).total_seconds() / 60
            sessions.append(
                {
                    "date": pending_entry["timestamp"].date().isoformat(),
                    "entry_time": pending_entry["timestamp"].strftime("%H:%M:%S"),
                    "exit_time": ev["timestamp"].strftime("%H:%M:%S"),
                    "duration_minutes": round(duration, 1),
                    "status": "completa",
                }
            )
            pending_entry = None

    if pending_entry is not None:
        sessions.append(
            {
                "date": pending_entry["timestamp"].date().isoformat(),
                "entry_time": pending_entry["timestamp"].strftime("%H:%M:%S"),
                "exit_time": "",
                "duration_minutes": "",
                "status": "en_curso",
            }
        )

    return sessions


def write_csv(sessions):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in sessions:
            writer.writerow(row)


def main():
    events = load_events()
    print(f"📂 {len(events)} evento(s) encontrados en gym_events/")
    sessions = pair_sessions(events)
    write_csv(sessions)
    print(f"✅ {len(sessions)} sesión(es) escritas en {CSV_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
