from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

if __package__:
    from . import cuda_resident_cr2_resource_schema as _schema
    from . import cuda_resident_cr2_resource_static as _static
else:
    import cuda_resident_cr2_resource_schema as _schema  # type: ignore[no-redef]
    import cuda_resident_cr2_resource_static as _static  # type: ignore[no-redef]

# Retained public aliases: the counter chain and the architecture tests import
# these names from this module.
ACHIEVED_FIELDS = _schema.ACHIEVED_FIELDS
LAUNCH_SEQUENCE = _schema.LAUNCH_SEQUENCE
PROFILE = _schema.PROFILE
PROFILE_V2 = _schema.PROFILE_V2
PROFILE_V3 = _schema.PROFILE_V3
PROFILE_V4 = _schema.PROFILE_V4
REPORT_KEYS = _schema.REPORT_KEYS
SCHEMA = _schema.SCHEMA
SCHEMA_V2 = _schema.SCHEMA_V2
SCHEMA_V3 = _schema.SCHEMA_V3
SCHEMA_V4 = _schema.SCHEMA_V4
_expected_api_counts = _schema.expected_api_counts
_expected_transfers = _schema.expected_transfers
_validate_report = _schema.validate_report
EvidenceError = _static.EvidenceError
KERNELS = _static.KERNELS
_kernel_catalog = _static.kernel_catalog
_kernel_id = _static.kernel_id
_launch_sequence = _static.launch_sequence
parse_cuobjdump_resources = _static.parse_cuobjdump_resources
parse_ptxas = _static.parse_ptxas
parse_sass = _static.parse_sass
_require = _static.require


PROBE_SCHEMA = "cuda_resident.cr2.resource_capture_probe.v1"
PROBE_SCHEMA_V2 = "cuda_resident.cp.resource_capture_probe.v2"
PROBE_SCHEMA_V3 = "cuda_resident.cp.resource_capture_probe.v3"
PROBE_SCHEMA_V4 = "cuda_resident.cp.resource_capture_probe.v4"
_PROBE_SCHEMA_BY_VERSION = {
    1: PROBE_SCHEMA,
    2: PROBE_SCHEMA_V2,
    3: PROBE_SCHEMA_V3,
    4: PROBE_SCHEMA_V4,
}

