#pragma once

#include <cmath>

namespace physics_runtime {

// The zero/invalid-dt value is an intentional pause/initialization compatibility
// default. Mass and reference area have no such aircraft-sized substitute.
inline constexpr double kIntegratorFallbackDtS = 0.05;
inline constexpr double kIntegratorFallbackMassKg = 15000.0;

[[nodiscard]] inline bool valid_mass(double value) noexcept {
    return std::isfinite(value) && value > 0.0;
}

[[nodiscard]] inline bool valid_reference_area(double value) noexcept {
    return std::isfinite(value) && value > 0.0;
}

[[nodiscard]] inline double resolve_integrator_dt(double value) noexcept {
    return std::isfinite(value) && value > 0.0 ? value : kIntegratorFallbackDtS;
}

} // namespace physics_runtime
