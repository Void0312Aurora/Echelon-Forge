from __future__ import annotations

import json
from pathlib import Path

import pytest



REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PATH = REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "takeoff_to_landing.py"


def test_air_scripted_cli_uses_neutral_registry_model() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "python.tasking_contracts.air_scripted_execution" in source
    assert "AIR_SCRIPTED_MODEL_REGISTRY.create_for" in source
    assert "AIR_SCRIPTED_EXECUTION_MODEL_ID" in source
    assert "ScriptedRuntimeAgent" in source
    assert "ScriptedRuntimeAgentSpec" in source
    assert "scripted_runtime_agent.step" in source
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
    assert "scripted_runtime_agent.close" in source


def test_air_scripted_cli_manifest_route_fails_closed_for_held_capability(tmp_path: Path) -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "scenario_path: str" in source
    assert "scenario_path=os.path.abspath(args.scenario)" in source
    assert 'getattr(sim_env, "scenario_path"' not in source
    assert 'runway_beacon.get("length"' in source

    from python.tasking_contracts.scripted_capability import (
        parse_scripted_capability,
        resolve_scripted_model_id,
    )

    scenario_path = tmp_path / "held_air.json"
    scenario_path.write_text(
        json.dumps(
            {
                "scripted_capability": {
                    "version": "scripted_capability.v1",
                    "domain": "air",
                    "label": "held",
                    "model_id": None,
                    "role_id": "autopilot_controller",
                    "lifecycle": "reset_decide_close",
                    "evidence_refs": ["test:held"],
                    "deferred_claims": ["runtime admission"],
                }
            }
        ),
        encoding="utf-8",
    )
    manifest = parse_scripted_capability(json.loads(scenario_path.read_text(encoding="utf-8")))
    with pytest.raises(ValueError, match="held"):
        resolve_scripted_model_id(
            manifest,
            expected_domain="air",
            expected_role_id="autopilot_controller",
        )
