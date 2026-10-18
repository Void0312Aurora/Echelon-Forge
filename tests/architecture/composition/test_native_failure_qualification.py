"""Real native setup faults through Python and the maintained facade."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

import ef_py

from python.scenario.runtime.models import ScenarioWorldLayout
from python.rl.runtime.world_batch.adapter import RuntimeFacadeAdapter
from python.tasking_contracts.failure_domains import (
    BatchResult,
    RecoveryAdmission,
    WorldState,
    project_host_fault,
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
    assert not runtime.batch_requires_host_recreate()
    assert "Unknown terrain_type" in runtime.batch_failure_reason()
    # The affected world changed timestep before terrain selection failed.
    assert runtime.world_raw_quarantine(1).get_time_step() == 0.1
    with pytest.raises(RuntimeError, match="failed-closed"):
        runtime.step_batch()
    with pytest.raises(RuntimeError, match="failed-closed"):
        runtime.get_agent_observations_batch([])
    outcome = project_native_batch_fault(
        runtime=runtime,
        batch_generation_ref=str(runtime.batch_generation()),
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
    status = facade.batch_failure_status()
    assert not status.healthy
    assert status.generation == 1
    assert not status.requires_host_recreate
    assert "Unknown terrain_type" in status.failure_reason
    outcome = project_native_batch_fault(
        runtime=facade,
        batch_generation_ref=str(status.generation),
        operation_ref="layout.1",
        operation="apply_world_layout",
        expected_world_indices=frozenset(range(4)),
        error_code="native.layout.exception",
    )
    assert outcome.result is BatchResult.FAILED
    assert outcome.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    assert any(
        diagnostic.startswith("native.batch.failure_reason:Unknown terrain_type")
        for diagnostic in outcome.diagnostics
    )
    assert all(
        row.state is WorldState.UNKNOWN_AFTER_FAULT and row.step_committed is None
        for row in outcome.worlds
    )
    for operation in (facade.step_batch, facade.export_composition_evidence):
        with pytest.raises(RuntimeError, match="failed-closed"):
            operation()
    facade.reset_batch()
    recovered = facade.batch_failure_status()
    assert recovered.healthy
    assert recovered.generation == 2
    assert not recovered.failure_reason
    facade.step_batch()
    assert facade.export_composition_evidence().available


def test_facade_adapter_projects_native_failure_and_recovers_through_owned_reset():
    adapter = RuntimeFacadeAdapter(4)
    layout = ScenarioWorldLayout(
        scenario_data={},
        seed=23,
        rotate_mission_heading_with_world=False,
        world_yaw_deg=0.0,
        world_yaw_origin_x=0.0,
        world_yaw_origin_y=0.0,
        time_step_s=0.1,
        terrain_type="qualification.invalid_terrain",
        terrain_type_source="qualification",
        wind_speed_mps=0.0,
        wind_dir_from_deg=0.0,
        wind_shear_mps_per_km=0.0,
        sun_azimuth_deg=0.0,
        sun_elevation_deg=45.0,
        maritime_configured=False,
        sea_state=0.0,
        wave_heading_deg=0.0,
        wave_period_s=8.0,
        zones=[],
        spawns=[],
    )
    with pytest.raises(ValueError, match="Unknown terrain_type"):
        adapter.apply_world_layout(1, layout)

    status = adapter.batch_failure_status()
    assert not status.healthy
    assert status.generation == 1
    outcome = project_native_batch_fault(
        runtime=adapter,
        batch_generation_ref=str(status.generation),
        operation_ref="adapter.layout.1",
        operation="RuntimeFacadeAdapter.apply_world_layout",
        expected_world_indices=frozenset(range(4)),
        error_code="native.adapter.setup.exception",
    )
    assert outcome.result is BatchResult.FAILED
    assert outcome.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
    with pytest.raises(RuntimeError, match="failed-closed"):
        adapter.step_batch()

    adapter.reset_batch()
    recovered = adapter.batch_failure_status()
    assert recovered.healthy
    assert recovered.generation == 2
    adapter.step_batch()


@pytest.fixture(scope="module")
def native_system_fault_probe():
    root = Path(__file__).resolve().parents[3]
    configured = os.environ.get("CMO_BUILD_DIR", "build")
    build = Path(configured)
    if not build.is_absolute():
        build = root / build
    suffix = ".exe" if os.name == "nt" else ""
    name = f"ef_native_system_fault_probe{suffix}"
    candidates = (build / name, build / "Release" / name, build / "Debug" / name)
    binary = next((path for path in candidates if path.is_file()), None)
    if binary is None and "CMO_BUILD_DIR" in os.environ:
        pytest.fail("configured build is missing ef_native_system_fault_probe")
    if binary is None:
        pytest.skip("build ef_native_system_fault_probe to run native callback fault gates")
    return binary


@pytest.mark.parametrize("world_count", [3, 4])
@pytest.mark.parametrize("worker_threads", [1, 2, 4])
def test_running_native_system_exception_is_fenced_and_requires_process_recreate(
    native_system_fault_probe, world_count, worker_threads
):
    result = subprocess.run(
        [str(native_system_fault_probe), "throw", str(world_count), str(worker_threads)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for phase in ("FAULT_CALLBACK_ENTERED", "FAULT_FENCED", "PROCESS_RECREATE_REQUIRED"):
        assert phase in result.stdout
    _assert_replacement_process(native_system_fault_probe, world_count)


@pytest.mark.parametrize("mode", ["fatal", "hang"])
@pytest.mark.parametrize("world_count", [3, 4])
def test_native_host_fault_is_bounded_and_terminates_generation(
    native_system_fault_probe, mode, world_count
):
    with subprocess.Popen(
        [str(native_system_fault_probe), mode, str(world_count), str(world_count)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as child:
        try:
            stdout, stderr = child.communicate(timeout=3 if mode == "hang" else 20)
            assert mode == "fatal", "nonterminating callback unexpectedly returned"
            assert child.returncode != 0, stdout + stderr
        except subprocess.TimeoutExpired:
            child.kill()
            stdout, stderr = child.communicate(timeout=5)
            assert mode == "hang", "fatal callback did not terminate within its bound"
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)
        assert "FAULT_CALLBACK_ENTERED" in stdout, stdout + stderr
        assert "FAULT_FENCED" not in stdout
        assert child.poll() is not None
        outcome = project_host_fault(
            batch_generation_ref=f"probe.{child.pid}",
            operation_ref="step.1",
            operation="step_batch",
            expected_world_indices=frozenset(range(world_count)),
            error_code=f"host.{mode}",
            process_survived=child.poll() is None,
        )
    assert outcome.result is BatchResult.FAILED
    assert outcome.recovery_admission is RecoveryAdmission.TERMINATE_GENERATION
    assert "host.process_survived:false" in outcome.diagnostics
    assert all(
        row.state is WorldState.UNKNOWN_AFTER_FAULT and row.step_committed is None
        for row in outcome.worlds
    )
    _assert_replacement_process(native_system_fault_probe, world_count)


def _assert_replacement_process(binary, world_count):
    replacement = subprocess.run(
        [str(binary), "healthy", str(world_count), str(world_count)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert replacement.returncode == 0, replacement.stdout + replacement.stderr
    assert "REPLACEMENT_PROCESS_HEALTHY" in replacement.stdout