# Keys a v2 probe adds on top of the v1 set. They record the cross-generation
# link (which schema it supersedes, whether the workload digest still matches
# the frozen capture) and the semantic catalog it was captured against, plus an
# explicit statement that this is a static capture carrying no achieved counters.
PROBE_KEYS_V2_ADDITIONS = {
    "achieved_counters_present",
    "expected_launch_sequence",
    "kernel_id_migration",
    "supersedes_schema_version",
    "trace_signature_matches_v1",
}
# A v3 probe records the CP-5 fold instead of the 1:1 rename map: a fusion is
# not a relabel and must not be reported through the migration key. A v4 probe
# records the CP-7b launch absorption: the kernel set is unchanged, so neither
# a migration nor a kernel fold applies.
PROBE_KEYS_V3_ADDITIONS = (PROBE_KEYS_V2_ADDITIONS - {"kernel_id_migration"}) | {"kernel_id_fold"}
PROBE_KEYS_V4_ADDITIONS = (PROBE_KEYS_V3_ADDITIONS - {"kernel_id_fold"}) | {"launch_absorption"}
PROBE_KEYS = {
    "backend_id",
    "blocks",
    "build_config",
    "capture",
    "cuda_architecture",
    "cuda_environment",
    "maintained_claim_allowed",
    "profile_id",
    "promotion_allowed",
    "public_support_enabled",
    "result",
    "runtime_kernel_resources",
    "schema_version",
    "threads_per_block",
    "trace_signature_algorithm",
    "trace_signature_bytes",
    "trace_signature_digest",
    "tuning_authorized",
    "window_count",
    "world_count",
}
_PROBE_KEYS_BY_VERSION = {
    1: PROBE_KEYS,
    2: PROBE_KEYS | PROBE_KEYS_V2_ADDITIONS,
    3: PROBE_KEYS | PROBE_KEYS_V3_ADDITIONS,
    4: PROBE_KEYS | PROBE_KEYS_V4_ADDITIONS,
}
_PROFILE_BY_VERSION = {1: PROFILE, 2: PROFILE_V2, 3: PROFILE_V3, 4: PROFILE_V4}
_SCHEMA_BY_VERSION = {1: SCHEMA, 2: SCHEMA_V2, 3: SCHEMA_V3, 4: SCHEMA_V4}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_probe(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    _require(isinstance(value, dict), "probe root must be an object")
    # A probe is checked against the generation it declares. v1 keeps its exact
    # frozen key set; v2 adds the cross-generation link fields and is otherwise
    # identical, so the workload invariants below apply unchanged to both.
    declared = value.get("schema_version")
    version = next(
        (
            candidate
            for candidate, schema in _PROBE_SCHEMA_BY_VERSION.items()
            if declared == schema
        ),
        None,
    )
    _require(version is not None, f"probe schema is not a known generation: {declared!r}")
    expected_keys = _PROBE_KEYS_BY_VERSION[version]
    _require(set(value) == expected_keys, "probe top-level keys do not match the frozen schema")
    _require(value["schema_version"] == _PROBE_SCHEMA_BY_VERSION[version], "probe schema mismatch")
    _require(value["profile_id"] == _PROFILE_BY_VERSION[version], "probe profile mismatch")
    if version > 1:
        _require(
            value["supersedes_schema_version"] == _PROBE_SCHEMA_BY_VERSION[version - 1],
            "probe must declare the schema it supersedes",
        )
        # A recapture is only comparable to the frozen evidence if it measured
        # the same workload, and it must never masquerade as a counter capture.
        _require(value["trace_signature_matches_v1"] is True, "v2 probe workload diverged")
        _require(
            value["achieved_counters_present"] is False,
            "a static capture must not claim achieved counters",
        )
    _require(value["build_config"] == "Release", "probe must be a Release build")
    _require(value["cuda_architecture"] == "sm_86", "probe must target sm_86")
    _require(value["world_count"] == 256, "probe must contain 256 worlds")
    _require(value["window_count"] == 1, "probe must contain exactly one window")
    _require(value["threads_per_block"] == 128, "probe block size mismatch")
    _require(value["blocks"] == 2, "probe grid size mismatch")
    _require(value["backend_id"] == "cuda_resident.rb7_phase_d", "probe backend mismatch")
    _require(value["trace_signature_algorithm"] == "fnv1a64", "trace digest mismatch")
    _require(value["trace_signature_bytes"] == 80469, "trace signature length mismatch")
    _require(value["trace_signature_digest"] == "cb31675ee34e5015", "trace drift")
    for flag in (
        "maintained_claim_allowed",
        "public_support_enabled",
        "promotion_allowed",
        "tuning_authorized",
    ):
        _require(value[flag] is False, f"probe must keep {flag}=false")
    capture = value["capture"]
    _require(isinstance(capture, dict), "probe capture must be an object")
    _require(
        set(capture)
        == {
            "range",
            "setup_outside",
            "resource_queries_outside",
            "public_export_inside",
            "device_consumer_inside",
            "diagnostic_materialization_inside",
            "operation_sequence",
        },
        "probe capture keys do not match the frozen schema",
    )
    _require(capture.get("range") == "cudaProfilerApi", "capture range mismatch")
    _require(capture.get("setup_outside") is True, "setup must stay outside capture")
    _require(capture.get("resource_queries_outside") is True, "resource query placement drift")
    _require(capture.get("public_export_inside") is True, "public export is missing")
    _require(capture.get("device_consumer_inside") is True, "device consumer is missing")
    _require(
        capture.get("diagnostic_materialization_inside") is False,
        "diagnostic materialization entered capture",
    )
    _require(
        capture.get("operation_sequence")
        == [
            "inject",
            "evaluate_empty",
            "advance_world_batch",
            "public_export",
            "acquire_device_lease",
            "consumer_submit",
            "consumer_event_await",
        ],
        "probe operation sequence drifted",
    )
    result = value["result"]
    _require(isinstance(result, dict), "probe result must be an object")
    _require(
        set(result)
        == {
            "agent_observation_count",
            "instrument_state_count",
            "consumer_world_count",
            "consumer_await_completed",
            "diagnostic_materialization_called",
        },
        "probe result keys do not match the frozen schema",
    )
    _require(result.get("diagnostic_materialization_called") is False, "diagnostic D2H ran")
    _require(result.get("agent_observation_count") == 256, "observation count mismatch")
    _require(result.get("instrument_state_count") == 256, "instrument count mismatch")
    _require(result.get("consumer_world_count") == 256, "consumer count mismatch")
    _require(result.get("consumer_await_completed") is True, "consumer wait is incomplete")
    environment = value["cuda_environment"]
    _require(isinstance(environment, dict), "CUDA environment must be an object")
    _require(
        set(environment)
        == {
            "device_ordinal",
            "device_name",
            "compute_capability",
            "driver_version",
            "runtime_version",
        },
        "CUDA environment keys do not match the frozen schema",
    )
    _require(environment["device_ordinal"] == 0, "CUDA device ordinal drifted")
    _require(environment["compute_capability"] == "8.6", "CUDA capability drifted")
    _require(bool(environment["device_name"]), "CUDA device name is empty")
    _require(environment["driver_version"] > 0, "CUDA driver version is invalid")
    _require(environment["runtime_version"] > 0, "CUDA runtime version is invalid")
    return value


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def parse_nsys(path: Path, schema_version: int = 1) -> dict[str, Any]:
    catalog = _kernel_catalog(schema_version)
    expected_launches = _launch_sequence(schema_version)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        kernel_columns = {
            "start",
            "end",
            "demangledName",
            "registersPerThread",
            "gridX",
            "gridY",
            "gridZ",
            "blockX",
            "blockY",
            "blockZ",
            "staticSharedMemory",
            "dynamicSharedMemory",
            "localMemoryPerThread",
        }
        _require(
            kernel_columns <= _table_columns(connection, "CUPTI_ACTIVITY_KIND_KERNEL"),
            "Nsight kernel table schema is incomplete",
        )
        rows = list(
            connection.execute(
                """
                SELECT k.start, k.end, s.value, k.registersPerThread,
                       k.gridX, k.gridY, k.gridZ, k.blockX, k.blockY, k.blockZ,
                       k.staticSharedMemory, k.dynamicSharedMemory, k.localMemoryPerThread
                  FROM CUPTI_ACTIVITY_KIND_KERNEL AS k
                  JOIN StringIds AS s ON s.id = k.demangledName
              ORDER BY k.start
                """
            )
        )
        _require(
            len(rows) == len(expected_launches),
            f"Nsight launch count is not exactly {len(expected_launches)}",
        )
        launches: list[dict[str, Any]] = []
        symbols_by_kernel: dict[str, set[str]] = {}
        for index, (row, expected) in enumerate(zip(rows, expected_launches, strict=True)):
            symbol = str(row[2])
            kernel_id = _kernel_id(symbol, schema_version)
            _require(kernel_id == expected[0], f"Nsight launch order drift at index {index}")
            _require(tuple(row[4:7]) == (2, 1, 1), f"Nsight grid drift at index {index}")
            _require(tuple(row[7:10]) == (128, 1, 1), f"Nsight block drift at index {index}")
            _require(row[10] == 0 and row[11] == 0, f"unexpected shared memory at index {index}")
            symbols_by_kernel.setdefault(kernel_id, set()).add(symbol)
            launches.append(
                {
                    "launch_index": index,
                    "kernel_id": kernel_id,
                    "semantic_stage": expected[1],
                    "grid": [int(value) for value in row[4:7]],
                    "block": [int(value) for value in row[7:10]],
                    "registers_per_thread_metadata": int(row[3]),
                    "static_shared_bytes_metadata": int(row[10]),
                    "dynamic_shared_bytes_metadata": int(row[11]),
                    "local_bytes_per_thread_metadata": int(row[12]),
                }
            )
        for spec in catalog:
            _require(
                len(symbols_by_kernel.get(spec.kernel_id, set())) == 1,
                f"Nsight exact symbol drift for {spec.kernel_id}",
            )
        raw_symbols = {symbol for values in symbols_by_kernel.values() for symbol in values}
        _require(
            len(raw_symbols) == len(catalog),
            f"Nsight raw unique kernel count is not {len(catalog)}",
        )
        symbol_inventory = [
            {
                "kernel_id": spec.kernel_id,
                "demangled_symbol_sha256": hashlib.sha256(
                    next(iter(symbols_by_kernel[spec.kernel_id])).encode("utf-8")
                ).hexdigest(),
            }
            for spec in catalog
        ]
        api_counts: dict[str, int] = {}
        for name, count in connection.execute(
            """
            SELECT s.value, COUNT(*)
              FROM CUPTI_ACTIVITY_KIND_RUNTIME AS r
              JOIN StringIds AS s ON s.id = r.nameId
          GROUP BY s.value
            """
        ):
            base_name = str(name).split("_v", 1)[0]
            api_counts[base_name] = api_counts.get(base_name, 0) + int(count)
        expected_api = _expected_api_counts(schema_version)
        for name, count in expected_api.items():
            _require(api_counts.get(name, 0) == count, f"Nsight API count mismatch for {name}")
        copies = list(
            connection.execute("SELECT srcKind, dstKind, bytes FROM CUPTI_ACTIVITY_KIND_MEMCPY")
        )
        kinds_by_name = {
            "host_to_device": (0, 2),
            "device_to_host": (2, 0),
            "device_to_device": (2, 2),
        }
        transfers: dict[str, dict[str, int]] = {}
        for name, kinds in kinds_by_name.items():
            expected_count = _expected_transfers(schema_version)[name]["copy_count"]
            selected = [int(row[2]) for row in copies if tuple(row[:2]) == kinds]
            _require(len(selected) == expected_count, f"Nsight transfer count mismatch for {name}")
            transfers[name] = {"copy_count": len(selected), "bytes": sum(selected)}
        synchronization_rows = connection.execute(
            "SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION"
        ).fetchone()
        _require(synchronization_rows is not None, "Nsight synchronization table is missing")
        return {
            "launches": launches,
            "unique_kernel_count": len(raw_symbols),
            "kernel_symbols": symbol_inventory,
            "api_counts": {name: api_counts.get(name, 0) for name in sorted(expected_api)},
            "synchronization_activity_rows": int(synchronization_rows[0]),
            "transfers": transfers,
        }
    finally:
        connection.close()


def _runtime_resources(probe: dict[str, Any], schema_version: int = 1) -> dict[str, dict[str, Any]]:
    rows = probe["runtime_kernel_resources"]
    _require(isinstance(rows, list), "runtime resource inventory must be an array")
    parsed: dict[str, dict[str, Any]] = {}
    required = {
        "kernel_id",
        "registers_per_thread",
        "local_bytes_per_thread",
        "static_shared_bytes",
        "threads_per_block",
        "active_blocks_per_multiprocessor",
        "active_warps_per_multiprocessor",
        "theoretical_occupancy",
    }
    if schema_version >= 2:
        # v2 rows carry the mangled-symbol fragment the row was matched by, so a
        # reader can tie a kernel_id back to the symbol without re-deriving it
        # from the catalog. It is provenance, not a measurement.
        required = required | {"symbol_fragment"}
    for row in rows:
        _require(isinstance(row, dict) and set(row) == required, "runtime resource row drift")
        kernel_id = str(row["kernel_id"])
        _require(kernel_id not in parsed, f"duplicate runtime resource row: {kernel_id}")
        integer_fields = (
            "registers_per_thread",
            "local_bytes_per_thread",
            "static_shared_bytes",
            "threads_per_block",
            "active_blocks_per_multiprocessor",
            "active_warps_per_multiprocessor",
        )
        _require(
            all(
                isinstance(row[field], int) and not isinstance(row[field], bool)
                for field in integer_fields
            ),
            f"runtime integer resource is invalid for {kernel_id}",
        )
        _require(row["registers_per_thread"] > 0, f"runtime registers are invalid for {kernel_id}")
        _require(
            row["local_bytes_per_thread"] >= 0, f"runtime local bytes are invalid for {kernel_id}"
        )
        _require(
            row["static_shared_bytes"] >= 0, f"runtime shared bytes are invalid for {kernel_id}"
        )
        _require(row["threads_per_block"] == 128, f"runtime block size drift for {kernel_id}")
        blocks = row["active_blocks_per_multiprocessor"]
        warps = row["active_warps_per_multiprocessor"]
        occupancy = row["theoretical_occupancy"]
        _require(
            blocks > 0 and warps == blocks * 4,
            f"runtime active warp relation drift for {kernel_id}",
        )
        _require(
            isinstance(occupancy, (int, float))
            and not isinstance(occupancy, bool)
            and math.isfinite(occupancy)
            and 0.0 < occupancy <= 1.0
            and math.isclose(occupancy, blocks / 12.0, rel_tol=1e-12, abs_tol=1e-12),
            f"runtime theoretical occupancy is invalid for {kernel_id}",
        )
        parsed[kernel_id] = row
    _require(
        set(parsed) == {spec.kernel_id for spec in _kernel_catalog(schema_version)},
        "runtime kernel set incomplete",
    )
    return parsed


def combine_resources(
    probe: dict[str, Any],
    ptxas: dict[str, dict[str, int]],
    cubin: dict[str, dict[str, int]],
    sass: dict[str, dict[str, int]],
    launches: list[dict[str, Any]],
    schema_version: int = 1,
) -> list[dict[str, Any]]:
    runtime = _runtime_resources(probe, schema_version)
    result: list[dict[str, Any]] = []
    for spec in _kernel_catalog(schema_version):
        kernel_id = spec.kernel_id
        compiled = ptxas[kernel_id]
        runtime_row = runtime[kernel_id]
        cubin_row = cubin[kernel_id]
        _require(
            compiled["registers_per_thread"]
            == runtime_row["registers_per_thread"]
            == cubin_row["registers_per_thread"],
            f"static register sources disagree for {kernel_id}",
        )
        _require(
            compiled["stack_frame_bytes"]
            == runtime_row["local_bytes_per_thread"]
            == cubin_row["stack_frame_bytes"],
            f"stack/local static sources disagree for {kernel_id}",
        )
        _require(
            runtime_row["static_shared_bytes"] == cubin_row["static_shared_bytes"],
            f"static shared sources disagree for {kernel_id}",
        )
        launch_rows = [row for row in launches if row["kernel_id"] == kernel_id]
        _require(len(launch_rows) == spec.launch_count, f"launch cardinality drift for {kernel_id}")
        result.append(
            {
                "kernel_id": kernel_id,
                "symbol_fragment": spec.symbol_fragment,
                "launch_instance_count": len(launch_rows),
                "registers_per_thread": compiled["registers_per_thread"],
                "register_sources_agree": True,
                "nsys_register_metadata_values": sorted(
                    {row["registers_per_thread_metadata"] for row in launch_rows}
                ),
                "stack_frame_bytes": compiled["stack_frame_bytes"],
                "runtime_local_bytes_per_thread": runtime_row["local_bytes_per_thread"],
                "cuobjdump_local_bytes": cubin_row["local_bytes"],
                "compiler_spill_store_bytes": compiled["spill_store_bytes"],
                "compiler_spill_load_bytes": compiled["spill_load_bytes"],
                "sass_ldl_instruction_count": sass[kernel_id]["ldl_instruction_count"],
                "sass_stl_instruction_count": sass[kernel_id]["stl_instruction_count"],
                "static_shared_bytes": runtime_row["static_shared_bytes"],
                "active_blocks_per_multiprocessor": runtime_row["active_blocks_per_multiprocessor"],
                "active_warps_per_multiprocessor": runtime_row["active_warps_per_multiprocessor"],
                "theoretical_occupancy": runtime_row["theoretical_occupancy"],
                "nsys_local_bytes_metadata_values": sorted(
                    {row["local_bytes_per_thread_metadata"] for row in launch_rows}
                ),
            }
        )
    return result


def _run_cuobjdump(tool: Path, binary: Path, option: str) -> str:
    completed = subprocess.run(
        [str(tool), option, str(binary)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout + completed.stderr


def _git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path.resolve().parent,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def validate_report(report: dict[str, Any]) -> None:
    _validate_report(report)


def probe_generation(probe: dict[str, Any]) -> int:
    """Return the catalog generation a validated probe belongs to.

    The static parsers match mangled symbols against a per-generation kernel
    catalog, so they need the same generation the probe declared. Deriving it
    here keeps `load_probe` as the single place that maps a schema string to a
    generation number.
    """
    declared = probe.get("schema_version")
    version = next(
        (
            candidate
            for candidate, schema in _PROBE_SCHEMA_BY_VERSION.items()
            if declared == schema
        ),
        None,
    )
    _require(version is not None, f"probe schema is not a known generation: {declared!r}")
    return version


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    _require(
        args.baseline_commit == _git_head(args.probe_source),
        "baseline commit does not match the candidate worktree HEAD",
    )
    probe = load_probe(args.probe)
    # The symbol catalog is generation-specific: a v2 capture carries semantic
    # kernel names, so parsing it against the v1 catalog would fail closed on an
    # incomplete kernel set rather than silently mismatching.
    generation = probe_generation(probe)
    ptxas_text = args.ptxas_log.read_text(encoding="utf-8", errors="replace")
    resource_text = _run_cuobjdump(args.cuobjdump, args.binary, "--dump-resource-usage")
    sass_text = _run_cuobjdump(args.cuobjdump, args.binary, "--dump-sass")
    ptxas = parse_ptxas(ptxas_text, generation)
    cubin = parse_cuobjdump_resources(resource_text, generation)
    sass = parse_sass(sass_text, generation)
    nsys = parse_nsys(args.nsys_sqlite, generation)
    resources = combine_resources(probe, ptxas, cubin, sass, nsys["launches"], generation)
    achieved = {field: None for field in ACHIEVED_FIELDS}
    # The report declares the same generation as the probe it was built from, so
    # the schema validator applies that generation's rules: v1 keeps its frozen
    # date/commit pins, v2 accepts its own capture date but must still declare an
    # unpromoted candidate state.
    report = {
        "schema_version": _SCHEMA_BY_VERSION[generation],
        "profile_id": _PROFILE_BY_VERSION[generation],
        "evidence_date": args.evidence_date,
        "source": {
            "baseline_commit": args.baseline_commit,
            "candidate_state": (
                "cr2_5a_unpromoted_worktree" if generation == 1 else "cp_unpromoted_worktree"
            ),
        },
        "inputs": {
            "source_hash_canonicalization": "utf8_lf",
            "probe_sha256": _sha256(args.probe),
            "nsys_sqlite_sha256": _sha256(args.nsys_sqlite),
            "ptxas_build_log_sha256": _sha256(args.ptxas_log),
            "binary_sha256": _sha256(args.binary),
            "probe_source_sha256": source_sha256(args.probe_source),
            "contract_source_sha256": source_sha256(args.contract_source),
            "collector_source_sha256": source_sha256(Path(__file__)),
            "static_parser_source_sha256": source_sha256(
                Path(__file__).with_name("cuda_resident_cr2_resource_static.py")
            ),
            "cuobjdump_resource_output_sha256": hashlib.sha256(
                resource_text.encode("utf-8")
            ).hexdigest(),
            "cuobjdump_sass_output_sha256": hashlib.sha256(sass_text.encode("utf-8")).hexdigest(),
        },
        "toolchain": {
            "build_config": "Release",
            "cuda_architecture": "sm_86",
            "maxrregcount_argument": 0,
            "register_cap": None,
            "maxrregcount_zero_interpretation": "no_cap",
            "nsight_systems_version": args.nsys_version,
        },
        "capture": {
            "range": "cudaProfilerApi",
            "world_count": probe["world_count"],
            "window_count": probe["window_count"],
            "trace_signature_algorithm": probe["trace_signature_algorithm"],
            "trace_signature_digest": probe["trace_signature_digest"],
            "setup_outside": True,
            "public_export_inside": True,
            "device_consumer_inside": True,
            "diagnostic_materialization_inside": False,
        },
        "launch_topology": {
            "source": "nsight_systems_sqlite_cuda_trace",
            "launch_instance_count": len(nsys["launches"]),
            "unique_kernel_count": nsys["unique_kernel_count"],
            "kernel_symbols": nsys["kernel_symbols"],
            "launches": nsys["launches"],
            "cuda_api_counts": nsys["api_counts"],
            "synchronization_activity_rows": nsys["synchronization_activity_rows"],
            "cuda_memcpy_transfers": nsys["transfers"],
        },
        "static_kernel_resources": resources,
        "interpretation": {
            "static_resource_sources_complete": True,
            "launch_topology_complete": True,
            "compiler_spills_are_not_inferred_from_stack_or_sass_local_instructions": True,
            "nsys_local_memory_metadata_is_not_an_achieved_traffic_counter": True,
            "cuda_memcpy_api_bytes_are_not_kernel_global_memory_traffic": True,
            "theoretical_occupancy_is_not_achieved_occupancy": True,
        },
        "achieved_counters": {
            "status": "pending_cr2_5b",
            **achieved,
        },
        "gates": {
            "cr2_5a_static_resource_complete": True,
            "cr2_5a_launch_topology_complete": True,
            "cr2_5_achieved_counter_gate_complete": False,
            "maintained_claim_allowed": False,
            "public_support_enabled": False,
            "promotion_allowed": False,
            "tuning_authorized": False,
        },
    }
    validate_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build fail-closed CR2-5a CUDA resource evidence")
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--nsys-sqlite", type=Path, required=True)
    parser.add_argument("--ptxas-log", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--cuobjdump", type=Path, required=True)
    parser.add_argument("--probe-source", type=Path, required=True)
    parser.add_argument("--contract-source", type=Path, required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--evidence-date", required=True)
    parser.add_argument("--nsys-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _require(re.fullmatch(r"[0-9a-f]{40}", args.baseline_commit) is not None, "invalid commit")
    report = build_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
