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
EVIDENCE = ROOT / "docs/plan/exact_runtime/cuda_resident_cr2_resource_evidence_20260804.json"
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


def test_frozen_v1_capture_identity_survives_the_semantic_kernel_migration() -> None:
    """The v1 capture identity is frozen historical record.

    The semantic stage migration renamed every phase-lettered kernel. The v1
    catalog, trace digest, and profile id must NOT follow that rename: the
    retained static-capture evidence hashes against them, so editing them to
    look semantic would invalidate the evidence rather than improve it.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    assert resource.SCHEMA in contract
    assert resource.PROBE_SCHEMA in contract
    assert resource.PROFILE in contract
    assert 'kTraceSignatureDigest = "cb31675ee34e5015"' in contract
    assert "kWorldCount = 256" in contract
    assert "kThreadsPerBlock = 128" in contract
    assert "kBlocks = 2" in contract
    # The v1 probe stays retired. v2 supersedes it; it is never revived.
    assert "kCaptureProbeV1Retired = true" in contract
    assert "kCaptureProbeV1RetirementReason" in contract
    for spec in resource.KERNELS:
        assert f'{{"{spec.kernel_id}", "{spec.symbol_fragment}", {spec.launch_count}}}' in contract
    for index, (kernel_id, stage) in enumerate(resource.LAUNCH_SEQUENCE):
        assert f'{{{index}, "{kernel_id}", "{stage}"}}' in contract


def test_v2_capture_supersedes_v1_without_reviving_the_retired_probe() -> None:
    """The v2 recapture must supersede v1, not revert its retirement.

    Since CP-5, v2 is itself frozen history: its catalog names the pre-fusion
    symbols, which the retained v2 static and counter evidence hashes against.
    The v2 identity, migration table, and static asserts must therefore stay in
    the contract untouched -- editing them to match the fused sources would
    invalidate that evidence exactly as relabeling v1 would have.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    # v2 identity is distinct from v1 and declares what it replaces.
    assert "cuda_resident.cp.resource_capture_probe.v2" in contract
    assert "cuda_resident.cp.kernel_resource_evidence.v2" in contract
    assert "cp.resource.steady_full_window_body.sm86.v2" in contract
    assert "kProbeSchemaV2Predecessor = kProbeSchemaV1" in contract

    # The retirement marker survives: neither v2 nor v3 flips it back.
    assert "kCaptureProbeV1Retired = true" in contract
    assert "static_assert(evidence::kCaptureProbeV1Retired);" in probe

    # Compile-time enforcement that v2 describes the same graph as v1.
    for guard in (
        "static_assert(kKernelSpecsV2.size() == 10);",
        "static_assert(kLaunchSequenceV2.size() == 12);",
        "static_assert(kernel_catalog_v2_is_complete());",
        "static_assert(kernel_migration_is_total());",
        "static_assert(launch_sequences_correspond());",
    ):
        assert guard in contract

    # The frozen v2 catalog keeps naming the pre-fusion symbols.
    for symbol in (
        "flight_dynamics_forces_kernel",
        "flight_dynamics_aerodynamics_kernel",
        "flight_dynamics_integrate_kernel",
        "instrument_projection_kernel",
        "configuration_projection_kernel",
        "episode_projection_kernel",
    ):
        assert f'"{symbol}"' in contract, f"v2 catalog is missing {symbol}"


def test_v3_capture_supersedes_v2_against_the_fused_window_graph() -> None:
    """v3 is a deliberate execution-graph change, not a relabel.

    CP-5 fused the six window-commit launches into one kernel. That claim is
    checked structurally: the v3 catalog exists with a fold table that is total
    on v2 and surjective onto v3, launch correspondence across the fold is a
    static assert, every v3 symbol is emitted by the current .cu sources, and
    the probe aligns its rows against v3 while the workload digest stays the
    frozen one.
    """
    contract = CONTRACT.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    # v3 identity is distinct and declares what it replaces.
    assert "cuda_resident.cp.resource_capture_probe.v3" in contract
    assert "cuda_resident.cp.kernel_resource_evidence.v3" in contract
    assert "cp.resource.steady_full_window_body.sm86.v3" in contract
    assert "kProbeSchemaV3Predecessor = kProbeSchemaV2" in contract

    # Compile-time enforcement of the fold claim.
    for guard in (
        "static_assert(kKernelSpecsV3.size() == 5);",
        "static_assert(kLaunchSequenceV3.size() == 7);",
        "static_assert(kernel_catalog_v3_is_complete());",
        "static_assert(kernel_fold_is_total_and_surjective());",
        "static_assert(launch_sequences_correspond_v2_to_v3());",
    ):
        assert guard in contract

    # Every v3 kernel must name the symbol the current sources actually emit.
    cuda_dir = ROOT / "src/runtime/facade/internal/cuda_resident"
    emitted_blob = "\n".join(
        source.read_text(encoding="utf-8") for source in cuda_dir.glob("*.cu")
    )
    v3_symbols = [
        "apply_barrier_kernel",
        "control_preparation_kernel",
        "window_commit_body_kernel",
        "pack_device_observation_kernel",
        "device_observation_consumer_smoke_kernel",
    ]
    for symbol in v3_symbols:
        assert f'"{symbol}"' in contract, f"v3 catalog is missing {symbol}"
        assert f"{symbol}(" in emitted_blob, (
            f"v3 catalog names {symbol}, which no .cu source emits"
        )

    # The probe must fail closed on catalog drift rather than emit a plausible
    # report -- the exact gap that let the rename go unnoticed.
    assert "require_catalog_alignment" in probe
    assert "kKernelSpecsV3" in probe
    # A static capture must never be mistaken for a counter capture.
    assert '"achieved_counters_present", false' in probe
    # A recapture grants no new authority.
    for withheld in (
        "kMaintainedClaimAllowed",
        "kPublicSupportEnabled",
        "kPromotionAllowed",
        "kTuningAuthorized",
    ):
        assert withheld in probe


