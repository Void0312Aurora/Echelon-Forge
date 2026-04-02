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
    _decode_initial_packed,
    _load_trace,
    _record_runtime_surface,
    _spawn_runtime_from_trace,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (
    _normalized_replay_blob_b64,
)


ensure_repo_imports()

import ef_py  # noqa: E402

_IGNORED_COMPONENT_DIGESTS = {"entity_id", "world_time_s"}


def _packed_component_digests(packed: bytes) -> list[dict[str, int]]:
    return [
        {str(name): int(value) for name, value in dict(state).items()}
        for state in ef_py.exact_world_step_state_v1_component_digests_packed(packed)
    ]


def _differing_components(expected: list[dict[str, int]], actual: list[dict[str, int]]) -> list[str]:
    differing: set[str] = set()
    for expected_state, actual_state in zip(expected, actual):
        for component in set(expected_state) | set(actual_state):
            if component in _IGNORED_COMPONENT_DIGESTS:
                continue
            if expected_state.get(component) != actual_state.get(component):
                differing.add(str(component))
    return sorted(differing)


def _component_digests_match(expected: list[dict[str, int]], actual: list[dict[str, int]]) -> bool:
    return not _differing_components(expected, actual)


def _decode_record_packed(record: dict[str, Any]) -> bytes | None:
    payload = record.get("packed_exact_state_b64")
    if not isinstance(payload, str) or not payload:
        return None
    return base64.b64decode(payload.encode("ascii"))


def compare_exact_world_step_system_trace(
    trace: str | Path | dict[str, Any],
    *,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_system_stage_trace_v1":
        raise ValueError(
            "compare_exact_world_step_system_trace expects trace_kind=cpu_exact_system_stage_trace_v1"
        )

    runtime, refs, entity_ids = _spawn_runtime_from_trace(loaded)
    initial_packed = _decode_initial_packed(loaded)
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, initial_packed)

    reports: list[dict[str, Any]] = []

    expected_records = list(loaded.get("stage_records", []))
    if not expected_records:
        raise ValueError("system trace is missing stage_records")

    initial_expected = dict(expected_records[0])
    initial_actual = _record_runtime_surface(runtime, refs, entity_ids, int(initial_expected.get("step_index", 0)))
    initial_actual["stage_name"] = "__initial__"
    initial_actual["stage_order"] = -1
    initial_actual["stage_domain"] = "initial"
    initial_actual_packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    initial_actual["packed_exact_state_b64"] = _normalized_replay_blob_b64(initial_actual_packed)
    initial_expected_digests = _packed_component_digests(_decode_record_packed(initial_expected) or initial_packed)
    initial_actual_digests = _packed_component_digests(initial_actual_packed)
    initial_compare = _compare_records(
        initial_expected,
        initial_actual,
        abs_tol=abs_tol,
        max_examples=max_examples,
    )
    reports.append(
        {
            "stage_name": "__initial__",
            "stage_order": -1,
            "stage_domain": "initial",
            "apply_signatures_match": list(initial_expected["apply_signatures"]) == list(initial_actual["apply_signatures"]),
            "packed_component_digests_match": _component_digests_match(initial_expected_digests, initial_actual_digests),
            "differing_components": _differing_components(initial_expected_digests, initial_actual_digests),
            "mismatch_count": int(initial_compare["mismatch_count"]),
            "max_abs_diff": float(initial_compare["max_abs_diff"]),
            "max_abs_diff_path": str(initial_compare["max_abs_diff_path"]),
            "first_mismatches": list(initial_compare["first_mismatches"]),
        }
    )

    active_worlds = [runtime.world(world_index) for world_index in range(int(loaded["world_count"]))]
    try:
        for world in active_worlds:
            world.begin_exact_stage_trace_frame()

        for expected_record in expected_records[1:]:
            stage_name = str(expected_record["stage_name"])
            for world in active_worlds:
                ok = bool(world.run_exact_stage_trace_stage(stage_name))
                if not ok:
                    raise RuntimeError(f"failed to run exact stage trace stage: {stage_name}")

            actual_record = _record_runtime_surface(runtime, refs, entity_ids, int(expected_record["step_index"]))
            actual_record["stage_name"] = stage_name
            actual_record["stage_order"] = int(expected_record["stage_order"])
            actual_record["stage_domain"] = str(expected_record["stage_domain"])
            actual_packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
            actual_record["packed_exact_state_b64"] = _normalized_replay_blob_b64(actual_packed)

            compare = _compare_records(
                expected_record,
                actual_record,
                abs_tol=abs_tol,
                max_examples=max_examples,
            )
            expected_packed = _decode_record_packed(expected_record)
            expected_digests = _packed_component_digests(expected_packed) if expected_packed is not None else []
            actual_digests = _packed_component_digests(actual_packed)

            reports.append(
                {
                    "stage_name": stage_name,
                    "stage_order": int(expected_record["stage_order"]),
                    "stage_domain": str(expected_record["stage_domain"]),
                    "apply_signatures_match": list(expected_record["apply_signatures"]) == list(actual_record["apply_signatures"]),
                    "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests) if expected_digests else True,
                    "differing_components": _differing_components(expected_digests, actual_digests) if expected_digests else [],
                    "mismatch_count": int(compare["mismatch_count"]),
                    "max_abs_diff": float(compare["max_abs_diff"]),
                    "max_abs_diff_path": str(compare["max_abs_diff_path"]),
                    "first_mismatches": list(compare["first_mismatches"]),
                }
            )
    finally:
        for world in reversed(active_worlds):
            try:
                world.end_exact_stage_trace_frame()
            except Exception:
                pass

    max_report = max(reports, key=lambda item: float(item["max_abs_diff"]), default=None)
    return {
        "trace_kind": loaded.get("trace_kind"),
        "world_count": int(loaded.get("world_count", 0)),
        "time_step_s": float(loaded.get("time_step_s", 0.0)),
        "stage_contract_inventory": list(loaded.get("stage_contract_inventory", [])),
        "record_count": len(reports),
        "traceable_stage_count": max(len(reports) - 1, 0),
        "final_stage_name": str(loaded.get("final_stage_name", "__initial__")),
        "all_apply_signatures_match": all(bool(report["apply_signatures_match"]) for report in reports),
        "all_packed_component_digests_match": all(bool(report["packed_component_digests_match"]) for report in reports),
        "total_mismatches": int(sum(int(report["mismatch_count"]) for report in reports)),
        "max_abs_diff": float(max((float(report["max_abs_diff"]) for report in reports), default=0.0)),
        "max_abs_diff_stage_name": str(max_report["stage_name"]) if max_report is not None else "",
        "max_abs_diff_path": str(max_report["max_abs_diff_path"]) if max_report is not None else "",
        "records": reports,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay a CPU exact system-stage trace through the traceable stage pipeline and diff every stage."
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON system-stage trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument(
        "--max-examples",
        type=int,
        default=8,
        help="Maximum number of mismatch examples to record per stage.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_system_trace(
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
                "world_count": report["world_count"],
                "traceable_stage_count": report["traceable_stage_count"],
                "final_stage_name": report["final_stage_name"],
                "all_apply_signatures_match": report["all_apply_signatures_match"],
                "all_packed_component_digests_match": report["all_packed_component_digests_match"],
                "total_mismatches": report["total_mismatches"],
                "max_abs_diff": report["max_abs_diff"],
                "max_abs_diff_stage_name": report["max_abs_diff_stage_name"],
                "max_abs_diff_path": report["max_abs_diff_path"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
