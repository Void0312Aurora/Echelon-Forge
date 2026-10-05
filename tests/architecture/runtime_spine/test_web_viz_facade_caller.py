from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "examples" / "viz" / "web_viz" / "server.py"


def test_web_viz_uses_the_simulation_owned_air_scenario_surface() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    ast.parse(source, filename=str(SOURCE))
    assert "create_scenario_backend" in source
    assert "AirFacadeScenarioRuntime" in source
    assert "runtime.reset" in source
    assert "runtime.step" in source
    assert "runtime.close" in source
    assert "RuntimeFacade" not in source
    assert "BatchWorldSetupRequest" not in source
    assert "SimulationKernel" not in source
    assert "WorldBatchRuntime" not in source
