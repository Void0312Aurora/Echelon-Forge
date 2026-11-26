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
    PolicyAdmission,
    PolicyDescriptor,
    PolicyRuntimeBinding,
    admit_policy,
    load_policy_checkpoint,
    select_policy,
    validate_policy_action,
    validate_policy_admission,
    project_policy_observation,
)
from python.tasking_contracts import policy as policy_contract
from python.tasking_contracts.common.decision_registry import (
    DecisionModelRegistration,
    DecisionModelRegistry,
    LegacyDecisionModelAdapter,
)
from python.tasking_contracts.common.decision_runtime import (
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


def maintained_observation_view_spec():
    # Only the maintained-view integration cases require the native adapter.
    pytest.importorskip("ef_py")
    from python.rl.runtime.world_batch.typed_observation_view import (
        maintained_observation_view_spec as owner_spec,
    )
    return owner_spec()


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


def _admit(policy: PolicyDescriptor, binding: AgentBinding | None = None, **overrides):
    evidence = dict(
        field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4}, checkpoint=policy.checkpoint,
    )
    evidence.update(overrides)
    return admit_policy(policy, _binding() if binding is None else binding, **evidence)


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


def test_selected_maintained_observation_view_is_admitted_and_recorded() -> None:
    policy = PolicyDescriptor(
        "community.air.policy",
        "1.0.0",
        ("learned",),
        ObservationContract("gym_envs.observation_view", 1, 0, required=()),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy,
        _binding(),
        field_catalogue={},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        observation_view=maintained_observation_view_spec(),
    )
    assert result.admitted
    assert result.observation_view_ref == "gym_envs.observation_view"
    assert result.observation_view_schema_version == "1.0"
    assert result.as_dict()["observation_view_ref"] == "gym_envs.observation_view"


def test_selected_observation_view_provenance_reaches_existing_model_context() -> None:
    policy = PolicyDescriptor(
        "community.air.policy",
        "1.0.0",
        ("learned",),
        ObservationContract("gym_envs.observation_view", 1, 0, required=()),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue={},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        observation_view=maintained_observation_view_spec(),
    )
    model = _BoundModel()
    runtime_binding = PolicyRuntimeBinding(
        policy,
        admission,
        model,
        bounds=((-1, 1),) * 4,
        timing="window",
    )
    runtime_binding.decide(observation={}, context={}, dt=0.0)
    assert model.observations[0][1]["policy_observation_view_ref"] == (
        "gym_envs.observation_view"
    )
    assert model.observations[0][1]["policy_observation_view_schema_version"] == "1.0"


def test_selected_observation_view_mismatch_fails_before_policy_admission() -> None:
    result = admit_policy(
        _policy(),
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        observation_view=maintained_observation_view_spec(),
    )
    assert not result.admitted
    assert (
        "policy.observation_view_ref_mismatch:air_observation!=gym_envs.observation_view"
        in result.diagnostics
    )


def test_invalid_selected_observation_view_is_rejected_before_field_consumption() -> None:
    view = replace(maintained_observation_view_spec(), schema_version="2.0")
    result = admit_policy(
        PolicyDescriptor(
            "community.air.policy",
            "1.0.0",
            ("learned",),
            ObservationContract("gym_envs.observation_view", 1, 0, required=()),
            ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
        ),
        _binding(),
        field_catalogue={},
        observation_version=(1, 0),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
        observation_view=view,
    )
    assert not result.admitted
    assert any(item.startswith("policy.observation_view_invalid:") for item in result.diagnostics)


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


