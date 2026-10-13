from __future__ import annotations

from dataclasses import replace
import hashlib
import math
import pytest

from python.tasking_contracts.policy import (
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyCheckpoint,
    PolicyCheckpointLoadError,
    PolicyDescriptor,
    PolicyRuntimeBinding,
    admit_policy,
    load_policy_checkpoint,
    select_policy,
    validate_policy_action,
    project_policy_observation,
)
from python.tasking_contracts.common.decision_runtime import (
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


class _BoundModel:
    model_kind = "scripted"

    def __init__(self, action=(0.0, 0.5, 0.0, -0.5)):
        self.action = action
        self.observations = []
        self.closed = False

    def reset(self, *, context):
        self.reset_context = context

    def decide(self, *, observation, context, dt):
        self.observations.append((observation, context, dt))
        return self.action

    def close(self):
        self.closed = True


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


def _checkpoint(policy: PolicyDescriptor) -> PolicyCheckpoint:
    return PolicyCheckpoint(
        checkpoint_ref="artifact://air/policy-v1",
        artifact_sha256="a" * 64,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        observation_view_ref=policy.observation.view_ref,
        observation_major=policy.observation.major,
        observation_minor=policy.observation.minor,
        action_interface_ref=policy.action.interface_ref,
        action_major=policy.action.major,
        action_minor=policy.action.minor,
        owner_ref="owner://policy-registry",
    )


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


def test_external_checkpoint_requires_owner_identity_and_contract_match() -> None:
    base = _policy(category="learned")
    checkpoint = _checkpoint(base)
    policy = replace(base, checkpoint=checkpoint)
    kwargs = dict(
        binding=_binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 2),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    missing = admit_policy(policy, **kwargs)
    assert not missing.admitted
    assert missing.diagnostics[0] == "policy.checkpoint_missing"

    admitted = admit_policy(policy, checkpoint=checkpoint, **kwargs)
    assert admitted.admitted and admitted.checkpoint == checkpoint
    assert admitted.as_dict()["checkpoint"]["artifact_sha256"] == "a" * 64

    changed = admit_policy(
        policy,
        checkpoint=replace(checkpoint, artifact_sha256="b" * 64),
        **kwargs,
    )
    assert not changed.admitted
    assert "policy.checkpoint_identity_mismatch" in changed.diagnostics


def test_external_checkpoint_provenance_reaches_existing_model_context() -> None:
    base = _policy(category="learned")
    checkpoint = _checkpoint(base)
    policy = replace(base, checkpoint=checkpoint)
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        checkpoint=checkpoint,
    )
    model = _BoundModel()
    binding = PolicyRuntimeBinding(
        policy,
        admission,
        model,
        bounds=((-1, 1),) * 4,
        timing="window",
    )
    binding.reset(context={})
    binding.decide(
        observation={"ownship.velocity": [1.0, 2.0, 3.0]},
        context={},
        dt=0.0,
    )
    assert model.observations[0][1]["policy_checkpoint_ref"] == checkpoint.checkpoint_ref
    assert model.observations[0][1]["policy_checkpoint_sha256"] == checkpoint.artifact_sha256
    assert model.observations[0][1]["policy_checkpoint_owner"] == checkpoint.owner_ref


def test_checkpoint_bytes_are_verified_before_owner_loading() -> None:
    base = _policy(category="learned")
    payload = b"owner-checkpoint-bytes"
    checkpoint = replace(_checkpoint(base), artifact_sha256=hashlib.sha256(payload).hexdigest())
    loaded: list[bytes] = []
    model = _BoundModel()

    result = load_policy_checkpoint(
        checkpoint,
        payload,
        owner_loader=lambda value: loaded.append(value) or model,
    )
    assert result is model
    assert loaded == [payload]

    with pytest.raises(PolicyCheckpointLoadError, match="artifact_digest_mismatch"):
        load_policy_checkpoint(checkpoint, b"tampered", owner_loader=lambda value: model)
    assert loaded == [payload]


def test_checkpoint_owner_loader_must_return_existing_model_protocol() -> None:
    base = _policy(category="learned")
    payload = b"owner-checkpoint-bytes"
    checkpoint = replace(_checkpoint(base), artifact_sha256=hashlib.sha256(payload).hexdigest())
    with pytest.raises(PolicyCheckpointLoadError, match="model_protocol_invalid"):
        load_policy_checkpoint(checkpoint, payload, owner_loader=lambda value: object())


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


def test_admitted_policy_binds_existing_model_lifecycle_and_action_owner() -> None:
    policy = _policy()
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    model = _BoundModel()
    binding = PolicyRuntimeBinding(
        policy,
        admission,
        model,
        bounds=((-1, 1),) * 4,
        timing="window",
    )
    runtime = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="a1",
            model_id=policy.policy_id,
            domain="air",
            role_id="autopilot",
            model_kind="scripted",
        ),
        binding,
    )
    runtime.reset(context={"episode": "e1"})
    step = runtime.step(
        observation={"ownship.velocity": [1.0, 2.0, 3.0]},
        clock_s=0.1,
        observation_version="air_observation@1.1",
    )
    action = step.action
    assert action == model.action
    assert model.observations[0][0] == ((1.0, 2.0, 3.0),)
    assert model.observations[0][1]["policy_id"] == policy.policy_id
    runtime.close()
    assert model.closed


def test_policy_runtime_binding_rejects_owner_action_before_projection() -> None:
    policy = _policy()
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    binding = PolicyRuntimeBinding(
        policy,
        admission,
        _BoundModel(action=(0.0, 2.0, 0.0, 0.0)),
        bounds=((-1, 1),) * 4,
        timing="window",
    )
    binding.reset(context={})
    with pytest.raises(ValueError, match=r"policy.action_out_of_bounds:action.values\[1\]"):
        binding.decide(
            observation={"ownship.velocity": [1.0, 2.0, 3.0]},
            context={},
            dt=0.0,
        )


def test_policy_runtime_binding_can_delegate_action_projection_to_owner_endpoint() -> None:
    policy = _policy()
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    projected: list[tuple[float, ...]] = []
    binding = PolicyRuntimeBinding(
        policy,
        admission,
        _BoundModel(),
        bounds=((-1, 1),) * 4,
        timing="window",
        action_projector=lambda action: projected.append(tuple(action)) or {"native": tuple(action)},
    )
    binding.reset(context={})
    result = binding.decide(
        observation={"ownship.velocity": [1.0, 2.0, 3.0]},
        context={},
        dt=0.0,
    )
    assert result == {"native": (0.0, 0.5, 0.0, -0.5)}
    assert projected == [(0.0, 0.5, 0.0, -0.5)]
