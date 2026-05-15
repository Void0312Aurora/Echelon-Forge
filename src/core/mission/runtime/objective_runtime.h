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
    double altitude_m = 0.0;
    double altitude_agl_m = 0.0;
    double speed_mps = 0.0;
    double ground_speed_mps = 0.0;
    double gear_fraction = 0.0;
    double heading_error_deg = 0.0;
    double command_code = 0.0;
    double ground_track_error_deg = 0.0;
    bool has_runway_cross_m = false;
    double runway_cross_m = 0.0;
    bool has_runway_from_threshold_m = false;
    double runway_from_threshold_m = 0.0;
    bool on_runway_geom = false;
    bool on_runway_task = false;
    bool on_ground = false;
    double sink_rate_abs_mps = 0.0;
    double ils_localizer_abs = 0.0;
    double ils_glideslope_abs = 0.0;
    double dme_m = 0.0;
    double heading_deg = 0.0;
    double x_m = 0.0;
    double y_m = 0.0;
    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    double target_heading_deg = 0.0;
};

struct ObjectiveShapingConfig {
    double runway_cross_penalty_weight = 0.0;
    double runway_cross_deadband_m = 0.0;
    double runway_cross_norm_m = 20.0;
    double runway_cross_power = 2.0;
    double runway_cross_clip = 0.0;

    double ground_track_penalty_weight = 0.0;
    double ground_track_deadband_deg = 0.0;
    double ground_track_norm_deg = 10.0;
    double ground_track_power = 2.0;
    double ground_track_clip = 0.0;
};

struct ConditionalObjectiveProducts {
    bool valid = false;
    bool matched = false;
    bool unknown_property = false;
    double status0 = 0.0;
    double status1 = 0.0;
    double status2 = 0.0;
    int status_count = 0;
    double success_runway_cross_penalty = 0.0;
    double success_ground_track_error_penalty = 0.0;
    double objective_bonus = 0.0;
};

ConditionalObjectiveProducts evaluate_conditional_objective(
    const ConditionalObjectiveSpec& spec,
    const ConditionalObjectiveInputs& inputs,
    const ObjectiveShapingConfig& shaping
);
