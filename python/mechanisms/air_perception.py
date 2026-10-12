"""Non-executing descriptors for the bounded native Air seeker proof.

The test lane calls the existing C++ LOS, range projection and CV tracker.
Publication occurs in one window; propagation uses elapsed seconds. These
descriptors neither install a provider nor grant production/backend admission.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from python.mechanisms.ports import (
    CompiledMechanismGraph,
    GraphEdge,
    MechanismSpec,
    MechanismSchemaVocabulary,
    PortSpec,
    SchemaVocabularyEntry,
    compile_mechanism_graph,
    compose_graph_as_mechanism,
)

NATIVE_IMPLEMENTATIONS = (
    "missile_guidance::world_los_from_relative_angles",
    "missile_guidance::world_position_from_los_range",
    "missile_guidance::update_world_cv_alpha_beta_tracker",
)
AIR_PERCEPTION_OWNER_SCHEMA_VOCABULARY = MechanismSchemaVocabulary(
    vocabulary_id="qualification.air.perception.schemas",
    version="1",
    entries=(
        SchemaVocabularyEntry(
            "RelativeAnglesWithObserverHeading.v1",
            NATIVE_IMPLEMENTATIONS[0],
        ),
        SchemaVocabularyEntry("WorldDirection3.v1", NATIVE_IMPLEMENTATIONS[0]),
        SchemaVocabularyEntry("RangeWithObserverPosition.v1", NATIVE_IMPLEMENTATIONS[1]),
        SchemaVocabularyEntry("Position3.v1", NATIVE_IMPLEMENTATIONS[1]),
        SchemaVocabularyEntry("CurrentAndMeasurementTime.v1", NATIVE_IMPLEMENTATIONS[2]),
        SchemaVocabularyEntry("WorldCvTrack.v1", NATIVE_IMPLEMENTATIONS[2]),
    ),
)
AIR_PERCEPTION_SCHEMA_VOCABULARY = AIR_PERCEPTION_OWNER_SCHEMA_VOCABULARY.schema_names
_PARAMETER_NAMES = frozenset({"alpha", "beta", "minimum_velocity_baseline_s", "maximum_speed_mps"})


def air_perception_qualification_graph(config: Mapping[str, Any]) -> CompiledMechanismGraph:
    """Describe exactly the parameterized native test slice before execution."""
    if config.get("schema_version") != "echelon_forge.air_perception_qualification.v1":
        raise ValueError("unsupported Air perception qualification schema")
    params = config["tracker_parameters"]
    if not isinstance(params, Mapping) or set(params) != _PARAMETER_NAMES:
        raise ValueError("tracker parameters must name the exact native CV parameter set")
    for name, value in params.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"tracker parameter {name} must be a finite number")
        if name in {"alpha", "beta"} and not 0.0 <= value <= 1.0:
            raise ValueError(f"tracker parameter {name} must be in [0, 1]")
        if name not in {"alpha", "beta"} and value <= 0:
            raise ValueError(f"tracker parameter {name} must be positive")
    policy = config["clock_policy"]
    if (
        not isinstance(policy, Mapping)
        or policy.get("publication_clock") != "window"
        or policy.get("numerical_rate") != "per_second"
        or policy.get("time_unit") != "second"
        or policy.get("measurement_epochs") != "monotonic_seconds"
        or policy.get("publication") != "after_tracker_update"
        or policy.get("lane") != "qualification_only"
    ):
        raise ValueError("unsupported Air perception numerical/publication clock policy")

    common = {
        "version": config["implementation_version"],
        "backend_ref": config["backend_ref"],
        "clock_policy": policy,
        "required_capabilities": ("air.seeker.world_cv",),
    }
    nodes = {
        "los": MechanismSpec(
            "qualification.air.relative_angles_to_los",
            inputs=(PortSpec("angles", "RelativeAnglesWithObserverHeading.v1", "degree"),),
            outputs=(PortSpec("direction", "WorldDirection3.v1", "dimensionless", "world_enu"),),
            implementation_ref=NATIVE_IMPLEMENTATIONS[0],
            **common,
        ),
        "projection": MechanismSpec(
            "qualification.air.los_range_to_measurement",
            inputs=(
                PortSpec("direction", "WorldDirection3.v1", "dimensionless", "world_enu"),
                PortSpec("range_observer", "RangeWithObserverPosition.v1", "meter", "world_enu"),
            ),
            outputs=(PortSpec("position", "Position3.v1", "meter", "world_enu"),),
            parameters={"negative_range_policy": "clamp_to_zero"},
            implementation_ref=NATIVE_IMPLEMENTATIONS[1],
            **common,
        ),
        "tracker": MechanismSpec(
            "qualification.air.world_cv_tracker",
            inputs=(
                PortSpec("position", "Position3.v1", "meter", "world_enu"),
                PortSpec("epochs", "CurrentAndMeasurementTime.v1", "second"),
            ),
            outputs=(PortSpec("track", "WorldCvTrack.v1", None, "world_enu"),),
            stateful=True,
            parameters=params,
            implementation_ref=NATIVE_IMPLEMENTATIONS[2],
            **common,
        ),
    }
    return compile_mechanism_graph(
        "qualification.air.perception",
        nodes,
        (
            GraphEdge("los", "direction", "projection", "direction"),
            GraphEdge("projection", "position", "tracker", "position"),
        ),
        external_inputs=frozenset({"los.angles", "projection.range_observer", "tracker.epochs"}),
        schema_vocabulary=AIR_PERCEPTION_OWNER_SCHEMA_VOCABULARY,
    )


def air_perception_composite(graph: CompiledMechanismGraph) -> MechanismSpec:
    return compose_graph_as_mechanism(
        graph,
        mechanism_id="qualification.air.PerceptionComposite",
        version="1",
        inputs=(
            PortSpec("angles", "RelativeAnglesWithObserverHeading.v1", "degree"),
            PortSpec("range_observer", "RangeWithObserverPosition.v1", "meter", "world_enu"),
            PortSpec("epochs", "CurrentAndMeasurementTime.v1", "second"),
        ),
        outputs=(PortSpec("track", "WorldCvTrack.v1", None, "world_enu"),),
        input_bindings={
            "angles": "los.angles",
            "range_observer": "projection.range_observer",
            "epochs": "tracker.epochs",
        },
        output_bindings={"track": "tracker.track"},
    )