def test_checkpoint_artifact_binding_factory_keeps_owner_loader_in_the_existing_binding() -> None:
    base = _policy(category="learned")
    payload = b"owner-checkpoint-bytes"
    checkpoint = replace(_checkpoint(base), artifact_sha256=hashlib.sha256(payload).hexdigest())
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
    loaded: list[bytes] = []
    model = _BoundModel()
    binding = PolicyRuntimeBinding.from_checkpoint_artifact(
        policy,
        admission,
        payload,
        owner_loader=lambda value: loaded.append(value) or model,
        bounds=((-1, 1),) * 4,
        timing="window",
    )
    binding.reset(context={})
    binding.decide(
        observation={"ownship.velocity": [1.0, 2.0, 3.0]},
        context={},
        dt=0.0,
    )
    assert loaded == [payload]
    assert model.observations[0][1]["policy_checkpoint_ref"] == checkpoint.checkpoint_ref


@pytest.mark.parametrize("case,exception,error", [
    ("forged", ValueError, "admission_not_owner_validated"),
    ("rejected", ValueError, "runtime_binding_not_admitted"),
    ("checkpoint", ValueError, "runtime_binding_checkpoint_mismatch"),
    ("timing", ValueError, "action_timing_mismatch"),
    ("dimension", ValueError, "action_dimension_mismatch"),
    ("authorizer", TypeError, "action_authorizer must be callable"),
    ("projector", TypeError, "action_projector must be callable"),
    ("false_projector", TypeError, "action_projector must be callable"),
    ("observation_projector", TypeError, "observation_projector must be callable"),
    ("action_values", TypeError, "action_values must be callable"),
    ("schema", ValueError, "admission_not_owner_validated"),
    ("identity", ValueError, "runtime_binding_not_admitted"),
    ("view_receipt", ValueError, "admission_not_owner_validated"),
    ("resealed", ValueError, "admission_not_owner_validated"),
    ("stale_policy", ValueError, "runtime_binding_policy_mismatch"),
    ("stale_owner", ValueError, "runtime_binding_checkpoint_mismatch"),
    ("nonfinite_bounds", ValueError, "bounds must be finite and ordered"),
    ("reversed_bounds", ValueError, "bounds must be finite and ordered"),
    ("malformed_bounds", ValueError, "bounds must be finite and ordered"),
])
def test_checkpoint_binding_rejects_invalid_contract_before_owner_loader(
    case, exception, error, monkeypatch
):
    payload = b"owner-checkpoint-bytes"
    base = _policy(category="learned")
    checkpoint = replace(_checkpoint(base), artifact_sha256=hashlib.sha256(payload).hexdigest())
    policy = replace(base, checkpoint=checkpoint)
    admission = admit_policy(
        policy, _binding(), field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4}, checkpoint=checkpoint,
    )
    assert admission.admitted
    kwargs = dict(bounds=((-1, 1),) * 4, timing="window")
    if case == "forged":
        admission = PolicyAdmission(True, policy.policy_id, (), checkpoint=checkpoint)
    elif case == "rejected":
        admission = admit_policy(
            policy, _binding(), field_catalogue={}, observation_version=(1, 1),
            action_versions={"PilotActionAssignment": (1, 0)},
            action_dimensions={"PilotActionAssignment": 4}, checkpoint=checkpoint,
        )
        assert not admission.admitted
    elif case == "checkpoint":
        policy = replace(policy, checkpoint=replace(checkpoint, artifact_sha256="a" * 64))
    elif case == "timing":
        kwargs["timing"] = "per_tick"
    elif case == "dimension":
        kwargs["bounds"] = ((-1, 1),) * 3
    elif case == "authorizer":
        kwargs["action_authorizer"] = object()
    elif case == "projector":
        kwargs["action_projector"] = object()
    elif case == "false_projector":
        kwargs["action_projector"] = False
    elif case in {"observation_projector", "action_values"}:
        kwargs[case] = object()
    elif case == "schema":
        admission = replace(admission, schema_version="echelon_forge.policy_contract.v2")
    elif case == "identity":
        admission = replace(admission, policy_id="another.policy")
    elif case == "view_receipt":
        admission = replace(admission, observation_view_ref="another.view")
    elif case == "resealed":
        rejected = _admit(policy, field_catalogue={})
        admission = replace(rejected, admitted=True, diagnostics=())
    elif case == "stale_policy":
        policy = replace(policy, stateful=True)
    elif case == "stale_owner":
        policy = replace(policy, checkpoint=replace(checkpoint, owner_ref="owner://changed"))
    elif case == "nonfinite_bounds":
        kwargs["bounds"] = ((-math.inf, 1),) * 4
    elif case == "reversed_bounds":
        kwargs["bounds"] = ((1, -1),) * 4
    elif case == "malformed_bounds":
        kwargs["bounds"] = ((-1, 0, 1),) * 4
    loaded = []
    checkpoint_loads = []
    original_loader = policy_contract.load_policy_checkpoint

    def checkpoint_loader(*args, **loader_kwargs):
        checkpoint_loads.append(True)
        return original_loader(*args, **loader_kwargs)

    monkeypatch.setattr(policy_contract, "load_policy_checkpoint", checkpoint_loader)
    with pytest.raises(exception, match=error):
        PolicyRuntimeBinding.from_checkpoint_artifact(
            policy, admission, payload,
            owner_loader=lambda value: loaded.append(value) or _BoundModel(), **kwargs,
        )
    assert loaded == []
    assert checkpoint_loads == []


