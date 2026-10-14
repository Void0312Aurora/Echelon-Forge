from __future__ import annotations

from dataclasses import replace
import math
import pytest

from python.tasking_contracts.policy import (
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyDescriptor,
    admit_policy,
    select_policy,
    validate_policy_action,
    project_policy_observation,
)


def _policy(
    *, category: str = "scripted", major: int = 1, field: str = "ownship.velocity"
) -> PolicyDescriptor:
    return PolicyDescriptor(
        "community.air.policy",
        "1.0.0",
        (category,),
        ObservationContract(
            "air_observation",
            major,
            1,
            required=(FieldSpec(field, "Vector3", (3,), "meter_per_second", "agent_observation"),),
        ),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
        legacy_model_kind=category,
    )


def _binding() -> AgentBinding:
    return AgentBinding(
        "autopilot",
        frozenset({"agent_observation", "belief"}),
        frozenset({"PilotActionAssignment"}),
        frozenset({"platform_control"}),
    )


def _catalogue() -> dict[str, FieldSpec]:
    return {"ownship.velocity": FieldSpec("ownship.velocity", "Vector3", (3,), "meter_per_second")}


def test_scripted_and_learned_categories_share_contract_admission() -> None:
    kwargs = dict(
        binding=_binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 2),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert admit_policy(_policy(category="scripted"), **kwargs).admitted
    assert admit_policy(_policy(category="learned"), **kwargs).admitted


def test_unknown_category_does_not_grant_authority() -> None:
    policy = PolicyDescriptor(
        "community.custom",
        "1",
        ("human", "unknown.community"),
        ObservationContract("air_observation", 1, 0, required=()),
        ActionContract("PilotActionAssignment", 1, 0, 4, "mission_command"),
    )
    result = admit_policy(
        policy,
        _binding(),
        field_catalogue={},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert result.admitted is False
    assert "policy.authority_scope_unauthorized" in result.diagnostics[0]


def test_missing_field_shape_and_action_dimension_fail_closed() -> None:
    result = admit_policy(
        _policy(field="tracks"),
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 3},
    )
    assert result.admitted is False
    assert any(item.startswith("policy.required_field_missing") for item in result.diagnostics)
    assert any(item.startswith("policy.action_dimension_mismatch") for item in result.diagnostics)


def test_present_optional_field_uses_the_same_typed_checks() -> None:
    policy = PolicyDescriptor(
        "p",
        "1",
        (),
        ObservationContract(
            "view",
            1,
            0,
            optional=(FieldSpec("temperature", "Scalar", (), "kelvin"),),
        ),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy,
        _binding(),
        field_catalogue={"temperature": FieldSpec("temperature", "Vector3", (3,), "meter")},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert result.admitted is False
    assert "policy.field_semantics_mismatch:observation.optional.temperature" in result.diagnostics


def test_registered_action_interface_without_dimension_evidence_is_rejected() -> None:
    result = admit_policy(
        _policy(),
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={},
    )
    assert result.admitted is False
    assert (
        "policy.action_dimension_missing:action.dimension.PilotActionAssignment"
        in result.diagnostics
    )


def test_major_version_and_unauthorized_truth_source_are_rejected() -> None:
    policy = PolicyDescriptor(
        "p",
        "1",
        (),
        ObservationContract(
            "view", 2, 0, required=(FieldSpec("truth", "Scalar", source_layer="world_truth"),)
        ),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy,
        _binding(),
        field_catalogue={"truth": FieldSpec("truth", "Scalar", source_layer="world_truth")},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert result.admitted is False
    assert "policy.version_major_mismatch" in result.diagnostics[0]
    assert any(item.startswith("policy.field_source_unauthorized") for item in result.diagnostics)


def test_unknown_action_interface_is_rejected_even_with_valid_category() -> None:
    policy = _policy()
    policy = PolicyDescriptor(
        policy.policy_id,
        policy.version,
        policy.categories,
        policy.observation,
        ActionContract("unknown", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={},
        action_dimensions={},
    )
    assert result.admitted is False
    assert "policy.action_interface_unknown:action.interface_ref.unknown" in result.diagnostics


def test_source_provenance_and_action_timing_are_semantics() -> None:
    result = admit_policy(
        _policy(),
        _binding(),
        field_catalogue={
            "ownship.velocity": replace(_catalogue()["ownship.velocity"], source_layer="belief")
        },
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        action_timings={"PilotActionAssignment": "per_tick"},
    )
    assert not result.admitted
    assert any("field_semantics_mismatch" in d for d in result.diagnostics)
    assert "policy.action_timing_mismatch:action.timing" in result.diagnostics


@pytest.mark.parametrize("invalid", [2.0, math.nan, math.inf])
def test_action_rejects_out_of_bounds_or_non_finite_value(invalid) -> None:
    assert validate_policy_action(
        _policy(), (0.0, invalid, 0.0, 0.0), bounds=((-1, 1),) * 4, timing="window"
    ) == ("policy.action_out_of_bounds:action.values[1]",)


def test_explicit_policy_selection_and_legacy_bridge_fail_closed() -> None:
    policies = {"a@1": _policy(), "b@1": replace(_policy(category="new.author.tag"), policy_id="b")}
    assert select_policy(policies, policy_ref="b@1").categories == ("new.author.tag",)
    with pytest.raises(ValueError, match="selection_ambiguous"):
        select_policy(policies)
    with pytest.raises(ValueError, match="legacy_model_kind_mismatch"):
        select_policy(policies, policy_ref="a@1", legacy_model_kind="learned")


def test_optional_minor_projection_has_explicit_default_and_stable_order() -> None:
    base = _policy()
    policy = replace(
        base,
        observation=replace(
            base.observation, optional=(FieldSpec("temperature", "Scalar", unit="kelvin"),)
        ),
    )
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 2),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert admission.admitted
    with pytest.raises(ValueError, match="field_value_missing:temperature"):
        project_policy_observation(
            policy, admission, {"ownship.velocity": [1, 2, 3]}, optional_defaults={}
        )
    values, sources = project_policy_observation(
        policy,
        admission,
        {"ownship.velocity": [1, 2, 3]},
        optional_defaults={"temperature": 273.15},
    )
    assert values == ((1, 2, 3), 273.15)
    assert sources == ("agent_observation:ownship.velocity", "explicit_default:temperature")
