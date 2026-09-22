from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from python.rl.runtime.rollout_gate import FileRolloutDecisionStore
from python.rl.runtime.rollout_gate import RolloutAdmission
from python.rl.runtime.rollout_gate import RolloutAdmissionError
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope
from python.rl.runtime.rollout_gate import canonical_json_bytes


KEY = b"p5d-local-test-key-0123456789abcdef"
KEY_ID = "p5d-test-key"
MANIFEST = "a" * 64
PLAN = "b" * 64


def _payload(
    *,
    state: str,
    sequence: int,
    decision_id: str,
    predecessor: str = "",
    writer_generation: int = 1,
    plan_sha256: str = PLAN,
    checkpoint_id: str = "",
) -> dict[str, str]:
    return {
        "authority_kind": "rollout_decision",
        "schema_version": "echelon_forge.rollout_decision.v1",
        "contract_version": "echelon_forge.rollout_decision_contract.v1",
        "writer_role": "release_controller",
        "decision_id": decision_id,
        "release_id": "release-p5d-local",
        "manifest_sha256": MANIFEST,
        "plan_sha256": plan_sha256,
        "plan_reader_generation_min": "1",
        "plan_reader_generation_max": "1",
        "predecessor_decision_id": predecessor,
        "state": state,
        "writer_generation": str(writer_generation),
        "decision_sequence": str(sequence),
        "cohort": "local-in-process",
        "rollback_deadline": "2026-12-31T00:00:00Z",
        "checkpoint_id": checkpoint_id,
        "irreversible_write_boundary": "none",
    }


def _envelope(**kwargs: object) -> dict[str, object]:
    return build_rollout_decision_envelope(
        _payload(**kwargs),
        key_id=KEY_ID,
        signing_key=KEY,
    )


