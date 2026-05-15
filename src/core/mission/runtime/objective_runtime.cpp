#include "core/mission/runtime/objective_runtime.h"

#include <algorithm>
#include <cmath>

namespace {

double clamp_value(double value, double lo, double hi) {
    return std::min(std::max(value, lo), hi);
}

double clipped_power_term(double err, double norm, double power, double clip) {
    if (err <= 0.0) {
        return 0.0;
    }
    double use_norm = norm;
    if (use_norm <= 1.0e-6) {
        use_norm = 1.0;
    }
    double x = err / use_norm;
    if (clip > 0.0) {
        x = std::min(x, clip);
    }
    return std::pow(x, clamp_value(power, 1.0, 8.0));
}

double resolve_target_value(const ConditionalObjectiveCondition& condition, const ConditionalObjectiveInputs& inputs) {
    switch (condition.target_kind) {
        case ConditionalObjectiveTargetKind::Literal:
            return condition.target_value;
        case ConditionalObjectiveTargetKind::CommandAltitude:
            return inputs.target_altitude_m * condition.target_scale;
        case ConditionalObjectiveTargetKind::CommandSpeed:
            return inputs.target_speed_mps * condition.target_scale;
        case ConditionalObjectiveTargetKind::CommandHeading:
            return inputs.target_heading_deg;
        default:
            return condition.target_value;
    }
}

bool resolve_property_value(
    const ConditionalObjectiveInputs& inputs,
    ConditionalObjectiveProperty property,
    double* out_value
) {
    if (out_value == nullptr) {
        return false;
    }
    switch (property) {
        case ConditionalObjectiveProperty::Altitude:
            *out_value = inputs.altitude_m;
            return true;
        case ConditionalObjectiveProperty::AltitudeAGL:
            *out_value = inputs.altitude_agl_m;
            return true;
        case ConditionalObjectiveProperty::Speed:
            *out_value = inputs.speed_mps;
            return true;
        case ConditionalObjectiveProperty::GroundSpeed:
            *out_value = inputs.ground_speed_mps;
            return true;
        case ConditionalObjectiveProperty::Gear:
            *out_value = inputs.gear_fraction;
            return true;
        case ConditionalObjectiveProperty::HeadingErrorDeg:
            *out_value = inputs.heading_error_deg;
            return true;
        case ConditionalObjectiveProperty::CommandCode:
            *out_value = inputs.command_code;
            return true;
        case ConditionalObjectiveProperty::GroundTrackErrorDeg:
            *out_value = inputs.ground_track_error_deg;
            return true;
        case ConditionalObjectiveProperty::RunwayCrossAbsM:
            *out_value = inputs.has_runway_cross_m ? std::abs(inputs.runway_cross_m) : std::numeric_limits<double>::infinity();
            return true;
        case ConditionalObjectiveProperty::RunwayFromThresholdM:
            *out_value = inputs.has_runway_from_threshold_m ? inputs.runway_from_threshold_m : std::numeric_limits<double>::infinity();
            return true;
        case ConditionalObjectiveProperty::OnRunwayGeom:
            *out_value = inputs.on_runway_geom ? 1.0 : 0.0;
            return true;
        case ConditionalObjectiveProperty::OnRunway:
            *out_value = inputs.on_runway_task ? 1.0 : 0.0;
            return true;
        case ConditionalObjectiveProperty::OnGround:
            *out_value = inputs.on_ground ? 1.0 : 0.0;
            return true;
        case ConditionalObjectiveProperty::SinkRateAbsMps:
            *out_value = inputs.sink_rate_abs_mps;
            return true;
        case ConditionalObjectiveProperty::IlsLocalizerAbs:
            *out_value = inputs.ils_localizer_abs;
            return true;
        case ConditionalObjectiveProperty::IlsGlideslopeAbs:
            *out_value = inputs.ils_glideslope_abs;
            return true;
        case ConditionalObjectiveProperty::DmeM:
            *out_value = inputs.dme_m;
            return true;
        case ConditionalObjectiveProperty::Heading:
            *out_value = inputs.heading_deg;
            return true;
        case ConditionalObjectiveProperty::X:
            *out_value = inputs.x_m;
            return true;
        case ConditionalObjectiveProperty::Y:
            *out_value = inputs.y_m;
            return true;
        case ConditionalObjectiveProperty::Unknown:
        default:
            return false;
    }
}

bool compare_value(double lhs, ConditionalObjectiveOp op, double rhs) {
    switch (op) {
        case ConditionalObjectiveOp::GreaterEqual:
            return lhs >= rhs;
        case ConditionalObjectiveOp::GreaterThan:
            return lhs > rhs;
        case ConditionalObjectiveOp::LessEqual:
            return lhs <= rhs;
        case ConditionalObjectiveOp::LessThan:
            return lhs < rhs;
        default:
            return false;
    }
}

}  // namespace

ConditionalObjectiveProducts evaluate_conditional_objective(
    const ConditionalObjectiveSpec& spec,
    const ConditionalObjectiveInputs& inputs,
    const ObjectiveShapingConfig& shaping
) {
    ConditionalObjectiveProducts out{};
    out.valid = true;

    bool matched = true;
    for (size_t i = 0; i < spec.conditions.size(); ++i) {
        const auto& condition = spec.conditions[i];
        double value = 0.0;
        const bool supported = resolve_property_value(
            inputs,
            condition.property_code,
            &value
        );
        if (!supported) {
            out.unknown_property = true;
            matched = false;
            break;
        }
        if (i == 0) {
            out.status0 = value;
        } else if (i == 1) {
            out.status1 = value;
        } else if (i == 2) {
            out.status2 = value;
        }
        if (i < 3) {
            out.status_count = static_cast<int>(i + 1);
        }
        const double target = resolve_target_value(condition, inputs);
        if (!compare_value(value, condition.op_code, target)) {
            matched = false;
            break;
        }
    }

    out.matched = matched;
    if (!matched) {
        return out;
    }

    out.objective_bonus = spec.reward_bonus;
    if (shaping.runway_cross_penalty_weight != 0.0 && inputs.has_runway_cross_m) {
        const double err = std::abs(inputs.runway_cross_m) - std::max(0.0, shaping.runway_cross_deadband_m);
        if (err > 0.0) {
            out.success_runway_cross_penalty = shaping.runway_cross_penalty_weight * clipped_power_term(
                err,
                shaping.runway_cross_norm_m <= 1.0e-6 ? 20.0 : shaping.runway_cross_norm_m,
                shaping.runway_cross_power,
                shaping.runway_cross_clip
            );
        }
    }
    if (shaping.ground_track_penalty_weight != 0.0) {
        const double err = inputs.ground_track_error_deg - std::max(0.0, shaping.ground_track_deadband_deg);
        if (err > 0.0) {
            out.success_ground_track_error_penalty = shaping.ground_track_penalty_weight * clipped_power_term(
                err,
                shaping.ground_track_norm_deg <= 1.0e-6 ? 10.0 : shaping.ground_track_norm_deg,
                shaping.ground_track_power,
                shaping.ground_track_clip
            );
        }
    }
    return out;
}
