from __future__ import annotations

import pytest

from python.tasking_contracts.common.scripted_registry import (
    ScriptedDecisionModel,
    ScriptedModelRegistration,
    ScriptedModelRegistry,
)


class _StubScriptedModel:
    def __init__(self, marker: str = "") -> None:
        self.marker = marker
        self.reset_context = None
        self.decisions: list[tuple[object, object, float]] = []
        self.closed = False

    def reset(self, *, context: object) -> None:
        self.reset_context = context

    def decide(self, *, observation: object, context: object, dt: float) -> object:
        self.decisions.append((observation, context, float(dt)))
        return {"marker": self.marker, "dt": float(dt)}

    def close(self) -> None:
        self.closed = True


def _registration(
    model_id: str = "air.execution.scripted",
    *,
    domain: str = "air",
    roles: tuple[str, ...] = ("autopilot_controller",),
    status: str = "maintained",
) -> ScriptedModelRegistration:
    return ScriptedModelRegistration(
        model_id=model_id,
        domain=domain,
        role_ids=roles,
        factory=_StubScriptedModel,
        status=status,
    )


def test_registry_resolves_by_domain_and_role_and_preserves_registration_order() -> None:
    registry = ScriptedModelRegistry(
        (
            _registration(),
            _registration(
                "air.c2.scripted",
                roles=("flight_lead",),
            ),
            _registration("naval.station.scripted", domain="naval", roles=("naval_warfare_commander",)),
        )
    )

    assert [entry.model_id for entry in registry.resolve(domain="air")] == [
        "air.execution.scripted",
        "air.c2.scripted",
    ]
    assert [entry.model_id for entry in registry.resolve(domain="air", role_id="flight_lead")] == [
        "air.c2.scripted"
    ]
    assert [entry.model_id for entry in registry.snapshot()] == [
        "air.execution.scripted",
        "air.c2.scripted",
        "naval.station.scripted",
    ]


def test_registry_creates_and_validates_the_neutral_lifecycle() -> None:
    registry = ScriptedModelRegistry((_registration(),))
    model = registry.create("air.execution.scripted", marker="baseline")

    assert isinstance(model, ScriptedDecisionModel)
    model.reset(context={"entity_id": 7})
    assert model.reset_context == {"entity_id": 7}
    assert model.decide(observation={"heading": 90.0}, context=None, dt=0.05) == {
        "marker": "baseline",
        "dt": 0.05,
    }
    model.close()
    assert model.closed is True


def test_registry_rejects_duplicate_ids_and_unknown_statuses() -> None:
    registry = ScriptedModelRegistry((_registration(),))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(_registration())
    with pytest.raises(ValueError, match="unknown scripted model status"):
        _registration("air.bad", status="rl")
    with pytest.raises(ValueError, match="unknown scripted model statuses"):
        registry.resolve(domain="air", statuses=frozenset({"rl"}))


def test_registry_rejects_a_factory_that_does_not_implement_the_lifecycle() -> None:
    registration = ScriptedModelRegistration(
        model_id="air.invalid",
        domain="air",
        role_ids=("autopilot_controller",),
        factory=lambda: object(),
    )
    registry = ScriptedModelRegistry((registration,))
    with pytest.raises(TypeError, match="without reset/decide/close"):
        registry.create("air.invalid")


def test_registry_create_for_resolves_one_role_and_validates_explicit_id() -> None:
    registry = ScriptedModelRegistry((_registration(),))
    inferred = registry.create_for(domain="air", role_id="autopilot_controller", marker="inferred")
    assert isinstance(inferred, _StubScriptedModel)
    assert inferred.marker == "inferred"

    explicit = registry.create_for(
        domain="air",
        role_id="autopilot_controller",
        model_id="air.execution.scripted",
        marker="explicit",
    )
    assert isinstance(explicit, _StubScriptedModel)
    assert explicit.marker == "explicit"

    with pytest.raises(ValueError, match="belongs to domain"):
        registry.create_for(
            domain="naval",
            role_id="autopilot_controller",
            model_id="air.execution.scripted",
        )
    with pytest.raises(ValueError, match="does not declare role"):
        registry.create_for(
            domain="air",
            role_id="flight_lead",
            model_id="air.execution.scripted",
        )


def test_registry_create_for_fails_closed_on_missing_or_ambiguous_role() -> None:
    registry = ScriptedModelRegistry((_registration(),))
    with pytest.raises(LookupError, match="no scripted model"):
        registry.create_for(domain="naval", role_id="naval_warfare_commander")

    registry.register(_registration("air.execution.scripted.v2"))
    with pytest.raises(ValueError, match="ambiguous scripted models"):
        registry.create_for(domain="air", role_id="autopilot_controller")
