"""Experiment-face owner package (unified architecture program, track T5).

Single owner for the typed Experiment definition
(``Experiment = ScenarioRef x ConfigComposition x Seeds x EvaluationProtocol``,
per the architecture baseline §1.5) and for the declarative config matrices
derived from it. Standard library only: importing this package must never
pull runtime, gym, or training dependencies.
"""

from python.experiment.composition import (
    compose_config,
    ensure_json_value,
    freeze_json_mapping,
    normalize_trailing_keys,
)
from python.experiment.definition import (
    ConfigComposition,
    EvaluationProtocol,
    Experiment,
    ExperimentRegistry,
    ScenarioRef,
    SeedSpec,
)
from python.experiment.report_envelope import (
    ENVELOPE_SCHEMA_VERSION,
    add_report_envelope_arg,
    apply_report_envelope,
    build_report_envelope,
    git_revision,
)

__all__ = [
    "ConfigComposition",
    "ENVELOPE_SCHEMA_VERSION",
    "EvaluationProtocol",
    "Experiment",
    "ExperimentRegistry",
    "ScenarioRef",
    "SeedSpec",
    "add_report_envelope_arg",
    "apply_report_envelope",
    "build_report_envelope",
    "compose_config",
    "ensure_json_value",
    "freeze_json_mapping",
    "git_revision",
    "normalize_trailing_keys",
]
