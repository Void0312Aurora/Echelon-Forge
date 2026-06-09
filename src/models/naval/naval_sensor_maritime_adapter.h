#pragma once

#include <algorithm>
#include <cmath>

#include "components/basic/common.h"
#include "components/naval/ship_platform.h"
#include "components/systems/sensor.h"
#include "core/interfaces/environment_model.h"

namespace naval::sensor {

inline IEnvironmentModel::MaritimeState maritime_state_for_sensor(
    const EnvironmentModelRef* env_ref,
    const flecs::entity& owner
) {
    if (env_ref && env_ref->model) {
        const auto state = env_ref->model->get_maritime_state();
        if (state.configured) {
            return state;
        }
    }

    IEnvironmentModel::MaritimeState state{};
    if (const ShipPlatform* ship = owner.get<ShipPlatform>()) {
        state.configured = true;
        state.sea_state = std::max(0.0, ship->sea_state);
        state.wave_heading_deg = ship->wave_heading_deg;
        state.wave_period_s = std::max(2.0, ship->wave_period_s);
    }
    return state;
}

inline bool is_maritime_surface_target(const flecs::entity& target) {
    if (const KeyEntity* target_key = target.get<KeyEntity>()) {
        return target_key->type == UnitType::Ship;
    }
    return target.get<ShipPlatform>() != nullptr;
}

inline double maritime_radar_sea_clutter_loss(
    const Sensor& sensor,
    const EnvironmentModelRef* env_ref,
    const flecs::entity& owner,
    const flecs::entity& target,
    double dist_m,
    double dz_m
) {
    constexpr double kPi = 3.14159265358979323846;

    if (!sensor.sea_clutter_enabled || sensor.sea_clutter_sensitivity <= 0.0) {
        return 1.0;
    }

    const auto maritime_state = maritime_state_for_sensor(env_ref, owner);
    const double sea_state = maritime_state.sea_state;
    if (sea_state <= 0.0 || !is_maritime_surface_target(target)) {
        return 1.0;
    }

    const double antenna_height = std::max(1.0, sensor.antenna_height_m);
    const double grazing_rad = std::atan2(std::abs(dz_m) + 2.0, std::max(1.0, dist_m));
    const double grazing_deg = grazing_rad * 180.0 / kPi;
    const double low_grazing_factor = std::clamp((5.0 - grazing_deg) / 5.0, 0.0, 1.0);
    const double sea_state_loss =
        sea_state * std::max(0.0, sensor.sea_state_loss_per_level) *
        std::clamp(sensor.sea_clutter_sensitivity, 0.0, 1.0);
    const double height_relief = std::clamp(antenna_height / 40.0, 0.0, 0.5);
    const double net_loss = std::max(
        0.0,
        sea_state_loss * (0.55 + 0.45 * low_grazing_factor) - height_relief
    );
    return std::clamp(1.0 - net_loss, 0.05, 1.0);
}

inline double maritime_radar_ducting_bonus_m(
    const Sensor& sensor,
    const EnvironmentModelRef* env_ref,
    const flecs::entity& owner
) {
    if (!sensor.enable_ducting) {
        return 0.0;
    }

    const auto maritime_state = maritime_state_for_sensor(env_ref, owner);
    const double sea_state = maritime_state.sea_state;
    const double calm_bias = std::clamp((3.0 - sea_state) / 3.0, 0.0, 1.0);
    const double gain_factor = std::max(1.0, sensor.ducting_gain_factor);
    const double bonus_cap = std::max(0.0, sensor.ducting_max_bonus_m);
    const double requested_extension_m = sensor.max_range * (gain_factor - 1.0);
    return std::min(bonus_cap, requested_extension_m * calm_bias);
}

inline double maritime_radar_target_height_m(
    const Sensor& sensor,
    const flecs::entity& target,
    const Transform& target_transform
) {
    double target_height = std::max(0.0, sensor.target_height_bias_m);
    if (const ShipPlatform* target_ship = target.get<ShipPlatform>()) {
        target_height = std::max(
            target_height,
            target_ship->height_above_waterline_m * 0.25
        );
    } else if (target_transform.z > 0.0) {
        target_height = std::max(target_height, target_transform.z);
    }
    return target_height;
}

}  // namespace naval::sensor