def test_checkpoint_binding_freezes_owner_inputs_before_loading() -> None:
    payload = b"owner-checkpoint-bytes"
    base = _policy()
    checkpoint = replace(_checkpoint(base), artifact_sha256=hashlib.sha256(payload).hexdigest())
    policy = replace(base, checkpoint=checkpoint)
    bounds = [[-1, 1] for _ in range(4)]

    def load_owner(value):
        assert value == payload
        bounds[0][:] = [math.nan, -math.inf]
        return _BoundModel()

    binding = PolicyRuntimeBinding.from_checkpoint_artifact(
        policy, _admit(policy), payload, owner_loader=load_owner, bounds=bounds, timing="window"
    )
    assert binding.bounds == ((-1, 1),) * 4


@pytest.mark.parametrize("change", ["version", "observation", "action", "legacy_kind"])
def test_admission_cannot_be_reused_for_a_changed_descriptor(change) -> None:
    policy = _policy()
    admission = _admit(policy)
    changed = {
        "version": replace(policy, version="2"),
        "observation": replace(policy, observation=replace(policy.observation, major=2)),
        "action": replace(policy, action=replace(policy.action, authority_scope="mission_command")),
        "legacy_kind": replace(policy, legacy_model_kind="human"),
    }[change]
    with pytest.raises(ValueError, match="runtime_binding_policy_mismatch"):
        PolicyRuntimeBinding(changed, admission, _BoundModel(), bounds=((-1, 1),) * 4, timing="window")
    with pytest.raises(ValueError, match="runtime_binding_policy_mismatch"):
        project_policy_observation(changed, admission, {}, optional_defaults={})


def test_admission_requires_fresh_validation_for_changed_owner_binding() -> None:
    policy = _policy()
    owner = _binding()
    admission = _admit(policy, owner)
    assert validate_policy_admission(policy, admission, binding=owner) == owner
    changed_owner = replace(owner, allowed_authority_scopes=frozenset())
    with pytest.raises(ValueError, match="owner_binding_mismatch"):
        validate_policy_admission(policy, admission, binding=changed_owner)
    assert not _admit(policy, changed_owner).admitted


@pytest.mark.parametrize("role,scope,error", [
    ("commander", "platform_control", "owner_role_mismatch"),
    ("autopilot", "mission_command", "owner_authority_mismatch"),
])
def test_runtime_rejects_policy_admission_under_another_owner(role, scope, error) -> None:
    policy = _policy()
    binding = PolicyRuntimeBinding(
        policy, _admit(policy), _BoundModel(), bounds=((-1, 1),) * 4, timing="window"
    )
    with pytest.raises(ValueError, match=error):
        DecisionRuntimeAgent(
            DecisionRuntimeAgentSpec("a", policy.policy_id, "air", role, authority_scope=scope), binding
        )


