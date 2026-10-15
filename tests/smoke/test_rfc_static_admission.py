"""Small stdlib-only negative fixtures for the mandatory RFC smoke gate."""

from python.mechanisms.ports import GraphEdge, MechanismSpec, PortSpec, compile_mechanism_graph
from python.tasking_contracts.failure_domains import (
    RecoveryAdmission,
    WorldState,
    WorldOutcome,
    build_batch_outcome,
)
from python.tasking_contracts.policy import (
    ActionContract,
    AgentBinding,
    FieldSpec,
    ObservationContract,
    PolicyDescriptor,
    admit_policy,
)


def test_delayed_feedback_requires_an_explicit_state_owner_and_window() -> None:
    stateful = MechanismSpec(
        "stateful",
        "1.0.0",
        inputs=(PortSpec("in", "scalar", "unit", "frame"),),
        outputs=(PortSpec("out", "scalar", "unit", "frame"),),
        stateful=True,
        delay_windows=1,
    )
    source = MechanismSpec(
        "source",
        "1.0.0",
        outputs=(PortSpec("out", "scalar", "unit", "frame"),),
    )
    target = MechanismSpec(
        "target",
        "1.0.0",
        inputs=(PortSpec("in", "scalar", "unit", "frame"),),
    )
    graph = compile_mechanism_graph(
        "invalid-delay",
        {"source": source, "target": target},
        (GraphEdge("source", "out", "target", "in", delayed=True),),
    )
    assert not graph.valid
    assert {
        "mechanism.delayed_edge_window_missing",
        "mechanism.delayed_edge_state_owner_missing",
    } <= {item.code for item in graph.diagnostics}


def test_policy_rejects_unknown_action_interface_before_runtime() -> None:
    policy = PolicyDescriptor(
        "community.air.policy",
        "1.0.0",
        ("scripted",),
        ObservationContract(
            "air_observation",
            1,
            0,
            required=(FieldSpec("ownship.velocity", "Vector3", (3,), "meter_per_second"),),
        ),
        ActionContract("PilotActionAssignment", 1, 0, 4, "platform_control"),
    )
    result = admit_policy(
        policy,
        AgentBinding(
            "autopilot",
            frozenset({"agent_observation"}),
            frozenset({"PilotActionAssignment"}),
            frozenset({"platform_control"}),
        ),
        field_catalogue={
            "ownship.velocity": FieldSpec(
                "ownship.velocity", "Vector3", (3,), "meter_per_second"
            )
        },
        observation_version=(1, 0),
        action_versions={},
        action_dimensions={},
    )
    assert not result.admitted
    assert "policy.action_interface_unknown:action.interface_ref.PilotActionAssignment" in result.diagnostics


def test_partial_batch_failure_fences_retry_and_success_projection() -> None:
    result = build_batch_outcome(
        batch_generation_ref="generation-1",
        operation_ref="operation-1",
        operation="step",
        worlds=(
            WorldOutcome(0, WorldState.COMPLETED, True),
            WorldOutcome(1, WorldState.UNKNOWN_AFTER_FAULT, None, "worker failure"),
        ),
        expected_world_indices=frozenset({0, 1}),
    )
    assert result.result.value == "partial_failure"
    assert result.recovery_admission is RecoveryAdmission.REQUIRE_EXPLICIT_RESET_OR_RECREATE
