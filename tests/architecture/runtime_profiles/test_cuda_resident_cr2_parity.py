from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_parity_compare as parity


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_parity_release_contract.h"
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_full_window_probe.cpp"
COMPARATOR = ROOT / "tools/diagnostics/cuda_resident_cr2_parity_compare.py"


def _synthetic_payload(monkeypatch: pytest.MonkeyPatch) -> tuple[dict, dict]:
    signature = "synthetic-cr2-fixed-air-trace"
    digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    monkeypatch.setattr(parity, "TRACE_SIGNATURE_SHA256", digest)
    monkeypatch.setitem(parity.POLICY, "trace_signature_sha256", digest)

    def session(lane: str, backend_id: str, ids: tuple[int, int], delta: float) -> dict:
        frames = []
        for window in range(2):
            worlds = []
            for world_slot, entity_id in enumerate(ids):
                observations = {}
                for path, *_ in parity.FIELD_RULES:
                    owner, field = path.split(".", 1)
                    if owner == "agent_observations":
                        baseline = {
                            "sim_time": 0.01 * (window + 1),
                            "x": 1000.0 + 10.0 * world_slot,
                            "y": 0.0,
                            "z": 1500.0,
                            "vx": 200.0 + world_slot,
                            "vy": 0.0,
                            "vz": 0.0,
                            "heading": 90.0,
                            "roll": 0.0,
                            "speed": 200.0 + world_slot,
                            "gear_state": 0.0,
                        }[field]
                        observations[field] = baseline + (delta if field in {"x", "vx"} else 0.0)
                worlds.append(
                    {
                        "world_slot": world_slot,
                        "released": {
                            "agent_observations": observations,
                            "instrument_states": {"throttle_pos": 0.65 + 0.01 * world_slot},
                        },
                        "diagnostic_identity": {"agent_observations": {"id": entity_id}},
                    }
                )
            frames.append(
                {
                    "window_index": window,
                    "request_id": f"cr2.window.{window}",
                    "source_barrier": "window_commit",
                    "capture_barrier": "export",
                    "worlds": worlds,
                }
            )
        return {
            "session_index": 0,
            "session_label": "first",
            "lane": lane,
            "backend_id": backend_id,
            "trace_signature": signature,
            "completed": True,
            "failure": None,
            "operations": parity._expected_operations(),
            "frames": frames,
        }

    def make(lane: str, backend_id: str, ids: tuple[int, int], delta: float) -> dict:
        first = session(lane, backend_id, ids, delta)
        reset = deepcopy(first)
        reset["session_index"] = 1
        reset["session_label"] = "same_backend_reset"
        for frame in reset["frames"]:
            for world in frame["worlds"]:
                world["diagnostic_identity"]["agent_observations"]["id"] += 10_000
        release = deepcopy(parity.POLICY)
        release.update(
            {
                "released_numeric_fields": [
                    {
                        "path": path,
                        "absolute_tolerance": absolute,
                        "relative_tolerance": relative,
                        "comparator": comparator,
                        "finite_required": True,
                        "normalize_signed_zero": True,
                    }
                    for path, absolute, relative, comparator in parity.FIELD_RULES
                ],
                "identity_diagnostic_fields": list(parity.IDENTITY_FIELDS),
                "excluded_fields": [
                    {"path": path, "reason": reason} for path, reason in parity.EXCLUDED_FIELDS
                ],
                "declared_barriers": list(parity.BARRIERS),
                "sessions": [first, reset],
            }
        )
        return {
            "schema_version": "cuda_resident.full_window_probe.v1",
            "surface_id": "cuda_resident.full_window_spi.v1",
            "lane": lane,
            "backend_id": backend_id,
            "trace_signature": signature,
            "completed": True,
            "failure": None,
            "operations": parity._expected_operations(),
            "parity_release": release,
        }

    return (
        make("cpu_reference", "flecs_cpu_reference", (11, 22), 0.0),
        make("cuda_resident", "cuda_resident.rb7_phase_d", (101, 202), 1.0e-4),
    )


