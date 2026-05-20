from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_SHIM = REPO_ROOT / "python" / "rl" / "runtime" / "agent_shim.py"
RUNTIME_FACADE_LAYERING = REPO_ROOT / "tests" / "architecture" / "test_runtime_facade_layering.py"


def test_wp12a_law14_read_side_allowlist_stays_focused() -> None:
    shim_source = AGENT_SHIM.read_text(encoding="utf-8")

    assert "LAW14_MAINTAINED_READ_LABEL_ALLOWLIST" in shim_source
    assert "OBS_FACADE_OBSERVATION_PACKET" in shim_source
    assert "OBS_DECISION_BELIEF_PACKET" in shim_source
    assert "OBS_AGENT_OBSERVATION_COMPAT" in shim_source
    assert "OBS_RAW_WORLD_TRUTH" in shim_source
    assert "OBS_DIAGNOSTICS_ORACLE" in shim_source
    assert (
        "maintained consumer fixtures may only use the Law 14 ObservationPacket/DecisionBelief read-side allowlist"
        in shim_source
    )
    assert "must not relabel privileged or raw surfaces as maintained" in shim_source


def test_wp12a_does_not_add_new_raw_runtime_escape_hatch() -> None:
    layering_source = RUNTIME_FACADE_LAYERING.read_text(encoding="utf-8")

    assert "SCOPED_ESCAPE_HATCH_ALLOWLIST" in layering_source
    assert "classification=\"diagnostics_only\"" in layering_source
    assert "classification=\"compatibility_only\"" in layering_source
