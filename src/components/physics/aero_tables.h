#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <optional>
#include <vector>

namespace aero_physics {

struct LookupTableValidation {
    bool require_two_points = false;
    bool require_finite_x = false;
    bool require_finite_breakpoints = false;
    bool require_finite_values = false;
    bool require_positive_values = false;
    bool require_strictly_increasing = false;
};

inline double clamp01(double value) {
    return std::clamp(value, 0.0, 1.0);
}

inline double lerp(double a, double b, double t) {
    return a + (b - a) * clamp01(t);
}

inline double smoothstep01(double x) {
    x = clamp01(x);
    return x * x * (3.0 - 2.0 * x);
}

inline LookupTableValidation positive_strict_lookup_validation() {
    LookupTableValidation validation;
    validation.require_two_points = true;
    validation.require_finite_x = true;
    validation.require_finite_breakpoints = true;
    validation.require_finite_values = true;
    validation.require_positive_values = true;
    validation.require_strictly_increasing = true;
    return validation;
}

inline bool lookup_table_valid(const std::vector<double> &breakpoints,
                               const std::vector<double> &values, double x,
                               const LookupTableValidation &validation = {}) {
    if (breakpoints.empty() || values.empty() || breakpoints.size() != values.size()) {
        return false;
    }
    if (validation.require_two_points && breakpoints.size() < 2) {
        return false;
    }
    if (validation.require_finite_x && !std::isfinite(x)) {
        return false;
    }
    for (std::size_t i = 0; i < breakpoints.size(); ++i) {
        if (validation.require_finite_breakpoints && !std::isfinite(breakpoints[i])) {
            return false;
        }
        if (validation.require_finite_values && !std::isfinite(values[i])) {
            return false;
        }
        if (validation.require_positive_values && values[i] <= 0.0) {
            return false;
        }
        if (validation.require_strictly_increasing && i > 0 &&
            breakpoints[i] <= breakpoints[i - 1]) {
            return false;
        }
    }
    return true;
}

inline std::optional<double> lookup_1d_optional(const std::vector<double> &breakpoints,
                                                const std::vector<double> &values, double x,
                                                const LookupTableValidation &validation = {}) {
    if (!lookup_table_valid(breakpoints, values, x, validation)) {
        return std::nullopt;
    }
    if (x <= breakpoints.front()) {
        return values.front();
    }
    if (x >= breakpoints.back()) {
        return values.back();
    }
    for (std::size_t i = 1; i < breakpoints.size(); ++i) {
        if (x <= breakpoints[i]) {
            const double span = std::max(1.0e-6, breakpoints[i] - breakpoints[i - 1]);
            const double frac = std::clamp((x - breakpoints[i - 1]) / span, 0.0, 1.0);
            return lerp(values[i - 1], values[i], frac);
        }
    }
    return values.back();
}

inline double lookup_1d_or(const std::vector<double> &breakpoints,
                           const std::vector<double> &values, double x, double fallback,
                           const LookupTableValidation &validation = {}) {
    return lookup_1d_optional(breakpoints, values, x, validation).value_or(fallback);
}

} // namespace aero_physics
