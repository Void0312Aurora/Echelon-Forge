#pragma once

#include <vector>

enum class ConditionalObjectiveProperty {
    Unknown = 0,
    Altitude,
    AltitudeAGL,
    Speed,
    GroundSpeed,
    Gear,
    HeadingErrorDeg,
    CommandCode,
    GroundTrackErrorDeg,
    RunwayCrossAbsM,
    RunwayFromThresholdM,
    OnRunwayGeom,
    OnRunway,
    OnGround,
    SinkRateAbsMps,
    IlsLocalizerAbs,
    IlsGlideslopeAbs,
    DmeM,
    Heading,
    X,
    Y,
    SelfActive,
    TargetActive,
    SelfHealth,
    TargetHealth,
    MissilesRemaining,
    TargetRangeM,
};

enum class ConditionalObjectiveOp {
    GreaterEqual = 0,
    GreaterThan,
    LessEqual,
    LessThan,
};

enum class ConditionalObjectiveTargetKind {
    Literal = 0,
    CommandAltitude,
    CommandSpeed,
    CommandHeading,
};

struct ConditionalObjectiveCondition {
    ConditionalObjectiveProperty property_code = ConditionalObjectiveProperty::Unknown;
    ConditionalObjectiveOp op_code = ConditionalObjectiveOp::GreaterEqual;
    ConditionalObjectiveTargetKind target_kind = ConditionalObjectiveTargetKind::Literal;
    double target_value = 0.0;
    double target_scale = 1.0;
};

struct ConditionalObjectiveSpec {
    std::vector<ConditionalObjectiveCondition> conditions;
    double reward_bonus = 1000.0;
};

struct ConditionalObjectiveInputs {
#define EF_OBJECTIVE_INPUT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/objective_inputs.inc"
};

struct ObjectiveShapingConfig {
#define EF_OBJECTIVE_SHAPING(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/objective_shaping.inc"
};

struct ConditionalObjectiveProducts {
#define EF_OBJECTIVE_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/objective_products.inc"
};

ConditionalObjectiveProducts
evaluate_conditional_objective(const ConditionalObjectiveSpec &spec,
                               const ConditionalObjectiveInputs &inputs,
                               const ObjectiveShapingConfig &shaping);