def test_serialized_admission_is_evidence_and_cannot_restore_a_receipt() -> None:
    policy = _policy()
    document = _admit(policy).as_dict()
    assert "_validation_marker" not in document
    reconstructed = PolicyAdmission(**document)
    with pytest.raises(ValueError, match="not_owner_validated"):
        project_policy_observation(policy, reconstructed, {}, optional_defaults={})


@pytest.mark.parametrize("kind", ["scripted", "learned", "human", "hybrid"])
def test_versioned_legacy_adapter_preserves_existing_runtime_action_parity(kind) -> None:
    policy = replace(_policy(), categories=("commander", "community.new"), legacy_model_kind=kind)
    registration = DecisionModelRegistration("air.legacy", "air", ("autopilot",), _BoundModel, kind)
    registry = DecisionModelRegistry((registration,))
    spec = DecisionRuntimeAgentSpec("a", registration.model_id, "air", "autopilot", model_kind=kind)
    adapter = LegacyDecisionModelAdapter.from_dict(spec.legacy_adapter.as_dict())
    admission = adapter.admit_policy(
        registry, policy, _binding(), field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert admission.admitted
    runtimes = []
    for migrated in (False, True):
        model = registry.create_for(
            domain=adapter.domain, role_id=adapter.role_id,
            model_id=adapter.model_id, model_kind=adapter.model_kind,
        )
        bound = PolicyRuntimeBinding(
            policy, admission, model, bounds=((-1, 1),) * 4, timing="window"
        ) if migrated else model
        runtime = DecisionRuntimeAgent(spec, bound)
        runtime.reset(episode_seed=7)
        runtimes.append((runtime, model))
    outputs = [runtime.step(observation={"ownship.velocity": [1, 2, 3]}, clock_s=0.1)
               for runtime, _model in runtimes]
    assert outputs[0] == outputs[1]
    for runtime, model in runtimes:
        runtime.close()
        assert model.closed


@pytest.mark.parametrize("case", ["kind", "role", "domain", "status"])
def test_legacy_adapter_rejects_selection_mismatch_without_constructing_models(case) -> None:
    created = []
    registry = DecisionModelRegistry((DecisionModelRegistration(
        "legacy", "air", ("autopilot",), lambda: created.append(True) or _BoundModel(),
        "scripted", status="demo" if case == "status" else "maintained",
    ),))
    adapter = LegacyDecisionModelAdapter("legacy", "air", "autopilot", "scripted")
    policy = _policy()
    if case == "kind":
        policy = replace(policy, legacy_model_kind="learned")
    elif case == "role":
        adapter = replace(adapter, role_id="commander")
    elif case == "domain":
        adapter = replace(adapter, domain="naval")
    with pytest.raises(ValueError, match="legacy_.*mismatch"):
        adapter.admit_policy(registry, policy, _binding(), statuses=frozenset({"maintained"}))
    assert created == []


def test_legacy_adapter_does_not_translate_categories_or_kinds_into_rights() -> None:
    registry = DecisionModelRegistry((DecisionModelRegistration(
        "legacy", "air", ("autopilot",), _BoundModel, "human",
    ),))
    adapter = LegacyDecisionModelAdapter("legacy", "air", "autopilot", "human")
    policy = replace(_policy(), categories=("human", "commander"), legacy_model_kind="human")
    denied = adapter.admit_policy(
        registry, policy, replace(_binding(), allowed_authority_scopes=frozenset()),
        field_catalogue=_catalogue(), observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    assert not denied.admitted
    assert any("authority_scope_unauthorized" in error for error in denied.diagnostics)


def test_legacy_adapter_requires_a_supported_explicit_format_version() -> None:
    document = LegacyDecisionModelAdapter("legacy", "air", "autopilot", "scripted").as_dict()
    with pytest.raises(ValueError, match="schema version"):
        LegacyDecisionModelAdapter.from_dict({**document, "schema_version": "v2"})
    del document["schema_version"]
    with pytest.raises(ValueError, match="format fields invalid"):
        LegacyDecisionModelAdapter.from_dict(document)


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


def test_runtime_binding_rejects_caller_constructed_admission() -> None:
    policy = _policy()
    forged = PolicyAdmission(True, policy.policy_id, ())
    with pytest.raises(ValueError, match="not_owner_validated"):
        PolicyRuntimeBinding(
            policy,
            forged,
            _BoundModel(),
            bounds=((-1, 1),) * 4,
            timing="window",
        )


def test_runtime_binding_rejects_resealed_owner_admission() -> None:
    policy = _policy()
    rejected = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 3},
    )
    assert not rejected.admitted
    resealed = replace(rejected, admitted=True, diagnostics=())
    with pytest.raises(ValueError, match="not_owner_validated"):
        PolicyRuntimeBinding(
            policy,
            resealed,
            _BoundModel(),
            bounds=((-1, 1),) * 4,
            timing="window",
        )


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


