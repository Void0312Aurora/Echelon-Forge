"""Build-tree maintained-facade recording, not a production training cutover."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from python.experiment.air_combat_matrix import MATRIX_ENTRIES, REGISTRY
from python.experiment.input_lock_artifacts import write_resolved_input_lock_artifacts
from python.experiment.resolved_input_lock import build_resolved_input_lock
from python.rl.runtime.resolved_input_lock_binding import (
    assert_run_receipt_input_lock_binding,
    load_resolved_input_lock_path,
)
from tools.maintenance.runtime_run_receipt import validate_run_receipt


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def native_facade_recording_binary():
    build = Path(os.environ.get("EF_FACADE_QUALIFICATION_BUILD_DIR", ROOT / "build-facade-current-attempt"))
    suffix = ".exe" if os.name == "nt" else ""
    binary = build / f"ef_runtime_facade_run_qualification_test{suffix}"
    if not binary.is_file():
        if "EF_FACADE_QUALIFICATION_BUILD_DIR" in os.environ:
            pytest.fail(f"configured build is missing the facade recording qualifier: {binary}")
        pytest.skip(f"build the native maintained-facade recording qualifier: {binary}")
    return binary


def _invoke(binary, case, environment):
    result = subprocess.run(
        [str(binary), "--no-skip", f"--test-case={case}", "--no-colors"],
        env=environment, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


@pytest.mark.parametrize("steps", [3, 7])
@pytest.mark.parametrize("control", ["complete", "wrong_run", "missing_payload", "corrupt_payload"])
def test_current_attempt_is_recorded_by_the_maintained_native_owner(
    native_facade_recording_binary, tmp_path, control, steps
):
    candidate = build_resolved_input_lock(
        MATRIX_ENTRIES[0].experiment, REGISTRY, repo_root=ROOT, effective_seeds=(42,)
    )
    projection = tmp_path / "resolved-experiment.json"
    payload = tmp_path / "native-input-lock.json"
    write_resolved_input_lock_artifacts(
        candidate, projection_path=projection, native_input_lock_path=payload
    )
    environment = dict(
        os.environ,
        EF_FACADE_INPUT_LOCK_PATH=str(payload),
        EF_FACADE_RUN_OUTPUT=str(tmp_path),
        EF_FACADE_FIXED_STEPS=str(steps),
    )
    _invoke(native_facade_recording_binary,
            "maintained facade records a real fixed-step attempt", environment)
    observed = json.loads((tmp_path / "observed.json").read_bytes())
    assert observed["run_id"] == "facade-current-attempt"
    assert observed["seed"] == 42 and observed["steps_completed"] == steps
    assert observed["healthy"] is True and observed["sim_time_s"] > 0
    assert observed["admitted_time_step_ns"] == 16666667
    assert observed["native_world_time_step_s"] == 16666667 / 1_000_000_000
    assert observed["cpu_frame_delta_s"] > 0
    assert observed["cpu_frame_delta_precision"] == "ecs_ftime_t"
    assert observed["host_mode"] == "native_cpp"
    assert observed["input_lock_semantics_executed"] is False
    if control == "wrong_run":
        environment["EF_FACADE_AUDIT_RUN_ID"] = "some-other-attempt"
    elif control in {"missing_payload", "corrupt_payload"}:
        blob = tmp_path / "ledger" / "blobs" / f"{candidate.digest}.data"
        assert blob.read_bytes() == payload.read_bytes()
        if control == "missing_payload":
            blob.unlink()
        else:
            blob.write_bytes(b"corrupted input artifact")
    if control != "complete":
        environment["EF_FACADE_EXPECT_REOPEN_FAILURE"] = "1"
    # This is a second native process with only a fresh read-only ledger owner.
    _invoke(native_facade_recording_binary,
            "maintained facade receipt independently reopens", environment)
    receipt_path = tmp_path / "receipt.json"
    if control != "complete":
        assert not receipt_path.exists()
        return
    receipt = validate_run_receipt(json.loads(receipt_path.read_bytes()))
    assert_run_receipt_input_lock_binding(load_resolved_input_lock_path(projection), receipt)
    run = receipt["payload"]
    assert run["run_id"] == observed["run_id"]
    assert run["attempt_id"] == "attempt-facade-current-attempt"
    assert run["terminal_state"] == "completed" and run["completion"]["durable_ack"] is True
    assert run["host_boot_id"] == observed["host_boot_id"]
    assert run["execution_scope"]["world_ids"] == [observed["world_id"]]
    assert run["execution_scope"]["episode_ids"] == [observed["episode_id"]]
    events = [event["event"] for event in run["lifecycle"]]
    assert events.index("shutdown") < events.index("reclamation") < events.index("terminal")
    result_ref = next(artifact for artifact in run["results"]["output_artifacts"]
                      if artifact["name"] == "maintained-facade-native-result")
    result_bytes = (tmp_path / "ledger" / "blobs" / f"{result_ref['digest']}.data").read_bytes()
    assert hashlib.sha256(result_bytes).hexdigest() == result_ref["digest"]
    assert json.loads(result_bytes) == observed
