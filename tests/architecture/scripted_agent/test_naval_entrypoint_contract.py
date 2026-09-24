from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_PATH = REPO_ROOT / "tools" / "eval" / "naval_station_policy_eval.py"


def test_naval_station_entrypoint_resolves_declared_scripted_capability() -> None:
    source = EVAL_PATH.read_text(encoding="utf-8")
    assert "NAVAL_SCRIPTED_MODEL_REGISTRY.create_for" in source
    assert "_scripted_model_id_for_scenario" in source
    assert "parse_scripted_capability" in source
    assert "resolve_scripted_model_id" in source
    assert "ScriptedRuntimeAgent" in source
    assert "ScriptedRuntimeAgentSpec" in source
    assert "scripted_runtime_agent.step" in source
