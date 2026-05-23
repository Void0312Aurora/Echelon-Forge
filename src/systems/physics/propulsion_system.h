#pragma once

#include <algorithm>
#include <cmath>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/command/air/control_input_resolution.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/physics/flight_dynamics_tuning.h"
#include "core/interfaces/environment_model.h"

namespace flight_dynamics {
    constexpr double kPropulsionSeaLevelDensity = 1.225;
    constexpr double kPropulsionSeaLevelTemperatureK = 288.15;
    constexpr double kPropulsionForceCanonicalQuantum = 0x1p-32;

    struct PropulsionAtmosphereInputs {
        double sigma = 1.0;
        double theta = 1.0;
        double mach = 0.0;
    };

    inline double canonicalize_propulsion_force_scalar(double value) {
        if (!std::isfinite(value) || kPropulsionForceCanonicalQuantum <= 0.0) {
            return value;
        }
        if (std::abs(value) <= (kPropulsionForceCanonicalQuantum * 0.5)) {
            return 0.0;
        }
        const double rounded = std::nearbyint(value / kPropulsionForceCanonicalQuantum) *
            kPropulsionForceCanonicalQuantum;
        return std::abs(rounded) <= (kPropulsionForceCanonicalQuantum * 0.5) ? 0.0 : rounded;
    }

    inline double first_order_step(double state, double command, double dt, double tau_s) {
        if (!std::isfinite(state)) {
            state = 0.0;
        }
        if (!std::isfinite(command)) {
            return state;
        }
        if (tau_s <= 1.0e-6 || dt <= 0.0) {
            return command;
        }
        const double gain = std::clamp(dt / (tau_s + dt), 0.0, 1.0);
        return state + gain * (command - state);
    }

    inline double propulsion_ram_factor(const EngineTuning& tuning, double mach) {
        mach = std::max(0.0, mach);
        const double rise_mach = std::min(mach, std::max(0.0, tuning.ram_rise_mach_cap));
        double factor = 1.0 + tuning.ram_rise_gain * rise_mach;
        if (mach > tuning.ram_decay_start_mach) {
            factor -= tuning.ram_decay_gain * (mach - tuning.ram_decay_start_mach);
        }
        return std::max(0.6, factor);
    }

    inline EngineTuning resolve_propulsion_runtime_tuning(
        const Propulsion& propulsion,
        const EngineTuning* attached_tuning
    ) {
        EngineTuning runtime_tuning = attached_tuning ? *attached_tuning : default_engine_tuning();
        runtime_tuning.enabled = true;
        if (runtime_tuning.mil_thrust_n <= 1.0) {
            runtime_tuning.mil_thrust_n = propulsion.mil_thrust_n;
        }
        if (runtime_tuning.ab_thrust_n <= runtime_tuning.mil_thrust_n) {
            runtime_tuning.ab_thrust_n = std::max(propulsion.ab_thrust_n, runtime_tuning.mil_thrust_n);
        }
        return runtime_tuning;
    }

