from __future__ import annotations

import math
import re
from typing import Any

if __package__:
    from .cuda_resident_cr2_json_types import StrictJson
    from .cuda_resident_cr2_resource_static import KERNELS, kernel_catalog, launch_sequence, require
else:
    from cuda_resident_cr2_json_types import StrictJson  # type: ignore[no-redef]
    from cuda_resident_cr2_resource_static import (  # type: ignore[no-redef]
        KERNELS,
        kernel_catalog,
        launch_sequence,
        require,
    )


SCHEMA = "cuda_resident.cr2.kernel_resource_evidence.v1"
PROFILE = "cr2.resource.steady_full_window_body.sm86.v1"
BASELINE_COMMIT = "08b48f299484428e7297f328ca860f8fadc31cc4"
EVIDENCE_DATE = "2026-08-04"

# v2 identity for the recapture against the semantic kernel catalog. v1 above
# stays frozen: the retained static-capture evidence hashes against it.
SCHEMA_V2 = "cuda_resident.cp.kernel_resource_evidence.v2"
PROFILE_V2 = "cp.resource.steady_full_window_body.sm86.v2"

_IDENTITY_BY_VERSION = {
    1: (SCHEMA, PROFILE),
    2: (SCHEMA_V2, PROFILE_V2),
}


def schema_version_of(report: dict[str, Any]) -> int:
    """Which capture generation a report claims to be.

    Reports are validated against the identity they declare rather than against
    a single hard-coded generation, so a v2 capture is not rejected merely for
    being newer than the frozen v1 evidence.
    """
    declared = report.get("schema_version")
    for version, (schema, _) in _IDENTITY_BY_VERSION.items():
        if declared == schema:
            return version
    raise_message = f"resource evidence schema is not a known generation: {declared!r}"
    require(False, raise_message)
    raise AssertionError(raise_message)  # pragma: no cover - require() always raises


