from __future__ import annotations

from python.tasking_contracts.policy import (
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyDescriptor,
    admit_policy,
)


def _policy(*, category: str = "scripted", major: int = 1, field: str = "ownship.velocity") -> PolicyDescriptor:
    return PolicyDescriptor(
        "community.air.policy", "1.0.0", (category,),
        ObservationContract(
            "air_observation", major, 1,
            required=(FieldSpec(field, "Vector3", (3,), "meter_per_second", "agent_observation"),),
        ),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
        legacy_model_kind=category,
    )


def _binding() -> AgentBinding:
    return AgentBinding(
        "autopilot", frozenset({"agent_observation", "belief"}),
        frozenset({"PilotActionAssignment"}), frozenset({"platform_control"}),
    )


def _catalogue() -> dict[str, FieldSpec]:
    return {"ownship.velocity": FieldSpec("ownship.velocity", "Vector3", (3,), "meter_per_second")}


def test_scripted_and_learned_categories_share_contract_admission() -> None:
    kwargs = dict(
        binding=_binding(), field_catalogue=_catalogue(), observation_version=(1, 2),
        action_versions={"PilotActionAssignment": (1, 0)}, action_dimensions={"PilotActionAssignment": 4},
    )
    assert admit_policy(_policy(category="scripted"), **kwargs).admitted
    assert admit_policy(_policy(category="learned"), **kwargs).admitted


def test_unknown_category_does_not_grant_authority() -> None:
    policy = PolicyDescriptor(
        "community.custom", "1", ("human", "unknown.community"),
        ObservationContract("air_observation", 1, 0, required=()),
        ActionContract("PilotActionAssignment", 1, 0, 4, "mission_command"),
    )
    result = admit_policy(
        policy, _binding(), field_catalogue={}, observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)}, action_dimensions={"PilotActionAssignment": 4},
    )
    assert result.admitted is False
    assert "policy.authority_scope_unauthorized" in result.diagnostics[0]


def test_missing_field_shape_and_action_dimension_fail_closed() -> None:
    result = admit_policy(
        _policy(field="tracks"), _binding(), field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)}, action_dimensions={"PilotActionAssignment": 3},
    )
    assert result.admitted is False
    assert any(item.startswith("policy.required_field_missing") for item in result.diagnostics)
    assert any(item.startswith("policy.action_dimension_mismatch") for item in result.diagnostics)


def test_major_version_and_unauthorized_truth_source_are_rejected() -> None:
    policy = PolicyDescriptor(
        "p", "1", (),
        ObservationContract("view", 2, 0, required=(FieldSpec("truth", "Scalar", source_layer="world_truth"),)),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy, _binding(),
        field_catalogue={"truth": FieldSpec("truth", "Scalar", source_layer="world_truth")},
        observation_version=(1, 0), action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert result.admitted is False
    assert "policy.version_major_mismatch" in result.diagnostics[0]
    assert any(item.startswith("policy.field_source_unauthorized") for item in result.diagnostics)


def test_unknown_action_interface_is_rejected_even_with_valid_category() -> None:
    policy = _policy()
    policy = PolicyDescriptor(
        policy.policy_id, policy.version, policy.categories, policy.observation,
        ActionContract("unknown", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy, _binding(), field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={}, action_dimensions={},
    )
    assert result.admitted is False
    assert "policy.action_interface_unknown:action.interface_ref.unknown" in result.diagnostics
