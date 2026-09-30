"""Small no-RL Air facade demonstration runner."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import ef_py
import numpy as np

from python.tasking_contracts.air.execution import AirScriptedExecutionModel

from .action import build_pilot_action
from .director import AirDirectorInput, AirScriptedDirector
from ..facade_batch import EntityKey, FacadeBatchBackend


@dataclass(frozen=True)
class AirFacadeDemoTrace:
    """Stable, compact evidence emitted by one demo run."""

    entity_keys: tuple[EntityKey, ...]
    phases: tuple[tuple[str, ...], ...]
    steps: int
    initial_sim_time_s: tuple[float, ...]
    final_sim_time_s: tuple[float, ...]
    final_positions_m: tuple[tuple[float, float, float], ...]
    action_norms: tuple[tuple[float, ...], ...]


def build_demo_setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    """Build a small airborne two-ship setup using maintained native DTOs."""

    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    for name, y_m in (("ScriptedLead", 0.0), ("ScriptedWing", -120.0)):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = ef_py.Side.Blue
        spawn.type_name = "F-16C_Block50"
        spawn.entity_name = name
        spawn.x = 0.0
        spawn.y = y_m
        spawn.z = 1200.0
        spawn.heading = 90.0
        spawn.vx = 180.0
        spawns.append(spawn)
    request.spawn_requests = spawns
    return request


def run_facade_scripted_demo(
    *,
    database_path: str,
    seed: int = 17,
    steps: int = 20,
) -> AirFacadeDemoTrace:
    """Run the direct scripted Air loop and return replay-friendly evidence."""

    if int(steps) <= 0:
        raise ValueError("Air facade demo steps must be positive")
    backend = FacadeBatchBackend(
        database_path=str(database_path),
        setup_factory=build_demo_setup,
        world_count=1,
        controlled_spawn_indices=(0, 1),
    )
    director = AirScriptedDirector()
    models: dict[EntityKey, AirScriptedExecutionModel] = {}
    phase_history: dict[EntityKey, list[str]] = {}
    action_history: dict[EntityKey, list[float]] = {}
    try:
        backend.seed(seed)
        initial = backend.reset()
        initial_times = tuple(float(obs.sim_time) for obs in initial.observations)
        for key in initial.entity_keys:
            models[key] = AirScriptedExecutionModel(action_dim=17, dt=0.05)
            phase_history[key] = []
            action_history[key] = []

        current = initial
        for _ in range(int(steps)):
            decisions: dict[EntityKey, Any] = {}
            for index, key in enumerate(current.entity_keys):
                decision = director.decide(
                    AirDirectorInput(
                        entity_id=key[1],
                        sim_time_s=float(current.observations[index].sim_time),
                        observation=current.observations[index],
                        instruments=current.instruments[index],
                        mission_command=SimpleNamespace(
                            command_code=1,
                            cmd_heading_deg=90.0,
                            cmd_altitude_m=1200.0,
                            cmd_speed_mps=180.0,
                        ),
                        waypoint_count=3,
                        remaining_waypoints=3,
                        ils=(1.0, 0.0, 0.0, 9000.0),
                        task_name="TASK_CAP",
                    )
                )
                decisions[key] = decision
                phase_history[key].append(decision.phase_name)

            backend.submit_air_director_decisions(decisions)
            observations = backend.air_scripted_observations()
            actions: dict[EntityKey, Any] = {}
            for index, key in enumerate(current.entity_keys):
                raw_action = models[key].step(observations[index], phase_name=decisions[key].phase_name)
                action = np.asarray(raw_action, dtype=np.float32).reshape(-1)
                action_history[key].extend([float(np.linalg.norm(action)), float(np.max(np.abs(action)))])
                actions[key] = build_pilot_action(
                    action,
                    action_mode="full",
                    instrument_state=current.instruments[index],
                )
            current = backend.step(actions)

        final_times = tuple(float(obs.sim_time) for obs in current.observations)
        final_positions = tuple(
            tuple(round(float(getattr(obs, name)), 6) for name in ("x", "y", "z"))
            for obs in current.observations
        )
        return AirFacadeDemoTrace(
            entity_keys=tuple(current.entity_keys),
            phases=tuple(tuple(phase_history[key]) for key in current.entity_keys),
            steps=int(steps),
            initial_sim_time_s=initial_times,
            final_sim_time_s=final_times,
            final_positions_m=final_positions,
            action_norms=tuple(
                tuple(round(value, 6) for value in action_history[key])
                for key in current.entity_keys
            ),
        )
    finally:
        for model in models.values():
            model.close()
        backend.close()


__all__ = ["AirFacadeDemoTrace", "build_demo_setup", "run_facade_scripted_demo"]
