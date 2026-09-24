from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PATH = REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "takeoff_to_landing.py"


def test_air_scripted_cli_uses_neutral_registry_model() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "python.tasking_contracts.air_scripted_execution" in source
    assert "AIR_SCRIPTED_MODEL_REGISTRY.create_for" in source
    assert "AIR_SCRIPTED_EXECUTION_MODEL_ID" in source
    assert "parse_scripted_capability" in source
    assert "resolve_scripted_model_id" in source
    assert "wrapper residual scale forced to zero" not in source
    assert "python.rl.control.scripted_" not in source


def test_air_scripted_cli_keeps_learned_wrapper_path_separate() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "if scripted:" in source
    assert "wrapper_class = None" in source
    assert "get_action_wrapper_spec(train_config or {})" in source
    assert "scripted_model.decide" in source
