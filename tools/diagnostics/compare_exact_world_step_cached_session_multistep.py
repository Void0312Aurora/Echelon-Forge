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
from tools.diagnostics.benchmark_exact_world_step_first_scope_chain_cached_session import (
    _exact_step_backend_enum,
    _make_pilot_assignments,
    _make_runtime,
)
from tools.diagnostics.compare_exact_world_step_shadow_trace import _compare_records, _load_trace
from tools.diagnostics.compare_exact_world_step_system_trace import (
    _component_digests_match,
    _differing_components,
    _packed_component_digests,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import _normalized_replay_blob_b64, _record_step

ensure_repo_imports()

import ef_py  # noqa: E402

_IGNORED_COMPONENT_DIGESTS = {"entity_id", "world_time_s"}


def _decode_record_packed(record: dict[str, Any]) -> bytes:
    payload = record.get("packed_exact_state_b64")
    if not isinstance(payload, str) or not payload:
        raise ValueError("record is missing packed_exact_state_b64")
    return base64.b64decode(payload.encode("ascii"))


def _record_runtime_step(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
    record = _record_step(runtime, refs, entity_ids, step_index)
    record["packed_exact_state_b64"] = _normalized_replay_blob_b64(
        runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    )
    return record


def _stage_record(step_trace: dict[str, Any], stage_name: str) -> dict[str, Any]:
    for record in step_trace.get("stage_records", []):
        if str(record.get("stage_name")) == stage_name:
            return dict(record)
    raise ValueError(f"step trace is missing stage record for {stage_name}")


def _strip_packed_blob(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out.pop("packed_exact_state_b64", None)
    return out


def _differing_state_components(expected_state: dict[str, int], actual_state: dict[str, int]) -> list[str]:
    differing: list[str] = []
    for component in sorted(set(expected_state) | set(actual_state)):
        if component in _IGNORED_COMPONENT_DIGESTS:
            continue
        if expected_state.get(component) != actual_state.get(component):
            differing.append(str(component))
    return differing


def _differing_states(
    expected: list[dict[str, int]],
    actual: list[dict[str, int]],
    refs: list[Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for state_index, (expected_state, actual_state) in enumerate(zip(expected, actual)):
        differing_components = _differing_state_components(expected_state, actual_state)
        if not differing_components:
            continue
        ref = refs[state_index]
        rows.append(
            {
                "state_index": int(state_index),
                "world_index": int(ref.world_index),
                "entity_id": int(ref.entity_id),
                "differing_components": differing_components,
            }
        )
    return rows


def _packed_states_have_missiles(packed: bytes) -> bool:
    surfaces = ef_py.exact_world_step_state_v1_combat_surfaces_packed(packed)
    for item in surfaces:
        combat = dict(item)
        missile = dict(combat.get("missile", {}))
        if bool(missile.get("present", False)):
            return True
    return False


def _localize_first_divergence(
    step_trace: dict[str, Any],
    *,
    refs: list[Any],
    use_gpu: bool,
    abs_tol: float,
    max_examples: int,
) -> dict[str, Any]:
    step_index = int(step_trace["step_index"])
    initial_record = _stage_record(step_trace, "__step_initial__")
    initial_packed = _decode_record_packed(initial_record)

    slice_specs: list[tuple[str, str, bytes]] = []

    command_lane_packed = bytes(ef_py.step_exact_world_step_command_lane_reference_cpu_packed(initial_packed))
    slice_specs.append(("CommandLane", "CommandLag", command_lane_packed))

    front_half_packed = bytes(ef_py.step_exact_world_step_front_half_packed(initial_packed, bool(use_gpu)))
    slice_specs.append(("FrontHalf", "GroundContact", front_half_packed))
    no_missiles = not _packed_states_have_missiles(front_half_packed)
    if no_missiles:
        rotational_packed = bytes(
            ef_py.step_exact_world_step_aircraft_tail_until_stage_packed(
                front_half_packed,
                "RotationalIntegrate",
                bool(use_gpu),
            )
        )
        slice_specs.append(("RotationalIntegrate", "RotationalIntegrate", rotational_packed))

        tail_packed = bytes(
            ef_py.step_exact_world_step_aircraft_tail_until_stage_packed(
                front_half_packed,
                "MassUpdate",
                bool(use_gpu),
            )
        )
        slice_specs.append(("AircraftTail", "MassUpdate", tail_packed))
    else:
        guidance_packed = bytes(ef_py.step_exact_world_step_missile_guidance_cuda_packed(front_half_packed, bool(use_gpu)))
        slice_specs.append(("MissileGuidance", "MissileGuidance", guidance_packed))

        tail_packed = bytes(ef_py.step_exact_world_step_aircraft_tail_cuda_packed(guidance_packed, bool(use_gpu)))
        slice_specs.append(("AircraftTail", "MassUpdate", tail_packed))

    reports: list[dict[str, Any]] = []
    first_mismatch_slice_name = ""
    first_mismatch_stage_name = ""
    for slice_name, stage_name, packed in slice_specs:
        expected_record = _stage_record(step_trace, stage_name)
        actual_packed_b64 = _normalized_replay_blob_b64(packed)
        actual_record = dict(expected_record)
        actual_record["packed_exact_state_b64"] = actual_packed_b64
        expected_packed = _decode_record_packed(expected_record)
        compare = _compare_records(
            _strip_packed_blob(expected_record),
            _strip_packed_blob(actual_record),
            abs_tol=abs_tol,
            max_examples=max_examples,
        )
        expected_digests = _packed_component_digests(expected_packed)
        actual_digests = _packed_component_digests(packed)
        differing_states = _differing_states(expected_digests, actual_digests, refs)
        packed_match = _component_digests_match(expected_digests, actual_digests)
        report = {
            "step_index": step_index,
            "slice_name": slice_name,
            "stage_name": stage_name,
            "apply_signatures_match": (
                list(expected_record["apply_signatures"])
                == list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed))
            ),
            "packed_component_digests_match": packed_match,
            "differing_components": _differing_components(expected_digests, actual_digests),
            "differing_states": differing_states,
            "mismatch_count": int(compare["mismatch_count"]),
            "max_abs_diff": float(compare["max_abs_diff"]),
            "max_abs_diff_path": str(compare["max_abs_diff_path"]),
            "first_mismatches": list(compare["first_mismatches"]),
        }
        reports.append(report)
        if not first_mismatch_slice_name and (
            (not bool(report["apply_signatures_match"]))
            or (not bool(report["packed_component_digests_match"]))
            or int(report["mismatch_count"]) > 0
        ):
            first_mismatch_slice_name = str(slice_name)
            first_mismatch_stage_name = str(stage_name)

    first_mismatch_state = next(
        (
            dict(item)
            for report in reports
            for item in list(report.get("differing_states", []))
        ),
        None,
    )
    return {
        "step_index": step_index,
        "first_mismatch_slice_name": first_mismatch_slice_name,
        "first_mismatch_stage_name": first_mismatch_stage_name,
        "first_mismatch_state": first_mismatch_state,
        "no_missiles": bool(no_missiles),
        "aircraft_tail_stage_localization": (
            _localize_aircraft_tail_divergence(
                step_trace,
                refs=refs,
                front_half_packed=front_half_packed,
                use_gpu=bool(use_gpu),
            )
            if bool(no_missiles)
            else None
        ),
        "records": reports,
    }


def _localize_front_half_divergence(
    step_trace: dict[str, Any],
    *,
    refs: list[Any],
    abs_tol: float,
    max_examples: int,
) -> dict[str, Any]:
    step_index = int(step_trace["step_index"])
    initial_record = _stage_record(step_trace, "__step_initial__")
    initial_packed = _decode_record_packed(initial_record)
    stage_names = [
        "FlightControl",
        "ClearForces",
        "ComputeAeroState",
        "ComputeForces",
        "ComputeAerodynamics",
        "GroundContact",
    ]

    reports: list[dict[str, Any]] = []
    first_mismatch_stage_name = ""
    for stage_name in stage_names:
        packed = bytes(ef_py.step_exact_world_step_front_half_until_stage_packed(initial_packed, stage_name))
        expected_record = _stage_record(step_trace, stage_name)
        expected_packed = _decode_record_packed(expected_record)
        expected_digests = _packed_component_digests(expected_packed)
        actual_digests = _packed_component_digests(packed)
        differing_states = _differing_states(expected_digests, actual_digests, refs)
        report = {
            "step_index": step_index,
            "stage_name": stage_name,
            "apply_signatures_match": (
                list(expected_record["apply_signatures"])
                == list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed))
            ),
            "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
            "differing_components": _differing_components(expected_digests, actual_digests),
            "differing_states": differing_states,
            "mismatch_count": 0,
            "max_abs_diff": 0.0,
            "max_abs_diff_path": "",
            "first_mismatches": [],
        }
        reports.append(report)
        if not first_mismatch_stage_name and (
            (not bool(report["apply_signatures_match"]))
            or (not bool(report["packed_component_digests_match"]))
            or int(report["mismatch_count"]) > 0
        ):
            first_mismatch_stage_name = stage_name

    first_mismatch_state = next(
        (
            dict(item)
            for report in reports
            for item in list(report.get("differing_states", []))
        ),
        None,
    )
    return {
        "step_index": step_index,
        "first_mismatch_stage_name": first_mismatch_stage_name,
        "first_mismatch_state": first_mismatch_state,
        "records": reports,
    }


def _localize_aircraft_tail_divergence(
    step_trace: dict[str, Any],
    *,
    refs: list[Any],
    front_half_packed: bytes,
    use_gpu: bool,
) -> dict[str, Any]:
    step_index = int(step_trace["step_index"])
    stage_names = [
        "RotationalIntegrate",
        "LeapfrogIntegrate",
        "NavigationSystem",
        "UpdateInstruments",
        "FuelConsumption",
        "MassUpdate",
    ]

    reports: list[dict[str, Any]] = []
    first_mismatch_stage_name = ""
    for stage_name in stage_names:
        packed = bytes(
            ef_py.step_exact_world_step_aircraft_tail_until_stage_packed(
                front_half_packed,
                stage_name,
                bool(use_gpu),
            )
        )
        expected_record = _stage_record(step_trace, stage_name)
        expected_packed = _decode_record_packed(expected_record)
        expected_digests = _packed_component_digests(expected_packed)
        actual_digests = _packed_component_digests(packed)
        differing_states = _differing_states(expected_digests, actual_digests, refs)
        report = {
            "step_index": step_index,
            "stage_name": stage_name,
            "apply_signatures_match": (
                list(expected_record["apply_signatures"])
                == list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed))
            ),
            "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
            "differing_components": _differing_components(expected_digests, actual_digests),
            "differing_states": differing_states,
            "mismatch_count": 0,
            "max_abs_diff": 0.0,
            "max_abs_diff_path": "",
            "first_mismatches": [],
        }
        reports.append(report)
        if not first_mismatch_stage_name and (
            (not bool(report["apply_signatures_match"]))
            or (not bool(report["packed_component_digests_match"]))
            or int(report["mismatch_count"]) > 0
        ):
            first_mismatch_stage_name = stage_name

    first_mismatch_state = next(
        (
            dict(item)
            for report in reports
            for item in list(report.get("differing_states", []))
        ),
        None,
    )
    return {
        "step_index": step_index,
        "first_mismatch_stage_name": first_mismatch_stage_name,
        "first_mismatch_state": first_mismatch_state,
        "records": reports,
    }