def test_rollout_slot_is_durable_single_writer_and_monotonic(tmp_path: Path) -> None:
    path = tmp_path / "rollout.json"
    store = FileRolloutDecisionStore(path, writer_id="release-controller-a", signing_key=KEY, key_id=KEY_ID)

    prepared = store.commit(_envelope(state="prepared", sequence=0, decision_id="decision-0"))
    assert prepared.state == "prepared"
    shadow = store.commit(
        _envelope(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"),
        expected_decision_sha256=prepared.decision_sha256,
    )
    canary_ready = store.commit(
        _envelope(state="canary-ready", sequence=2, decision_id="decision-2", predecessor="decision-1"),
        expected_decision_sha256=shadow.decision_sha256,
    )
    canary = store.commit(
        _envelope(state="production-canary", sequence=3, decision_id="decision-3", predecessor="decision-2"),
        expected_decision_sha256=canary_ready.decision_sha256,
    )
    assert canary.production_authorized
    assert FileRolloutDecisionStore(
        path,
        writer_id="release-controller-restarted",
        signing_key=KEY,
        key_id=KEY_ID,
    ).read(expected_release_id="release-p5d-local", expected_manifest_sha256=MANIFEST, expected_plan_sha256=PLAN).decision_sha256 == canary.decision_sha256


def test_rollout_slot_rejects_stale_writer_and_invalid_transition(tmp_path: Path) -> None:
    store = FileRolloutDecisionStore(tmp_path / "rollout.json", writer_id="release-controller", signing_key=KEY, key_id=KEY_ID)
    prepared = store.commit(_envelope(state="prepared", sequence=0, decision_id="decision-0"))
    with pytest.raises(RolloutAdmissionError, match="compare-and-swap"):
        store.commit(
            _envelope(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"),
            expected_decision_sha256="0" * 64,
        )
    with pytest.raises(RolloutAdmissionError, match="state transition"):
        store.commit(
            _envelope(state="stable", sequence=1, decision_id="decision-1", predecessor="decision-0"),
            expected_decision_sha256=prepared.decision_sha256,
        )


def test_kill_switch_closes_admission_and_backout_is_typed(tmp_path: Path) -> None:
    store = FileRolloutDecisionStore(tmp_path / "rollout.json", writer_id="release-controller", signing_key=KEY, key_id=KEY_ID)
    prepared = store.commit(_envelope(state="prepared", sequence=0, decision_id="decision-0"))
    shadow = store.commit(_envelope(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"), expected_decision_sha256=prepared.decision_sha256)
    canary_ready = store.commit(_envelope(state="canary-ready", sequence=2, decision_id="decision-2", predecessor="decision-1"), expected_decision_sha256=shadow.decision_sha256)
    canary = store.commit(_envelope(state="production-canary", sequence=3, decision_id="decision-3", predecessor="decision-2"), expected_decision_sha256=canary_ready.decision_sha256)
    killed = store.trip_kill_switch(["wrong_epoch_result", "security_denial"])
    assert not killed.production_authorized
    assert killed.kill_switch_reasons == ("security_denial", "wrong_epoch_result")

    backed_out = store.commit(
        _envelope(
            state="backed-out",
            sequence=4,
            decision_id="decision-4",
            predecessor="decision-3",
            checkpoint_id="checkpoint-n-1",
        ),
        expected_decision_sha256=canary.decision_sha256,
    )
    assert backed_out.state == "backed-out"
    assert not backed_out.admissions_open
    assert backed_out.writer_advancement_frozen
    with pytest.raises(RolloutAdmissionError, match="production-authorized"):
        backed_out.assert_production_authorized()


def test_rollout_slot_tamper_and_wrong_key_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "rollout.json"
    store = FileRolloutDecisionStore(path, writer_id="release-controller", signing_key=KEY, key_id=KEY_ID)
    store.commit(_envelope(state="prepared", sequence=0, decision_id="decision-0"))
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["decision"]["payload"]["state"] = "production-canary"
    path.write_bytes(canonical_json_bytes(raw))
    with pytest.raises(RolloutAdmissionError):
        RolloutAdmission.from_slot(path, verification_key=KEY, expected_key_id=KEY_ID)
    with pytest.raises(RolloutAdmissionError):
        RolloutAdmission.from_slot(path, verification_key=hashlib.sha256(KEY).digest(), expected_key_id=KEY_ID)


def test_maintained_adapter_requires_explicit_production_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from python.rl.runtime.world_batch import adapter as adapter_module

    path = tmp_path / "rollout.json"
    store = FileRolloutDecisionStore(path, writer_id="release-controller", signing_key=KEY, key_id=KEY_ID)
    prepared = store.commit(_envelope(state="prepared", sequence=0, decision_id="decision-0"))
    shadow = store.commit(_envelope(state="shadow", sequence=1, decision_id="decision-1", predecessor="decision-0"), expected_decision_sha256=prepared.decision_sha256)
    canary_ready = store.commit(_envelope(state="canary-ready", sequence=2, decision_id="decision-2", predecessor="decision-1"), expected_decision_sha256=shadow.decision_sha256)
    store.commit(_envelope(state="production-canary", sequence=3, decision_id="decision-3", predecessor="decision-2"), expected_decision_sha256=canary_ready.decision_sha256)

    monkeypatch.setattr(adapter_module.ef_py, "RuntimeFacade", lambda _world_count: object())
    with pytest.raises(RuntimeError, match="requires an admitted RolloutDecision"):
        adapter_module.RuntimeFacadeAdapter(1, require_production_admission=True)
    admitted = adapter_module.RuntimeFacadeAdapter(
        1,
        production_rollout_path=str(path),
        production_rollout_key=KEY,
        require_production_admission=True,
        production_release_id="release-p5d-local",
        production_manifest_sha256=MANIFEST,
        production_plan_sha256=PLAN,
    )
    assert admitted.rollout_admission is not None
    assert admitted.rollout_admission.production_authorized


def test_release_controller_cli_commits_signed_slot(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    key_path = tmp_path / "rollout.key"
    slot_path = tmp_path / "rollout.json"
    payload_path.write_bytes(canonical_json_bytes(_payload(state="prepared", sequence=0, decision_id="decision-0")))
    key_path.write_bytes(KEY)
    result = subprocess.run(
        [
            sys.executable,
            "tools/maintenance/commit_runtime_rollout_decision.py",
            "--slot",
            str(slot_path),
            "--payload",
            str(payload_path),
            "--key-file",
            str(key_path),
            "--key-id",
            KEY_ID,
            "--writer-id",
            "release-controller-cli",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["state"] == "prepared"
