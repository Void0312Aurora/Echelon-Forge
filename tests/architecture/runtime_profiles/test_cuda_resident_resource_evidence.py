from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_resource_evidence as resource


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_resource_evidence_contract.h"
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_resource_probe.cpp"
COLLECTOR = ROOT / "tools/diagnostics/cuda_resident_cr2_resource_evidence.py"
STATIC_PARSER = ROOT / "tools/diagnostics/cuda_resident_cr2_resource_static.py"
SCHEMA_VALIDATOR = ROOT / "tools/diagnostics/cuda_resident_cr2_resource_schema.py"
EVIDENCE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_resource_evidence_20260804.json"
CMAKE = ROOT / "CMakeLists.txt"
EVIDENCE_COMMIT = "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8"


def _git_blob(commit: str, path: Path) -> bytes:
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _git_source_sha256(commit: str, path: Path) -> str:
    content = _git_blob(commit, path).replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _valid_probe() -> dict[str, object]:
    resources = []
    for spec in resource.KERNELS:
        resources.append(
            {
                "kernel_id": spec.kernel_id,
                "registers_per_thread": 32,
                "local_bytes_per_thread": 0,
                "static_shared_bytes": 0,
                "threads_per_block": 128,
                "active_blocks_per_multiprocessor": 12,
                "active_warps_per_multiprocessor": 48,
                "theoretical_occupancy": 1.0,
            }
        )
    return {
        "backend_id": "cuda_resident.rb7_phase_d",
        "blocks": 2,
        "build_config": "Release",
        "capture": {
            "range": "cudaProfilerApi",
            "setup_outside": True,
            "resource_queries_outside": True,
            "public_export_inside": True,
            "device_consumer_inside": True,
            "diagnostic_materialization_inside": False,
            "operation_sequence": [
                "inject",
                "evaluate_empty",
                "advance_world_batch",
                "public_export",
                "acquire_device_lease",
                "consumer_submit",
                "consumer_event_await",
            ],
        },
        "cuda_architecture": "sm_86",
        "cuda_environment": {
            "device_ordinal": 0,
            "device_name": "test GPU",
            "compute_capability": "8.6",
            "driver_version": 1,
            "runtime_version": 1,
        },
        "maintained_claim_allowed": False,
        "profile_id": resource.PROFILE,
        "promotion_allowed": False,
        "public_support_enabled": False,
        "result": {
            "agent_observation_count": 256,
            "instrument_state_count": 256,
            "consumer_world_count": 256,
            "consumer_await_completed": True,
            "diagnostic_materialization_called": False,
        },
        "runtime_kernel_resources": resources,
        "schema_version": resource.PROBE_SCHEMA,
        "threads_per_block": 128,
        "trace_signature_algorithm": "fnv1a64",
        "trace_signature_bytes": 80469,
        "trace_signature_digest": "cb31675ee34e5015",
        "tuning_authorized": False,
        "window_count": 1,
        "world_count": 256,
    }