def test_python_kernel_catalog_has_no_second_owner() -> None:
    """The Python collector must derive its catalog from the C++ contract.

    This module previously hard-coded its own copy of the kernel catalog. When
    the semantic stage migration renamed the kernels, the C++ side moved and
    nothing forced the Python side to follow, so the collector silently kept
    validating against symbols that no longer existed. Parsing the contract
    removes the second owner; this test keeps it removed.
    """
    from tools.diagnostics import cuda_resident_cr2_resource_static as static

    source = STATIC_PARSER.read_text(encoding="utf-8")
    # No literal kernel catalog may be reintroduced.
    assert 'KernelSpec("apply_barrier"' not in source, "kernel catalog was re-hard-coded"
    assert "kKernelSpecs" in source and "kKernelSpecsV2" in source

    contract = CONTRACT.read_text(encoding="utf-8")
    expected_shape = {1: (10, 12), 2: (10, 12), 3: (5, 7)}
    for version, array_name in ((1, "kKernelSpecs"), (2, "kKernelSpecsV2"), (3, "kKernelSpecsV3")):
        catalog = static.kernel_catalog(version)
        kernel_count, launch_count = expected_shape[version]
        assert len(catalog) == kernel_count, f"v{version} catalog shape drifted"
        assert sum(spec.launch_count for spec in catalog) == launch_count
        for spec in catalog:
            entry = f'{{"{spec.kernel_id}", "{spec.symbol_fragment}", {spec.launch_count}}}'
            assert entry in contract, f"v{version} entry not found in contract: {entry}"

    # v1 and v2 must agree on shape while differing on names -- that is what
    # makes the two evidence generations comparable. v3 deliberately changes
    # the shape: the fold table, not a 1:1 map, carries its comparability.
    v1, v2, v3 = static.kernel_catalog(1), static.kernel_catalog(2), static.kernel_catalog(3)
    assert [spec.launch_count for spec in v1] == [spec.launch_count for spec in v2]
    assert {spec.symbol_fragment for spec in v1} != {spec.symbol_fragment for spec in v2}
    assert len(v3) < len(v2)
    assert {spec.symbol_fragment for spec in v3} < (
        {spec.symbol_fragment for spec in v2} | {"window_commit_body_kernel"}
    )

    # The retained v1 alias must keep pointing at v1 so existing validators and
    # the frozen evidence they check are unaffected.
    assert static.KERNELS == v1

    with pytest.raises(static.EvidenceError):
        static.kernel_catalog(4)


    """CMake restores capture dependencies only against a versioned catalog.

    The retirement made restoring backend/profiler dependencies conditional on a
    versioned kernel catalog existing first. That precondition is now met, so the
    dependencies are present -- but the target must stay inside the CUDA-on block
    and must say why it is allowed to have them.
    """
    cmake = CMAKE.read_text(encoding="utf-8")
    target_index = cmake.index("add_executable(ef_cuda_resident_resource_probe")
    assert cmake.rfind("if (EF_ENABLE_CUDA_RESIDENT_BACKEND)", 0, target_index) >= 0
    assert cmake.find("else()", target_index) > target_index
    target = cmake[target_index : cmake.index("else()", target_index)]
    assert "kKernelSpecsV2" in cmake and "kKernelSpecsV3" in cmake
    for restored_capture_dependency in (
        "cuda_resident_replay_harness.cpp",
        "ef_cuda_resident_backend",
        "nlohmann_json::nlohmann_json",
        "EF_RESOURCE_CAPTURE_BUILD_CONFIG",
    ):
        assert restored_capture_dependency in target


