from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "examples" / "viz" / "web_viz" / "server.py"


def test_web_viz_uses_the_maintained_facade_batch_surface() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    ast.parse(source, filename=str(SOURCE))
    assert "RuntimeFacade" in source
    assert "BatchWorldSetupRequest" in source
    assert "facade.apply_world_setup" in source
    assert "facade.step_batch" in source
    assert "get_agent_observations_batch" in source
    assert "SimulationKernel" not in source
    assert "WorldBatchRuntime" not in source
