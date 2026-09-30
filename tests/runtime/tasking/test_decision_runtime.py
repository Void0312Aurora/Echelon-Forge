from __future__ import annotations

import pytest

from python.tasking_contracts.common.decision_registry import (
    DecisionModelRegistration,
    DecisionModelRegistry,
)
from python.tasking_contracts.common.decision_runtime import (
    DECISION_RUNTIME_ACTION_DECIDED,
    DECISION_RUNTIME_ACTION_HELD,
    DecisionRuntimeAgentSpec,
    DecisionRuntimeRoster,
)


class _FakeModel:
    model_kind = "scripted"

    def __init__(self, *, label: str = "fake") -> None:
        self.label = label
        self.reset_contexts: list[dict] = []
        self.decisions: list[tuple[float, object]] = []
        self.closed = False

    def reset(self, *, context):
        self.reset_contexts.append(dict(context))
        self.closed = False

    def decide(self, *, observation, context, dt):
        self.decisions.append((float(dt), observation))
        return {"label": self.label, "observation": observation, "clock_s": context["clock_s"]}

    def close(self):
        self.closed = True


def _spec(agent_id: str, *, period: float = 0.0, active: bool = True):
    return DecisionRuntimeAgentSpec(
        agent_id=agent_id,
        model_id=f"{agent_id}.model",
        domain="air" if agent_id.startswith("air") else "naval",
        role_id="autopilot_controller",
        decision_period_s=period,
        active=active,
    )


def test_runtime_holds_action_until_expiry_and_exposes_provenance() -> None:
    model = _FakeModel()
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    agent = DecisionRuntimeAgent(_spec("air-1", period=2.0), model)
    agent.reset(context={"mission": "demo"}, episode_seed=17)
    first = agent.step(observation="obs-1", clock_s=0.0, observation_version="v1")
    held = agent.step(observation="obs-2", clock_s=1.0, observation_version="v2")
    renewed = agent.step(observation="obs-3", clock_s=2.0, observation_version="v3")

    assert first.report.action_source == DECISION_RUNTIME_ACTION_DECIDED
    assert first.report.model_kind == "scripted"
    assert held.report.action_source == DECISION_RUNTIME_ACTION_HELD
    assert held.action == first.action
    assert renewed.report.action_source == DECISION_RUNTIME_ACTION_DECIDED
    assert renewed.action != first.action
    assert model.reset_contexts[0]["episode_seed"] == 17
    assert model.reset_contexts[0]["replay_identity"].startswith("air-1:air-1.model:seed=17")
    assert [entry[0] for entry in model.decisions] == [0.0, 2.0]


def test_runtime_decision_dt_is_independent_of_held_polls() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    model = _FakeModel()
    agent = DecisionRuntimeAgent(_spec("air-1", period=1.0), model)
    agent.reset()
    agent.step(observation="obs-0", clock_s=0.0)
    agent.step(observation="obs-held", clock_s=0.9)
    agent.step(observation="obs-1", clock_s=1.0)

    assert [entry[0] for entry in model.decisions] == [0.0, 1.0]


def test_runtime_rejects_backwards_clock_and_missing_reset() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    agent = DecisionRuntimeAgent(_spec("air-1"), _FakeModel())
    with pytest.raises(RuntimeError, match="must be reset"):
        agent.step(observation=None, clock_s=0.0)
    agent.reset(episode_seed=1)
    agent.step(observation=None, clock_s=2.0)
    with pytest.raises(ValueError, match="moved backwards"):
        agent.step(observation=None, clock_s=1.0)


def test_runtime_rejects_unknown_model_kind() -> None:
    with pytest.raises(ValueError, match="unknown decision model kind"):
        DecisionRuntimeAgentSpec(
            "air-unknown",
            "air.unknown",
            "air",
            "autopilot_controller",
            model_kind="unknown",
        )


