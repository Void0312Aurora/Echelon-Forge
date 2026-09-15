#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

#include "models/weapons/missile_guidance_math.h"

namespace missile_guidance {

inline bool finite_world_cva_vector(const Vec3 &value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

inline Vec3 suppress_world_cva_acceleration_roundoff(const Vec3 &value) {
    constexpr double kRoundoffFloorMps2 = 1.0e-10;
    return {std::abs(value.x) < kRoundoffFloorMps2 ? 0.0 : value.x,
            std::abs(value.y) < kRoundoffFloorMps2 ? 0.0 : value.y,
            std::abs(value.z) < kRoundoffFloorMps2 ? 0.0 : value.z};
}

// World-frame constant-acceleration tracker used only when the guidance
// estimator explicitly opts into maneuver observability. The CV tracker below
// intentionally publishes zero acceleration and remains unchanged.
struct WorldCvaAlphaBetaGammaTrackerState {
    static constexpr std::size_t kMeasurementHistoryCapacity = 100;
    bool position_valid = false;
    bool velocity_valid = false;
    bool acceleration_valid = false;
    std::uint32_t accepted_measurement_count = 0;
    Vec3 corrected_position_world_m{};
    Vec3 corrected_velocity_world_mps{};
    Vec3 corrected_acceleration_world_mps2{};
    Vec3 last_measurement_position_world_m{};
    Vec3 first_measurement_position_world_m{};
    std::array<Vec3, kMeasurementHistoryCapacity> measurement_history_positions{};
    std::array<double, kMeasurementHistoryCapacity> measurement_history_times{};
    std::size_t measurement_history_count = 0;
    std::size_t measurement_history_next = 0;
    Vec3 last_prediction_position_world_m{};
    Vec3 last_residual_world_m{};
    double correction_time_s = 0.0;
    double first_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_update_dt_s = 0.0;
};

struct WorldCvaAlphaBetaGammaTrackerParams {
    double alpha = 0.20;
    double beta = 0.02;
    double gamma = 0.5;
    double minimum_velocity_baseline_s = 0.5;
    double minimum_acceleration_baseline_s = 0.5;
};

inline void append_world_cva_measurement(WorldCvaAlphaBetaGammaTrackerState &state,
                                         const Vec3 &position_world_m, double time_s) {
    const std::size_t index = state.measurement_history_next;
    state.measurement_history_positions[index] = position_world_m;
    state.measurement_history_times[index] = time_s;
    state.measurement_history_next =
        (index + 1) % WorldCvaAlphaBetaGammaTrackerState::kMeasurementHistoryCapacity;
    state.measurement_history_count = std::min(
        state.measurement_history_count + 1,
        WorldCvaAlphaBetaGammaTrackerState::kMeasurementHistoryCapacity);
}

inline bool estimate_world_cva_acceleration_from_history(
    const WorldCvaAlphaBetaGammaTrackerState &state, Vec3 *out_acceleration_world_mps2) {
    if (!out_acceleration_world_mps2 || state.measurement_history_count < 3) {
        return false;
    }

    const double reference_time_s = state.last_measurement_time_s;
    std::array<std::array<double, 3>, 3> normal{};
    std::array<double, 3> rhs_x{};
    std::array<double, 3> rhs_y{};
    std::array<double, 3> rhs_z{};
    for (std::size_t sample = 0; sample < state.measurement_history_count; ++sample) {
        const std::size_t index =
            (state.measurement_history_next +
             WorldCvaAlphaBetaGammaTrackerState::kMeasurementHistoryCapacity -
             state.measurement_history_count + sample) %
            WorldCvaAlphaBetaGammaTrackerState::kMeasurementHistoryCapacity;
        const double tau_s = state.measurement_history_times[index] - reference_time_s;
        const std::array<double, 3> basis{1.0, tau_s, tau_s * tau_s};
        const Vec3 &position = state.measurement_history_positions[index];
        for (std::size_t row = 0; row < 3; ++row) {
            for (std::size_t column = 0; column < 3; ++column) {
                normal[row][column] += basis[row] * basis[column];
            }
            rhs_x[row] += basis[row] * position.x;
            rhs_y[row] += basis[row] * position.y;
            rhs_z[row] += basis[row] * position.z;
        }
    }

    auto solve = [](std::array<std::array<double, 3>, 3> matrix,
                    std::array<double, 3> rhs, std::array<double, 3> *solution) {
        if (!solution) return false;
        for (std::size_t pivot = 0; pivot < 3; ++pivot) {
            std::size_t best = pivot;
            for (std::size_t row = pivot + 1; row < 3; ++row) {
                if (std::abs(matrix[row][pivot]) > std::abs(matrix[best][pivot])) best = row;
            }
            if (std::abs(matrix[best][pivot]) <= 1.0e-12) return false;
            if (best != pivot) {
                std::swap(matrix[best], matrix[pivot]);
                std::swap(rhs[best], rhs[pivot]);
            }
            const double diagonal = matrix[pivot][pivot];
            for (std::size_t column = pivot; column < 3; ++column)
                matrix[pivot][column] /= diagonal;
            rhs[pivot] /= diagonal;
            for (std::size_t row = 0; row < 3; ++row) {
                if (row == pivot) continue;
                const double factor = matrix[row][pivot];
                for (std::size_t column = pivot; column < 3; ++column)
                    matrix[row][column] -= factor * matrix[pivot][column];
                rhs[row] -= factor * rhs[pivot];
            }
        }
        *solution = rhs;
        return true;
    };

    std::array<double, 3> solution_x{};
    std::array<double, 3> solution_y{};
    std::array<double, 3> solution_z{};
    if (!solve(normal, rhs_x, &solution_x) || !solve(normal, rhs_y, &solution_y) ||
        !solve(normal, rhs_z, &solution_z)) {
        return false;
    }
    *out_acceleration_world_mps2 = suppress_world_cva_acceleration_roundoff(
        {2.0 * solution_x[2], 2.0 * solution_y[2], 2.0 * solution_z[2]});
    return finite_world_cva_vector(*out_acceleration_world_mps2);
}

struct WorldCvaAlphaBetaGammaTrackerInput {
    double current_time_s = 0.0;
    bool has_measurement = false;
    Vec3 measurement_position_world_m{};
    double measurement_time_s = 0.0;
};

struct WorldCvaAlphaBetaGammaTrackerOutput {
    bool position_valid = false;
    bool velocity_valid = false;
    bool acceleration_valid = false;
    bool measurement_accepted = false;
    bool measurement_rejected_nonmonotonic = false;
    bool measurement_rejected_invalid = false;
    bool coasted = false;
    Vec3 position_world_m{};
    Vec3 velocity_world_mps{};
    Vec3 acceleration_world_mps2{};
    Vec3 measurement_position_world_m{};
    Vec3 prediction_position_world_m{};
    Vec3 residual_world_m{};
    double state_time_s = 0.0;
    double last_measurement_time_s = -std::numeric_limits<double>::infinity();
    double update_dt_s = 0.0;
    std::uint32_t accepted_measurement_count = 0;
};

inline WorldCvaAlphaBetaGammaTrackerOutput propagate_world_cva_alpha_beta_gamma_tracker(
    const WorldCvaAlphaBetaGammaTrackerState &state, double current_time_s) {
    WorldCvaAlphaBetaGammaTrackerOutput output;
    output.position_valid = state.position_valid;
    output.velocity_valid = state.velocity_valid;
    output.acceleration_valid = state.acceleration_valid;
    output.last_measurement_time_s = state.last_measurement_time_s;
    output.measurement_position_world_m = state.last_measurement_position_world_m;
    output.prediction_position_world_m = state.last_prediction_position_world_m;
    output.residual_world_m = state.last_residual_world_m;
    output.update_dt_s = state.last_update_dt_s;
    output.accepted_measurement_count = state.accepted_measurement_count;
    if (!state.position_valid) {
        output.state_time_s = std::isfinite(current_time_s) ? current_time_s : 0.0;
        return output;
    }
    const double requested_time_s = std::isfinite(current_time_s) ? current_time_s
                                                                   : state.correction_time_s;
    output.state_time_s = std::max(requested_time_s, state.correction_time_s);
    const double dt = output.state_time_s - state.correction_time_s;
    output.position_world_m = state.corrected_position_world_m +
                              state.corrected_velocity_world_mps * dt +
                              state.corrected_acceleration_world_mps2 * (0.5 * dt * dt);
    output.velocity_world_mps = state.corrected_velocity_world_mps +
                                state.corrected_acceleration_world_mps2 * dt;
    output.acceleration_world_mps2 = state.corrected_acceleration_world_mps2;
    output.coasted = dt > 0.0;
    return output;
}

inline WorldCvaAlphaBetaGammaTrackerOutput update_world_cva_alpha_beta_gamma_tracker(
    WorldCvaAlphaBetaGammaTrackerState &state,
    const WorldCvaAlphaBetaGammaTrackerParams &params,
    const WorldCvaAlphaBetaGammaTrackerInput &input) {
    bool accepted = false;
    bool rejected_nonmonotonic = false;
    bool rejected_invalid = false;
    if (input.has_measurement) {
        const bool valid = std::isfinite(input.measurement_time_s) &&
                           finite_world_cva_vector(input.measurement_position_world_m);
        if (!valid) {
            rejected_invalid = true;
        } else if (state.position_valid &&
                   input.measurement_time_s <= state.last_measurement_time_s) {
            rejected_nonmonotonic = true;
        } else if (!state.position_valid) {
            state.position_valid = true;
            state.corrected_position_world_m = input.measurement_position_world_m;
            state.last_measurement_position_world_m = input.measurement_position_world_m;
            state.first_measurement_position_world_m = input.measurement_position_world_m;
            state.last_prediction_position_world_m = input.measurement_position_world_m;
            state.last_residual_world_m = {};
            state.correction_time_s = input.measurement_time_s;
            state.first_measurement_time_s = input.measurement_time_s;
            state.last_measurement_time_s = input.measurement_time_s;
            state.last_update_dt_s = 0.0;
            state.accepted_measurement_count = 1;
            append_world_cva_measurement(state, input.measurement_position_world_m,
                                         input.measurement_time_s);
            accepted = true;
        } else {
            const double dt = input.measurement_time_s - state.last_measurement_time_s;
            const double baseline = input.measurement_time_s - state.first_measurement_time_s;
            const Vec3 predicted = state.corrected_position_world_m +
                                   state.corrected_velocity_world_mps * dt +
                                   state.corrected_acceleration_world_mps2 * (0.5 * dt * dt);
            const Vec3 residual = input.measurement_position_world_m - predicted;
            state.last_prediction_position_world_m = predicted;
            state.last_residual_world_m = residual;
            if (!state.velocity_valid) {
                // Bootstrap over a widening baseline, matching the CV tracker's
                // noise-resistant admission rule. Acceleration is not published
                // until a later correction has a valid velocity state.
                state.corrected_velocity_world_mps =
                    (input.measurement_position_world_m - state.first_measurement_position_world_m) /
                    baseline;
                state.corrected_position_world_m = input.measurement_position_world_m;
                state.velocity_valid = state.accepted_measurement_count >= 2 &&
                                       baseline >= std::max(0.0, params.minimum_velocity_baseline_s);
            } else {
                const double alpha = std::clamp(params.alpha, 0.0, 1.0);
                const double beta = std::clamp(params.beta, 0.0, 2.0);
                const Vec3 predicted_velocity = state.corrected_velocity_world_mps +
                                                state.corrected_acceleration_world_mps2 * dt;
                state.corrected_position_world_m = predicted + residual * alpha;
                state.corrected_velocity_world_mps =
                    predicted_velocity + residual * (beta / dt);
            }
            state.last_measurement_position_world_m = input.measurement_position_world_m;
            state.correction_time_s = input.measurement_time_s;
            state.last_measurement_time_s = input.measurement_time_s;
            state.last_update_dt_s = dt;
            ++state.accepted_measurement_count;
            append_world_cva_measurement(state, input.measurement_position_world_m,
                                         input.measurement_time_s);
            if (baseline >= std::max(0.0, params.minimum_acceleration_baseline_s)) {
                Vec3 historical_acceleration{};
                if (estimate_world_cva_acceleration_from_history(state, &historical_acceleration)) {
                    const double gamma = std::clamp(params.gamma, 0.0, 1.0);
                    state.corrected_acceleration_world_mps2 =
                        state.corrected_acceleration_world_mps2 * (1.0 - gamma) +
                        historical_acceleration * gamma;
                    state.acceleration_valid = true;
                }
            }
            accepted = true;
        }
    }
    auto output = propagate_world_cva_alpha_beta_gamma_tracker(state, input.current_time_s);
    output.measurement_accepted = accepted;
    output.measurement_rejected_nonmonotonic = rejected_nonmonotonic;
    output.measurement_rejected_invalid = rejected_invalid;
    return output;
}

// A world-frame constant-velocity tracker. The state is anchored at the most
// recent accepted measurement timestamp; propagation to the caller's current
// time is returned as an output and does not consume a measurement epoch.
struct WorldCvAlphaBetaTrackerState {
    bool position_valid = false;
    bool velocity_valid = false;
    std::uint32_t accepted_measurement_count = 0;

    Vec3 corrected_position_world_m{};
    Vec3 corrected_velocity_world_mps{};
    Vec3 last_measurement_position_world_m{};
    Vec3 first_measurement_position_world_m{};
    Vec3 last_prediction_position_world_m{};
    Vec3 last_residual_world_m{};

    double correction_time_s = 0.0;
    double first_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_measurement_time_s = -std::numeric_limits<double>::infinity();
    double last_update_dt_s = 0.0;
};

struct WorldCvAlphaBetaTrackerParams {
    double alpha = 0.20;
    double beta = 0.02;
    double minimum_velocity_baseline_s = 0.5;
};

struct WorldCvAlphaBetaTrackerInput {
    double current_time_s = 0.0;
    bool has_measurement = false;
    Vec3 measurement_position_world_m{};
    double measurement_time_s = 0.0;
};

struct WorldCvAlphaBetaTrackerOutput {
    bool position_valid = false;
    bool velocity_valid = false;
    bool measurement_accepted = false;
    bool measurement_rejected_nonmonotonic = false;
    bool measurement_rejected_invalid = false;
    bool coasted = false;

    Vec3 position_world_m{};
    Vec3 velocity_world_mps{};
    Vec3 acceleration_world_mps2{};
    Vec3 measurement_position_world_m{};
    Vec3 prediction_position_world_m{};
    Vec3 residual_world_m{};

    double state_time_s = 0.0;
    double last_measurement_time_s = -std::numeric_limits<double>::infinity();
    double update_dt_s = 0.0;
    std::uint32_t accepted_measurement_count = 0;
};

inline bool finite_world_cv_vector(const Vec3 &value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

inline WorldCvAlphaBetaTrackerOutput
propagate_world_cv_alpha_beta_tracker(const WorldCvAlphaBetaTrackerState &state,
                                      double current_time_s) {
    WorldCvAlphaBetaTrackerOutput output;
    output.position_valid = state.position_valid;
    output.velocity_valid = state.velocity_valid;
    output.last_measurement_time_s = state.last_measurement_time_s;
    output.measurement_position_world_m = state.last_measurement_position_world_m;
    output.prediction_position_world_m = state.last_prediction_position_world_m;
    output.residual_world_m = state.last_residual_world_m;
    output.update_dt_s = state.last_update_dt_s;
    output.accepted_measurement_count = state.accepted_measurement_count;
    output.acceleration_world_mps2 = {0.0, 0.0, 0.0};

    if (!state.position_valid) {
        output.state_time_s = std::isfinite(current_time_s) ? current_time_s : 0.0;
        return output;
    }

    const double requested_time_s =
        std::isfinite(current_time_s) ? current_time_s : state.correction_time_s;
    output.state_time_s = std::max(requested_time_s, state.correction_time_s);
    const double coast_dt_s = output.state_time_s - state.correction_time_s;
    output.position_world_m =
        state.corrected_position_world_m + state.corrected_velocity_world_mps * coast_dt_s;
    output.velocity_world_mps = state.corrected_velocity_world_mps;
    output.coasted = coast_dt_s > 0.0;
    return output;
}

inline WorldCvAlphaBetaTrackerOutput
update_world_cv_alpha_beta_tracker(WorldCvAlphaBetaTrackerState &state,
                                   const WorldCvAlphaBetaTrackerParams &params,
                                   const WorldCvAlphaBetaTrackerInput &input) {
    bool measurement_accepted = false;
    bool measurement_rejected_nonmonotonic = false;
    bool measurement_rejected_invalid = false;

    if (input.has_measurement) {
        const bool measurement_valid = std::isfinite(input.measurement_time_s) &&
                                       finite_world_cv_vector(input.measurement_position_world_m);
        if (!measurement_valid) {
            measurement_rejected_invalid = true;
        } else if (state.position_valid &&
                   input.measurement_time_s <= state.last_measurement_time_s) {
            // Correction is tied strictly to a new measurement epoch. Repeated
            // and out-of-order sensor frames must not create false kinematics.
            measurement_rejected_nonmonotonic = true;
        } else if (!state.position_valid) {
            state.position_valid = true;
            state.velocity_valid = false;
            state.accepted_measurement_count = 1;
            state.corrected_position_world_m = input.measurement_position_world_m;
            state.corrected_velocity_world_mps = {0.0, 0.0, 0.0};
            state.last_measurement_position_world_m = input.measurement_position_world_m;
            state.first_measurement_position_world_m = input.measurement_position_world_m;
            state.last_prediction_position_world_m = input.measurement_position_world_m;
            state.last_residual_world_m = {0.0, 0.0, 0.0};
            state.correction_time_s = input.measurement_time_s;
            state.first_measurement_time_s = input.measurement_time_s;
            state.last_measurement_time_s = input.measurement_time_s;
            state.last_update_dt_s = 0.0;
            measurement_accepted = true;
        } else {
            const double measurement_dt_s =
                input.measurement_time_s - state.last_measurement_time_s;
            if (!state.velocity_valid) {
                // Bootstrap across a widening baseline so short-cadence angular
                // noise is not published as a several-hundred-m/s velocity.
                const double baseline_dt_s =
                    input.measurement_time_s - state.first_measurement_time_s;
                state.corrected_velocity_world_mps =
                    (input.measurement_position_world_m -
                     state.first_measurement_position_world_m) /
                    baseline_dt_s;
                state.last_prediction_position_world_m = state.corrected_position_world_m;
                state.last_residual_world_m =
                    input.measurement_position_world_m - state.corrected_position_world_m;
                state.corrected_position_world_m = input.measurement_position_world_m;
                ++state.accepted_measurement_count;
                state.velocity_valid =
                    state.accepted_measurement_count >= 3 &&
                    baseline_dt_s >= std::max(0.0, params.minimum_velocity_baseline_s);
            } else {
                const Vec3 predicted_position_world_m =
                    state.corrected_position_world_m +
                    state.corrected_velocity_world_mps * measurement_dt_s;
                const Vec3 residual_world_m =
                    input.measurement_position_world_m - predicted_position_world_m;
                state.last_prediction_position_world_m = predicted_position_world_m;
                state.last_residual_world_m = residual_world_m;
                const double alpha = std::clamp(params.alpha, 0.0, 1.0);
                const double beta = std::clamp(params.beta, 0.0, 2.0);

                state.corrected_position_world_m =
                    predicted_position_world_m + residual_world_m * alpha;
                state.corrected_velocity_world_mps = state.corrected_velocity_world_mps +
                                                     residual_world_m * (beta / measurement_dt_s);
                ++state.accepted_measurement_count;
                state.velocity_valid = true;
            }

            state.last_measurement_position_world_m = input.measurement_position_world_m;
            state.correction_time_s = input.measurement_time_s;
            state.last_measurement_time_s = input.measurement_time_s;
            state.last_update_dt_s = measurement_dt_s;
            measurement_accepted = true;
        }
    }

    WorldCvAlphaBetaTrackerOutput output =
        propagate_world_cv_alpha_beta_tracker(state, input.current_time_s);
    output.measurement_accepted = measurement_accepted;
    output.measurement_rejected_nonmonotonic = measurement_rejected_nonmonotonic;
    output.measurement_rejected_invalid = measurement_rejected_invalid;
    return output;
}

} // namespace missile_guidance
