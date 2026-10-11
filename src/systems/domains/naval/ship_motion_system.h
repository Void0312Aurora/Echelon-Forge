#pragma once

#include <algorithm>
#include <cmath>
#include <numbers>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/domains/naval/command/mission_command_naval.h"
#include "components/domains/naval/command/station_keeping.h"
#include "components/command/pilot_action.h"
#include "components/combat/common/damage_common.h"
#include "components/domains/naval/platform/ship_maneuvering.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/physics/physics_input_policy.h"
#include "components/physics/forces.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/stable_entity_identity.h"

namespace {

inline double ship_wave_heading_factor_deg(double wave_heading_deg, double ship_heading_deg) {
    const double rel_deg = std::remainder(wave_heading_deg - ship_heading_deg, 360.0);
    return std::abs(rel_deg);
}

inline double ship_head_seas_factor(double wave_heading_deg, double ship_heading_deg) {
    const double abs_rel_deg = ship_wave_heading_factor_deg(wave_heading_deg, ship_heading_deg);
    const double head_component = std::abs(std::cos(Math::to_radians(abs_rel_deg)));
    return std::clamp(head_component, 0.0, 1.0);
}

inline double ship_beam_seas_factor(double wave_heading_deg, double ship_heading_deg) {
    const double abs_rel_deg = ship_wave_heading_factor_deg(wave_heading_deg, ship_heading_deg);
    const double beam_component = std::abs(std::sin(Math::to_radians(abs_rel_deg)));
    return std::clamp(beam_component, 0.0, 1.0);
}

inline double ship_sea_state_scale(double sea_state) {
    return std::clamp(sea_state / 6.0, 0.0, 1.0);
}

inline bool ship_pilot_action_requests_manual_takeover(const PilotAction &pilot) {
    constexpr double kPrimaryAxisDeadband = 0.05;
    constexpr double kThrottleDeadband = 0.05;
    return bool(pilot.active) && (std::abs(pilot.stick_roll) > kPrimaryAxisDeadband ||
                                  std::abs(pilot.rudder) > kPrimaryAxisDeadband ||
                                  std::abs(pilot.throttle - 0.5) > kThrottleDeadband);
}

// Resolve a stationing directive onto an ordered heading and speed through the
// velocity-command station-keeping law
// (components/domains/naval/command/station_keeping.h). Returns false, leaving
// the outputs untouched, when the intent carries no usable station.
inline bool resolve_ship_station_command(flecs::world world, const Transform &own_transform,
                                         const NavalCommandIntent &naval_intent,
                                         double fallback_heading_deg,
                                         double *commanded_heading_deg_out,
                                         double *commanded_speed_mps_out,
                                         double minimum_maneuver_speed_mps) {
    if (commanded_heading_deg_out == nullptr || commanded_speed_mps_out == nullptr) {
        return false;
    }
    const auto stationing = mission_command_naval_stationing_directive(naval_intent);
    const std::uint64_t reference_entity_id = stationing.reference_entity_id;
    const double station_radius_m = std::max(0.0, stationing.station_radius_m);
    if (reference_entity_id == 0 || station_radius_m <= 0.0) {
        return false;
    }

    const auto reference_entity = world.entity(reference_entity_id);
    if (!reference_entity.is_valid()) {
        return false;
    }

    const Transform *reference_transform = reference_entity.get<Transform>();
    const Velocity *reference_velocity = reference_entity.get<Velocity>();
    if (reference_transform == nullptr || reference_velocity == nullptr) {
        return false;
    }

    const naval_station_keeping::StationCommand command =
        naval_station_keeping::station_keeping_command(
            reference_transform->x, reference_transform->y, reference_velocity->vx,
            reference_velocity->vy, stationing.station_bearing_deg, station_radius_m,
            own_transform.x, own_transform.y, fallback_heading_deg, minimum_maneuver_speed_mps,
            own_transform.heading);
    *commanded_heading_deg_out = Math::normalize_heading_deg(command.heading_deg);
    *commanded_speed_mps_out = std::max(0.0, command.speed_mps);
    return true;
}

} // namespace