def compare_exact_world_step_cached_session_multistep(
    trace: str | Path | dict[str, Any],
    *,
    use_gpu: bool = False,
    use_runtime_step_batch_backend: bool = False,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_cached_session_multistep_trace_v1":
        raise ValueError(
            "compare_exact_world_step_cached_session_multistep expects "
            "trace_kind=cpu_exact_cached_session_multistep_trace_v1"
        )

    runtime, refs = _make_runtime(
        seed=int(loaded.get("seed", 101)),
        time_step_s=float(loaded.get("time_step_s", 0.05)),
        world_count=int(loaded.get("world_count", 1)),
    )
    entity_ids = [int(ref.entity_id) for ref in refs]
    runtime.prime_exact_world_step_first_scope_chain_cached_session(refs)
    if use_runtime_step_batch_backend:
        runtime.set_exact_world_step_backend(_exact_step_backend_enum(use_gpu=bool(use_gpu)))

    step_reports: list[dict[str, Any]] = []
    first_divergence_step = 0
    first_divergence_localization: dict[str, Any] | None = None

    for step_trace in loaded.get("step_traces", []):
        step_index = int(step_trace["step_index"])
        assignments = _make_pilot_assignments(refs, step_index - 1)
        if use_runtime_step_batch_backend:
            runtime.set_pilot_actions_batch(assignments)
            runtime.step_batch()
            stepped_packed = bytes(runtime.extract_exact_world_step_states_v1_batch_packed(refs))
        else:
            runtime.set_pilot_actions_exact_world_step_first_scope_chain_cached_session(assignments)
            stepped_packed = bytes(
                runtime.step_exact_world_step_first_scope_chain_cached_session_packed(bool(use_gpu), False)
            )
            runtime.apply_exact_world_step_states_v1_batch_packed(refs, stepped_packed)

        expected_record = dict(step_trace["final_record"])
        actual_record = _record_runtime_step(runtime, refs, entity_ids, step_index)
        actual_record["stage_name"] = "MassUpdate"
        actual_record["stage_order"] = int(expected_record.get("stage_order", 25))
        actual_record["stage_domain"] = str(expected_record.get("stage_domain", "logistics"))

        compare = _compare_records(
            _strip_packed_blob(expected_record),
            _strip_packed_blob(actual_record),
            abs_tol=abs_tol,
            max_examples=max_examples,
        )
        expected_packed = _decode_record_packed(expected_record)
        expected_digests = _packed_component_digests(expected_packed)
        actual_digests = _packed_component_digests(stepped_packed)
        differing_states = _differing_states(expected_digests, actual_digests, refs)
        report = {
            "step_index": step_index,
            "apply_signatures_match": (
                list(expected_record["apply_signatures"])
                == list(actual_record["apply_signatures"])
            ),
            "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
            "differing_components": _differing_components(expected_digests, actual_digests),
            "differing_states": differing_states,
            "mismatch_count": int(compare["mismatch_count"]),
            "max_abs_diff": float(compare["max_abs_diff"]),
            "max_abs_diff_path": str(compare["max_abs_diff_path"]),
            "first_mismatches": list(compare["first_mismatches"]),
        }
        step_reports.append(report)

        if first_divergence_step == 0 and (
            (not bool(report["apply_signatures_match"]))
            or (not bool(report["packed_component_digests_match"]))
            or int(report["mismatch_count"]) > 0
        ):
            first_divergence_step = step_index
            first_divergence_localization = _localize_first_divergence(
                step_trace,
                refs=refs,
                use_gpu=bool(use_gpu),
                abs_tol=abs_tol,
                max_examples=max_examples,
            )
            if (
                bool(use_gpu)
                and isinstance(first_divergence_localization, dict)
                and str(first_divergence_localization.get("first_mismatch_slice_name", "")) == "FrontHalf"
            ):
                first_divergence_localization["front_half_stage_localization"] = _localize_front_half_divergence(
                    step_trace,
                    refs=refs,
                    abs_tol=abs_tol,
                    max_examples=max_examples,
                )

    chain_stats = ef_py.last_exact_world_step_first_scope_chain_cuda_stats()
    return {
        "trace_kind": loaded.get("trace_kind"),
        "scenario_kind": loaded.get("scenario_kind"),
        "steps": int(loaded.get("steps", 0)),
        "world_count": int(loaded.get("world_count", len(refs))),
        "use_gpu_requested": bool(use_gpu),
        "runtime_step_batch_backend_used": bool(use_runtime_step_batch_backend),
        "used_cuda": bool(getattr(chain_stats, "used_cuda", False)),
        "all_apply_signatures_match": all(bool(item["apply_signatures_match"]) for item in step_reports),
        "all_packed_component_digests_match": all(bool(item["packed_component_digests_match"]) for item in step_reports),
        "total_mismatches": int(sum(int(item["mismatch_count"]) for item in step_reports)),
        "first_divergence_step": int(first_divergence_step),
        "first_divergence_localization": first_divergence_localization,
        "records": step_reports,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the cached-session multi-step benchmark fixture through CPU or GPU cached sessions and "
            "localize the first repeated-step divergence."
        )
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON cached-session multistep trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument("--max-examples", type=int, default=8, help="Maximum mismatch examples per step/slice.")
    parser.add_argument("--gpu", action="store_true", help="Run the cached-session replay on the CUDA backend.")
    parser.add_argument(
        "--runtime-step-batch-backend",
        action="store_true",
        help="Replay through the experimental step_batch backend switch instead of direct cached-session stepping.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_cached_session_multistep(
        args.trace,
        use_gpu=bool(args.gpu),
        use_runtime_step_batch_backend=bool(args.runtime_step_batch_backend),
        abs_tol=float(args.abs_tol),
        max_examples=int(args.max_examples),
    )

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "trace_kind": report["trace_kind"],
        "steps": report["steps"],
        "world_count": report["world_count"],
        "use_gpu_requested": report["use_gpu_requested"],
        "runtime_step_batch_backend_used": report["runtime_step_batch_backend_used"],
        "used_cuda": report["used_cuda"],
        "all_apply_signatures_match": report["all_apply_signatures_match"],
        "all_packed_component_digests_match": report["all_packed_component_digests_match"],
        "total_mismatches": report["total_mismatches"],
        "first_divergence_step": report["first_divergence_step"],
    }
    if isinstance(report["first_divergence_localization"], dict):
        summary["first_divergence_slice"] = report["first_divergence_localization"].get("first_mismatch_slice_name", "")
        summary["first_divergence_stage"] = report["first_divergence_localization"].get("first_mismatch_stage_name", "")
        summary["first_divergence_state"] = report["first_divergence_localization"].get("first_mismatch_state", {})
        summary["first_divergence_no_missiles"] = report["first_divergence_localization"].get("no_missiles", False)
        front_half_stage_localization = report["first_divergence_localization"].get("front_half_stage_localization")
        if isinstance(front_half_stage_localization, dict):
            summary["front_half_first_divergence_stage"] = front_half_stage_localization.get(
                "first_mismatch_stage_name",
                "",
            )
            summary["front_half_first_divergence_state"] = front_half_stage_localization.get(
                "first_mismatch_state",
                {},
            )
        aircraft_tail_stage_localization = report["first_divergence_localization"].get("aircraft_tail_stage_localization")
        if isinstance(aircraft_tail_stage_localization, dict):
            summary["aircraft_tail_first_divergence_stage"] = aircraft_tail_stage_localization.get(
                "first_mismatch_stage_name",
                "",
            )
            summary["aircraft_tail_first_divergence_state"] = aircraft_tail_stage_localization.get(
                "first_mismatch_state",
                {},
            )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