    inline PropulsionAtmosphereInputs resolve_propulsion_atmosphere_inputs(
        const Transform& transform,
        const Velocity& velocity,
        const AeroState* aero_state,
        const EnvironmentModelRef* env_ref
    ) {
        PropulsionAtmosphereInputs inputs{};
        double oat_temperature_k = kPropulsionSeaLevelTemperatureK;
        double speed_of_sound = 340.29;
        if (env_ref && env_ref->model) {
            const AtmosphericData atm = env_ref->model->get_atmosphere_at(
                transform.x,
                transform.y,
                transform.z
            );
            inputs.sigma = atm.air_density / kPropulsionSeaLevelDensity;
            oat_temperature_k = atm.temperature;
            speed_of_sound = atm.speed_of_sound;
        } else {
            constexpr double kG = 9.80665;
            constexpr double kR = 287.0;
            constexpr double kL = 0.0065;
            constexpr double kP0 = 101325.0;
            constexpr double kGamma = 1.4;
            constexpr double kT11 = 216.65;
            constexpr double kP11 = 22632.1;

            const double h = std::max(0.0, transform.z);
            double pressure = kP0;
            if (h < 11000.0) {
                oat_temperature_k = kPropulsionSeaLevelTemperatureK - (kL * h);
                pressure = kP0 * std::pow(
                    1.0 - (kL * h / kPropulsionSeaLevelTemperatureK),
                    kG / (kR * kL)
                );
            } else {
                oat_temperature_k = kT11;
                pressure = kP11 * std::exp(-kG * (h - 11000.0) / (kR * kT11));
            }
            const double rho = pressure / (kR * oat_temperature_k);
            inputs.sigma = rho / kPropulsionSeaLevelDensity;
            speed_of_sound = std::sqrt(kGamma * kR * oat_temperature_k);
        }

        inputs.theta = oat_temperature_k / kPropulsionSeaLevelTemperatureK;
        if (aero_state && std::isfinite(aero_state->mach_number)) {
            inputs.mach = std::max(0.0, aero_state->mach_number);
            return inputs;
        }

        const double speed = std::sqrt(
            (velocity.vx * velocity.vx) +
            (velocity.vy * velocity.vy) +
            (velocity.vz * velocity.vz)
        );
        if (speed_of_sound > 1.0) {
            inputs.mach = speed / speed_of_sound;
        }
        return inputs;
    }

    inline void advance_propulsion_state(
        Propulsion& propulsion,
        const EngineTuning& tuning,
        double throttle_command,
        double dt,
        const PropulsionAtmosphereInputs& atmosphere
    ) {
        throttle_command = std::clamp(throttle_command, 0.0, 1.0);
        propulsion.throttle_command = throttle_command;

        const double throttle_target =
            (throttle_command <= tuning.throttle_ab_threshold)
                ? throttle_command
                : tuning.throttle_ab_threshold;
        const double spool_tau = (throttle_target >= propulsion.throttle_state)
            ? tuning.tau_spool_up_s
            : tuning.tau_spool_down_s;
        propulsion.throttle_state = first_order_step(
            propulsion.throttle_state,
            throttle_target,
            dt,
            spool_tau
        );
        propulsion.throttle_state = std::clamp(propulsion.throttle_state, 0.0, 1.0);

        const double dry_span = std::max(0.0, 1.0 - tuning.throttle_idle_bias);
        double dry_throttle = 0.0;
        if (dry_span > 1.0e-6) {
            dry_throttle = (propulsion.throttle_state - tuning.throttle_idle_bias) / dry_span;
        }
        dry_throttle = std::clamp(dry_throttle, 0.0, 1.0);

        propulsion.dry_thrust_command_n = tuning.mil_thrust_n * dry_throttle;
        propulsion.dry_thrust_state_n = first_order_step(
            propulsion.dry_thrust_state_n,
            propulsion.dry_thrust_command_n,
            dt,
            spool_tau
        );
        propulsion.dry_thrust_state_n = std::clamp(
            propulsion.dry_thrust_state_n,
            0.0,
            std::max(tuning.mil_thrust_n, propulsion.dry_thrust_command_n)
        );

        propulsion.ab_command = 0.0;
        if (throttle_command > tuning.throttle_ab_threshold) {
            const double ab_span = std::max(1.0e-6, 1.0 - tuning.throttle_ab_threshold);
            propulsion.ab_command = (throttle_command - tuning.throttle_ab_threshold) / ab_span;
        }
        propulsion.ab_command = std::clamp(propulsion.ab_command, 0.0, 1.0);

        const double ab_tau = (propulsion.ab_command >= propulsion.ab_state)
            ? tuning.tau_ab_light_s
            : tuning.tau_ab_extinguish_s;
        propulsion.ab_state = first_order_step(propulsion.ab_state, propulsion.ab_command, dt, ab_tau);
        propulsion.ab_state = std::clamp(propulsion.ab_state, 0.0, 1.0);

        const double ab_extra_thrust_n =
            std::max(0.0, tuning.ab_thrust_n - tuning.mil_thrust_n) * propulsion.ab_state;

        const double sigma = std::max(0.01, atmosphere.sigma);
        const double theta = std::max(0.30, atmosphere.theta);
        const double sigma_factor = std::pow(sigma, tuning.thrust_sigma_exponent);
        const double theta_factor = std::pow(theta, tuning.thrust_theta_exponent);
        const double ram_factor = propulsion_ram_factor(tuning, atmosphere.mach);
        const double installed_factor = sigma_factor * theta_factor * ram_factor;

        propulsion.current_thrust_n =
            (propulsion.dry_thrust_state_n + ab_extra_thrust_n) * installed_factor;
        propulsion.current_thrust_n = canonicalize_propulsion_force_scalar(
            std::max(0.0, propulsion.current_thrust_n)
        );
        propulsion.afterburner_active = propulsion.ab_state >= 0.15;
        propulsion.current_tsfc = propulsion.afterburner_active
            ? tuning.tsfc_ab_kg_per_nh
            : tuning.tsfc_mil_kg_per_nh;
    }

