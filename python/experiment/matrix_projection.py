"""Shared projection vocabulary for declarative run-config matrices.

Every config matrix owned by the Experiment face (the air-combat set, the
cooperative flight-shaping set) projects its registered
:class:`~python.experiment.definition.Experiment` objects into checked-in
JSON files through the same two concepts:

- :class:`RenderStyle` pins the per-entry serialization dialect required for
  byte parity with the historical checked-in file (scalar-array layout plus
  verbatim literal spellings the shortest-form JSON encoder would rewrite).
- :class:`MatrixEntryBase` binds one experiment to its pinned output path
  under the owning matrix directory.

This module is standard library only and performs no IO; concrete matrices
(``air_combat_matrix``, ``cooperative_flight_matrix``) subclass
:class:`MatrixEntryBase` with their own ``MATRIX_DIR`` and register through
``ExperimentRegistry`` (extension via registration, G5). Serialization is
owned by ``tools/maintenance/experiment_matrix/generate.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import ClassVar, Mapping

from python.experiment.definition import Experiment

SCALAR_ARRAY_LAYOUTS = ("inline", "expanded")


@dataclass(frozen=True)
class RenderStyle:
    """Per-entry serialization dialect required for byte parity."""

    scalar_array_layout: str = "inline"
    literal_overrides: Mapping[tuple[str, ...], str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scalar_array_layout not in SCALAR_ARRAY_LAYOUTS:
            raise ValueError(
                f"scalar_array_layout must be one of {SCALAR_ARRAY_LAYOUTS}, "
                f"got {self.scalar_array_layout!r}"
            )
        overrides = dict(self.literal_overrides)
        for path, literal in overrides.items():
            if (
                not isinstance(path, tuple)
                or not path
                or not all(isinstance(part, str) and part for part in path)
            ):
                raise ValueError(f"literal override path must be a tuple of keys: {path!r}")
            if not isinstance(literal, str) or not literal:
                raise ValueError(f"literal override must be a non-empty string: {literal!r}")
        object.__setattr__(self, "literal_overrides", MappingProxyType(overrides))


@dataclass(frozen=True)
class MatrixEntryBase:
    """One registered experiment plus its pinned output projection.

    Concrete matrices subclass this with their own ``MATRIX_DIR`` class
    variable; construction fails fast when the output path does not sit at
    ``MATRIX_DIR/<experiment_id>.json``.
    """

    experiment: Experiment
    output_path: str
    render: RenderStyle

    MATRIX_DIR: ClassVar[str] = ""

    def __post_init__(self) -> None:
        matrix_dir = type(self).MATRIX_DIR
        if not matrix_dir:
            raise TypeError(
                f"{type(self).__name__} must declare a non-empty MATRIX_DIR class variable"
            )
        expected = f"{matrix_dir}/{self.experiment.experiment_id}.json"
        if self.output_path != expected:
            raise ValueError(
                f"matrix output path must be {expected}, got {self.output_path!r}"
            )
