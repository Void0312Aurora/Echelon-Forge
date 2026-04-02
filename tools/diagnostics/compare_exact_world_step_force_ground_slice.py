from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports
from tools.diagnostics.compare_exact_world_step_shadow_trace import (
    _compare_records,
    _load_trace,
    _record_runtime_surface,
    _spawn_runtime_from_trace,
)
from tools.diagnostics.compare_exact_world_step_system_trace import (
    _component_digests_match,
    _differing_components,
    _packed_component_digests,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (
    _normalized_replay_blob_b64,
)


ensure_repo_imports()

import ef_py  # noqa: E402


def _decode_record_packed(record: dict[str, Any]) -> bytes:
    payload = record.get("packed_exact_state_b64")
    if not isinstance(payload, str) or not payload:
        raise ValueError("stage record is missing packed_exact_state_b64")
    return base64.b64decode(payload.encode("ascii"))


def _strip_runtime_clock_fields(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    truth = []
    for item in list(record.get("truth", [])):
        current = dict(item)
        current.pop("sim_time", None)
        truth.append(current)
    terminal = []
    for item in list(record.get("terminal", [])):
        current = dict(item)
        current.pop("sim_time", None)
        terminal.append(current)
    out["truth"] = truth
    out["terminal"] = terminal
    return out


def compare_exact_world_step_force_ground_slice(
    trace: str | Path | dict[str, Any],
    *,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_system_stage_trace_v1":
        raise ValueError(
            "compare_exact_world_step_force_ground_slice expects trace_kind=cpu_exact_system_stage_trace_v1"
        )

    stage_records = list(loaded.get("stage_records", []))
    target_record = next((record for record in stage_records if record.get("stage_name") == "GroundContact"), None)
    if target_record is None:
        raise ValueError("system trace does not contain a GroundContact stage record")

    initial_payload = loaded.get("initial_exact_state_packed_b64")
    if not isinstance(initial_payload, str) or not initial_payload:
        raise ValueError("trace is missing initial_exact_state_packed_b64")
    initial_packed = base64.b64decode(initial_payload.encode("ascii"))
    after_command_lane = bytes(ef_py.step_exact_world_step_command_lane_reference_cpu_packed(initial_packed))
    after_control_aero = bytes(ef_py.step_exact_world_step_control_aero_reference_cpu_packed(after_command_lane))
    stepped_packed = bytes(ef_py.step_exact_world_step_force_ground_reference_cpu_packed(after_control_aero))

    command_lane_stats = ef_py.last_exact_world_step_command_lane_stats()
    control_aero_stats = ef_py.last_exact_world_step_control_aero_stats()
    force_ground_stats = ef_py.last_exact_world_step_force_ground_stats()

    runtime, refs, entity_ids = _spawn_runtime_from_trace(loaded)
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, stepped_packed)
    actual_record = _record_runtime_surface(runtime, refs, entity_ids, int(target_record["step_index"]))
    actual_record["stage_name"] = "GroundContact"
    actual_record["stage_order"] = int(target_record["stage_order"])
    actual_record["stage_domain"] = str(target_record["stage_domain"])
    actual_record["packed_exact_state_b64"] = _normalized_replay_blob_b64(stepped_packed)

    compare = _compare_records(
        _strip_runtime_clock_fields(target_record),
        _strip_runtime_clock_fields(actual_record),
        abs_tol=abs_tol,
        max_examples=max_examples,
    )
    expected_digests = _packed_component_digests(_decode_record_packed(target_record))
    actual_digests = _packed_component_digests(stepped_packed)

    return {
        "trace_kind": loaded.get("trace_kind"),
        "target_stage_name": "GroundContact",
        "world_count": int(loaded.get("world_count", 0)),
        "apply_signatures_match": list(target_record["apply_signatures"]) == list(actual_record["apply_signatures"]),
        "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
        "differing_components": _differing_components(expected_digests, actual_digests),
        "mismatch_count": int(compare["mismatch_count"]),
        "max_abs_diff": float(compare["max_abs_diff"]),
        "max_abs_diff_path": str(compare["max_abs_diff_path"]),
        "first_mismatches": list(compare["first_mismatches"]),
        "command_lane_state_count": int(getattr(command_lane_stats, "state_count", 0)),
        "command_lane_total_ms": float(getattr(command_lane_stats, "total_ms", 0.0)),
        "control_aero_state_count": int(getattr(control_aero_stats, "state_count", 0)),
        "control_aero_total_ms": float(getattr(control_aero_stats, "total_ms", 0.0)),
        "force_ground_state_count": int(getattr(force_ground_stats, "state_count", 0)),
        "force_ground_total_ms": float(getattr(force_ground_stats, "total_ms", 0.0)),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the exact CPU force/ground executor slice (chained after command-lane and control/aero slices) "
            "and compare it against the GroundContact stage in a system trace."
        )
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON system-stage trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument(
        "--max-examples",
        type=int,
        default=8,
        help="Maximum number of mismatch examples to record.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_force_ground_slice(
        args.trace,
        abs_tol=float(args.abs_tol),
        max_examples=int(args.max_examples),
    )

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "trace_kind": report["trace_kind"],
                "target_stage_name": report["target_stage_name"],
                "apply_signatures_match": report["apply_signatures_match"],
                "packed_component_digests_match": report["packed_component_digests_match"],
                "mismatch_count": report["mismatch_count"],
                "max_abs_diff": report["max_abs_diff"],
                "max_abs_diff_path": report["max_abs_diff_path"],
                "force_ground_state_count": report["force_ground_state_count"],
                "force_ground_total_ms": report["force_ground_total_ms"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