    inline double propulsion_fuel_flow_kg_per_s(
        const Propulsion& propulsion,
        double mil_power_flow_rate = 0.0,
        double ab_flow_rate_multiplier = 1.0
    ) {
        const double thrust_n = std::max(0.0, propulsion.current_thrust_n);
        const double tsfc_nh = std::max(0.0, propulsion.current_tsfc);
        if (thrust_n > 0.0 && tsfc_nh > 0.0) {
            return (thrust_n * tsfc_nh) / 3600.0;
        }
        if (mil_power_flow_rate <= 0.0) {
            return 0.0;
        }
        const double throttle_state = std::clamp(
            std::max(propulsion.throttle_state, propulsion.throttle_command),
            0.0,
            1.0
        );
        const double ab_state = std::clamp(propulsion.ab_state, 0.0, 1.0);
        const double dry_flow_rate =
            mil_power_flow_rate * (0.1 + (0.9 * throttle_state));
        const double ab_multiplier = std::max(1.0, ab_flow_rate_multiplier);
        return dry_flow_rate * (1.0 + ((ab_multiplier - 1.0) * ab_state));
    }

    inline double propulsion_engine_rpm_pct(const Propulsion& propulsion) {
        const double throttle_state = std::clamp(propulsion.throttle_state, 0.0, 1.0);
        const double ab_state = std::clamp(propulsion.ab_state, 0.0, 1.0);
        return (throttle_state * 100.0) + (ab_state * 10.0);
    }

    inline void register_propulsion_system(flecs::world& ecs) {
        ecs.system<Propulsion, const Transform, const Velocity, const FlightModel, const AeroState>(
            "ComputePropulsion"
        )
            .kind(flecs::OnUpdate)
            .run([](flecs::iter& it) {
                const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();
                double dt = it.delta_time();
                if (dt <= 0.0) {
                    dt = 0.05;
                }

                while (it.next()) {
                    auto propulsion = it.field<Propulsion>(0);
                    auto transform = it.field<const Transform>(1);
                    auto velocity = it.field<const Velocity>(2);
                    auto aero = it.field<const AeroState>(4);

                    for (auto i : it) {
                        const flecs::entity entity = it.entity(i);
                        const ResolvedAirControlInput control_input = resolve_air_control_input(
                            entity.get<PilotAction>(),
                            entity.get<MissionCommandControlState>(),
                            nullptr,
                            nullptr,
                            0.0
                        );
                        const double throttle_command = control_input.throttle_command;
                        const EngineTuning runtime_tuning = resolve_propulsion_runtime_tuning(
                            propulsion[i],
                            entity.get<EngineTuning>()
                        );
                        const PropulsionAtmosphereInputs atmosphere =
                            resolve_propulsion_atmosphere_inputs(
                                transform[i],
                                velocity[i],
                                &aero[i],
                                env_ref
                            );
                        advance_propulsion_state(
                            propulsion[i],
                            runtime_tuning,
                            throttle_command,
                            dt,
                            atmosphere
                        );
                    }
                }
            });
    }
}
