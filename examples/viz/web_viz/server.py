"""Minimal web visualizer backed by the simulation-owned Air scenario path."""

from __future__ import annotations

import json
from threading import Event

from flask import Flask, render_template
from flask_socketio import SocketIO

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.simulation import create_scenario_backend
from python.simulation.air import AirFacadeScenarioRuntime


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

SCENARIO_PATH = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json"
)
DATABASE_PATH = resolve_repo_path("examples", "config", "database")
with open(SCENARIO_PATH, "r", encoding="utf-8") as handle:
    SCENARIO_DATA = json.load(handle)
ENVIRONMENT = SCENARIO_DATA.get("environment", {}) if isinstance(SCENARIO_DATA, dict) else {}
MAX_STEPS = int(ENVIRONMENT.get("max_steps", 800) or 800) if isinstance(ENVIRONMENT, dict) else 800

stop_event = Event()


def _state_payload(result) -> dict:
    entities = SCENARIO_DATA.get("entities", []) if isinstance(SCENARIO_DATA, dict) else []
    units = []
    for index, observation in enumerate(result.snapshot.observations):
        config = entities[index] if index < len(entities) and isinstance(entities[index], dict) else {}
        side = str(config.get("side") or "Unknown")
        units.append(
            {
                "id": index + 1,
                "name": str(config.get("name") or f"air:slot:{index}"),
                "side": side,
                "type": "Aircraft",
                "platform_type": str(config.get("type") or "Aircraft"),
                "x": float(observation.x),
                "y": float(observation.y),
                "z": float(observation.z),
                "heading": float(getattr(observation, "heading", 0.0)),
                "speed": float(getattr(observation, "speed", 0.0)),
                "ias": float(getattr(observation, "speed", 0.0)),
                "hp": float(getattr(observation, "health", 100.0)),
                "max_hp": 100.0,
                "active": True,
                "is_active": True,
            }
        )
    return {
        "contract_version": "examples.viz.state_frame.v1",
        "tick": float(result.frame.sim_time_s[0]) if result.frame.sim_time_s else float(result.step_index),
        "units": units,
        "mission_status": None,
        "tactical": {"sensor_rings": [], "datalinks": [], "tracks": [], "nav": [], "weapons": []},
        "simulation": {
            "provider": "facade_batch",
            "step": int(result.step_index),
            "replay_identities": list(result.replay_identities),
        },
    }


def simulation_loop() -> None:
    """Own the scenario runtime for one bounded visualizer lifecycle."""

    runtime = None
    try:
        backend = create_scenario_backend(
            backend_id="facade_batch",
            database_path=DATABASE_PATH,
            scenario_path=SCENARIO_PATH,
        )
        runtime = AirFacadeScenarioRuntime(backend)
        runtime.reset(42)
        for _ in range(MAX_STEPS):
            if stop_event.is_set():
                break
            result = runtime.step()
            socketio.emit("state_update", _state_payload(result))
            socketio.sleep(0.1)
    finally:
        if runtime is not None:
            runtime.close()


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    socketio.start_background_task(simulation_loop)
    print("Starting Web Server on port 5000...")
    try:
        socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
    finally:
        stop_event.set()
