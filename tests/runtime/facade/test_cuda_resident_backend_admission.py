from __future__ import annotations

from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_CANDIDATE_FEATURES = [
    "canonical_world_setup.fixed_air_fixture",
    "pilot_action.flight_controls",
    "airframe_dynamics.six_dof",
    "instruments.air_execution",
    "observation.agent_air_execution",
    "reward.execution_episode",
    "termination.execution_episode",
    "export.host_snapshot",
    "export.device_observation_view",
]


def test_runtime_batch_config_keeps_the_two_field_cpu_default() -> None:
    config = ef_py.RuntimeBatchConfig()

    assert config.world_count == 0
    assert config.worker_threads == 1
    assert not hasattr(config, "backend_profile_id")
    assert not hasattr(config, "capability_manifest_id")

    config_fields = Path(
        resolve_repo_path("src", "runtime", "facade", "detail", "runtime_batch_config.inc")
    ).read_text(encoding="utf-8")
    assert (
        sum(
            line.startswith("EF_RUNTIME_BATCH_CONFIG_FIELD(") for line in config_fields.splitlines()
        )
        == 2
    )


def test_cpu_backend_request_is_explicitly_admitted_without_mutation() -> None:
    facade = ef_py.RuntimeFacade(0)
    request = ef_py.RuntimeBackendRequest()
    request.backend_profile_id = "cpu_exact.reference"
    request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"

    admission = facade.admit_backend_request(request)

    assert admission.admitted is True
    assert admission.maintained_selection is True
    assert admission.experimental_selection is False
    assert facade.batch_config().world_count == 0


def test_candidate_request_stays_rejected_until_backend_is_compiled() -> None:
    facade = ef_py.RuntimeFacade(0)
    request = ef_py.RuntimeBackendRequest()
    request.backend_profile_id = "resident_state.unmaintained_candidate"
    request.capability_manifest_id = "cuda_resident.air_execution.fixed_step.v1"
    request.parity_budget_ref = "parity_budget.resident_state.unmaintained_candidate.v1"
    request.requested_feature_ids = _CANDIDATE_FEATURES
    request.allow_unmaintained_candidate = True

    admission = facade.admit_backend_request(request)

    assert admission.admitted is False
    assert admission.maintained_selection is False
    assert admission.experimental_selection is False
    assert admission.rejection_reason == "backend_request_experimental_backend_not_compiled"
    capabilities = facade.capabilities()
    assert capabilities.supports_resident_state is False
    assert capabilities.supports_exact_gpu_backend is False
    assert capabilities.supports_device_observation_view is False


def test_missing_and_unsupported_candidate_features_fail_closed() -> None:
    facade = ef_py.RuntimeFacade(0)

    missing = ef_py.RuntimeBackendRequest()
    missing_admission = facade.admit_backend_request(missing)
    assert missing_admission.rejection_reason == "backend_request_missing_profile_id"

    unsupported = ef_py.RuntimeBackendRequest()
    unsupported.backend_profile_id = "resident_state.unmaintained_candidate"
    unsupported.capability_manifest_id = "cuda_resident.air_execution.fixed_step.v1"
    unsupported.parity_budget_ref = "parity_budget.resident_state.unmaintained_candidate.v1"
    unsupported.requested_feature_ids = [*_CANDIDATE_FEATURES, "pilot_action.weapon_controls"]
    unsupported.allow_unmaintained_candidate = True

    unsupported_admission = facade.admit_backend_request(unsupported)
    assert (
        unsupported_admission.rejection_reason
        == "backend_request_feature_not_supported_by_manifest"
    )
