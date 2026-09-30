"""Neutral registry for decision-model factories of every supported kind.

This module owns model-factory registration only. It deliberately does not own
the compiled ``AgentRole`` contract, scenario loading, world stepping, or RL
adapters. Those surfaces remain consumers of this registry. Keeping the
registry in ``python.tasking_contracts`` preserves the maintained dependency
direction::

    gym_envs -> python.tasking_contracts <- python.rl

The registry uses a structural lifecycle protocol rather
than inventing a second observation or action DTO. Domain adapters pass the
existing observation/intent/action packets through ``observation`` and the
factory's returned value. A later slice may add typed helpers only when two
named domain consumers require the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, runtime_checkable


DECISION_MODEL_KINDS: frozenset[str] = frozenset(
    {"scripted", "learned", "human", "hybrid"}
)
DECISION_MODEL_STATUSES: frozenset[str] = frozenset(
    {"maintained", "adapter", "demo", "diagnostics"}
)


@runtime_checkable
class DecisionModel(Protocol):
    """Minimal lifecycle required from a registered decision model.

    ``context`` and ``observation`` intentionally remain opaque at this layer.
    The common runtime must not duplicate domain observation or action DTOs;
    domain adapters own those payloads and the registry only controls model
    selection and lifecycle entry points.
    """

    def reset(self, *, context: Any) -> None: ...

    def decide(self, *, observation: Any, context: Any, dt: float) -> Any: ...

    def close(self) -> None: ...


DecisionModelFactory = Callable[..., DecisionModel]


@dataclass(frozen=True)
class DecisionModelRegistration:
    """Immutable declaration for one decision model factory."""

    model_id: str
    domain: str
    role_ids: tuple[str, ...]
    factory: DecisionModelFactory
    model_kind: str
    status: str = "maintained"
    note: str = ""

    def __post_init__(self) -> None:
        model_id = str(self.model_id).strip()
        domain = str(self.domain).strip().lower()
        roles = tuple(str(role).strip() for role in self.role_ids)
        if not model_id:
            raise ValueError("decision model_id must be non-empty")
        if not domain:
            raise ValueError("decision model domain must be non-empty")
        if not roles or any(not role for role in roles):
            raise ValueError("decision model role_ids must contain non-empty role ids")
        if len(set(roles)) != len(roles):
            raise ValueError("decision model role_ids must be unique")
        if not callable(self.factory):
            raise TypeError("decision model factory must be callable")
        model_kind = str(self.model_kind).strip().lower()
        if model_kind not in DECISION_MODEL_KINDS:
            raise ValueError(f"unknown decision model kind: {self.model_kind!r}")
        status = str(self.status).strip().lower()
        if status not in DECISION_MODEL_STATUSES:
            raise ValueError(f"unknown decision model status: {self.status!r}")
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "role_ids", roles)
        object.__setattr__(self, "model_kind", model_kind)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "note", str(self.note))


class DecisionModelRegistry:
    """Deterministic registry for decision model declarations.

    The registry is intentionally explicit and small: duplicate ids fail
    closed, resolution order is registration order, and model construction is
    the only operation that invokes a factory. It does not import or discover
    Python modules implicitly.
    """

    def __init__(self, registrations: tuple[DecisionModelRegistration, ...] = ()) -> None:
        self._registrations: dict[str, DecisionModelRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: DecisionModelRegistration) -> None:
        if not isinstance(registration, DecisionModelRegistration):
            raise TypeError("registry entries must be DecisionModelRegistration")
        if registration.model_id in self._registrations:
            raise ValueError(f"decision model already registered: {registration.model_id}")
        self._registrations[registration.model_id] = registration

    def get(self, model_id: str) -> DecisionModelRegistration:
        key = str(model_id).strip()
        try:
            return self._registrations[key]
        except KeyError as exc:
            raise KeyError(f"unknown decision model: {key}") from exc

    def resolve(
        self,
        *,
        domain: str,
        role_id: str | None = None,
        model_kind: str | None = None,
        statuses: frozenset[str] | None = None,
    ) -> tuple[DecisionModelRegistration, ...]:
        domain_key = str(domain).strip().lower()
        role_key = None if role_id is None else str(role_id).strip()
        kind_key = None if model_kind is None else str(model_kind).strip().lower()
        if kind_key is not None and kind_key not in DECISION_MODEL_KINDS:
            raise ValueError(f"unknown decision model kind: {model_kind!r}")
        allowed_statuses = DECISION_MODEL_STATUSES if statuses is None else frozenset(statuses)
        unknown_statuses = allowed_statuses - DECISION_MODEL_STATUSES
        if unknown_statuses:
            raise ValueError(f"unknown decision model statuses: {sorted(unknown_statuses)!r}")
        return tuple(
            registration
            for registration in self._registrations.values()
            if registration.domain == domain_key
            and (role_key is None or role_key in registration.role_ids)
            and (kind_key is None or registration.model_kind == kind_key)
            and registration.status in allowed_statuses
        )

    def create(self, model_id: str, **factory_kwargs: Any) -> DecisionModel:
        registration = self.get(model_id)
        model = registration.factory(**factory_kwargs)
        if not isinstance(model, DecisionModel):
            raise TypeError(
                f"decision model factory {registration.model_id!r} returned an object "
                "without reset/decide/close lifecycle methods"
            )
        return model

    def create_for(
        self,
        *,
        domain: str,
        role_id: str,
        model_id: str | None = None,
        model_kind: str | None = None,
        statuses: frozenset[str] | None = None,
        **factory_kwargs: Any,
    ) -> DecisionModel:
        """Create the model admitted for one domain/role pair.

        A scenario may provide ``model_id`` for deterministic selection.  The
        registry still validates that the selected declaration belongs to the
        requested domain, role, and allowed status set.  Without an explicit
        id exactly one registration must match; ambiguity fails closed rather
        than silently choosing registration order.
        """

        if model_id is not None and str(model_id).strip():
            registration = self.get(model_id)
            domain_key = str(domain).strip().lower()
            role_key = str(role_id).strip()
            kind_key = None if model_kind is None else str(model_kind).strip().lower()
            if kind_key is not None and kind_key not in DECISION_MODEL_KINDS:
                raise ValueError(f"unknown decision model kind: {model_kind!r}")
            allowed_statuses = DECISION_MODEL_STATUSES if statuses is None else frozenset(statuses)
            unknown_statuses = allowed_statuses - DECISION_MODEL_STATUSES
            if unknown_statuses:
                raise ValueError(f"unknown decision model statuses: {sorted(unknown_statuses)!r}")
            if registration.domain != domain_key:
                raise ValueError(
                    f"decision model {registration.model_id!r} belongs to domain {registration.domain!r}, "
                    f"not {domain_key!r}"
                )
            if role_key not in registration.role_ids:
                raise ValueError(
                    f"decision model {registration.model_id!r} does not declare role {role_key!r}"
                )
            if kind_key is not None and registration.model_kind != kind_key:
                raise ValueError(
                    f"decision model {registration.model_id!r} has kind {registration.model_kind!r}, "
                    f"not {kind_key!r}"
                )
            if registration.status not in allowed_statuses:
                raise ValueError(
                    f"decision model {registration.model_id!r} has status {registration.status!r}, "
                    f"not admitted by {sorted(allowed_statuses)!r}"
                )
            return self.create(registration.model_id, **factory_kwargs)

        matches = self.resolve(domain=domain, role_id=role_id, model_kind=model_kind, statuses=statuses)
        if not matches:
            raise LookupError(
                f"no decision model registered for domain={str(domain).strip().lower()!r}, "
                f"role={str(role_id).strip()!r}"
            )
        if len(matches) != 1:
            raise ValueError(
                f"ambiguous decision models for domain={str(domain).strip().lower()!r}, "
                f"role={str(role_id).strip()!r}: {[entry.model_id for entry in matches]!r}"
            )
        return self.create(matches[0].model_id, **factory_kwargs)

    def snapshot(self) -> tuple[DecisionModelRegistration, ...]:
        """Return registrations in deterministic insertion order."""

        return tuple(self._registrations.values())

    def as_mapping(self) -> Mapping[str, DecisionModelRegistration]:
        """Return an immutable view for diagnostics and scenario compilation."""

        return MappingProxyType(self._registrations)


__all__ = [
    "DECISION_MODEL_KINDS",
    "DECISION_MODEL_STATUSES",
    "DecisionModel",
    "DecisionModelFactory",
    "DecisionModelRegistration",
    "DecisionModelRegistry",
]