def test_collectors_validate_against_the_generation_a_report_declares() -> None:
    """A v2 capture must not be rejected merely for being newer than v1.

    The collectors previously pinned a single generation, so the v2 probe would
    have failed on profile mismatch and no counter attempt could have been
    validated at all. Identity is now version-aware while the frozen v1 pins stay
    exact.
    """
    from tools.diagnostics import cuda_resident_cr2_resource_evidence as collector
    from tools.diagnostics import cuda_resident_cr2_resource_schema as schema
    from tools.diagnostics import cuda_resident_cr2_resource_static as static

    # v1 identity is unchanged and still exactly pinned.
    assert schema.SCHEMA == "cuda_resident.cr2.kernel_resource_evidence.v1"
    assert schema.PROFILE == "cr2.resource.steady_full_window_body.sm86.v1"
    assert collector.PROBE_SCHEMA == "cuda_resident.cr2.resource_capture_probe.v1"

    # v2 and v3 identities exist and are distinct.
    assert schema.SCHEMA_V2 == "cuda_resident.cp.kernel_resource_evidence.v2"
    assert schema.PROFILE_V2 == "cp.resource.steady_full_window_body.sm86.v2"
    assert collector.PROBE_SCHEMA_V2 == "cuda_resident.cp.resource_capture_probe.v2"
    assert schema.SCHEMA_V3 == "cuda_resident.cp.kernel_resource_evidence.v3"
    assert schema.PROFILE_V3 == "cp.resource.steady_full_window_body.sm86.v3"
    assert collector.PROBE_SCHEMA_V3 == "cuda_resident.cp.resource_capture_probe.v3"

    # The frozen evidence must keep validating as v1, unchanged.
    frozen = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert schema.schema_version_of(frozen) == 1
    schema.validate_report(frozen)

    # An unknown generation fails closed rather than defaulting to v1.
    with pytest.raises(static.EvidenceError):
        schema.schema_version_of({"schema_version": "cuda_resident.made_up.v9"})

    # The launch sequence is derived from the contract, not duplicated here.
    v1_launches = static.launch_sequence(1)
    v2_launches = static.launch_sequence(2)
    v3_launches = static.launch_sequence(3)
    assert schema.LAUNCH_SEQUENCE == v1_launches
    assert len(v1_launches) == len(v2_launches) == 12
    assert len(v3_launches) == 7
    assert [kernel for kernel, _ in v1_launches] != [kernel for kernel, _ in v2_launches]
    # Barrier placement is what makes v1 and v2 comparable; across the CP-5
    # fold the three barriers keep their roles while the six window launches
    # between stage_publish and window_commit collapse into one.
    assert [
        index for index, (kernel, _) in enumerate(v1_launches) if kernel == "apply_barrier"
    ] == [index for index, (kernel, _) in enumerate(v2_launches) if kernel == "apply_barrier"]
    assert [
        index for index, (kernel, _) in enumerate(v3_launches) if kernel == "apply_barrier"
    ] == [0, 2, 4]
    assert v3_launches[3] == ("window_commit_body", "window_commit_body")
    with pytest.raises(static.EvidenceError):
        static.launch_sequence(4)

    # The versioned API expectations pin what the fusion changed: five fewer
    # launches per captured window and nothing else.
    assert schema.expected_api_counts(2)["cudaLaunchKernel"] == 12
    assert schema.expected_api_counts(3)["cudaLaunchKernel"] == 7
    unchanged_v2 = {k: v for k, v in schema.expected_api_counts(2).items() if k != "cudaLaunchKernel"}
    unchanged_v3 = {k: v for k, v in schema.expected_api_counts(3).items() if k != "cudaLaunchKernel"}
    assert unchanged_v2 == unchanged_v3

    # v2/v3 probes carry the cross-generation link and must never claim
    # counters. v3 records the fold, not the 1:1 migration.
    assert collector.PROBE_KEYS_V2_ADDITIONS == {
        "achieved_counters_present",
        "expected_launch_sequence",
        "kernel_id_migration",
        "supersedes_schema_version",
        "trace_signature_matches_v1",
    }
    assert collector.PROBE_KEYS_V3_ADDITIONS == {
        "achieved_counters_present",
        "expected_launch_sequence",
        "kernel_id_fold",
        "supersedes_schema_version",
        "trace_signature_matches_v1",
    }
    collector_source = COLLECTOR.read_text(encoding="utf-8")
    assert "a static capture must not claim achieved counters" in collector_source
    assert "v2 probe workload diverged" in collector_source
    # A recapture grants no authority: the unpromoted state must survive.
    validator_source = SCHEMA_VALIDATOR.read_text(encoding="utf-8")
    assert "resource candidate state must remain unpromoted" in validator_source


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
