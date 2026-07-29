from __future__ import annotations

from tests.architecture.helpers import REPO_ROOT


ADMISSION_HEADER = REPO_ROOT / "src/runtime/contracts/cuda_resident_backend_admission.h"
PARITY_HEADER = REPO_ROOT / "src/runtime/contracts/parity_budget_contracts.h"
SELECTED_SLICE_HEADER = REPO_ROOT / "src/runtime/contracts/cuda_resident_selected_slice_contract.h"
RUNTIME_CONFIG_FIELDS = REPO_ROOT / "src/runtime/facade/detail/runtime_batch_config.inc"
FACADE_CONFIG = REPO_ROOT / "src/runtime/facade/runtime_facade_config.cpp"


def test_candidate_manifest_is_bounded_and_backend_neutral() -> None:
    text = ADMISSION_HEADER.read_text(encoding="utf-8")

    for required in (
        "cuda_resident.air_execution.fixed_step.v1",
        "canonical_world_setup.fixed_air_fixture",
        "pilot_action.flight_controls",
        "airframe_dynamics.six_dof",
        "instruments.air_execution",
        "observation.agent_air_execution",
        "reward.execution_episode",
        "termination.execution_episode",
        "export.host_snapshot",
        "export.device_observation_view",
    ):
        assert required in text

    for forbidden in (
        '"pilot_action.sensor_controls"',
        '"pilot_action.weapon_controls"',
        '"dynamic_entity_families"',
        '"spatial_interaction"',
        '"weapons_and_effects"',
        '"naval"',
        '"ground"',
    ):
        assert forbidden in text

    assert "cuda_runtime" not in text
    assert "flecs" not in text.lower()
    assert "void *" not in text
    assert "bounded_air_execution_required_feature_contract" in text
    assert "bounded_air_execution_supported_feature_contract" in text
    assert "bounded_air_execution_forbidden_feature_contract" in text
    assert "manifest != bounded_air_execution_manifest()" in text


def test_selected_slice_budget_declares_typed_surfaces_and_all_barriers() -> None:
    text = PARITY_HEADER.read_text(encoding="utf-8")
    selected_slice_text = SELECTED_SLICE_HEADER.read_text(encoding="utf-8")

    for barrier in (
        '"input_injection"',
        '"stage_publish"',
        '"partial_sync_commit"',
        '"window_commit"',
        '"export"',
    ):
        assert barrier in text

    assert 'kParityComparatorExact = "exact"' in text
    assert '"absolute_or_relative"' in text
    assert ".absolute_tolerance = 1.0e-9" in text
    assert ".relative_tolerance = 1.0e-12" in text
    assert ".absolute_tolerance = 1.0e-8" in text
    assert ".relative_tolerance = 1.0e-10" in text
    assert '"disabled for the RB2 selected slice' in text
    assert ".enabled = false" in text
    assert '"agent_observation_identity"' in text
    assert '"agent_observation_numeric"' in text
    assert 'current_selected_field("observation.id", "AgentObservation", unsigned_integer' in text
    assert 'future_selected_field("events.timestamp", "EventOrderKeyContract", float64' in text
    assert 'future_selected_field("export.schema_version", "ExportEnvelopeContract", string' in text
    assert (
        "record.selected_slice_fields != resident_candidate_selected_slice_field_contract()" in text
    )

    for typed_surface in (
        "struct DeviceClockContract",
        "struct ShardVersionContract",
        "struct SnapshotLineageContract",
        "struct SnapshotIdentityContract",
        "struct EventOrderKeyContract",
        "struct ExportEnvelopeContract",
    ):
        assert typed_surface in selected_slice_text

    for exact_snapshot_field in (
        "world_id",
        "global_version",
        "barrier_id",
        "barrier_sequence",
        "shard_versions",
        "lineage",
    ):
        assert exact_snapshot_field in selected_slice_text


def test_backend_request_does_not_expand_runtime_batch_config_or_enable_cuda() -> None:
    config_fields = RUNTIME_CONFIG_FIELDS.read_text(encoding="utf-8")
    facade_config = FACADE_CONFIG.read_text(encoding="utf-8")

    assert (
        sum(
            line.startswith("EF_RUNTIME_BATCH_CONFIG_FIELD(") for line in config_fields.splitlines()
        )
        == 2
    )
    assert "backend_profile_id" not in config_fields
    assert "capability_manifest_id" not in config_fields
    assert ".compiled_experimental_backend = false" in facade_config
    assert "supports_resident_state = false" in facade_config
    assert "supports_exact_gpu_backend = false" in facade_config
    assert "supports_device_observation_view = false" in facade_config
