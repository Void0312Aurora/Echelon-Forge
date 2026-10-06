"""Small no-RL Air facade demonstration runner."""

from __future__ import annotations

import ef_py
from .. import create_scenario_backend
from .scenario_runtime import AirFacadeScenarioRun, AirFacadeScenarioRuntime

AirFacadeDemoTrace = AirFacadeScenarioRun


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
    """Run the simulation-owned scripted Air scenario runtime."""

    if int(steps) <= 0:
        raise ValueError("Air facade demo steps must be positive")
    backend = create_scenario_backend(
        backend_id="facade_batch",
        database_path=str(database_path),
        setup_factory=build_demo_setup,
        world_count=1,
        controlled_spawn_indices=(0, 1),
    )
    runtime = AirFacadeScenarioRuntime(backend)
    try:
        return runtime.run(seed=int(seed), steps=int(steps))
    finally:
        runtime.close()


__all__ = ["AirFacadeDemoTrace", "build_demo_setup", "run_facade_scripted_demo"]
