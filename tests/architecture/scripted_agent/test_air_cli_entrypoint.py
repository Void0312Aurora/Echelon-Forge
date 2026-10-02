from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PATH = REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "takeoff_to_landing.py"


def test_air_scripted_cli_uses_neutral_registry_model() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "python.tasking_contracts.air.execution.model" in source
    assert "AIR_SCRIPTED_MODEL_REGISTRY.create_for" in source
    assert "AIR_SCRIPTED_EXECUTION_MODEL_ID" in source
    assert "DecisionRuntimeAgent" in source
    assert "DecisionRuntimeAgentSpec" in source
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

    from python.tasking_contracts.common.scripted_capability import (
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

def test_air_scripted_cli_import_and_config_selection_without_rl_or_native() -> None:
    source = textwrap.dedent(
        """
        import builtins
        import contextlib
        import io
        import sys
        from python import runtime_bootstrap

        runtime_bootstrap.ensure_repo_imports = lambda: "."
        original_import = builtins.__import__

        def reject_training_import(name, *args, **kwargs):
            if name == "ef_py" or name == "python.rl" or name.startswith("python.rl."):
                raise AssertionError(f"CLI imported policy/native runtime eagerly: {name}")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = reject_training_import
        import tools.diagnostics.flight_trajectory.takeoff_to_landing as cli

        assert cli._optional_finite_float(float("nan")) is None
        assert cli._optional_finite_float(2.5) == 2.5
        called = {}

        def stop_before_simulation(**kwargs):
            called.update(kwargs)
            raise RuntimeError("stop-before-simulation")

        cli._make_env = stop_before_simulation
        sys.argv = ["air-cli", "--scenario", "scenario.json", "--scripted", "--output", "out.png"]
        try:
            cli.main()
        except RuntimeError as exc:
            assert str(exc) == "stop-before-simulation"
        else:
            raise AssertionError("scripted CLI did not reach the runtime constructor")
        assert called["scripted"] is True
        assert called["train_config"] is None

        sys.argv = ["air-cli", "--scenario", "scenario.json", "--model", "model.zip", "--output", "out.png"]
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                cli.main()
            except SystemExit as exc:
                assert exc.code == 2
            else:
                raise AssertionError("learned CLI accepted a missing training configuration")
        print("scripted-cli-import-and-args-ok")
        """
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(REPO_ROOT), env.get("PYTHONPATH", ""))))
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "scripted-cli-import-and-args-ok" in result.stdout
def test_air_cli_selects_declared_runway_length_for_scripted_controller() -> None:
    from types import SimpleNamespace

    from tools.diagnostics.flight_trajectory.takeoff_to_landing import _pick_runway_beacon

    loader = SimpleNamespace(
        scenario_data={
            "mission_command": {
                "post_waypoint_transition": {"recovery_runway_id": 2}
            }
        },
        post_waypoint_transition={},
        ils_beacons=[
            {"runway_id": 1, "name": "Runway 09", "cx": 0.0, "cy": 0.0, "length": 1800.0},
            {"runway_id": 2, "name": "Runway 27", "cx": 0.0, "cy": 0.0, "length": 3200.0},
        ],
    )
    selected = _pick_runway_beacon(loader, 0.0, 0.0)
    assert selected is not None
    assert selected["runway_id"] == 2
    assert selected["length"] == 3200.0


def test_air_cli_finite_json_normalizes_complete_nested_summary() -> None:
    from tools.diagnostics.flight_trajectory.takeoff_to_landing import _finite_json

    normalized = _finite_json(
        {
            "final_position_xyz_m": [np.float32(12.0), float("nan"), float("inf")],
            "world_yaw_deg": np.float64(-float("inf")),
            "mission_status": {"phase": "landing", "value": float("nan")},
            "nested": (1.0, np.float32(float("nan"))),
        }
    )

    assert normalized == {
        "final_position_xyz_m": [12.0, None, None],
        "world_yaw_deg": None,
        "mission_status": {"phase": "landing", "value": None},
        "nested": [1.0, None],
    }
    json.dumps(normalized, allow_nan=False)