def _write_probe(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _ptxas_text(
    *, include_no_cap: bool = True, omit_properties: str = "", architecture: str = "sm_86"
) -> str:
    lines = ["nvcc " + ("-maxrregcount=0" if include_no_cap else "")]
    for index, spec in enumerate(resource.KERNELS):
        lines.append(
            f"ptxas info : Compiling entry function '{spec.symbol_fragment}' for '{architecture}'"
        )
        if spec.kernel_id != omit_properties:
            lines.append(
                f"{index} bytes stack frame, {index + 1} bytes spill stores, "
                f"{index + 2} bytes spill loads"
            )
        lines.append(f"ptxas info : Used {index + 20} registers")
    return "\n".join(lines)


def _write_nsys(
    path: Path,
    *,
    launch_ids: tuple[str, ...] | None = None,
    extra_diagnostic_d2h: int = 0,
    symbol_overrides: dict[int, str] | None = None,
) -> None:
    ids = launch_ids or tuple(kernel_id for kernel_id, _ in resource.LAUNCH_SEQUENCE)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            """
            CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (
                start INTEGER, end INTEGER, demangledName INTEGER,
                registersPerThread INTEGER, gridX INTEGER, gridY INTEGER, gridZ INTEGER,
                blockX INTEGER, blockY INTEGER, blockZ INTEGER,
                staticSharedMemory INTEGER, dynamicSharedMemory INTEGER,
                localMemoryPerThread INTEGER
            )
            """
        )
        fragments = {spec.kernel_id: spec.symbol_fragment for spec in resource.KERNELS}
        for index, kernel_id in enumerate(ids):
            name_id = index + 1
            symbol = (symbol_overrides or {}).get(index, fragments[kernel_id])
            connection.execute("INSERT INTO StringIds VALUES (?, ?)", (name_id, symbol))
            connection.execute(
                "INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES "
                "(?, ?, ?, ?, 2, 1, 1, 128, 1, 1, 0, 0, 0)",
                (index * 100, index * 100 + 50, name_id, 32),
            )
        connection.execute("CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME (nameId INTEGER)")
        api_counts = {
            "cudaDeviceSynchronize_v3020": 5,
            "cudaEventCreateWithFlags_v3020": 2,
            "cudaEventRecord_v3020": 2,
            "cudaEventSynchronize_v3020": 1,
            "cudaStreamWaitEvent_v3020": 1,
            "cudaLaunchKernel_v7000": 12,
            "cudaMalloc_v3020": 4,
            "cudaMemcpy_v3020": 13,
            "cudaMemset_v3020": 5,
            "cudaProfilerStart_v4000": 1,
        }
        next_id = 100
        for name, count in api_counts.items():
            connection.execute("INSERT INTO StringIds VALUES (?, ?)", (next_id, name))
            connection.executemany(
                "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?)",
                [(next_id,)] * count,
            )
            next_id += 1
        connection.execute(
            "CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY (srcKind INTEGER, dstKind INTEGER, bytes INTEGER)"
        )
        connection.executemany(
            "INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?, ?, ?)",
            [(0, 2, 1)] * 3 + [(2, 0, 1)] * (7 + extra_diagnostic_d2h) + [(2, 2, 1)] * 3,
        )
        connection.execute("CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION (start INTEGER)")
        connection.executemany(
            "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?)",
            [(index,) for index in range(8)],
        )
        connection.commit()
    finally:
        connection.close()


def test_cr2_5a_probe_has_one_bounded_profiler_window_and_cuda_only_target() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")
    assert resource.SCHEMA in contract
    assert resource.PROBE_SCHEMA in contract
    assert resource.PROFILE in contract
    assert 'kTraceSignatureDigest = "cb31675ee34e5015"' in contract
    assert "kWorldCount = 256" in contract
    assert "kThreadsPerBlock = 128" in contract
    assert "kBlocks = 2" in contract
    for spec in resource.KERNELS:
        assert f'{{"{spec.kernel_id}", "{spec.symbol_fragment}", {spec.launch_count}}}' in contract
    for index, (kernel_id, stage) in enumerate(resource.LAUNCH_SEQUENCE):
        assert f'{{{index}, "{kernel_id}", "{stage}"}}' in contract
    assert probe.count("ProfilerRange capture") == 1
    assert probe.index("backend.setup") < probe.index("ProfilerRange capture")
    assert probe.index("query_kernel_resources") < probe.index("ProfilerRange capture")
    captured = probe.split("ProfilerRange capture", 1)[1].split("capture.stop()", 1)[0]
    operations = (
        "backend.inject",
        "backend.evaluate",
        "backend.advance",
        "backend.export_state",
        "backend.acquire_device_observation_lease",
        "consumer.submit",
        "consumer.await",
    )
    for operation in operations:
        assert operation in captured
    assert [captured.index(operation) for operation in operations] == sorted(
        captured.index(operation) for operation in operations
    )
    assert "materialize_for_diagnostics" not in probe
    target_index = cmake.index("add_executable(ef_cuda_resident_resource_probe")
    assert cmake.rfind("if (EF_ENABLE_CUDA_EXPERIMENTS)", 0, target_index) >= 0
    assert cmake.find("else()", target_index) > target_index
    target = cmake[target_index : cmake.index("else()", target_index)]
    assert "ef_cuda_resident_backend" in target