def test_cr2_parity_contract_has_explicit_disjoint_partition_and_size() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "kReleasedNumericFields" in text
    assert "kIdentityDiagnosticFields" in text
    assert "kExcludedFields" in text
    assert "partition_is_complete" in text
    assert "static_assert(partition_is_complete()" in text
    assert "kTraceProfileId" in text
    assert "kTraceSignatureSha256" in text
    assert len(text.splitlines()) < 600


def test_cr2_parity_probe_projects_only_release_whitelist() -> None:
    text = PROBE.read_text(encoding="utf-8")
    assert "diagnostic_identity" in text
    assert '"world_slot"' in text
    assert '"released"' in text
    assert (
        '"pitch"'
        not in text[text.index("released_world_json") : text.index("released_frames_json")]
    )
    assert "kPayloadCapturePath" in text
    assert len(text.splitlines()) < 700


def test_cr2_parity_comparator_reports_tolerances_and_accepts_lane_local_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    summary = parity.compare(cpu, cuda)
    assert summary["status"] == "pass"
    assert summary["coverage"] == {
        "raw_field_count": 66,
        "released_numeric_field_count": 12,
        "identity_diagnostic_field_count": 1,
        "excluded_field_count": 53,
        "partition_complete": True,
    }
    assert all(
        field["comparison_count"] == field["matched_count"] == 4
        for field in summary["cross_lane_fields"]
    )
    assert summary["identity_diagnostics"]["raw_allocator_ids_required_to_match"] is False
    assert summary["identity_diagnostics"]["cpu_reset_changed_count"] == 4
    assert summary["identity_diagnostics"]["cuda_reset_changed_count"] == 4


def test_cr2_parity_rejects_seed_or_action_trace_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["parity_release"]["sessions"][0]["trace_signature"] = "mutated-action-trace"
    with pytest.raises(RuntimeError, match="frozen trace signature"):
        parity.compare(cpu, cuda)


def test_cr2_parity_rejects_nonfinite_and_over_tolerance_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["parity_release"]["sessions"][0]["frames"][0]["worlds"][0]["released"][
        "agent_observations"
    ]["x"] = float("nan")
    with pytest.raises(RuntimeError, match="not finite"):
        parity.compare(cpu, cuda)

    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["parity_release"]["sessions"][0]["frames"][0]["worlds"][0]["released"][
        "agent_observations"
    ]["x"] += 1.0e-2
    with pytest.raises(RuntimeError, match="cross_lane field diverged"):
        parity.compare(cpu, cuda)


def test_cr2_parity_rejects_payload_fields_outside_explicit_release_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["parity_release"]["sessions"][0]["frames"][0]["worlds"][0]["released"][
        "agent_observations"
    ]["pitch"] = 0.0
    with pytest.raises(RuntimeError, match="keys diverged"):
        parity.compare(cpu, cuda)


def test_cr2_parity_rejects_outer_payload_outside_exact_probe_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["unexpected_raw_payload"] = {"agent_observations": {"pitch": 0.0}}
    with pytest.raises(RuntimeError, match="outer_probe keys diverged"):
        parity.compare(cpu, cuda)


def test_cr2_parity_rejects_same_backend_reset_value_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cpu["parity_release"]["sessions"][1]["frames"][0]["worlds"][0]["released"][
        "agent_observations"
    ]["x"] += 1.0e-12
    with pytest.raises(RuntimeError, match="cpu_reset field diverged"):
        parity.compare(cpu, cuda)


def test_cr2_parity_keeps_public_support_and_measured_consumer_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cpu, cuda = _synthetic_payload(monkeypatch)
    cuda["parity_release"]["public_support_enabled"] = True
    with pytest.raises(RuntimeError, match="public_support_enabled"):
        parity.compare(cpu, cuda)


def test_cr2_parity_comparator_is_bounded() -> None:
    assert len(COMPARATOR.read_text(encoding="utf-8").splitlines()) < 700
