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

from python.testing.runtime import ensure_repo_imports, resolve_repo_path
from tools.diagnostics.generate_exact_world_step_parity_trace import (
    _entity_ref,
    _serialize_instrument,
    _serialize_terminal,
    _serialize_truth,
)


ensure_repo_imports()

import ef_py  # noqa: E402


def _load_trace(trace: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(trace, dict):
        return trace
    path = Path(trace)
    return json.loads(path.read_text(encoding="utf-8"))


def _decode_initial_packed(trace: dict[str, Any]) -> bytes:
    payload = trace.get("initial_exact_state_packed_b64")
    if not isinstance(payload, str) or not payload:
        raise ValueError("trace is missing initial_exact_state_packed_b64")
    return base64.b64decode(payload.encode("ascii"))


def _spawn_runtime_from_trace(trace: dict[str, Any]) -> tuple[Any, list[Any], list[int]]:
    seeds = [int(seed) for seed in trace.get("seeds", [])]
    if not seeds:
        raise ValueError("trace is missing seeds")
    db_path = str(trace.get("database_path") or resolve_repo_path("examples", "config", "database"))
    runtime = ef_py.WorldBatchRuntime(len(seeds))
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch(seeds)
    runtime.set_time_step(float(trace.get("time_step_s", 1.0 / 60.0)))

    refs: list[Any] = []
    entity_ids: list[int] = []
    for world_setup in trace.get("world_setup", []):
        world_index = int(world_setup["world_index"])
        world = runtime.world(world_index)
        spawn = dict(world_setup["spawn"])
        entity_id = int(world.spawn_unit(
            ef_py.Side.Blue,
            str(spawn["type_name"]),
            float(spawn["x"]),
            float(spawn["y"]),
            float(spawn["z"]),
            float(spawn["heading"]),
            float(spawn["pitch"]),
            float(spawn["roll"]),
            float(spawn["vx"]),
            float(spawn["vy"]),
            float(spawn["vz"]),
        ))
        mission_cmd = world_setup.get("mission_command")
        if isinstance(mission_cmd, dict):
            cmd = ef_py.MissionCommand()
            cmd.command_code = int(mission_cmd.get("command_code", 0))
            cmd.cmd_heading_deg = float(mission_cmd.get("cmd_heading_deg", 0.0))
            cmd.cmd_altitude_m = float(mission_cmd.get("cmd_altitude_m", 0.0))
            cmd.cmd_speed_mps = float(mission_cmd.get("cmd_speed_mps", 0.0))
            cmd.active = bool(mission_cmd.get("active", False))
            world.set_mission_command(entity_id, cmd)
        refs.append(_entity_ref(world_index, entity_id))
        entity_ids.append(entity_id)

    if len(refs) != len(seeds):
        raise RuntimeError("trace world_setup count does not match seeds")
    return runtime, refs, entity_ids


def _record_runtime_surface(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
    truths = runtime.get_agent_observations_batch(refs)
    instruments = runtime.get_instrument_states_batch(refs)
    return {
        "step_index": int(step_index),
        "apply_signatures": [
            int(value)
            for value in runtime.extract_exact_world_step_state_v1_apply_signatures_batch(refs)
        ],
        "truth": [_serialize_truth(value, entity_slot) for entity_slot, value in enumerate(truths)],
        "instrument": [_serialize_instrument(value) for value in instruments],
        "hidden_dynamics": list(runtime.extract_exact_world_step_state_v1_hidden_surfaces_batch(refs)),
        "terminal": [
            _serialize_terminal(runtime.world(int(ref.world_index)), entity_id, entity_slot, truth, inst)
            for entity_slot, (ref, entity_id, truth, inst) in enumerate(zip(refs, entity_ids, truths, instruments))
        ],
    }


def _append_mismatch(
    summary: dict[str, Any],
    path: str,
    expected: Any,
    actual: Any,
    diff: float | None = None,
) -> None:
    summary["mismatch_count"] += 1
    if len(summary["first_mismatches"]) >= summary["max_examples"]:
        return
    item = {
        "path": path,
        "expected": expected,
        "actual": actual,
    }
    if diff is not None:
        item["abs_diff"] = diff
    summary["first_mismatches"].append(item)


def _compare_values(
    expected: Any,
    actual: Any,
    *,
    path: str,
    abs_tol: float,
    summary: dict[str, Any],
) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys | actual_keys):
            if key == "apply_signatures":
                continue
            child_path = f"{path}.{key}" if path else str(key)
            if key not in expected:
                _append_mismatch(summary, child_path, "<missing>", actual[key])
                continue
            if key not in actual:
                _append_mismatch(summary, child_path, expected[key], "<missing>")
                continue
            _compare_values(expected[key], actual[key], path=child_path, abs_tol=abs_tol, summary=summary)
        return

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            _append_mismatch(summary, f"{path}.length" if path else "length", len(expected), len(actual))
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            _compare_values(expected_item, actual_item, path=child_path, abs_tol=abs_tol, summary=summary)
        return

    if isinstance(expected, bool) or isinstance(actual, bool):
        if bool(expected) != bool(actual):
            _append_mismatch(summary, path, bool(expected), bool(actual))
        return

    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        diff = abs(float(expected) - float(actual))
        if diff > summary["max_abs_diff"]:
            summary["max_abs_diff"] = diff
            summary["max_abs_diff_path"] = path
        if diff > abs_tol:
            _append_mismatch(summary, path, expected, actual, diff)
        return

    if expected != actual:
        _append_mismatch(summary, path, expected, actual)


def _compare_records(expected: dict[str, Any], actual: dict[str, Any], *, abs_tol: float, max_examples: int) -> dict[str, Any]:
    summary = {
        "mismatch_count": 0,
        "max_abs_diff": 0.0,
        "max_abs_diff_path": "",
        "first_mismatches": [],
        "max_examples": int(max_examples),
    }
    _compare_values(expected, actual, path="", abs_tol=abs_tol, summary=summary)
    return {
        "mismatch_count": int(summary["mismatch_count"]),
        "max_abs_diff": float(summary["max_abs_diff"]),
        "max_abs_diff_path": str(summary["max_abs_diff_path"]),
        "first_mismatches": list(summary["first_mismatches"]),
    }


def _step_mode_summary(
    trace: dict[str, Any],
    *,
    use_gpu: bool,
    abs_tol: float,
    max_examples: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[bytes]]:
    runtime, refs, entity_ids = _spawn_runtime_from_trace(trace)
    packed = _decode_initial_packed(trace)
    total_h2d_ms = 0.0
    total_kernel_ms = 0.0
    total_d2h_ms = 0.0
    total_ms = 0.0
    used_cuda = False
    step_reports: list[dict[str, Any]] = []
    actual_records: list[dict[str, Any]] = []
    packed_history: list[bytes] = []

    for step_index, expected_record in enumerate(trace.get("step_records", [])):
        packed_history.append(bytes(packed))
        runtime.apply_exact_world_step_states_v1_batch_packed(refs, packed)
        actual_record = _record_runtime_surface(runtime, refs, entity_ids, step_index)
        actual_records.append(actual_record)

        packed_signatures = [
            int(value) for value in ef_py.exact_world_step_states_v1_apply_signatures_packed(packed)
        ]
        record_compare = _compare_records(expected_record, actual_record, abs_tol=abs_tol, max_examples=max_examples)
        step_reports.append(
            {
                "step_index": int(step_index),
                "packed_apply_signatures_match": packed_signatures == list(expected_record["apply_signatures"]),
                "live_apply_signatures_match": actual_record["apply_signatures"] == list(expected_record["apply_signatures"]),
                "mismatch_count": int(record_compare["mismatch_count"]),
                "max_abs_diff": float(record_compare["max_abs_diff"]),
                "max_abs_diff_path": str(record_compare["max_abs_diff_path"]),
                "first_mismatches": list(record_compare["first_mismatches"]),
            }
        )

        if step_index + 1 >= len(trace["step_records"]):
            break

        packed = ef_py.step_exact_world_step_states_v1_prototype_packed(packed, 1, bool(use_gpu))
        stats = ef_py.last_exact_world_step_prototype_stats()
        used_cuda = used_cuda or bool(getattr(stats, "used_cuda", False))
        total_h2d_ms += float(getattr(stats, "host_to_device_ms", 0.0))
        total_kernel_ms += float(getattr(stats, "kernel_ms", 0.0))
        total_d2h_ms += float(getattr(stats, "device_to_host_ms", 0.0))
        total_ms += float(getattr(stats, "total_ms", 0.0))

    all_packed_match = all(report["packed_apply_signatures_match"] for report in step_reports)
    all_live_match = all(report["live_apply_signatures_match"] for report in step_reports)
    return (
        {
            "mode": "gpu_shadow" if use_gpu else "cpu_reference",
            "used_cuda": bool(used_cuda),
            "step_count": len(step_reports),
            "all_packed_apply_signatures_match": bool(all_packed_match),
            "all_live_apply_signatures_match": bool(all_live_match),
            "max_abs_diff_vs_trace": max((report["max_abs_diff"] for report in step_reports), default=0.0),
            "total_mismatches_vs_trace": int(sum(report["mismatch_count"] for report in step_reports)),
            "host_to_device_ms": float(total_h2d_ms),
            "kernel_ms": float(total_kernel_ms),
            "device_to_host_ms": float(total_d2h_ms),
            "total_step_ms": float(total_ms),
            "steps": step_reports,
        },
        actual_records,
        packed_history,
    )


def compare_exact_world_step_shadow_trace(
    trace: str | Path | dict[str, Any],
    *,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    cpu_summary, cpu_records, cpu_packed_history = _step_mode_summary(
        loaded,
        use_gpu=False,
        abs_tol=abs_tol,
        max_examples=max_examples,
    )
    gpu_summary, gpu_records, gpu_packed_history = _step_mode_summary(
        loaded,
        use_gpu=True,
        abs_tol=abs_tol,
        max_examples=max_examples,
    )

    cpu_vs_gpu_steps: list[dict[str, Any]] = []
    for step_index, (cpu_record, gpu_record, cpu_packed, gpu_packed) in enumerate(
        zip(cpu_records, gpu_records, cpu_packed_history, gpu_packed_history)
    ):
        compare = _compare_records(cpu_record, gpu_record, abs_tol=abs_tol, max_examples=max_examples)
        apply_signatures_match = list(cpu_record["apply_signatures"]) == list(gpu_record["apply_signatures"])
        differing_components: list[str] = []
        if not apply_signatures_match:
            cpu_digests = ef_py.exact_world_step_state_v1_component_digests_packed(cpu_packed)
            gpu_digests = ef_py.exact_world_step_state_v1_component_digests_packed(gpu_packed)
            differing_components = sorted({
                component
                for cpu_state, gpu_state in zip(cpu_digests, gpu_digests)
                for component in set(cpu_state) | set(gpu_state)
                if cpu_state.get(component) != gpu_state.get(component)
            })
        cpu_vs_gpu_steps.append(
            {
                "step_index": int(step_index),
                "apply_signatures_match": bool(apply_signatures_match),
                "differing_components": differing_components,
                "mismatch_count": int(compare["mismatch_count"]),
                "max_abs_diff": float(compare["max_abs_diff"]),
                "max_abs_diff_path": str(compare["max_abs_diff_path"]),
                "first_mismatches": list(compare["first_mismatches"]),
            }
        )

    return {
        "trace_kind": loaded.get("trace_kind"),
        "world_count": int(loaded.get("world_count", 0)),
        "steps": int(loaded.get("steps", 0)),
        "time_step_s": float(loaded.get("time_step_s", 0.0)),
        "cpu_reference": cpu_summary,
        "gpu_shadow": gpu_summary,
        "cpu_vs_gpu": {
            "step_count": len(cpu_vs_gpu_steps),
            "all_apply_signatures_match": all(report["apply_signatures_match"] for report in cpu_vs_gpu_steps),
            "max_abs_diff": max((report["max_abs_diff"] for report in cpu_vs_gpu_steps), default=0.0),
            "total_mismatches": int(sum(report["mismatch_count"] for report in cpu_vs_gpu_steps)),
            "steps": cpu_vs_gpu_steps,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay a Phase 1 parity trace through the Phase 2 exact-step shadow prototype."
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON parity trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument(
        "--max-examples",
        type=int,
        default=8,
        help="Maximum number of mismatch examples to record per step.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_shadow_trace(
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
                "steps": report["steps"],
                "cpu_trace_max_abs_diff": report["cpu_reference"]["max_abs_diff_vs_trace"],
                "gpu_trace_max_abs_diff": report["gpu_shadow"]["max_abs_diff_vs_trace"],
                "cpu_vs_gpu_all_apply_signatures_match": report["cpu_vs_gpu"]["all_apply_signatures_match"],
                "cpu_vs_gpu_max_abs_diff": report["cpu_vs_gpu"]["max_abs_diff"],
                "gpu_used_cuda": report["gpu_shadow"]["used_cuda"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
