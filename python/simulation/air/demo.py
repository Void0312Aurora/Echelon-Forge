"""Small no-RL Air facade demonstration runner."""

from __future__ import annotations

from .. import create_scenario_backend
from python.runtime_bootstrap import resolve_repo_path
from .scenario_runtime import AirFacadeScenarioRun, AirFacadeScenarioRuntime

AirFacadeDemoTrace = AirFacadeScenarioRun
DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json"
)


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
        scenario_path=DEFAULT_SCENARIO,
    )
    runtime = AirFacadeScenarioRuntime(backend)
    try:
        return runtime.run(seed=int(seed), steps=int(steps))
    finally:
        runtime.close()


__all__ = ["AirFacadeDemoTrace", "run_facade_scripted_demo"]
