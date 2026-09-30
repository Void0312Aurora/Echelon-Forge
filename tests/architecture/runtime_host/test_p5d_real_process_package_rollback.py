from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

from tools.maintenance.p5d_process_rollback_drill import launch_runtime_process
from tools.maintenance.p5d_rollout_operations import rehearse_package_restart
from tools.maintenance.runtime_authority_contracts import authority_digest_sha256
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes as authority_json_bytes
from tools.maintenance.runtime_durable_artifact_ledger import SQLiteArtifactLedger
from tools.maintenance.runtime_durable_artifact_ledger import RECEIPT_MEDIA_TYPE
from tools.maintenance.runtime_durable_artifact_ledger import RELEASE_MANIFEST_MEDIA_TYPE
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope

from tests.architecture.runtime_host import test_rollout_evidence_binding as evidence_fixtures


def _sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_dir(name: str) -> Path:
  path = Path(name)
  if not path.is_absolute():
    path = Path(__file__).resolve().parents[3] / path
  return path.resolve()


def _release_for_packages(package_digests: tuple[str, str]) -> dict[str, object]:
  release = deepcopy(evidence_fixtures._release_envelope())
  payload = release["payload"]
  payload["package_set"] = [
    {"name": "cmo-n", "sha256": package_digests[0]},
    {"name": "cmo-n-minus-1", "sha256": package_digests[1]},
  ]
  release["payload_sha256"] = authority_digest_sha256(
    "release.manifest",
    RELEASE_MANIFEST_MEDIA_TYPE,
    authority_json_bytes(payload),
  )
  return release


def _decision(*, release: dict[str, object], state: str, sequence: int, decision_id: str, predecessor: str, writer_generation: str, plan_sha256: str = evidence_fixtures.PLAN) -> dict[str, object]:
  payload = evidence_fixtures._rollout_payload(
      state=state,
      sequence=sequence,
      decision_id=decision_id,
      predecessor=predecessor,
      manifest=release["payload_sha256"],
    ) | {"writer_generation": writer_generation, "plan_sha256": plan_sha256}
  return build_rollout_decision_envelope(
    payload,
    key_id=evidence_fixtures.KEY_ID,
    signing_key=evidence_fixtures.KEY,
  )


def _receipt_for(*, decision: dict[str, object], release: dict[str, object], package_digest: str, wheel_digest: str, plan_sha256: str = evidence_fixtures.PLAN) -> dict[str, object]:
  receipt = evidence_fixtures._receipt_envelope(
    decision_id=decision["payload"]["decision_id"],
    manifest_sha256=release["payload_sha256"],
  )
  payload = receipt["payload"]
  payload["release_binding"]["rollout_decision_sha256"] = decision["payload_sha256"]
  payload["plan_binding"]["plan_sha256"] = plan_sha256
  payload["package"]["digest"] = package_digest
  payload["package"]["wheel_digest"] = wheel_digest
  receipt["payload_sha256"] = authority_digest_sha256(
    "runtime.run-receipt",
    RECEIPT_MEDIA_TYPE,
    authority_json_bytes(payload),
  )
  return receipt


def test_real_process_and_package_restart_are_bound_to_durable_backout(tmp_path: Path) -> None:
  current_build = _build_dir("build-long-horizon-p5d-wheel")
  rollback_build = _build_dir("build-long-horizon-p5c-wheel-final3")
  current_binding = next(current_build.glob("Release/ef_py*.pyd"))
  rollback_binding = next(rollback_build.glob("Release/ef_py*.pyd"))
  current_package = hashlib.sha256(
    f"generation=1\nbuild={current_build}\nnative={_sha256(current_binding)}\n".encode()
  ).hexdigest()
  rollback_package = hashlib.sha256(
    f"generation=0\nbuild={rollback_build}\nnative={_sha256(rollback_binding)}\n".encode()
  ).hexdigest()
  release = _release_for_packages((current_package, rollback_package))
  ledger = SQLiteArtifactLedger(tmp_path / "ledger")
  token = ledger.acquire_fence(
    "rollout:release-evidence-test",
    "release-controller",
    role="release_controller",
  )
  process = None
  rollback_process = None
  try:
    predecessor = ""
    states = ("prepared", "shadow", "canary-ready", "production-canary")
    for sequence, state in enumerate(states):
      decision = _decision(
        release=release,
        state=state,
        sequence=sequence,
        decision_id=f"decision-real-{sequence}",
        predecessor=predecessor,
        writer_generation="1",
      )
      ledger.commit_rollout_admission(
        token,
        decision,
        release_manifest=release,
        run_receipt=_receipt_for(
          decision=decision,
          release=release,
          package_digest=current_package,
          wheel_digest=_sha256(current_binding),
        ),
        verification_key=evidence_fixtures.KEY,
        audit_identity="release-controller-real-drill",
        expected_slot_version=sequence,
        expected_package_digest=current_package,
        expected_wheel_digest=_sha256(current_binding),
      )
      predecessor = decision["payload"]["decision_id"]

    process = launch_runtime_process(
      current_build,
      epoch="epoch-production-canary",
      state_dir=tmp_path / "processes",
    )
    assert process.observation["pid"] > 0
    assert process.observation["boot_identity"]
    source_boot_identity = process.observation["boot_identity"]
    killed = ledger.trip_rollout_kill_switch(
      token,
      ["package_rollback_drill"],
      verification_key=evidence_fixtures.KEY,
      audit_identity="release-controller-real-drill",
    )
    assert not killed["admissions_open"]
    process.stop()
    process = None

    backout = _decision(
      release=release,
      state="backed-out",
      sequence=4,
      decision_id="decision-real-backout",
      predecessor=predecessor,
      writer_generation="0",
      plan_sha256="f" * 64,
    )
    ledger.commit_rollout_admission(
      token,
      backout,
      release_manifest=release,
      run_receipt=_receipt_for(
        decision=backout,
        release=release,
        package_digest=rollback_package,
        wheel_digest=_sha256(rollback_binding),
        plan_sha256="f" * 64,
      ),
      verification_key=evidence_fixtures.KEY,
      audit_identity="release-controller-real-drill",
      expected_slot_version=4,
      expected_package_digest=rollback_package,
      expected_wheel_digest=_sha256(rollback_binding),
      admissions_open=False,
      writer_advancement_frozen=True,
      kill_switch_reasons=("package_rollback_drill",),
    )
    rollback_process = launch_runtime_process(
      rollback_build,
      epoch="epoch-package-rollback",
      state_dir=tmp_path / "processes",
    )
    assert rollback_process.observation["epoch"] == "epoch-package-rollback"
    assert rollback_process.observation["boot_identity"] != source_boot_identity
    result = rehearse_package_restart(
      current_generation=1,
      target_generation=0,
      source_epoch="epoch-production-canary",
      target_epoch="epoch-package-rollback",
      checkpoint_available=True,
      package_available=True,
      admission_closed=True,
      journals_finalized=True,
      source_stopped=True,
      new_boot_identity=True,
      caller_resynchronized=True,
      receipt_finalized=True,
      recovery_duration_s=1.0,
    )
    assert result.accepted
    assert result.package_restarted
    assert result.checkpoint_validated
  finally:
    if process is not None:
      process.stop()
    if rollback_process is not None:
      rollback_process.stop()
    ledger.close()
