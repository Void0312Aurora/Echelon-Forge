from __future__ import annotations

import pytest

from tools.maintenance.p5d_rollout_operations import RolloutOperationsError
from tools.maintenance.p5d_rollout_operations import RolloutTelemetryRecorder
from tools.maintenance.p5d_rollout_operations import RolloutTelemetrySnapshot
from tools.maintenance.p5d_rollout_operations import rehearse_package_restart
from tools.maintenance.p5d_rollout_operations import rehearse_same_release_checkpoint_recovery


PLAN = "a" * 64


def _healthy_recorder() -> RolloutTelemetryRecorder:
    recorder = RolloutTelemetryRecorder(
        release_id="release-operations-test",
        plan_sha256=PLAN,
        epoch="epoch-1",
    )
    recorder.record_admission(accepted=True)
    recorder.record_replacement(success=True, duration_s=1.2)
    recorder.record_drain(completed=True)
    recorder.record_backout(recovered=True, duration_s=2.5)
    recorder.record_crash_receipt(reconciled=True, delay_s=1.0)
    recorder.record_artifact_retrieval(available=True)
    recorder.record_caller_adoption(adopted=True)
    return recorder


def test_rollout_telemetry_snapshot_is_tagged_and_meets_initial_slos() -> None:
    recorder = _healthy_recorder()
    snapshot = recorder.snapshot()
    report = recorder.evaluate_slo()

    assert report.passed
    assert report.reasons == ()
    document = snapshot.to_document()
    assert document["schema_version"] == "echelon_forge.p5d_rollout_telemetry.v1"
    assert document["release_id"] == "release-operations-test"
    assert document["plan_sha256"] == PLAN
    assert document["ratios"]["caller_adoption"] == 1.0
    assert "secret" not in str(document).lower()


def test_rollout_telemetry_fails_closed_on_safety_and_missing_observations() -> None:
    recorder = RolloutTelemetryRecorder(
        release_id="release-operations-test",
        plan_sha256=PLAN,
        epoch="epoch-1",
    )
    recorder.record_safety_event(wrong_epoch_result=True)
    report = recorder.evaluate_slo()

    assert not report.passed
    assert "zero-tolerance-safety-event" in report.reasons
    assert "replacement-observation-missing" in report.reasons
    with pytest.raises(RolloutOperationsError, match="successes exceed"):
        RolloutTelemetrySnapshot(
            release_id="release-operations-test",
            plan_sha256=PLAN,
            epoch="epoch-1",
            replacement_attempts=1,
            replacement_successes=2,
        )


def test_same_release_checkpoint_recovery_requires_new_epoch_and_no_truth_export() -> None:
    result = rehearse_same_release_checkpoint_recovery(
        current_generation=2,
        source_epoch="epoch-1",
        target_epoch="epoch-2",
        checkpoint_available=True,
        checkpoint_validated=True,
        source_faulted=True,
        source_truth_exported=False,
        admission_closed=True,
        caller_resynchronized=True,
        receipt_finalized=True,
        recovery_duration_s=4.0,
    )
    assert result.accepted
    assert result.protocol == "same-release-checkpoint-recovery"
    assert result.source_generation == result.target_generation == 2
    assert result.target_epoch != result.source_epoch

    with pytest.raises(RolloutOperationsError, match="must not be exported"):
        rehearse_same_release_checkpoint_recovery(
            current_generation=2,
            source_epoch="epoch-1",
            target_epoch="epoch-2",
            checkpoint_available=True,
            checkpoint_validated=True,
            source_faulted=True,
            source_truth_exported=True,
            admission_closed=True,
            caller_resynchronized=True,
            receipt_finalized=True,
            recovery_duration_s=4.0,
        )


def test_package_restart_requires_stop_new_boot_and_caller_resync() -> None:
    result = rehearse_package_restart(
        current_generation=2,
        target_generation=1,
        source_epoch="epoch-2",
        target_epoch="epoch-3",
        checkpoint_available=True,
        package_available=True,
        admission_closed=True,
        journals_finalized=True,
        source_stopped=True,
        new_boot_identity=True,
        caller_resynchronized=True,
        receipt_finalized=True,
        recovery_duration_s=5.0,
    )
    assert result.accepted
    assert result.protocol == "package-restart-from-checkpoint"
    assert result.package_restarted
    assert result.checkpoint_validated

    with pytest.raises(RolloutOperationsError, match="new boot identity"):
        rehearse_package_restart(
            current_generation=2,
            target_generation=1,
            source_epoch="epoch-2",
            target_epoch="epoch-3",
            checkpoint_available=True,
            package_available=True,
            admission_closed=True,
            journals_finalized=True,
            source_stopped=True,
            new_boot_identity=False,
            caller_resynchronized=True,
            receipt_finalized=True,
            recovery_duration_s=5.0,
        )


def test_package_restart_without_checkpoint_is_a_new_run_and_irreversible_boundary_fails_stop() -> None:
    result = rehearse_package_restart(
        current_generation=2,
        target_generation=1,
        source_epoch="epoch-2",
        target_epoch="epoch-3",
        checkpoint_available=False,
        package_available=True,
        admission_closed=True,
        journals_finalized=True,
        source_stopped=True,
        new_boot_identity=True,
        caller_resynchronized=True,
        receipt_finalized=True,
        recovery_duration_s=5.0,
    )
    assert result.accepted
    assert result.protocol == "package-restart-new-run"
    assert not result.checkpoint_validated

    fail_stop = rehearse_package_restart(
        current_generation=2,
        target_generation=1,
        source_epoch="epoch-2",
        target_epoch="epoch-3",
        checkpoint_available=True,
        package_available=True,
        admission_closed=False,
        journals_finalized=False,
        source_stopped=False,
        new_boot_identity=False,
        caller_resynchronized=False,
        receipt_finalized=False,
        recovery_duration_s=0.0,
        irreversible_write_boundary="external-write-v2",
    )
    assert not fail_stop.accepted
    assert fail_stop.fail_stop
    assert fail_stop.protocol == "stop-or-roll-forward"
