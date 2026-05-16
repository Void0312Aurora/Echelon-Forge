#pragma once

#include <algorithm>
#include <cmath>

#include "components/physics/dynamics.h"
#include "components/physics/flight_dynamics_tuning.h"

namespace flight_dynamics {
    struct PropulsionAtmosphereInputs {
        double sigma = 1.0;
        double theta = 1.0;
        double mach = 0.0;
    };

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
        propulsion.current_thrust_n = std::max(0.0, propulsion.current_thrust_n);
        propulsion.afterburner_active = propulsion.ab_state >= 0.15;
        propulsion.current_tsfc = propulsion.afterburner_active
            ? tuning.tsfc_ab_kg_per_nh
            : tuning.tsfc_mil_kg_per_nh;
    }
}
