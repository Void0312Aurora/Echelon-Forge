"""Typed Experiment definitions: the Experiment-face vocabulary owner.

This module freezes the typed Experiment definition from
``docs/architecture/standards/simulation_system_architecture_design.md`` §1.5:

    Experiment = ScenarioRef x ConfigComposition x Seeds x EvaluationProtocol

Design rules implemented here:

1. Experiment definitions are declarative data, not imperative code: every
   type is a frozen dataclass whose payload is deep-frozen and validated at
   construction (fail fast on illegal combinations).
2. Extension is registration (G5): scenarios, config bases, evaluation
   protocols, and experiments attach through ``ExperimentRegistry``; nothing
   here special-cases a concrete matrix.
3. Zero bootstrap side effects: standard library only, no IO, and no
   ``ef_py``/gym/SB3 imports. Run configurations are *projections* of these
   definitions; rendering them to files is owned by the generator tool
   (``tools/maintenance/experiment_matrix/generate.py``).

Curriculum stage and comparability constraints are named by the §1.5
amendment but are not yet used by any registered matrix; per the program's
"registry content follows actual usage" rule they are deliberately not
fields yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from python.experiment.composition import freeze_json_mapping

_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_]*\Z")


def _require_identifier(value: str, description: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(
            f"{description} must match [a-z0-9][a-z0-9_]*, got {value!r}"
        )


@dataclass(frozen=True)
class ScenarioRef:
    """Repository-relative reference to one scenario JSON document."""

    path: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path:
            raise ValueError(f"scenario path must be a non-empty string, got {self.path!r}")
        if "\\" in self.path:
            raise ValueError(f"scenario path must use posix separators: {self.path!r}")
        parts = self.path.split("/")
        if self.path.startswith("/") or ":" in parts[0]:
            raise ValueError(f"scenario path must be repository-relative: {self.path!r}")
        if ".." in parts or "" in parts:
            raise ValueError(f"scenario path must not contain empty or '..' segments: {self.path!r}")
        if not self.path.endswith(".json"):
            raise ValueError(f"scenario path must reference a .json document: {self.path!r}")


@dataclass(frozen=True)
class SeedSpec:
    """Normalized seed set: strictly increasing, unique, non-negative ints.

    Direct construction fails fast on unnormalized input; ``normalize`` is
    the sanctioned constructor for arbitrary iterables. An empty tuple means
    the experiment delegates seeding to the training bootstrap default.
    """

    values: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.values, tuple):
            raise TypeError(f"seed values must be a tuple, got {type(self.values).__name__}")
        for value in self.values:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"seed values must be ints, got {value!r}")
            if value < 0:
                raise ValueError(f"seed values must be non-negative, got {value!r}")
        if list(self.values) != sorted(set(self.values)):
            raise ValueError(
                f"seed values must be strictly increasing and unique: {self.values!r}; "
                "use SeedSpec.normalize() for arbitrary iterables"
            )

    @classmethod
    def normalize(cls, values: Iterable[int]) -> "SeedSpec":
        collected: list[int] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"seed values must be ints, got {value!r}")
            collected.append(value)
        return cls(tuple(sorted(set(collected))))


@dataclass(frozen=True)
class EvaluationProtocol:
    """One registered evaluation protocol name plus its intent description."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        _require_identifier(self.name, "evaluation protocol name")
        if not isinstance(self.description, str):
            raise TypeError("evaluation protocol description must be a string")


@dataclass(frozen=True)
class ConfigComposition:
    """base + delta configuration composition.

    ``base_id`` names a registered config base; ``delta`` is the per-run
    override mapping. The delta is validated as strict JSON and deep-frozen
    at construction; its key order is semantic (novel keys append in delta
    order during composition).
    """

    base_id: str
    delta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_identifier(self.base_id, "config base id")
        object.__setattr__(self, "delta", freeze_json_mapping(self.delta))


@dataclass(frozen=True)
class Experiment:
    """Typed Experiment definition aligned with the §1.5 Experiment face."""

    experiment_id: str
    scenario: ScenarioRef
    config: ConfigComposition
    seeds: SeedSpec
    evaluation_protocol: str

    def __post_init__(self) -> None:
        _require_identifier(self.experiment_id, "experiment id")
        if not isinstance(self.scenario, ScenarioRef):
            raise TypeError(f"scenario must be a ScenarioRef, got {type(self.scenario).__name__}")
        if not isinstance(self.config, ConfigComposition):
            raise TypeError(
                f"config must be a ConfigComposition, got {type(self.config).__name__}"
            )
        if not isinstance(self.seeds, SeedSpec):
            raise TypeError(f"seeds must be a SeedSpec, got {type(self.seeds).__name__}")
        _require_identifier(self.evaluation_protocol, "evaluation protocol reference")


class ExperimentRegistry:
    """Registration socket for config bases, protocols, and experiments (G5).

    Registration is fail-fast: duplicate names and dangling references
    (unknown config base, unknown evaluation protocol) raise immediately.
    """

    def __init__(self) -> None:
        self._config_bases: dict[str, Mapping[str, Any]] = {}
        self._protocols: dict[str, EvaluationProtocol] = {}
        self._experiments: dict[str, Experiment] = {}

    def register_config_base(self, base_id: str, config: Mapping[str, Any]) -> None:
        _require_identifier(base_id, "config base id")
        if base_id in self._config_bases:
            raise ValueError(f"duplicate config base registration: {base_id}")
        self._config_bases[base_id] = freeze_json_mapping(config)

    def register_evaluation_protocol(self, protocol: EvaluationProtocol) -> None:
        if not isinstance(protocol, EvaluationProtocol):
            raise TypeError(
                f"expected an EvaluationProtocol, got {type(protocol).__name__}"
            )
        if protocol.name in self._protocols:
            raise ValueError(f"duplicate evaluation protocol registration: {protocol.name}")
        self._protocols[protocol.name] = protocol

    def register_experiment(self, experiment: Experiment) -> None:
        if not isinstance(experiment, Experiment):
            raise TypeError(f"expected an Experiment, got {type(experiment).__name__}")
        if experiment.experiment_id in self._experiments:
            raise ValueError(
                f"duplicate experiment registration: {experiment.experiment_id}"
            )
        if experiment.config.base_id not in self._config_bases:
            raise ValueError(
                f"experiment {experiment.experiment_id} references unregistered "
                f"config base: {experiment.config.base_id}"
            )
        if experiment.evaluation_protocol not in self._protocols:
            raise ValueError(
                f"experiment {experiment.experiment_id} references unregistered "
                f"evaluation protocol: {experiment.evaluation_protocol}"
            )
        self._experiments[experiment.experiment_id] = experiment

    def config_base(self, base_id: str) -> Mapping[str, Any]:
        if base_id not in self._config_bases:
            raise KeyError(f"unknown config base: {base_id}")
        return self._config_bases[base_id]

    def evaluation_protocol(self, name: str) -> EvaluationProtocol:
        if name not in self._protocols:
            raise KeyError(f"unknown evaluation protocol: {name}")
        return self._protocols[name]

    def experiment(self, experiment_id: str) -> Experiment:
        if experiment_id not in self._experiments:
            raise KeyError(f"unknown experiment: {experiment_id}")
        return self._experiments[experiment_id]

    @property
    def config_base_ids(self) -> tuple[str, ...]:
        return tuple(self._config_bases)

    @property
    def evaluation_protocol_names(self) -> tuple[str, ...]:
        return tuple(self._protocols)

    @property
    def experiments(self) -> tuple[Experiment, ...]:
        return tuple(self._experiments.values())