def test_existing_runtime_path_runs_owner_action_authorization_before_projection() -> None:
    policy = _policy(category="novel.owner.category")
    admission = admit_policy(
        policy,
        _binding(),
        field_catalogue=_catalogue(),
        observation_version=(1, 1),
        action_versions={"PilotActionAssignment": (1, 0)},
        action_dimensions={"PilotActionAssignment": 4},
    )
    projected: list[tuple[float, ...]] = []
    owner_state = {"authorized": True}

    def owner_authorizer(action, context, _dt):
        del action
        errors = []
        if context.get("action_mask_open") is not True:
            errors.append("policy.action_mask_closed")
        if context.get("authority_scope") != "platform_control" or not owner_state["authorized"]:
            errors.append("policy.action_authority_missing")
        expiry = context.get("action_expires_at_s")
        if expiry is None or context["clock_s"] > expiry:
            errors.append("policy.action_expired")
        return tuple(errors)

    binding = PolicyRuntimeBinding(
        policy,
        admission,
        _BoundModel(),
        bounds=((-1, 1),) * 4,
        timing="window",
        action_authorizer=owner_authorizer,
        action_projector=lambda action: projected.append(tuple(action)) or tuple(action),
    )
    runtime = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="a1",
            model_id=policy.policy_id,
            domain="air",
            role_id="autopilot",
            model_kind="scripted",
            authority_scope="platform_control",
        ),
        binding,
    )
    runtime.reset(context={})
    accepted = runtime.step(
        observation={"ownship.velocity": [1.0, 2.0, 3.0]},
        clock_s=0.1,
        observation_version="air_observation@1.1",
        context={"action_mask_open": True, "action_expires_at_s": 1.0},
    )
    assert accepted.action == (0.0, 0.5, 0.0, -0.5)
    assert projected == [accepted.action]

    owner_state["authorized"] = False
    with pytest.raises(ValueError, match="policy.action_authority_missing"):
        runtime.step(
            observation={"ownship.velocity": [1.0, 2.0, 3.0]}, clock_s=0.15,
            context={"action_mask_open": True, "action_expires_at_s": 1.0},
        )
    assert projected == [accepted.action]
    owner_state["authorized"] = True

    with pytest.raises(ValueError, match="policy.action_mask_closed"):
        runtime.step(
            observation={"ownship.velocity": [1.0, 2.0, 3.0]}, clock_s=0.2,
            context={"action_mask_open": False, "action_expires_at_s": 1.0},
        )
    assert projected == [accepted.action]

    with pytest.raises(ValueError, match="policy.action_expired"):
        runtime.step(
            observation={"ownship.velocity": [1.0, 2.0, 3.0]},
            clock_s=2.0,
            observation_version="air_observation@1.1",
            context={"action_mask_open": True, "action_expires_at_s": 1.0},
            force_decide=True,
        )
    assert projected == [accepted.action]
    runtime.close()