def test_cr2_5a_evidence_records_static_resources_without_counter_or_tuning_claims() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    resource.validate_report(evidence)
    assert evidence["source"]["baseline_commit"] == "08b48f299484428e7297f328ca860f8fadc31cc4"
    assert evidence["inputs"]["source_hash_canonicalization"] == "utf8_lf"
    assert evidence["inputs"]["probe_source_sha256"] == _git_source_sha256(EVIDENCE_COMMIT, PROBE)
    assert evidence["inputs"]["contract_source_sha256"] == _git_source_sha256(
        EVIDENCE_COMMIT, CONTRACT
    )
    assert evidence["inputs"]["collector_source_sha256"] == _git_source_sha256(
        EVIDENCE_COMMIT, COLLECTOR
    )
    assert evidence["inputs"]["static_parser_source_sha256"] == _git_source_sha256(
        EVIDENCE_COMMIT, STATIC_PARSER
    )
    assert EVIDENCE.stat().st_size < 524_288
    assert evidence["launch_topology"]["launch_instance_count"] == 12
    assert evidence["launch_topology"]["unique_kernel_count"] == 10
    symbol_rows = evidence["launch_topology"]["kernel_symbols"]
    assert len(symbol_rows) == 10
    assert len({row["demangled_symbol_sha256"] for row in symbol_rows}) == 10
    launches = evidence["launch_topology"]["launches"]
    assert [(row["kernel_id"], row["semantic_stage"]) for row in launches] == list(
        resource.LAUNCH_SEQUENCE
    )
    assert all(row["grid"] == [2, 1, 1] for row in launches)
    assert all(row["block"] == [128, 1, 1] for row in launches)
    assert evidence["launch_topology"]["cuda_api_counts"] == {
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
    assert evidence["launch_topology"]["cuda_memcpy_transfers"] == {
        "device_to_device": {"bytes": 677376, "copy_count": 3},
        "device_to_host": {"bytes": 229908, "copy_count": 7},
        "host_to_device": {"bytes": 14080, "copy_count": 3},
    }

    expected = {
        "apply_barrier": (30, 0, 0, 0, 1.0),
        "phase_a_controls": (34, 0, 0, 0, 1.0),
        "phase_b_forces": (66, 40, 3, 2, 7 / 12),
        "phase_b_aerodynamics": (66, 40, 3, 2, 7 / 12),
        "phase_b_integrate": (64, 40, 3, 2, 8 / 12),
        "phase_d_instruments": (64, 40, 3, 2, 8 / 12),
        "phase_d_configuration": (34, 0, 0, 0, 1.0),
        "phase_d_projection": (40, 0, 0, 0, 1.0),
        "phase_d_pack": (16, 0, 0, 0, 1.0),
        "phase_d_consumer": (14, 0, 0, 0, 1.0),
    }
    rows = {row["kernel_id"]: row for row in evidence["static_kernel_resources"]}
    assert set(rows) == set(expected)
    for kernel_id, (registers, stack, ldl, stl, occupancy) in expected.items():
        row = rows[kernel_id]
        assert row["registers_per_thread"] == registers
        assert row["stack_frame_bytes"] == stack
        assert row["compiler_spill_store_bytes"] == 0
        assert row["compiler_spill_load_bytes"] == 0
        assert row["sass_ldl_instruction_count"] == ldl
        assert row["sass_stl_instruction_count"] == stl
        assert row["theoretical_occupancy"] == pytest.approx(occupancy)
        assert row["nsys_local_bytes_metadata_values"] == [0]
    assert rows["phase_d_consumer"]["nsys_register_metadata_values"] == [16]
    assert evidence["toolchain"]["maxrregcount_argument"] == 0
    assert evidence["toolchain"]["register_cap"] is None
    assert evidence["toolchain"]["maxrregcount_zero_interpretation"] == "no_cap"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda probe: probe.update({"unexpected_raw_payload": {}}),
        lambda probe: probe.update({"promotion_allowed": True}),
        lambda probe: probe["capture"].update({"diagnostic_materialization_inside": True}),
        lambda probe: probe.update({"trace_signature_bytes": 80470}),
    ],
)
def test_probe_validation_rejects_scope_or_trace_drift(tmp_path: Path, mutation) -> None:
    probe = _valid_probe()
    mutation(probe)
    with pytest.raises(resource.EvidenceError):
        resource.load_probe(_write_probe(tmp_path, probe))


