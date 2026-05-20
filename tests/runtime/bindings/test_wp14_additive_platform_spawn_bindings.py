from __future__ import annotations

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def _valid_platform_capability() -> object:
    capability = ef_py.PlatformCapability()
    capability.capability_id = "mobility:F-16C_Block50"
    capability.family = "mobility"
    capability.capability_type = "fixed_wing_flight"
    capability.implementation_ref = "DefaultUnitFactory"
    capability.evidence_refs = ["unit_definition:F-16C_Block50"]
    capability.required = True
    capability.supported = True
    return capability


def _valid_capability_bundle(capability: object) -> object:
    bundle = ef_py.CapabilityBundle()
    bundle.bundle_id = "bundle:F-16C_Block50"
    bundle.source_type_name = "F-16C_Block50"
    bundle.capabilities = [capability]
    bundle.template_evidence_ref = "template:F-16C_Block50"
    bundle.evidence_refs = ["content:type_name:F-16C_Block50"]
    bundle.compatibility_path_preserved = True
    return bundle


def _valid_resolved_spawn_plan(capability: object) -> object:
    plan = ef_py.ResolvedPlatformSpawnPlan()
    plan.plan_id = "plan:typed-spawn:lead"
    plan.source_request_kind = "typed_platform_request"
    plan.source_type_name = "F-16C_Block50"
    plan.capability_bundle_id = "bundle:F-16C_Block50"
    plan.resolved_platform_definition_ref = "definition:F-16C_Block50"
    plan.materialization_strategy = "resolved_spawn_plan_bridge"
    plan.template_evidence_ref = "template:F-16C_Block50"
    plan.resolution_evidence_ref = "resolver:type-name"
    plan.materialization_evidence_ref = "materialization:factory-bridge"
    plan.evidence_refs = ["resolved:typed-spawn:lead"]
    plan.resolved_capabilities = [capability]
    plan.compatibility_path_preserved = True
    plan.admitted = True
    return plan


def _valid_typed_platform_spawn_request() -> object:
    capability = _valid_platform_capability()
    request = ef_py.TypedPlatformSpawnRequest()
    request.world_index = 0
    request.side = ef_py.Side.Blue
    request.request_id = "typed-spawn:lead"
    request.source_type_name = "F-16C_Block50"
    request.entity_name = "Lead"
    request.is_agent = True
    request.x = -1400.0
    request.y = 0.0
    request.z = 1200.0
    request.heading = 90.0
    request.vy = 180.0
    request.capability_bundle = _valid_capability_bundle(capability)
    request.resolved_spawn_plan = _valid_resolved_spawn_plan(capability)
    request.facade_evidence_refs = [
        "BatchWorldSetupRequest.typed_platform_spawn_requests"
    ]
    request.compatibility_path_preserved = True
    return request


def test_wp14_additive_platform_spawn_dtos_are_python_constructible_and_round_trip() -> None:
    assert hasattr(ef_py, "PlatformCapability")
    assert hasattr(ef_py, "CapabilityBundle")
    assert hasattr(ef_py, "ResolvedPlatformSpawnPlan")
    assert hasattr(ef_py, "TypedPlatformSpawnRequest")
    assert hasattr(ef_py, "TypedPlatformSpawnValidationResult")
    assert hasattr(ef_py, "validate_typed_platform_spawn_request")

    request = _valid_typed_platform_spawn_request()

    assert request.request_id == "typed-spawn:lead"
    assert request.source_type_name == "F-16C_Block50"
    assert request.capability_bundle.bundle_id == "bundle:F-16C_Block50"
    assert request.capability_bundle.source_type_name == "F-16C_Block50"
    assert list(request.capability_bundle.capabilities)[0].family == "mobility"
    assert request.resolved_spawn_plan.source_request_kind == "typed_platform_request"
    assert list(request.facade_evidence_refs) == [
        "BatchWorldSetupRequest.typed_platform_spawn_requests"
    ]

    setup = ef_py.BatchWorldSetupRequest()
    legacy_spawn = ef_py.WorldSpawnRequest()
    legacy_spawn.type_name = "F-16C_Block50"
    setup.spawn_requests = [legacy_spawn]
    setup.typed_platform_spawn_requests = [request]

    assert list(setup.spawn_requests)[0].type_name == "F-16C_Block50"
    assert list(setup.typed_platform_spawn_requests)[0].request_id == "typed-spawn:lead"


def test_wp14_valid_typed_platform_spawn_request_validates_in_python() -> None:
    result = ef_py.validate_typed_platform_spawn_request(
        _valid_typed_platform_spawn_request()
    )

    assert bool(result.valid)
    assert not bool(result.fail_closed)
    assert result.rejection_reason == ""
    assert list(result.errors) == []


def test_wp14_typed_platform_spawn_request_fails_closed_for_missing_fields() -> None:
    missing_request_id = _valid_typed_platform_spawn_request()
    missing_request_id.request_id = ""

    result = ef_py.validate_typed_platform_spawn_request(missing_request_id)

    assert not bool(result.valid)
    assert bool(result.fail_closed)
    assert result.rejection_reason == "typed_platform_spawn_request_id_required"
    assert "request_id is required" in list(result.errors)

    missing_evidence = _valid_typed_platform_spawn_request()
    missing_evidence.facade_evidence_refs = []

    result = ef_py.validate_typed_platform_spawn_request(missing_evidence)

    assert not bool(result.valid)
    assert bool(result.fail_closed)
    assert result.rejection_reason == "typed_platform_spawn_evidence_required"
