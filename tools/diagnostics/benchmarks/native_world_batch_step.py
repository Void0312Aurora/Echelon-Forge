#!/usr/bin/env python3
"""Native WorldBatchRuntime step benchmark with worker-pool occupancy detection.

Measures the C++ batch step path directly (no Python env orchestration) over a
worlds x units x threads sweep and reports, per case:

- wall time per batch step and world-steps per second;
- process CPU / wall (how many cores the process actually kept busy);
- native worker-pool occupancy = busy thread time / (wall * participating threads),
  read from ``WorldBatchRuntime.worker_pool_stats()``;
- optional per-system Flecs time shares (``--system-timing``).

With ``--baseline`` the run is compared case-by-case against an earlier JSON
output of this benchmark, and ``--max-regression`` turns a throughput loss beyond
the given fraction into a non-zero exit code so the benchmark can gate changes.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import configure_sim_log_level, ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py  # noqa: E402
from tools.diagnostics.common import load_json_config, write_json_output  # noqa: E402

SCHEMA = "echelon_forge.native_world_batch_step_benchmark.v1"


class _NoPoolStats:
    """Stand-in for builds that predate WorldBatchRuntime.worker_pool_stats()."""

    busy_ns = 0
    thread_wall_ns = 0
    wall_ns = 0
    pool_threads = 0


def _native_capabilities(batch: Any) -> dict[str, bool]:
    # Older ef_py builds lack the occupancy/timing diagnostics; the throughput
    # numbers stay comparable, so A/B runs against such a build still work.
    return {
        "worker_pool_stats": hasattr(batch, "worker_pool_stats"),
        "system_timing": hasattr(batch, "set_system_timing_enabled"),
    }


def _parse_int_list(raw: str, *, name: str, minimum: int) -> list[int]:
    values: list[int] = []
    for token in str(raw).split(","):
        token = token.strip()
        if not token:
            continue
        value = int(token)
        if value < minimum:
            raise ValueError(f"--{name} values must be >= {minimum}, got {value}")
        values.append(value)
    if not values:
        raise ValueError(f"--{name} must list at least one value")
    return values


def _spawn_requests(worlds: int, units: int, type_name: str) -> list[Any]:
    requests = []
    for world in range(worlds):
        for unit in range(units):
            request = ef_py.WorldSpawnRequest()
            request.world_index = world
            request.side = ef_py.Side.Blue if unit % 2 == 0 else ef_py.Side.Red
            request.type_name = type_name
            request.entity_name = f"bench_{world}_{unit}"
            # Opposing pairs on a lattice: each pair closes head-on at 20 km so
            # sensors, guidance and damage bookkeeping all run every step.
            request.x = 3000.0 * float(unit // 2)
            request.y = 20000.0 * float(unit % 2)
            request.z = 5000.0 + 250.0 * float(unit // 2)
            request.heading = 0.0 if unit % 2 == 0 else 180.0
            request.vx = 200.0
            requests.append(request)
    return requests


def _system_timing_summary(batch: Any, *, measured_wall_s: float, top: int) -> dict[str, Any]:
    per_system: dict[str, float] = {}
    for row in batch.system_timings():
        name = str(row.system_name) or "<anonymous>"
        per_system[name] = per_system.get(name, 0.0) + float(row.time_spent_s)
    total_s = sum(per_system.values())
    ranked = sorted(per_system.items(), key=lambda item: item[1], reverse=True)
    return {
        "measured_system_time_s": float(total_s),
        "measured_wall_s": float(measured_wall_s),
        "systems": [
            {
                "name": name,
                "time_s": float(seconds),
                "share": float(seconds / total_s) if total_s > 0.0 else 0.0,
            }
            for name, seconds in ranked[: max(1, int(top))]
        ],
    }


def _run_case(
    *,
    worlds: int,
    units: int,
    threads: int,
    steps: int,
    warmup: int,
    repeats: int,
    dt: float,
    type_name: str,
    database: str,
    system_timing: bool,
    top_systems: int,
) -> dict[str, Any]:
    batch = ef_py.WorldBatchRuntime(int(worlds))
    capabilities = _native_capabilities(batch)
    if system_timing and not capabilities["system_timing"]:
        # Drop the instrumented repeat main() added; this build cannot time systems.
        system_timing = False
        repeats = max(1, int(repeats) - 1)
    batch.set_worker_threads(int(threads))
    if not batch.load_database(database):
        raise RuntimeError(f"failed to load unit database {database!r}")
    batch.set_time_step(float(dt))
    batch.reset_batch([7 + i for i in range(int(worlds))])
    if units > 0:
        ids = batch.spawn_units_batch(_spawn_requests(int(worlds), int(units), type_name))
        if any(int(entity_id) == 0 for entity_id in ids):
            raise RuntimeError(f"spawning {type_name!r} failed in at least one world")
    for _ in range(max(0, int(warmup))):
        batch.step_batch()

    samples: list[dict[str, float]] = []
    timing_summary: dict[str, Any] | None = None
    for repeat in range(max(1, int(repeats))):
        last_repeat = repeat == max(1, int(repeats)) - 1
        if system_timing and last_repeat:
            # Timing adds a clock read around every system run, so only the last
            # repeat is instrumented and the throughput samples stay clean.
            batch.set_system_timing_enabled(True)
        if capabilities["worker_pool_stats"]:
            batch.reset_worker_pool_stats()
        cpu0 = time.process_time()
        t0 = time.perf_counter()
        for _ in range(int(steps)):
            batch.step_batch()
        wall_s = time.perf_counter() - t0
        cpu_s = time.process_time() - cpu0
        stats = batch.worker_pool_stats() if capabilities["worker_pool_stats"] else _NoPoolStats()
        if system_timing and last_repeat:
            timing_summary = _system_timing_summary(batch, measured_wall_s=wall_s, top=top_systems)
            batch.set_system_timing_enabled(False)
            continue
        thread_wall_ns = float(stats.thread_wall_ns)
        samples.append(
            {
                "wall_s": float(wall_s),
                "cpu_s": float(cpu_s),
                "pool_busy_ns": float(stats.busy_ns),
                "pool_thread_wall_ns": thread_wall_ns,
                "pool_wall_ns": float(stats.wall_ns),
                "pool_occupancy": float(stats.busy_ns) / thread_wall_ns if thread_wall_ns > 0 else 0.0,
                "pool_threads": float(stats.pool_threads),
            }
        )

    if not samples:
        raise RuntimeError("system timing needs --repeats >= 2 to keep one clean throughput sample")
    best = min(samples, key=lambda row: row["wall_s"])
    effective_threads = int(batch.effective_worker_threads())
    wall_s = best["wall_s"]
    result: dict[str, Any] = {
        "worlds": int(worlds),
        "units_per_world": int(units),
        "configured_threads": int(threads),
        "effective_threads": effective_threads,
        "steps": int(steps),
        "repeats": len(samples),
        "ms_per_batch_step": 1000.0 * wall_s / float(steps),
        "ms_per_world_step": 1000.0 * wall_s / float(steps * worlds),
        "world_steps_per_s": float(steps * worlds) / wall_s,
        "process_cpu_per_wall": best["cpu_s"] / wall_s,
        "process_cpu_utilization": best["cpu_s"] / (wall_s * effective_threads),
        "pool_occupancy": best["pool_occupancy"] if capabilities["worker_pool_stats"] else None,
        "pool_dispatch_share_of_wall": (
            best["pool_wall_ns"] / (wall_s * 1e9) if capabilities["worker_pool_stats"] else None
        ),
        "pool_threads": int(best["pool_threads"]) if capabilities["worker_pool_stats"] else None,
        "native_capabilities": capabilities,
        "ms_per_batch_step_samples": [1000.0 * row["wall_s"] / float(steps) for row in samples],
    }
    if timing_summary is not None:
        result["system_timing"] = timing_summary
    return result


def _case_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (int(row["worlds"]), int(row["units_per_world"]), int(row["configured_threads"]))


def _compare(cases: list[dict[str, Any]], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = {_case_key(row): row for row in baseline.get("cases", []) if isinstance(row, dict)}
    rows = []
    for case in cases:
        reference = baseline_rows.get(_case_key(case))
        if reference is None:
            continue
        before = float(reference["world_steps_per_s"])
        after = float(case["world_steps_per_s"])
        rows.append(
            {
                "worlds": case["worlds"],
                "units_per_world": case["units_per_world"],
                "configured_threads": case["configured_threads"],
                "baseline_world_steps_per_s": before,
                "world_steps_per_s": after,
                "speedup": after / before if before > 0.0 else float("nan"),
                "baseline_pool_occupancy": reference.get("pool_occupancy"),
                "pool_occupancy": case["pool_occupancy"],
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Native WorldBatchRuntime step benchmark with worker-pool occupancy detection."
    )
    parser.add_argument("--worlds", default="1,8,32", help="Comma-separated world counts.")
    parser.add_argument("--units", default="2", help="Comma-separated units per world.")
    parser.add_argument("--threads", default="1,8,16,32", help="Comma-separated worker thread counts; 0 = auto.")
    parser.add_argument("--steps", type=int, default=100, help="Measured batch steps per repeat.")
    parser.add_argument("--warmup", type=int, default=10, help="Unmeasured batch steps before measuring.")
    parser.add_argument("--repeats", type=int, default=3, help="Measured repeats per case; the fastest is reported.")
    parser.add_argument("--dt", type=float, default=0.05, help="World time step in seconds.")
    parser.add_argument("--unit-type", default="F-16C_Block50", help="Unit database type name to spawn.")
    parser.add_argument(
        "--database",
        default=resolve_repo_path("examples", "config", "database"),
        help="Unit database directory.",
    )
    parser.add_argument(
        "--system-timing",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Add one extra instrumented repeat per case and report per-system Flecs time shares.",
    )
    parser.add_argument("--top-systems", type=int, default=12, help="Systems listed per case with --system-timing.")
    parser.add_argument("--baseline", default="", help="Earlier JSON output of this benchmark to compare against.")
    parser.add_argument(
        "--max-regression",
        type=float,
        default=None,
        help="Fail (exit 2) when any compared case loses more than this fraction of throughput, e.g. 0.10.",
    )
    parser.add_argument("--label", default="", help="Free-form label recorded in the output (e.g. a commit).")
    parser.add_argument("--sim-log-level", default="warn", help="Native simulation log level.")
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    worlds_list = _parse_int_list(args.worlds, name="worlds", minimum=1)
    units_list = _parse_int_list(args.units, name="units", minimum=0)
    threads_list = _parse_int_list(args.threads, name="threads", minimum=0)
    repeats = max(1, int(args.repeats)) + (1 if args.system_timing else 0)

    cases = []
    print("Native World Batch Step Benchmark")
    print("=" * 33)
    print(
        f"{'worlds':>6} {'units':>5} {'thr':>4} {'ms/batch':>9} {'world-steps/s':>13} "
        f"{'cpu/wall':>8} {'cpu util':>8} {'pool occ':>8}"
    )
    for worlds in worlds_list:
        for units in units_list:
            for threads in threads_list:
                case = _run_case(
                    worlds=worlds,
                    units=units,
                    threads=threads,
                    steps=max(1, int(args.steps)),
                    warmup=int(args.warmup),
                    repeats=repeats,
                    dt=float(args.dt),
                    type_name=str(args.unit_type),
                    database=str(args.database),
                    system_timing=bool(args.system_timing),
                    top_systems=int(args.top_systems),
                )
                cases.append(case)
                print(
                    f"{case['worlds']:6d} {case['units_per_world']:5d} {case['effective_threads']:4d} "
                    f"{case['ms_per_batch_step']:9.3f} {case['world_steps_per_s']:13.1f} "
                    f"{case['process_cpu_per_wall']:8.2f} {100.0 * case['process_cpu_utilization']:7.1f}% "
                    + (
                        f"{100.0 * case['pool_occupancy']:7.1f}%"
                        if case["pool_occupancy"] is not None
                        else f"{'n/a':>8}"
                    )
                )
                for system in case.get("system_timing", {}).get("systems", [])[:5]:
                    print(f"{'':>26}{100.0 * system['share']:5.1f}%  {system['name']}")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "label": str(args.label),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python": platform.python_version(),
        },
        "unit_type": str(args.unit_type),
        "dt": float(args.dt),
        "cases": cases,
    }

    exit_code = 0
    if args.baseline:
        baseline = load_json_config(str(args.baseline))
        if baseline.get("schema") != SCHEMA:
            raise ValueError(f"baseline {args.baseline!r} is not a {SCHEMA} document")
        comparison = _compare(cases, baseline)
        payload["baseline"] = {"path": str(args.baseline), "label": baseline.get("label", "")}
        payload["comparison"] = comparison
        print()
        print(f"vs baseline {baseline.get('label', '') or args.baseline}")
        for row in comparison:
            print(
                f"{row['worlds']:6d} {row['units_per_world']:5d} {row['configured_threads']:4d} "
                f"speedup x{row['speedup']:.2f}  ({row['baseline_world_steps_per_s']:.1f} -> "
                f"{row['world_steps_per_s']:.1f} world-steps/s)"
            )
        if args.max_regression is not None:
            floor = 1.0 - float(args.max_regression)
            regressions = [row for row in comparison if row["speedup"] < floor]
            payload["regressions"] = regressions
            if regressions:
                print(f"REGRESSION: {len(regressions)} case(s) below x{floor:.2f} of baseline throughput")
                exit_code = 2

    write_json_output(str(args.json_out), payload)
    if args.json_out:
        print(f"wrote {os.path.abspath(str(args.json_out))}")
    else:
        print(json.dumps({"schema": SCHEMA, "case_count": len(cases)}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
