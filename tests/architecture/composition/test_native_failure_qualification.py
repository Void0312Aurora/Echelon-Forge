"""Real native setup faults through Python and the maintained facade."""

from __future__ import annotations

import pytest

import ef_py

from python.tasking_contracts.failure_domains import (
    BatchResult,
    RecoveryAdmission,
    WorldState,
    project_native_batch_fault,
)


@pytest.mark.parametrize("world_count", [3, 4])
@pytest.mark.parametrize("worker_threads", [1, 2, 4])
def test_native_partial_setup_failure_is_fenced_and_projects_unknown(world_count, worker_threads):
    runtime = ef_py.WorldBatchRuntime(world_count)
    runtime.set_worker_threads(worker_threads)
    runtime.apply_world_setup_batch([11], [], [], [], [], [0.2])
    request = ef_py.WorldTerrainAssignment()
    request.world_index = 1
    request.terrain_type = "qualification.invalid_terrain"
    with pytest.raises(ValueError, match="Unknown terrain_type"):
        runtime.apply_world_setup_batch([23], [request], [], [], [], [0.1])
    assert not runtime.batch_healthy()
    assert "Unknown terrain_type" in runtime.batch_failure_reason()
    # The affected world changed timestep before terrain selection failed.
    assert runtime.world_raw_quarantine(1).get_time_step() == 0.1
    with pytest.raises(RuntimeError, match="failed-closed"):
        runtime.step_batch()
    with pytest.raises(RuntimeError, match="failed-closed"):
        runtime.get_agent_observations_batch([])
    outcome = project_native_batch_fault(
        runtime=runtime,
        batch_generation_ref="qualification.native.failed",
        operation_ref="setup.1",
        operation="apply_world_setup_batch",
        expected_world_indices=frozenset(range(world_count)),
        error_code="native.setup.exception",
    )
    assert outcome.result is BatchResult.FAILED
    assert outcome.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    assert all(
        row.state is WorldState.UNKNOWN_AFTER_FAULT and row.step_committed is None
        for row in outcome.worlds
    )
    with pytest.raises(ValueError):
        runtime.reset_batch([11, 17])
    assert not runtime.batch_healthy()
    runtime.reset_batch([31])
    assert runtime.batch_healthy() and not runtime.batch_failure_reason()
    runtime.step_batch()


def test_facade_keeps_native_failure_fence_and_explicit_reset_recovery():
    facade = ef_py.RuntimeFacade(4)
    request = ef_py.RuntimeWorldLayoutRequest()
    request.world_index = 99
    with pytest.raises(IndexError):
        facade.apply_world_layout(request)
    facade.step_batch()  # Index preflight did not poison the generation.
    request.world_index = 1
    request.time_steps = [0.1]
    request.terrain_type = "qualification.invalid_terrain"
    with pytest.raises(ValueError, match="Unknown terrain_type"):
        facade.apply_world_layout(request)
    for operation in (facade.step_batch, facade.export_composition_evidence):
        with pytest.raises(RuntimeError, match="failed-closed"):
            operation()
    facade.reset_batch()
    facade.step_batch()
    assert facade.export_composition_evidence().available
