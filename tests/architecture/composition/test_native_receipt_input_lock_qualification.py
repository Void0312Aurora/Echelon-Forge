"""Actual candidate-host receipt references, not full Air experiment execution."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from python.experiment.air_combat_matrix import MATRIX_ENTRIES, REGISTRY
from python.experiment.resolved_input_lock import (
    InputLockError,
    build_resolved_input_lock,
    canonical_json_bytes,
    compare_resolved_input_locks,
    join_run_receipt_path,
    project_compiled_scenario_dependencies,
)
from python.scenario.compiler import ScenarioCompiler
from python.tasking_contracts.failure_domains import (
    WorldOutcome,
    WorldState,
    build_batch_outcome,
    project_unresolved_batch_fault,
)
from tools.maintenance.runtime_run_receipt import validate_run_receipt


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def native_candidate_binary():
    build = Path(os.environ.get("CMO_BUILD_DIR", "build"))
    if not build.is_absolute():
        build = ROOT / build
    suffix = ".exe" if os.name == "nt" else ""
    name = f"ef_runtime_kernel_candidate_test{suffix}"
    candidates = (build / name, build / "Release" / name, build / "Debug" / name)
    binary = next((path for path in candidates if path.is_file()), None)
    if binary is None and "CMO_BUILD_DIR" in os.environ:
        pytest.fail("configured build is missing ef_runtime_kernel_candidate_test")
    if binary is None:
        pytest.skip("build ef_runtime_kernel_candidate_test for native receipt qualification")
    return binary


@pytest.mark.parametrize("mode", ["complete", "drift", "missing"])
def test_native_host_persists_and_reopens_input_lock_reference(
    native_candidate_binary, tmp_path, mode
):
    experiment = MATRIX_ENTRIES[0].experiment
    compiled = ScenarioCompiler.compile_path(str(ROOT / experiment.scenario.path))
    candidate = build_resolved_input_lock(
        experiment,
        REGISTRY,
        repo_root=ROOT,
        effective_seeds=(42,),
        dependencies=project_compiled_scenario_dependencies(compiled, repo_root=ROOT),
    )
    artifact = tmp_path / "input-lock.json"
    # Hash exactly the owner-defined input_lock component; the larger experiment
    # projection includes status/provenance outside this identity.
    artifact.write_bytes(canonical_json_bytes(candidate.as_dict()["input_lock"]))
    environment = dict(os.environ)
    environment.update(
        EF_RFC_INPUT_LOCK_PATH=str(artifact),
        EF_RFC_OUTPUT_DIR=str(tmp_path),
        EF_RFC_RECEIPT_MODE=mode,
    )
    result = subprocess.run(
        [
            str(native_candidate_binary),
            "--no-skip",
            "--test-case=RFC239 native candidate publishes an input-lock-bound receipt",
            "--no-colors",
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    receipt_path = tmp_path / "receipt.json"
    if mode == "missing":
        assert not receipt_path.exists()
        return
    receipt = validate_run_receipt(json.loads(receipt_path.read_bytes()))
    payload = receipt["payload"]
    assert payload["inputs"]["artifacts"]["resolved_input_lock"] == candidate.digest
    assert payload["completion"]["durable_ack"] is True
    assert payload["terminal_state"] == ("completed" if mode == "complete" else "failed")
    # Native owner reopening verified the durable header, journal and referenced
    # blobs. Python consumes the owner output without creating a RunReceipt.
    native = json.loads((tmp_path / "native.json").read_bytes())
    assert native["steps_completed"] == 3
    assert native["host_mode"] == "dark"
    assert native["input_lock_semantics_executed"] is False
    kwargs = dict(
        batch_generation_ref=payload["writer_generation"],
        operation_ref="qualification.steps",
        operation="step",
        expected_world_indices=frozenset({0}),
    )
    if mode == "complete":
        outputs = payload["results"]["output_artifacts"]
        topology_ref = next(
            item for item in outputs if item["name"] == "runtime-cpu-scheduler-topology"
        )
        topology_blob = tmp_path / "ledger" / "blobs" / f"{topology_ref['digest']}.data"
        topology_bytes = topology_blob.read_bytes()
        assert hashlib.sha256(topology_bytes).hexdigest() == topology_ref["digest"]
        topology = json.loads(topology_bytes)
        assert native["realized_topology_digest"] == topology["sha256"]
        assert native["topology_artifact_digest"] == topology_ref["digest"]
        assert topology["topology"]["nodes"]
        assert topology["active_pipeline_order"]
        scope_ref = next(item for item in outputs if item["name"] == "runtime-world-scope-binding")
        scope_blob = tmp_path / "ledger" / "blobs" / f"{scope_ref['digest']}.data"
        assert native["world_scope_artifact_digest"] == scope_ref["digest"]
        scope_bytes = scope_blob.read_bytes()
        assert hashlib.sha256(scope_bytes).hexdigest() == scope_ref["digest"]
        assert json.loads(scope_bytes)["world_bindings"] == native["receipt_world_bindings"]
        outcome = build_batch_outcome(
            **kwargs, worlds=(WorldOutcome(0, WorldState.COMPLETED, True),)
        )
    else:
        outcome = project_unresolved_batch_fault(**kwargs, error_code="input.provenance_drift")
    joined = join_run_receipt_path(
        candidate, receipt_path=receipt_path, native_runtime=native, outcome=outcome,
        native_topology_path=topology_blob if mode == "complete" else None,
        native_world_scope_path=scope_blob if mode == "complete" else None,
    )
    assert joined.status == ("completed" if mode == "complete" else "unknown")
    comparison = compare_resolved_input_locks(joined, joined)
    assert not comparison.comparable
    if mode == "complete":
        assert "input_lock_semantics_executed" in comparison.differences
        with pytest.raises(InputLockError, match="receipt_topology_artifact_required"):
            join_run_receipt_path(
                candidate, receipt_path=receipt_path, native_runtime=native, outcome=outcome
            )
        with pytest.raises(InputLockError, match="receipt_world_scope_artifact_required"):
            join_run_receipt_path(
                candidate, receipt_path=receipt_path, native_runtime=native, outcome=outcome,
                native_topology_path=topology_blob,
            )
        mismatched = {**native, "world_scope_artifact_digest": "f" * 64}
        with pytest.raises(InputLockError, match="receipt_world_scope_binding_mismatch"):
            join_run_receipt_path(
                candidate, receipt_path=receipt_path, native_runtime=mismatched, outcome=outcome,
                native_topology_path=topology_blob, native_world_scope_path=scope_blob,
            )
        for field in ("realized_topology_digest", "topology_artifact_digest"):
            mismatched = {**native, field: "f" * 64}
            with pytest.raises(InputLockError, match="receipt_topology_.*mismatch"):
                join_run_receipt_path(
                    candidate, receipt_path=receipt_path, native_runtime=mismatched,
                    outcome=outcome, native_topology_path=topology_blob,
                    native_world_scope_path=scope_blob,
                )
        blob = tmp_path / "ledger" / "blobs" / f"{candidate.digest}.data"
        for audit_mode, damaged_blob in (
            ("audit_missing_blob", blob),
            ("audit_missing_topology", topology_blob),
            ("audit_corrupt_topology", topology_blob),
            ("audit_missing_world_scope", scope_blob),
            ("audit_corrupt_world_scope", scope_blob),
        ):
            original_bytes = damaged_blob.read_bytes()
            if audit_mode.startswith("audit_corrupt_"):
                damaged_blob.write_bytes(b"{}")
            else:
                damaged_blob.unlink()
            if damaged_blob == topology_blob:
                with pytest.raises(InputLockError, match="receipt_topology_(unreadable|artifact_mismatch)"):
                    join_run_receipt_path(
                        candidate, receipt_path=receipt_path, native_runtime=native,
                        outcome=outcome, native_topology_path=topology_blob,
                        native_world_scope_path=scope_blob,
                    )
            if damaged_blob == scope_blob:
                with pytest.raises(InputLockError, match="receipt_world_scope_(unreadable|artifact_mismatch)"):
                    join_run_receipt_path(
                        candidate, receipt_path=receipt_path, native_runtime=native,
                        outcome=outcome, native_topology_path=topology_blob,
                        native_world_scope_path=scope_blob,
                    )
            environment["EF_RFC_RECEIPT_MODE"] = audit_mode
            audit = subprocess.run(
                result.args,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            assert audit.returncode == 0, audit.stdout + audit.stderr
            assert "1 passed" in audit.stdout
            damaged_blob.write_bytes(original_bytes)
