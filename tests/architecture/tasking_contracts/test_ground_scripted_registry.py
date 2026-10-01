"""Contract tests for the Ground scripted model behind the neutral registry."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from python.tasking_contracts.common.decision_registry import DecisionModel
from python.tasking_contracts.common.decision_runtime import (
    DECISION_RUNTIME_ACTION_DECIDED,
    DECISION_RUNTIME_ACTION_HELD,
    DecisionRuntimeAgentSpec,
    DecisionRuntimeRoster,
)
from python.tasking_contracts.common.scripted_capability import (
    ScriptedCapabilityManifest,
    resolve_scripted_model_id,
)
from python.tasking_contracts.ground.execution import (
    GROUND_INFANTRY_CONTROLLER_ROLE_ID,
    GROUND_INFANTRY_SCRIPTED_MODEL_ID,
    GROUND_SCRIPTED_MODEL_REGISTRY,
    GroundInfantryDecision,
    GroundInfantryObjectiveTask,
    GroundInfantryObservation,
    GroundScriptedTaskError,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
GROUND_CONTRACT_ROOT = REPO_ROOT / "python" / "tasking_contracts" / "ground"


def _task(**overrides: object) -> GroundInfantryObjectiveTask:
    values: dict[str, object] = {
        "objective_xy_m": (410.0, 100.0),
        "objective_radius_m": 2.0,
    }
    values.update(overrides)
    return GroundInfantryObjectiveTask(**values)  # type: ignore[arg-type]


def _observation(x: float, y: float, **overrides: object) -> GroundInfantryObservation:
    values: dict[str, object] = {"position_xy_m": (x, y), "operational": True}
    values.update(overrides)
    return GroundInfantryObservation(**values)  # type: ignore[arg-type]


def test_ground_model_is_registered_as_a_scoped_scripted_adapter() -> None:
    entry = GROUND_SCRIPTED_MODEL_REGISTRY.get(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    assert entry.domain == "ground"
    assert entry.model_kind == "scripted"
    assert entry.status == "adapter"
    assert entry.role_ids == (GROUND_INFANTRY_CONTROLLER_ROLE_ID,)
    resolved = GROUND_SCRIPTED_MODEL_REGISTRY.resolve(
        domain="ground", role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID, model_kind="scripted"
    )
    assert [item.model_id for item in resolved] == [GROUND_INFANTRY_SCRIPTED_MODEL_ID]
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="ground", role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID
    )
    assert isinstance(model, DecisionModel)


def test_ground_registry_fails_closed_on_wrong_domain_role_kind_or_unregistered_role() -> None:
    with pytest.raises(ValueError, match="belongs to domain"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="air",
            role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
            model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
        )
    with pytest.raises(ValueError, match="does not declare role"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="ground",
            role_id="ground_commander",
            model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
        )
    with pytest.raises(ValueError, match="has kind"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="ground",
            role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
            model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
            model_kind="learned",
        )
    with pytest.raises(ValueError, match="not admitted"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="ground",
            role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
            model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
            statuses=frozenset({"maintained"}),
        )
    # The platoon command node remains an identity carrier with no model.
    with pytest.raises(LookupError, match="no decision model"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create_for(domain="ground", role_id="ground_commander")
    with pytest.raises(TypeError, match="reset context"):
        GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID, waypoint=(1, 2))


def test_held_ground_manifest_cannot_route_to_the_registered_model() -> None:
    held = ScriptedCapabilityManifest.from_mapping(
        {
            "version": "scripted_capability.v1",
            "domain": "ground",
            "label": "held",
            "model_id": GROUND_INFANTRY_SCRIPTED_MODEL_ID,
            "role_id": GROUND_INFANTRY_CONTROLLER_ROLE_ID,
            "lifecycle": "reset_decide_close",
            "evidence_refs": ["test:tests/architecture/tasking_contracts/test_ground_scripted_registry.py"],
            "deferred_claims": ["route planning"],
        }
    )
    with pytest.raises(ValueError, match="held"):
        resolve_scripted_model_id(
            held,
            expected_domain="ground",
            expected_role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
        )


def test_ground_model_moves_to_objective_then_latches_the_static_hold() -> None:
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    model.reset(context={"task": _task(stance="crouch")})

    moving = model.decide(observation=_observation(400.0, 100.0), context={}, dt=0.0)
    assert isinstance(moving, GroundInfantryDecision)
    assert moving.ground_task_mode == "move_static"
    assert moving.desired_heading_deg == pytest.approx(90.0)
    assert moving.desired_speed_fraction == pytest.approx(1.0)
    assert moving.stance == "crouch"
    assert moving.route_intent == "direct"
    assert moving.objective_reached is False
    assert moving.fire_requested is False
    assert moving.command_action() == {
        "ground_task_mode": "move_static",
        "desired_heading_deg": pytest.approx(90.0),
        "desired_speed_fraction": 1.0,
        "stance": "crouch",
        "route_intent": "direct",
    }

    arrived = model.decide(observation=_observation(409.0, 100.0), context={}, dt=1.0)
    assert arrived.ground_task_mode == "occupy_static"
    assert arrived.desired_speed_fraction == 0.0
    assert arrived.objective_reached is True

    # A later drift outside the tolerance does not re-open movement.
    drifted = model.decide(observation=_observation(405.0, 100.0), context={}, dt=1.0)
    assert drifted.ground_task_mode == "occupy_static"
    assert drifted.objective_reached is True

    model.reset(context={"task": _task(hold_task_mode="support_static")})
    again = model.decide(observation=_observation(405.0, 100.0), context={}, dt=0.0)
    assert again.ground_task_mode == "move_static"
    assert model.decide(observation=_observation(410.0, 100.0), context={}, dt=1.0).ground_task_mode == (
        "support_static"
    )
    model.close()
    with pytest.raises(RuntimeError, match="closed"):
        model.decide(observation=_observation(410.0, 100.0), context={}, dt=1.0)


def test_ground_fire_request_requires_assigned_target_and_commander_authorization() -> None:
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    model.reset(context={"task": _task()})
    no_target = model.decide(
        observation=_observation(400.0, 100.0, authorization_to_fire=True), context={}, dt=0.0
    )
    unauthorized = model.decide(
        observation=_observation(400.0, 100.0, assigned_target_id=7), context={}, dt=0.0
    )
    authorized = model.decide(
        observation=_observation(400.0, 100.0, assigned_target_id=7, authorization_to_fire=True),
        context={},
        dt=0.0,
    )
    assert (no_target.fire_requested, no_target.fire_target_id) == (False, 0)
    assert (unauthorized.fire_requested, unauthorized.fire_target_id) == (False, 0)
    assert (authorized.fire_requested, authorized.fire_target_id) == (True, 7)
    # Requesting fire never changes the movement decision.
    assert authorized.command_action() == no_target.command_action()

    disabled = model.decide(
        observation=_observation(
            400.0, 100.0, operational=False, assigned_target_id=7, authorization_to_fire=True
        ),
        context={},
        dt=1.0,
    )
    assert disabled.fire_requested is False
    assert disabled.desired_speed_fraction == 0.0
    assert disabled.reason == "not_operational"


def test_ground_task_and_observation_fail_closed_on_unrepresentable_values() -> None:
    with pytest.raises(GroundScriptedTaskError, match="direct route intent"):
        _task(route_intent="bridge")
    with pytest.raises(GroundScriptedTaskError, match="hold_task_mode"):
        _task(hold_task_mode="move_static")
    with pytest.raises(GroundScriptedTaskError, match="objective_radius_m"):
        _task(objective_radius_m=0.0)
    with pytest.raises(GroundScriptedTaskError, match="speed_fraction"):
        _task(speed_fraction=0.0)
    with pytest.raises(GroundScriptedTaskError, match="finite"):
        _task(objective_xy_m=(float("nan"), 0.0))
    with pytest.raises(GroundScriptedTaskError, match="stance"):
        _task(stance="kneel")
    with pytest.raises(GroundScriptedTaskError, match="bool"):
        _observation(0.0, 0.0, operational=1)
    model = GROUND_SCRIPTED_MODEL_REGISTRY.create(GROUND_INFANTRY_SCRIPTED_MODEL_ID)
    with pytest.raises(RuntimeError, match="reset"):
        model.decide(observation=_observation(0.0, 0.0), context={}, dt=0.0)
    with pytest.raises(TypeError, match="GroundInfantryObjectiveTask"):
        model.reset(context={"task": {"objective_xy_m": (1.0, 2.0)}})
    model.reset(context={"task": _task()})
    with pytest.raises(TypeError, match="GroundInfantryObservation"):
        model.decide(observation={"position_xy_m": (0.0, 0.0)}, context={}, dt=0.0)


def test_ground_model_runs_through_the_common_runtime_roster_with_hold_and_report() -> None:
    spec = DecisionRuntimeAgentSpec(
        agent_id="ground:rifleman",
        model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
        domain="ground",
        role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
        decision_period_s=1.0,
        authority_scope="platform_control",
    )
    roster = DecisionRuntimeRoster.from_registry(GROUND_SCRIPTED_MODEL_REGISTRY, (spec,))
    try:
        roster.reset(context_by_agent={spec.agent_id: {"task": _task()}}, episode_seed=11)
        first = roster.step(
            observations={spec.agent_id: _observation(400.0, 100.0)},
            clock_s=0.0,
            observation_versions={spec.agent_id: "ground:0"},
        )[spec.agent_id]
        held = roster.step(
            observations={spec.agent_id: _observation(401.0, 100.0)},
            clock_s=0.5,
            observation_versions={spec.agent_id: "ground:1"},
        )[spec.agent_id]
        assert first.report.domain == "ground"
        assert first.report.role_id == GROUND_INFANTRY_CONTROLLER_ROLE_ID
        assert first.report.action_source == DECISION_RUNTIME_ACTION_DECIDED
        assert held.report.action_source == DECISION_RUNTIME_ACTION_HELD
        assert held.action is first.action
        assert roster.agent(spec.agent_id).replay_identity.endswith("seed=11:reset=1")
    finally:
        roster.close()


def test_ground_contract_package_is_dependency_terminal() -> None:
    forbidden = ("python.rl", "gym_envs", "ef_py", "numpy", "gymnasium", "python.simulation")
    for path in sorted(GROUND_CONTRACT_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                assert not any(name == item or name.startswith(f"{item}.") for item in forbidden), (
                    path,
                    name,
                )