inline void register_ship_motion_system(flecs::world &ecs) {
    // Surge and yaw follow the maneuvering law in
    // components/domains/naval/platform/ship_maneuvering.h. The yaw rate is
    // carried in AngularVelocity::r (rad/s, positive turning the heading
    // clockwise); ships carry no Inertia or ForceAccumulator, so no rigid-body
    // integrator touches it.
    //
    // Damage reaches mobility here: PlatformDamageState::mobility_capability is
    // the surviving propulsive power fraction. The naval damage system runs
    // later in the step (stage 29), so motion reads the capability of the
    // previous step, a one-step lag.
    ecs.system<Transform, Velocity, AngularVelocity, const ShipPlatform>("ShipMotion")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto transform = it.field<Transform>(0);
                auto velocity = it.field<Velocity>(1);
                auto angular = it.field<AngularVelocity>(2);
                auto ship = it.field<const ShipPlatform>(3);
                const EnvironmentModelRef *env_ref = it.world().get<EnvironmentModelRef>();

                const double dt = physics_runtime::resolve_entity_dt(it.delta_time());
                const ecs_world_info_t *info = ecs_get_world_info(it.world().c_ptr());
                const double current_time =
                    info ? static_cast<double>(info->world_time_total) : 0.0;

                for (auto i : it) {
                    const ship_maneuvering::Envelope hull =
                        ship_maneuvering::make_envelope(ship[i]);
                    const PilotAction *pilot = it.entity(i).get<PilotAction>();
                    const NavalCommandIntent *naval_intent = it.entity(i).get<NavalCommandIntent>();
                    const PlatformDamageState *damage = it.entity(i).get<PlatformDamageState>();

                    const double speed_mps = std::hypot(velocity[i].vx, velocity[i].vy);
                    const double heading_deg = Math::normalize_heading_deg(transform[i].heading);
                    const double yaw_rate = angular[i].r;

                    // Engine order and rudder. Without an order the ship keeps
                    // making turns for its present speed with the rudder amidships.
                    double ordered_speed_mps = speed_mps;
                    double commanded_yaw_rate = 0.0;
                    if (pilot && ship_pilot_action_requests_manual_takeover(*pilot)) {
                        const double rudder =
                            std::clamp(pilot->rudder + pilot->stick_roll, -1.0, 1.0);
                        commanded_yaw_rate =
                            rudder * ship_maneuvering::max_yaw_rate_rad_s(hull, speed_mps);
                        ordered_speed_mps =
                            std::clamp(pilot->throttle, 0.0, 1.0) * hull.max_speed_mps;
                    } else if (naval_intent && naval_intent->active) {
                        double commanded_heading_deg =
                            Math::normalize_heading_deg(naval_intent->cmd_heading_deg);
                        ordered_speed_mps = std::max(0.0, naval_intent->cmd_speed_mps);
                        resolve_ship_station_command(
                            it.world(), transform[i], *naval_intent, commanded_heading_deg,
                            &commanded_heading_deg, &ordered_speed_mps,
                            (hull.steerageway_mps + naval_station_keeping::kHeadingSpeedFloorMps) /
                                hull.turn_speed_ratio);
                        const double heading_error_rad = Math::to_radians(
                            std::remainder(commanded_heading_deg - heading_deg, 360.0));
                        commanded_yaw_rate = ship_maneuvering::commanded_yaw_rate_rad_s(
                            hull, speed_mps, heading_error_rad, yaw_rate);
                    }

                    double sea_state = ship[i].sea_state;
                    double wave_heading_deg = ship[i].wave_heading_deg;
                    double wave_period_s = ship[i].wave_period_s;
                    if (env_ref && env_ref->model) {
                        const auto maritime_state = env_ref->model->get_maritime_state();
                        if (maritime_state.configured) {
                            sea_state = maritime_state.sea_state;
                            wave_heading_deg = maritime_state.wave_heading_deg;
                            wave_period_s = maritime_state.wave_period_s;
                        }
                    }
                    const double sea_state_scale = ship_sea_state_scale(sea_state);
                    const double head_seas_factor =
                        ship_head_seas_factor(wave_heading_deg, transform[i].heading);
                    const double beam_seas_factor =
                        ship_beam_seas_factor(wave_heading_deg, transform[i].heading);
                    const double added_resistance_fraction = std::clamp(
                        std::max(0.0, ship[i].added_resistance_fraction_sea_state_6) *
                            sea_state_scale * (0.65 * head_seas_factor + 0.35 * beam_seas_factor),
                        0.0, 0.6);

                    const double mobility_capability = damage ? damage->mobility_capability : 1.0;
                    const bool mobility_kill = damage ? damage->mobility_kill : false;
                    ordered_speed_mps = std::clamp(ordered_speed_mps, 0.0,
                                                   ship_maneuvering::attainable_speed_mps(
                                                       hull, mobility_capability, mobility_kill,
                                                       1.0 - added_resistance_fraction));

                    const double turn_multiplier =
                        ship_maneuvering::turn_resistance_multiplier(hull, speed_mps, yaw_rate);
                    const double propulsive_accel = ship_maneuvering::propulsive_accel_mps2(
                        hull, ordered_speed_mps, speed_mps, turn_multiplier,
                        ship_maneuvering::propulsive_thrust_fraction(mobility_capability,
                                                                     mobility_kill));
                    const double next_speed_mps = ship_maneuvering::step_speed_mps(
                        hull, speed_mps, propulsive_accel, turn_multiplier, dt);
                    const double next_yaw_rate = ship_maneuvering::step_yaw_rate_rad_s(
                        hull, speed_mps, yaw_rate, commanded_yaw_rate, dt);

                    // Advance along the arc: heading by the trapezoid of the yaw
                    // rate, position at the mid-step heading and speed.
                    const double heading_step_deg =
                        0.5 * (yaw_rate + next_yaw_rate) * dt * 180.0 / std::numbers::pi_v<double>;
                    const double mid_heading_rad =
                        Math::to_radians(heading_deg + 0.5 * heading_step_deg);
                    const double mid_speed_mps = 0.5 * (speed_mps + next_speed_mps);
                    transform[i].x += std::sin(mid_heading_rad) * mid_speed_mps * dt;
                    transform[i].y += std::cos(mid_heading_rad) * mid_speed_mps * dt;
                    transform[i].z = 0.0;

                    const double next_heading_deg =
                        Math::normalize_heading_deg(heading_deg + heading_step_deg);
                    const double heading_rad = Math::to_radians(next_heading_deg);
                    transform[i].heading = next_heading_deg;
                    velocity[i].vx = std::sin(heading_rad) * next_speed_mps;
                    velocity[i].vy = std::cos(heading_rad) * next_speed_mps;
                    velocity[i].vz = 0.0;
                    angular[i].r = next_yaw_rate;

                    if (sea_state_scale > 0.0) {
                        wave_period_s = std::max(2.0, wave_period_s > 0.0 ? wave_period_s : 8.0);
                        const double omega = (2.0 * std::numbers::pi_v<double>) / wave_period_s;
                        const double roll_amplitude_deg =
                            std::max(0.0, ship[i].max_roll_deg_sea_state_6) * sea_state_scale *
                            (0.35 + 0.65 * beam_seas_factor);
                        const double pitch_amplitude_deg =
                            std::max(0.0, ship[i].max_pitch_deg_sea_state_6) * sea_state_scale *
                            (0.35 + 0.65 * head_seas_factor);
                        // Derived from the stable serial, not the raw Flecs id: the id moves
                        // with the census, with earlier spawns and with post-reset recycling,
                        // so a raw-id phase would drift with unrelated changes to other units
                        // (docs/architecture/work/active/stable_entity_identity, P1 E4). This is
                        // a pure function of the serial, not a stochastic draw, so it does not
                        // go through stochastic_draw.h.
                        //
                        // Every ship carries a serial: it is a `KeyEntity`-bearing SimObject and
                        // therefore stamped on creation. A missing serial here is not a
                        // legitimate "not yet identified" state to fall back from silently; it
                        // is an invariant violation on the same footing as a missing serial at a
                        // stochastic draw site (P5 review N1).
                        const StableEntitySerial *serial = it.entity(i).get<StableEntitySerial>();
                        if (serial == nullptr) {
                            stable_identity::identity_invariant_violation(
                                "ship_motion_system: sea-state phase",
                                "ship carries no StableEntitySerial",
                                static_cast<std::uint64_t>(it.entity(i).id()));
                        }
                        const double phase_seed =
                            std::fmod(static_cast<double>(serial->value % 1024ULL) * 0.137,
                                      2.0 * std::numbers::pi_v<double>);
                        transform[i].roll =
                            roll_amplitude_deg * std::sin(omega * current_time + phase_seed);
                        transform[i].pitch =
                            pitch_amplitude_deg *
                            std::sin(omega * current_time * 0.93 + phase_seed * 0.7 +
                                     std::numbers::pi_v<double> / 6.0);
                    } else {
                        transform[i].pitch = 0.0;
                        transform[i].roll = 0.0;
                    }
                }
            }
        });
}
