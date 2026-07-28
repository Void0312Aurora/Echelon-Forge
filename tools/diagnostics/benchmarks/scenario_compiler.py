#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import time
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path
from tools.diagnostics.common import write_json_output

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.scenario.compiler import ScenarioCompiler  # noqa: E402


DATABASE_PATH = resolve_repo_path("examples", "config", "database")
DEFAULT_INLINE_CONTRACT = resolve_repo_path(
    "tests", "contracts", "env", "landing", "ils_threshold_crossing_height_regression.json"
)


def _load_inline_contract(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    scenario = payload.get("scenario_inline", None)
    if not isinstance(scenario, dict):
        raise ValueError(f"{path} does not contain scenario_inline")
    return scenario


def _write_temp_scenario(scenario: dict[str, Any], *, stem: str) -> str:
    fd, tmp_path = tempfile.mkstemp(prefix=f"{stem}_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(scenario, f, ensure_ascii=True)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return tmp_path


def _legacy_parse_merge(path: str) -> dict[str, Any]:
    project_root = REPO_ROOT
    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)
    imports = scenario.get("imports", None)
    if isinstance(imports, list):
        for imp in imports:
            if not isinstance(imp, dict):
                continue
            rel = imp.get("file")
            if not rel:
                continue
            full_path = os.path.join(project_root, str(rel))
            if not os.path.exists(full_path):
                continue
            with open(full_path, "r", encoding="utf-8") as f:
                prefab = json.load(f)
            if "zones" in prefab:
                if "environment" not in scenario or not isinstance(scenario.get("environment"), dict):
                    scenario["environment"] = {}
                current_zones = scenario["environment"].get("zones", [])
                if not isinstance(current_zones, list):
                    current_zones = []
                current_zones.extend(copy.deepcopy(prefab["zones"]))
                scenario["environment"]["zones"] = current_zones
            if "entities" in prefab:
                current_entities = scenario.get("entities", [])
                if not isinstance(current_entities, list):
                    current_entities = []
                current_entities.extend(copy.deepcopy(prefab["entities"]))
                scenario["entities"] = current_entities
    return scenario


def _time_call(fn, *, iters: int) -> float:
    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        fn()
    elapsed = time.perf_counter() - start
    return 1000.0 * elapsed / max(1, int(iters))


def _make_loader() -> ScenarioLoader:
    sim = ef_py.SimulationKernel()
    sim.load_database(DATABASE_PATH)
    return ScenarioLoader(sim)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 scenario compiler benchmark.")
    parser.add_argument("--scenario", default="", help="Scenario JSON path. If omitted, uses a temp inline contract scenario.")
    parser.add_argument("--iters", type=int, default=64, help="Iterations per timing bucket.")
    parser.add_argument("--seed", type=int, default=0, help="Base seed for loader resets.")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON results.")
    args = parser.parse_args()

    temp_scenario_path = ""
    scenario_path = os.path.abspath(args.scenario) if args.scenario else ""
    if not scenario_path:
        temp_scenario_path = _write_temp_scenario(
            _load_inline_contract(DEFAULT_INLINE_CONTRACT),
            stem="phase2_compiler",
        )
        scenario_path = temp_scenario_path

    try:
        legacy_ms = _time_call(lambda: _legacy_parse_merge(scenario_path), iters=int(args.iters))

        def _compile_cold():
            ScenarioCompiler.clear_cache()
            ScenarioCompiler.compile_path(scenario_path)

        compiled_cold_ms = _time_call(_compile_cold, iters=int(args.iters))

        ScenarioCompiler.clear_cache()
        compiled = ScenarioCompiler.compile_path(scenario_path)
        compiled_warm_ms = _time_call(lambda: ScenarioCompiler.compile_path(scenario_path), iters=int(args.iters))
        instantiate_ms = _time_call(lambda: compiled.instantiate(), iters=int(args.iters))
        instantiate_runtime_ms = _time_call(lambda: compiled.instantiate_runtime(), iters=int(args.iters))

        loader = _make_loader()
        seed_counter = {"value": int(args.seed)}

        def _load_compiled():
            seed_counter["value"] += 1
            loader.load_compiled_scenario(compiled, seed=seed_counter["value"])

        load_compiled_ms = _time_call(_load_compiled, iters=max(8, int(args.iters) // 4))

        results = {
            "scenario": scenario_path,
            "iters": int(args.iters),
            "legacy_parse_merge_ms": float(legacy_ms),
            "compiled_cold_ms": float(compiled_cold_ms),
            "compiled_warm_ms": float(compiled_warm_ms),
            "instantiate_ms": float(instantiate_ms),
            "instantiate_runtime_ms": float(instantiate_runtime_ms),
            "load_compiled_ms": float(load_compiled_ms),
            "warm_speedup_vs_legacy": float(legacy_ms / max(compiled_warm_ms, 1.0e-12)),
            "instantiate_speedup_vs_legacy": float(legacy_ms / max(instantiate_ms, 1.0e-12)),
            "instantiate_runtime_speedup_vs_full": float(instantiate_ms / max(instantiate_runtime_ms, 1.0e-12)),
            "compiled_summary": {
                "source_path": compiled.source_path,
                "scenario_name": compiled.scenario_name,
                "zone_count": int(compiled.zone_count),
                "entity_count": int(compiled.entity_count),
                "import_count": int(len(compiled.imported_files)),
            },
        }

        print("Scenario Compiler Phase 2 Benchmark")
        print("=" * 36)
        print(f"legacy parse+merge : {results['legacy_parse_merge_ms']:.4f} ms")
        print(f"compiled cold      : {results['compiled_cold_ms']:.4f} ms")
        print(f"compiled warm      : {results['compiled_warm_ms']:.4f} ms")
        print(f"instantiate        : {results['instantiate_ms']:.4f} ms")
        print(f"instantiate runtime: {results['instantiate_runtime_ms']:.4f} ms")
        print(f"load_compiled      : {results['load_compiled_ms']:.4f} ms")
        print(f"warm speedup       : {results['warm_speedup_vs_legacy']:.2f}x")
        print(f"instantiate speedup: {results['instantiate_speedup_vs_legacy']:.2f}x")
        print(f"runtime/full inst  : {results['instantiate_runtime_speedup_vs_full']:.2f}x")

        write_json_output(str(args.json_out), results)
        return 0
    finally:
        if temp_scenario_path:
            try:
                os.unlink(temp_scenario_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