# The launch sequence is derived from the C++ contract rather than duplicated
# here, for the same reason the kernel catalog is: a second copy is what let the
# semantic rename go unnoticed.
LAUNCH_SEQUENCE = launch_sequence(1)
ACHIEVED_FIELDS = (
    "achieved_occupancy",
    "branch_divergence",
    "global_memory_traffic",
    "local_memory_traffic",
    "shared_memory_traffic",
)
REPORT_KEYS = {
    "schema_version",
    "profile_id",
    "evidence_date",
    "source",
    "inputs",
    "toolchain",
    "capture",
    "launch_topology",
    "static_kernel_resources",
    "interpretation",
    "achieved_counters",
    "gates",
}
SOURCE_KEYS = {"baseline_commit", "candidate_state"}
INPUT_KEYS = {
    "binary_sha256",
    "collector_source_sha256",
    "contract_source_sha256",
    "cuobjdump_resource_output_sha256",
    "cuobjdump_sass_output_sha256",
    "nsys_sqlite_sha256",
    "probe_sha256",
    "probe_source_sha256",
    "ptxas_build_log_sha256",
    "source_hash_canonicalization",
    "static_parser_source_sha256",
}
TOOLCHAIN_KEYS = {
    "build_config",
    "cuda_architecture",
    "maxrregcount_argument",
    "maxrregcount_zero_interpretation",
    "nsight_systems_version",
    "register_cap",
}
CAPTURE_KEYS = {
    "device_consumer_inside",
    "diagnostic_materialization_inside",
    "public_export_inside",
    "range",
    "setup_outside",
    "trace_signature_algorithm",
    "trace_signature_digest",
    "window_count",
    "world_count",
}
TOPOLOGY_KEYS = {
    "cuda_api_counts",
    "cuda_memcpy_transfers",
    "kernel_symbols",
    "launch_instance_count",
    "launches",
    "source",
    "synchronization_activity_rows",
    "unique_kernel_count",
}
LAUNCH_KEYS = {
    "block",
    "dynamic_shared_bytes_metadata",
    "grid",
    "kernel_id",
    "launch_index",
    "local_bytes_per_thread_metadata",
    "registers_per_thread_metadata",
    "semantic_stage",
    "static_shared_bytes_metadata",
}
STATIC_RESOURCE_KEYS = {
    "active_blocks_per_multiprocessor",
    "active_warps_per_multiprocessor",
    "compiler_spill_load_bytes",
    "compiler_spill_store_bytes",
    "cuobjdump_local_bytes",
    "kernel_id",
    "launch_instance_count",
    "nsys_local_bytes_metadata_values",
    "nsys_register_metadata_values",
    "register_sources_agree",
    "registers_per_thread",
    "runtime_local_bytes_per_thread",
    "sass_ldl_instruction_count",
    "sass_stl_instruction_count",
    "stack_frame_bytes",
    "static_shared_bytes",
    "symbol_fragment",
    "theoretical_occupancy",
}
EXPECTED_API_COUNTS = {
    "cudaDeviceSynchronize": 5,
    "cudaEventCreateWithFlags": 2,
    "cudaEventRecord": 2,
    "cudaEventSynchronize": 1,
    "cudaFree": 0,
    "cudaLaunchKernel": 12,
    "cudaMalloc": 4,
    "cudaMemcpy": 13,
    "cudaMemset": 5,
    "cudaProfilerStart": 1,
    "cudaStreamWaitEvent": 1,
}
EXPECTED_TRANSFERS = {
    "device_to_device": {"bytes": 677376, "copy_count": 3},
    "device_to_host": {"bytes": 229908, "copy_count": 7},
    "host_to_device": {"bytes": 14080, "copy_count": 3},
}
INTERPRETATION_KEYS = {
    "compiler_spills_are_not_inferred_from_stack_or_sass_local_instructions",
    "cuda_memcpy_api_bytes_are_not_kernel_global_memory_traffic",
    "launch_topology_complete",
    "nsys_local_memory_metadata_is_not_an_achieved_traffic_counter",
    "static_resource_sources_complete",
    "theoretical_occupancy_is_not_achieved_occupancy",
}
GATE_KEYS = {
    "cr2_5_achieved_counter_gate_complete",
    "cr2_5a_launch_topology_complete",
    "cr2_5a_static_resource_complete",
    "maintained_claim_allowed",
    "promotion_allowed",
    "public_support_enabled",
    "tuning_authorized",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")
_STRICT = StrictJson(require)
_object = _STRICT.object
_list = _STRICT.list
_nonnegative_integer = _STRICT.nonnegative_integer
_positive_integer = _STRICT.positive_integer
_exact_integer = _STRICT.exact_integer
_exact_integer_list = _STRICT.exact_integer_list
_exact_integer_map = _STRICT.exact_integer_map


def _validate_transfer_map(value: Any) -> None:
    transfers = _object(value, set(EXPECTED_TRANSFERS), "CUDA copy inventory")
    for direction, expected in EXPECTED_TRANSFERS.items():
        _exact_integer_map(transfers[direction], expected, f"CUDA copy inventory.{direction}")


def _validate_source_and_inputs(report: dict[str, Any], version: int = 1) -> None:
    source = _object(report["source"], SOURCE_KEYS, "resource evidence source")
    if version == 1:
        require(source["baseline_commit"] == BASELINE_COMMIT, "resource baseline commit drifted")
        require(
            source["candidate_state"] == "cr2_5a_unpromoted_worktree",
            "resource candidate state drifted",
        )
    else:
        # A v2 capture records its own baseline commit. What must not drift is
        # that the candidate is still unpromoted -- a recapture grants no
        # authority, so the state must continue to say so.
        require(
            isinstance(source["baseline_commit"], str)
            and re.fullmatch(r"[0-9a-f]{40}", source["baseline_commit"]) is not None,
            "resource baseline commit is not a full commit id",
        )
        require(
            isinstance(source["candidate_state"], str)
            and source["candidate_state"].endswith("_unpromoted_worktree"),
            "resource candidate state must remain unpromoted",
        )

    inputs = _object(report["inputs"], INPUT_KEYS, "resource evidence inputs")
    require(inputs["source_hash_canonicalization"] == "utf8_lf", "source hash mode drifted")
    for key in INPUT_KEYS - {"source_hash_canonicalization"}:
        value = inputs[key]
        require(
            isinstance(value, str) and _SHA256.fullmatch(value) is not None,
            f"resource input {key} is not a SHA-256 digest",
        )


def _validate_toolchain_and_capture(report: dict[str, Any]) -> None:
    toolchain = _object(report["toolchain"], TOOLCHAIN_KEYS, "resource toolchain")
    require(toolchain["build_config"] == "Release", "resource build config drifted")
    require(toolchain["cuda_architecture"] == "sm_86", "resource architecture drifted")
    _exact_integer(toolchain["maxrregcount_argument"], 0, "resource register argument")
    require(toolchain["register_cap"] is None, "resource register cap must remain absent")
    require(
        toolchain["maxrregcount_zero_interpretation"] == "no_cap",
        "resource no-cap interpretation drifted",
    )
    require(
        toolchain["nsight_systems_version"] == "2025.3.2",
        "resource Nsight Systems version drifted",
    )

    capture = _object(report["capture"], CAPTURE_KEYS, "resource capture")
    require(capture["range"] == "cudaProfilerApi", "resource capture range drifted")
    _exact_integer(capture["world_count"], 256, "resource capture world count")
    _exact_integer(capture["window_count"], 1, "resource capture window count")
    require(capture["trace_signature_algorithm"] == "fnv1a64", "trace algorithm drifted")
    require(capture["trace_signature_digest"] == "cb31675ee34e5015", "trace digest drifted")
    for key in ("setup_outside", "public_export_inside", "device_consumer_inside"):
        require(capture[key] is True, f"resource capture must keep {key}=true")
    require(
        capture["diagnostic_materialization_inside"] is False,
        "diagnostic materialization entered the captured range",
    )


def _validate_launch_topology(
    report: dict[str, Any], version: int = 1
) -> tuple[dict[str, Any], list[Any]]:
    kernels = kernel_catalog(version)
    sequence = launch_sequence(version)
    topology = _object(report["launch_topology"], TOPOLOGY_KEYS, "launch topology")
    require(topology["source"] == "nsight_systems_sqlite_cuda_trace", "topology source drifted")
    launches = _list(topology["launches"], "launch inventory")
    require(len(launches) == len(sequence), "launch inventory cardinality drifted")
    _exact_integer(topology["launch_instance_count"], len(launches), "launch instance count")

    for index, (row_value, expected) in enumerate(zip(launches, sequence, strict=True)):
        row = _object(row_value, LAUNCH_KEYS, f"launch row {index}")
        _exact_integer(row["launch_index"], index, f"launch index at row {index}")
        require(
            (row["kernel_id"], row["semantic_stage"]) == expected,
            f"launch sequence drifted at row {index}",
        )
        _exact_integer_list(row["grid"], [2, 1, 1], f"launch grid at row {index}")
        _exact_integer_list(row["block"], [128, 1, 1], f"launch block at row {index}")
        _positive_integer(row["registers_per_thread_metadata"], "launch register metadata")
        for key in (
            "dynamic_shared_bytes_metadata",
            "local_bytes_per_thread_metadata",
            "static_shared_bytes_metadata",
        ):
            _exact_integer(row[key], 0, f"launch {key} at row {index}")

    expected_ids = [spec.kernel_id for spec in kernels]
    _exact_integer(topology["unique_kernel_count"], len(set(expected_ids)), "unique kernel count")
    require(
        {row["kernel_id"] for row in launches} == set(expected_ids), "launch kernel set drifted"
    )
    symbols = _list(topology["kernel_symbols"], "kernel symbol inventory")
    require(len(symbols) == len(kernels), "kernel symbol inventory cardinality drifted")
    symbol_ids: list[str] = []
    symbol_hashes: list[str] = []
    for index, value in enumerate(symbols):
        row = _object(value, {"kernel_id", "demangled_symbol_sha256"}, f"symbol row {index}")
        symbol_ids.append(row["kernel_id"])
        symbol_hashes.append(row["demangled_symbol_sha256"])
        require(
            isinstance(row["demangled_symbol_sha256"], str)
            and _SHA256.fullmatch(row["demangled_symbol_sha256"]) is not None,
            f"symbol hash is invalid at row {index}",
        )
    require(symbol_ids == expected_ids, "kernel symbol order or identity drifted")
    require(len(set(symbol_hashes)) == len(kernels), "kernel symbol hashes are not unique")
    _exact_integer_map(topology["cuda_api_counts"], EXPECTED_API_COUNTS, "CUDA API inventory")
    _validate_transfer_map(topology["cuda_memcpy_transfers"])
    _exact_integer(topology["synchronization_activity_rows"], 8, "synchronization activity rows")
    return topology, launches


def _validate_static_resources(
    report: dict[str, Any], launches: list[Any], version: int = 1
) -> None:
    kernels = kernel_catalog(version)
    rows = _list(report["static_kernel_resources"], "static resource inventory")
    require(len(rows) == len(kernels), "static resource inventory cardinality drifted")
    by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(rows):
        row = _object(value, STATIC_RESOURCE_KEYS, f"static resource row {index}")
        kernel_id = row["kernel_id"]
        require(isinstance(kernel_id, str) and kernel_id not in by_id, "duplicate kernel resource")
        by_id[kernel_id] = row
    require(set(by_id) == {spec.kernel_id for spec in kernels}, "static kernel set drifted")

    for spec in kernels:
        row = by_id[spec.kernel_id]
        launch_rows = [item for item in launches if item["kernel_id"] == spec.kernel_id]
        require(
            row["symbol_fragment"] == spec.symbol_fragment, f"symbol drift for {spec.kernel_id}"
        )
        _exact_integer(
            row["launch_instance_count"],
            spec.launch_count,
            f"launch cardinality for {spec.kernel_id}",
        )
        require(
            row["launch_instance_count"] == len(launch_rows),
            f"launch cardinality drift for {spec.kernel_id}",
        )
        require(
            row["register_sources_agree"] is True, f"register sources disagree for {spec.kernel_id}"
        )
        _positive_integer(row["registers_per_thread"], f"registers for {spec.kernel_id}")
        _exact_integer_list(
            row["nsys_register_metadata_values"],
            sorted({item["registers_per_thread_metadata"] for item in launch_rows}),
            f"Nsight register metadata for {spec.kernel_id}",
        )
        _exact_integer_list(
            row["nsys_local_bytes_metadata_values"],
            sorted({item["local_bytes_per_thread_metadata"] for item in launch_rows}),
            f"Nsight local metadata for {spec.kernel_id}",
        )
        shared_values = {item["static_shared_bytes_metadata"] for item in launch_rows}
        require(
            shared_values == {row["static_shared_bytes"]},
            f"static shared metadata drift for {spec.kernel_id}",
        )
        for key in (
            "compiler_spill_load_bytes",
            "compiler_spill_store_bytes",
            "cuobjdump_local_bytes",
            "runtime_local_bytes_per_thread",
            "sass_ldl_instruction_count",
            "sass_stl_instruction_count",
            "stack_frame_bytes",
            "static_shared_bytes",
        ):
            _nonnegative_integer(row[key], f"{key} for {spec.kernel_id}")
        require(
            row["stack_frame_bytes"] == row["runtime_local_bytes_per_thread"],
            f"stack and runtime local bytes disagree for {spec.kernel_id}",
        )
        if row["stack_frame_bytes"] == 0:
            require(
                row["sass_ldl_instruction_count"] == row["sass_stl_instruction_count"] == 0,
                f"zero-stack kernel has local SASS instructions for {spec.kernel_id}",
            )
        blocks = _positive_integer(
            row["active_blocks_per_multiprocessor"],
            f"active blocks for {spec.kernel_id}",
        )
        warps = _positive_integer(
            row["active_warps_per_multiprocessor"],
            f"active warps for {spec.kernel_id}",
        )
        require(warps == blocks * 4, f"active block/warp relation drift for {spec.kernel_id}")
        occupancy = row["theoretical_occupancy"]
        require(
            type(occupancy) is float and math.isfinite(occupancy) and 0.0 < occupancy <= 1.0,
            f"theoretical occupancy is invalid for {spec.kernel_id}",
        )
        require(
            math.isclose(float(occupancy), warps / 48.0, rel_tol=1e-12, abs_tol=1e-12),
            f"theoretical occupancy relation drift for {spec.kernel_id}",
        )


def validate_report(report: dict[str, Any]) -> None:
    require(
        isinstance(report, dict) and set(report) == REPORT_KEYS, "resource evidence keys drifted"
    )
    # A report is validated against the generation it declares. The frozen v1
    # evidence and a v2 recapture describe the same execution graph under
    # different kernel names, so pinning one generation here would reject the
    # other for no substantive reason.
    version = schema_version_of(report)
    expected_schema, expected_profile = _IDENTITY_BY_VERSION[version]
    require(report["schema_version"] == expected_schema, "resource evidence schema mismatch")
    require(report["profile_id"] == expected_profile, "resource evidence profile mismatch")
    if version == 1:
        # The frozen capture is pinned to its exact recorded date; a v2 capture
        # carries its own collection date and must not be forced onto v1's.
        require(report["evidence_date"] == EVIDENCE_DATE, "resource evidence date drifted")
    else:
        require(
            isinstance(report["evidence_date"], str)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", report["evidence_date"]) is not None,
            "resource evidence date is not an ISO date",
        )
    _validate_source_and_inputs(report, version)
    _validate_toolchain_and_capture(report)
    _, launches = _validate_launch_topology(report, version)
    _validate_static_resources(report, launches, version)

    interpretation = _object(report["interpretation"], INTERPRETATION_KEYS, "interpretation")
    require(all(value is True for value in interpretation.values()), "interpretation gate drifted")
    achieved = _object(
        report["achieved_counters"],
        {"status", *ACHIEVED_FIELDS},
        "achieved counter state",
    )
    require(achieved["status"] == "pending_cr2_5b", "CR2-5a cannot close counter capture")
    for field in ACHIEVED_FIELDS:
        require(achieved[field] is None, f"CR2-5a must leave {field} null")

    gates = _object(report["gates"], GATE_KEYS, "resource evidence gates")
    require(gates["cr2_5a_static_resource_complete"] is True, "static gate incomplete")
    require(gates["cr2_5a_launch_topology_complete"] is True, "topology gate incomplete")
    for flag in (
        "cr2_5_achieved_counter_gate_complete",
        "maintained_claim_allowed",
        "public_support_enabled",
        "promotion_allowed",
        "tuning_authorized",
    ):
        require(gates[flag] is False, f"CR2-5a must keep {flag}=false")