def test_ptxas_parser_requires_explicit_spills_and_no_cap_argument() -> None:
    parsed = resource.parse_ptxas(_ptxas_text())
    assert parsed["apply_barrier"]["spill_store_bytes"] == 1
    assert parsed["phase_d_consumer"]["spill_load_bytes"] == 11
    with pytest.raises(resource.EvidenceError, match="no-cap"):
        resource.parse_ptxas(_ptxas_text(include_no_cap=False))
    with pytest.raises(resource.EvidenceError, match="properties missing"):
        resource.parse_ptxas(_ptxas_text(omit_properties="phase_b_forces"))
    with pytest.raises(resource.EvidenceError, match="no-cap"):
        resource.parse_ptxas(_ptxas_text() + "\nnvcc -maxrregcount=64")
    with pytest.raises(resource.EvidenceError, match="architecture drift"):
        resource.parse_ptxas(_ptxas_text(architecture="sm_80"))


def test_nsys_parser_rejects_wrong_launch_order_and_diagnostic_readback(tmp_path: Path) -> None:
    wrong_order = list(kernel_id for kernel_id, _ in resource.LAUNCH_SEQUENCE)
    wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
    wrong_path = tmp_path / "wrong.sqlite"
    _write_nsys(wrong_path, launch_ids=tuple(wrong_order))
    with pytest.raises(resource.EvidenceError, match="launch order"):
        resource.parse_nsys(wrong_path)

    diagnostic_path = tmp_path / "diagnostic.sqlite"
    _write_nsys(diagnostic_path, extra_diagnostic_d2h=2)
    with pytest.raises(resource.EvidenceError, match="device_to_host"):
        resource.parse_nsys(diagnostic_path)

    variant_path = tmp_path / "variant.sqlite"
    _write_nsys(variant_path, symbol_overrides={2: "variant_apply_barrier_kernel"})
    with pytest.raises(resource.EvidenceError, match="exact symbol drift"):
        resource.parse_nsys(variant_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("threads_per_block", 64),
        ("active_blocks_per_multiprocessor", 0),
        ("active_warps_per_multiprocessor", 0),
        ("theoretical_occupancy", None),
        ("theoretical_occupancy", 0.0),
    ],
)
def test_runtime_resource_validation_rejects_invalid_or_null_values(field: str, value) -> None:
    probe = _valid_probe()
    probe["runtime_kernel_resources"][0][field] = value
    with pytest.raises(resource.EvidenceError):
        resource._runtime_resources(probe)


def test_runtime_resource_validation_rejects_missing_fields() -> None:
    probe = _valid_probe()
    del probe["runtime_kernel_resources"][0]["theoretical_occupancy"]
    with pytest.raises(resource.EvidenceError, match="row drift"):
        resource._runtime_resources(probe)


def test_cr2_5a_report_rejects_theoretical_values_copied_into_achieved_fields() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    mutated = deepcopy(evidence)
    mutated["achieved_counters"]["achieved_occupancy"] = 7 / 12
    with pytest.raises(resource.EvidenceError, match="achieved_occupancy"):
        resource.validate_report(mutated)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["launch_topology"].pop("launches"),
        lambda value: value.update({"static_kernel_resources": []}),
        lambda value: value["capture"].pop("range"),
        lambda value: value["inputs"].pop("nsys_sqlite_sha256"),
        lambda value: value["launch_topology"].pop("cuda_api_counts"),
        lambda value: value["launch_topology"].pop("cuda_memcpy_transfers"),
    ],
    ids=(
        "launch-inventory",
        "static-resource-inventory",
        "capture-provenance",
        "input-provenance",
        "cuda-api-inventory",
        "cuda-copy-inventory",
    ),
)
def test_cr2_5a_report_rejects_incomplete_evidence_sections(mutation) -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    mutation(evidence)
    with pytest.raises(resource.EvidenceError):
        resource.validate_report(evidence)


def test_cr2_5a_new_modules_remain_below_soft_size_targets() -> None:
    assert len(CONTRACT.read_text(encoding="utf-8").splitlines()) <= 600
    assert len(PROBE.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(COLLECTOR.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(STATIC_PARSER.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(SCHEMA_VALIDATOR.read_text(encoding="utf-8").splitlines()) <= 700
    this_file = Path(__file__)
    assert len(this_file.read_text(encoding="utf-8").splitlines()) <= 700