def test_runtime_rejects_unclassified_or_mismatched_direct_models() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    class _UnclassifiedModel(_FakeModel):
        model_kind = None

    with pytest.raises(ValueError, match="must declare model_kind"):
        DecisionRuntimeAgent(_spec("air-unclassified"), _UnclassifiedModel())

    class _LearnedModel(_FakeModel):
        model_kind = "learned"

    with pytest.raises(ValueError, match="kind mismatch"):
        DecisionRuntimeAgent(_spec("air-mismatch"), _LearnedModel())


def test_roster_routes_active_agents_in_stable_order_and_skips_inactive() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    first = _FakeModel(label="first")
    second = _FakeModel(label="second")
    inactive = _FakeModel(label="inactive")
    roster = DecisionRuntimeRoster(
        [
            DecisionRuntimeAgent(_spec("air-2"), second),
            DecisionRuntimeAgent(_spec("air-1"), first),
            DecisionRuntimeAgent(_spec("naval-1", active=False), inactive),
        ]
    )
    roster.reset(episode_seed=9)
    result = roster.step(
        observations={"air-1": "a", "air-2": "b"},
        clock_s=0.0,
        observation_versions={"air-1": "v-a", "air-2": "v-b"},
    )
    assert list(result) == ["air-1", "air-2"]
    assert result["air-1"].report.observation_version == "v-a"
    assert result["air-2"].report.observation_version == "v-b"
    assert inactive.decisions == []


def test_roster_from_registry_requires_explicit_domain_role_match() -> None:
    registry = DecisionModelRegistry(
        (
            DecisionModelRegistration(
                model_id="air.model",
                domain="air",
                role_ids=("autopilot_controller",),
                factory=lambda **kwargs: _FakeModel(label="registry"),
                model_kind="scripted",
            ),
        )
    )
    roster = DecisionRuntimeRoster.from_registry(
        registry,
        (DecisionRuntimeAgentSpec("air-1", "air.model", "air", "autopilot_controller"),),
    )
    roster.reset(episode_seed=3)
    result = roster.step(observations={"air-1": "obs"}, clock_s=0.0)
    assert result["air-1"].action["label"] == "registry"
    with pytest.raises(ValueError, match="belongs to domain"):
        DecisionRuntimeRoster.from_registry(
            registry,
            (DecisionRuntimeAgentSpec("naval-1", "air.model", "naval", "autopilot_controller"),),
        )

    registry.register(
        DecisionModelRegistration(
            model_id="air.learned",
            domain="air",
            role_ids=("autopilot_controller",),
            factory=_FakeModel,
            model_kind="learned",
        )
    )
    learned_roster = DecisionRuntimeRoster.from_registry(
        registry,
        (
            DecisionRuntimeAgentSpec(
                "air-2",
                "air.learned",
                "air",
                "autopilot_controller",
                model_kind="learned",
            ),
        ),
    )
    learned_roster.reset(episode_seed=4)
    learned_result = learned_roster.step(observations={"air-2": "obs"}, clock_s=0.0)
    assert learned_result["air-2"].action["label"] == "fake"
    assert learned_result["air-2"].report.model_kind == "learned"


def test_roster_rejects_duplicate_and_missing_active_entries() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    one = DecisionRuntimeAgent(_spec("air-1"), _FakeModel())
    roster = DecisionRuntimeRoster([one])
    with pytest.raises(ValueError, match="duplicate"):
        roster.add(DecisionRuntimeAgent(_spec("air-1"), _FakeModel()))
    roster.reset()
    with pytest.raises(KeyError, match="missing observation"):
        roster.step(observations={}, clock_s=0.0)


def test_roster_preflights_all_active_observations_before_stepping() -> None:
    from python.tasking_contracts.common.decision_runtime import DecisionRuntimeAgent

    first_model = _FakeModel(label="first")
    second_model = _FakeModel(label="second")
    roster = DecisionRuntimeRoster(
        [
            DecisionRuntimeAgent(_spec("air-1"), first_model),
            DecisionRuntimeAgent(_spec("air-2"), second_model),
        ]
    )
    roster.reset()

    with pytest.raises(KeyError, match="air-2"):
        roster.step(observations={"air-1": "present"}, clock_s=0.0)

    assert first_model.decisions == []
    assert second_model.decisions == []
