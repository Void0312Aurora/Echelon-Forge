#include "simulation_kernel_state_owner_adapters.h"

#include "core/engine/state_transfer_component_reflection.h"

#include "components/basic/tags.h"
#include "components/command/common/comm_message.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/air/combat/damage_air.h"
#include "core/engine/simulation_kernel.h"
#include "core/interfaces/unit_factory.h"
#include "runtime/contracts/backend_profile_contracts.h"

#include <flecs/addons/json.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cctype>
#include <cmath>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <utility>
#include <vector>

namespace runtime::host::integration {

namespace {

// These X-macro field tables use deliberate continuation alignment. Keep the
// generated member lists stable instead of letting clang-format rewrite them.
// clang-format off
#define EF_P4B_MISSILE_DOUBLE_FIELDS(X)                                                                                                    \
    X(max_speed)                                                                                                                           \
    X(turn_rate) X(fuse_distance) X(damage) X(seeker_fov_deg) X(seeker_lock_range) X(guidance_delay_s) X(                                  \
        guidance_update_period_s) X(last_guidance_time) X(launch_time) X(max_flight_time_s)                                                \
        X(nav_gain) X(proximity_min_dist_m) X(proximity_min_time_s) X(proximity_last_dist_m) X(                                            \
            proximity_min_local_forward_m) X(proximity_min_local_right_m) X(proximity_min_local_up_m)                                      \
            X(proximity_last_sample_time_s) X(proximity_last_missile_x_m) X(proximity_last_missile_y_m) X(                                 \
                proximity_last_missile_z_m) X(proximity_last_target_x_m) X(proximity_last_target_y_m)                                      \
                X(proximity_last_target_z_m) X(fuze_nearest_approach_time_s) X(fuze_detonation_time_s) X(                                  \
                    fuze_detonation_x) X(fuze_detonation_y) X(fuze_detonation_z) X(fuze_detonation_heading_deg)                            \
                    X(fuze_detonation_pitch_deg) X(fuze_detonation_roll_deg) X(fuze_quality) X(                                            \
                        fuze_hit_probability) X(fuze_closure_mps) X(fuze_missile_axis_forward) X(fuze_missile_axis_right)                  \
                        X(fuze_missile_axis_up) X(fuze_target_signature) X(fuze_signature_scale) X(                                        \
                            fuze_effective_reliability) X(fuze_contact_surface_distance_m) X(fuze_contact_penetration_depth_m)             \
                            X(fuze_contact_surface_tolerance_m) X(fuze_sensor_opportunity_score) X(                                        \
                                fuze_target_detection_confidence) X(fuze_target_detection_threshold) X(fuze_mechanism_coverage_score)      \
                                X(filtered_bearing_deg) X(filtered_elevation_deg) X(filtered_range_m) X(                                   \
                                    filtered_closing_speed_mps) X(bearing_rate_deg_s) X(elevation_rate_deg_s)                              \
                                    X(last_track_time_s) X(track_memory_timeout_s) X(current_speed_mps) X(                                 \
                                        commanded_lateral_accel_mps2) X(commanded_lateral_accel_x_mps2)                                    \
                                        X(commanded_lateral_accel_y_mps2) X(commanded_lateral_accel_z_mps2) X(                             \
                                            achieved_lateral_accel_mps2) X(burnout_time_s) X(boost_duration_s)                             \
                                            X(sustain_duration_s) X(guidance_bearing_filter_tau_s) X(                                      \
                                                guidance_elevation_filter_tau_s) X(guidance_range_filter_tau_s) X(guidance_boost_thrust_n) \
                                                X(guidance_sustain_thrust_n) X(guidance_cd0_subsonic) X(                                   \
                                                    guidance_cd0_supersonic) X(guidance_induced_drag_k)                                    \
                                                    X(guidance_max_lateral_g) X(guidance_autopilot_tau_s) X(                               \
                                                        guidance_max_accel_response_g_per_s) X(apn_target_accel_gain)                      \
                                                        X(prev_bearing_rate_deg_s) X(                                                      \
                                                            prev_elevation_rate_deg_s) X(filtered_bearing_accel_rad_s2)                    \
                                                            X(filtered_elevation_accel_rad_s2) X(                                          \
                                                                target_kinematics_time_s) X(target_track_x_m)                              \
                                                                X(                                                                         \
                                                                    target_track_y_m) X(target_track_z_m)                                  \
                                                                    X(target_track_vx_mps) X(                                              \
                                                                        target_track_vy_mps)                                               \
                                                                        X(target_track_vz_mps) X(                                          \
                                                                            target_track_ax_mps2) X(target_track_ay_mps2)                  \
                                                                            X(                                                             \
                                                                                target_track_az_mps2) X(guidance_lead_time_s)              \
                                                                                X(guidance_lead_blend) X(                                  \
                                                                                    guidance_apn_lateral_accel_mps2)                       \
                                                                                    X(autopilot_filter_state_mps2) X(                      \
                                                                                        autopilot_rate_state_mps3)                         \
                                                                                        X(autopilot_actuator_state_mps2)                   \
                                                                                            X(autopilot_damping) X(                        \
                                                                                                guidance_mach_transonic_start)             \
                                                                                                X(guidance_mach_transonic_end)             \
                                                                                                    X(guidance_cd0_power_on_ratio)         \
                                                                                                        X(seeker_activation_range_m)

#define EF_P4B_MISSILE_BOOL_FIELDS(X)                                                              \
    X(active)                                                                                      \
    X(shared_launch_initialized) X(proximity_engaged) X(fuze_delay_armed)                          \
        X(fuze_contact_inside_hitbox) X(fuze_terminal_track_valid) X(fuze_target_detected)         \
            X(runtime_initialized) X(seeker_has_valid_track) X(seeker_has_range)                   \
                X(apn_rate_history_valid) X(target_kinematics_valid) X(use_kalman_seeker)          \
                    X(midcourse_datalink_supported) X(terminal_seeker_active)

#define EF_P4B_MISSILE_STRING_FIELDS(X)                                                            \
    X(fuze_signature_source)                                                                       \
    X(fuze_sensor_opportunity_source) X(fuze_target_detection_source)                              \
        X(fuze_detonation_point_source)

#define EF_P4B_MISSILE_VECTOR_FIELDS(X)                                                            \
    X(guidance_cd0_mach_breakpoints)                                                               \
    X(guidance_cd0_mach_values) X(guidance_induced_drag_k_mach_breakpoints)                        \
        X(guidance_induced_drag_k_mach_values)

#define EF_P4B_VULNERABILITY_ROW_STRING_FIELDS(X)                                                  \
    X(row_id)                                                                                      \
    X(source_ref) X(provenance) X(weapon_family) X(aspect_bucket) X(closure_bucket)                \
        X(miss_distance_bucket) X(component_name) X(component_system)                              \
            X(component_redundancy_group_id)

#define EF_P4B_VULNERABILITY_ROW_DOUBLE_FIELDS(X)                                                  \
    X(family_scale)                                                                                \
    X(aspect_scale) X(closure_scale) X(miss_distance_scale) X(effect_scale)                        \
        X(component_failure_probability) X(min_fragment_energy_j) X(max_fragment_energy_j)         \
            X(min_fragment_areal_density_per_m2) X(max_fragment_areal_density_per_m2)              \
                X(min_penetration_margin) X(max_penetration_margin) X(min_blast_overpressure_kpa)  \
                    X(max_blast_overpressure_kpa) X(min_blast_impulse_kpa_ms)                      \
                        X(max_blast_impulse_kpa_ms) X(min_blast_scaled_distance_m_kg13)            \
                            X(max_blast_scaled_distance_m_kg13) X(min_rod_cut_margin)              \
                                X(max_rod_cut_margin) X(min_surface_incidence_cos)                 \
                                    X(max_surface_incidence_cos)

#define EF_P4B_VULNERABILITY_ROW_BOOL_FIELDS(X)                                                    \
    X(has_component_failure_probability)                                                           \
    X(has_min_fragment_energy_j) X(has_max_fragment_energy_j)                                      \
        X(has_min_fragment_areal_density_per_m2) X(has_max_fragment_areal_density_per_m2)          \
            X(has_min_penetration_margin) X(has_max_penetration_margin)                            \
                X(has_min_blast_overpressure_kpa) X(has_max_blast_overpressure_kpa)                \
                    X(has_min_blast_impulse_kpa_ms) X(has_max_blast_impulse_kpa_ms)                \
                        X(has_min_blast_scaled_distance_m_kg13)                                    \
                            X(has_max_blast_scaled_distance_m_kg13) X(has_min_rod_cut_margin)      \
                                X(has_max_rod_cut_margin) X(has_min_surface_incidence_cos)         \
                                    X(has_max_surface_incidence_cos)

#define EF_P4B_VULNERABILITY_PROFILE_STRING_FIELDS(X)                                              \
    X(provenance)                                                                                  \
    X(evidence_dataset_ref) X(calibration_status) X(evidence_schema_version)                       \
        X(evidence_source_kind) X(evidence_source_ref) X(evidence_validation_artifact_ref)         \
            X(evidence_validation_manifest_schema_version) X(evidence_validation_status)           \
                X(evidence_validation_artifact_sha256) X(evidence_validated_surrogate_model_ref)   \
                    X(evidence_validation_benchmark_ref) X(evidence_validation_metrics_ref)        \
                        X(evidence_validation_acceptance_criteria_ref)

#define EF_P4B_VULNERABILITY_PROFILE_BOOL_FIELDS(X)                                                \
    X(synthetic)                                                                                   \
    X(calibrated) X(evidence_dataset_valid) X(effect_scale_authority)                              \
        X(component_failure_probability_authority) X(pk_authority) X(deterministic_fuze_authority)

#define EF_P4B_VULNERABILITY_PROFILE_DOUBLE_FIELDS(X)                                              \
    X(blast_scale)                                                                                 \
    X(fragmentation_scale) X(continuous_rod_scale) X(hit_to_kill_scale) X(nose_aspect_scale)       \
        X(beam_aspect_scale) X(tail_aspect_scale) X(high_closure_scale) X(low_closure_scale)       \
            X(near_miss_scale) X(direct_hit_scale)
// clang-format on

std::vector<std::uint8_t> bytes(std::string value) {
    return {value.begin(), value.end()};
}

std::string text(const std::vector<std::uint8_t> &value) {
    return {reinterpret_cast<const char *>(value.data()), value.size()};
}

std::string flecs_json_value(const nlohmann::json &value) {
    if (value.is_number_float()) {
        std::array<char, 768> buffer{};
        const auto [end, error] =
            std::to_chars(buffer.data(), buffer.data() + buffer.size(), value.get<double>(),
                          std::chars_format::fixed, std::numeric_limits<double>::max_digits10);
        if (error != std::errc{}) {
            throw std::runtime_error("floating-point value cannot be formatted for Flecs restore");
        }
        std::string formatted(buffer.data(), end);
        if (const auto dot = formatted.find('.'); dot != std::string::npos) {
            while (formatted.back() == '0') {
                formatted.pop_back();
            }
            if (formatted.back() == '.') {
                formatted.push_back('0');
            }
        }
        return formatted;
    }
    if (value.is_array()) {
        std::string formatted = "[";
        bool first = true;
        for (const auto &element : value) {
            if (!first) {
                formatted.push_back(',');
            }
            first = false;
            formatted += flecs_json_value(element);
        }
        formatted.push_back(']');
        return formatted;
    }
    if (value.is_object()) {
        std::string formatted = "{";
        bool first = true;
        for (const auto &[key, element] : value.items()) {
            if (!first) {
                formatted.push_back(',');
            }
            first = false;
            formatted += nlohmann::json(key).dump();
            formatted.push_back(':');
            formatted += flecs_json_value(element);
        }
        formatted.push_back('}');
        return formatted;
    }
    return value.dump();
}

std::string f64_bits(double value) {
    constexpr char hex[] = "0123456789abcdef";
    std::uint64_t bits = std::bit_cast<std::uint64_t>(value);
    std::string encoded(16, '0');
    for (std::size_t index = 0; index < encoded.size(); ++index) {
        encoded[encoded.size() - index - 1] = hex[bits & 0xfU];
        bits >>= 4U;
    }
    return encoded;
}

bool decode_f64_bits(const nlohmann::json &encoded, double *value) {
    if (value == nullptr || !encoded.is_string()) {
        return false;
    }
    const auto &text = encoded.get_ref<const std::string &>();
    if (text.size() != 16) {
        return false;
    }
    std::uint64_t bits = 0;
    const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), bits, 16);
    if (error != std::errc{} || end != text.data() + text.size()) {
        return false;
    }
    *value = std::bit_cast<double>(bits);
    return true;
}

bool only_object_keys(const nlohmann::json &encoded,
                      std::initializer_list<std::string_view> allowed) {
    if (!encoded.is_object()) {
        return false;
    }
    const std::set<std::string_view> allowed_keys(allowed);
    for (auto iterator = encoded.begin(); iterator != encoded.end(); ++iterator) {
        if (!allowed_keys.contains(iterator.key())) {
            return false;
        }
    }
    return true;
}

nlohmann::json encode_f64_vector(const std::vector<double> &values) {
    nlohmann::json encoded = nlohmann::json::array();
    for (const double value : values) {
        encoded.push_back(f64_bits(value));
    }
    return encoded;
}

bool decode_f64_vector(const nlohmann::json &encoded, std::vector<double> *values) {
    if (values == nullptr || !encoded.is_array()) {
        return false;
    }
    std::vector<double> candidate;
    candidate.reserve(encoded.size());
    for (const auto &element : encoded) {
        double value = 0.0;
        if (!decode_f64_bits(element, &value)) {
            return false;
        }
        candidate.push_back(value);
    }
    *values = std::move(candidate);
    return true;
}

nlohmann::json encode_missile(const Missile &missile) {
    nlohmann::json encoded{
        {"schema", "missile-runtime.v3"},     {"attacker_id", missile.attacker_id},
        {"target_id", missile.target_id},     {"rng_state", missile.rng_state},
        {"seeker_mode", missile.seeker_mode}, {"autopilot_order", missile.autopilot_order},
    };
#define EF_ENCODE_DOUBLE(name) encoded[#name] = f64_bits(missile.name);
    EF_P4B_MISSILE_DOUBLE_FIELDS(EF_ENCODE_DOUBLE)
#undef EF_ENCODE_DOUBLE
#define EF_ENCODE_BOOL(name) encoded[#name] = missile.name;
    EF_P4B_MISSILE_BOOL_FIELDS(EF_ENCODE_BOOL)
#undef EF_ENCODE_BOOL
#define EF_ENCODE_STRING(name) encoded[#name] = missile.name;
    EF_P4B_MISSILE_STRING_FIELDS(EF_ENCODE_STRING)
#undef EF_ENCODE_STRING
#define EF_ENCODE_VECTOR(name) encoded[#name] = encode_f64_vector(missile.name);
    EF_P4B_MISSILE_VECTOR_FIELDS(EF_ENCODE_VECTOR)
#undef EF_ENCODE_VECTOR

    auto &ekf_state = encoded["ekf_state"];
    ekf_state = {{"initialized", missile.ekf_state.initialized},
                 {"last_predict_time_s", f64_bits(missile.ekf_state.last_predict_time_s)},
                 {"x", nlohmann::json::array()},
                 {"P", nlohmann::json::array()}};
    for (const double value : missile.ekf_state.x) {
        ekf_state["x"].push_back(f64_bits(value));
    }
    for (const double value : missile.ekf_state.P) {
        ekf_state["P"].push_back(f64_bits(value));
    }
    encoded["ekf_params"] = {
        {"process_noise_sigma_a", f64_bits(missile.ekf_params.process_noise_sigma_a)},
        {"maneuver_tau_s", f64_bits(missile.ekf_params.maneuver_tau_s)},
        {"meas_noise_angle_rad", f64_bits(missile.ekf_params.meas_noise_angle_rad)},
        {"meas_noise_range_m", f64_bits(missile.ekf_params.meas_noise_range_m)},
        {"track_memory_timeout_s", f64_bits(missile.ekf_params.track_memory_timeout_s)},
    };
    const auto &warhead = missile.warhead_profile;
    encoded["warhead_profile"] = {
        {"family", warhead.family},
        {"mass_kg", f64_bits(warhead.mass_kg)},
        {"lethal_radius_m", f64_bits(warhead.lethal_radius_m)},
        {"damage_scalar", f64_bits(warhead.damage_scalar)},
        {"explosive_mass_kg", f64_bits(warhead.explosive_mass_kg)},
        {"case_mass_kg", f64_bits(warhead.case_mass_kg)},
        {"gurney_constant_mps", f64_bits(warhead.gurney_constant_mps)},
        {"fragment_mass_kg", f64_bits(warhead.fragment_mass_kg)},
        {"fragment_count", f64_bits(warhead.fragment_count)},
        {"projection_radius_fraction", f64_bits(warhead.projection_radius_fraction)},
        {"projection_min_radius_m", f64_bits(warhead.projection_min_radius_m)},
        {"projection_max_radius_m", f64_bits(warhead.projection_max_radius_m)},
        {"projection_min_effect_scale", f64_bits(warhead.projection_min_effect_scale)},
        {"projection_max_effect_scale", f64_bits(warhead.projection_max_effect_scale)},
        {"projection_falloff_exponent", f64_bits(warhead.projection_falloff_exponent)},
        {"projection_max_projected_hitboxes", warhead.projection_max_projected_hitboxes},
        {"synthetic", warhead.synthetic},
        {"damage_scalar_synthetic", warhead.damage_scalar_synthetic},
        {"provenance", warhead.provenance},
    };
    const auto &fuze = missile.fuze_profile;
    encoded["fuze_profile"] = {
        {"type", fuze.type},
        {"trigger_radius_m", f64_bits(fuze.trigger_radius_m)},
        {"delay_s", f64_bits(fuze.delay_s)},
        {"reliability", f64_bits(fuze.reliability)},
        {"trigger_logic", fuze.trigger_logic},
        {"coverage_profile", fuze.coverage_profile},
        {"synthetic", fuze.synthetic},
        {"provenance", fuze.provenance},
    };
    return encoded;
}

bool decode_missile(const nlohmann::json &encoded, Missile *missile) {
    if (missile == nullptr || !encoded.is_object() ||
        encoded.value("schema", "") != "missile-runtime.v3" ||
        encoded.size() != encode_missile(Missile{}).size()) {
        return false;
    }
    Missile candidate{};
    try {
        candidate.attacker_id = encoded.at("attacker_id").get<std::uint64_t>();
        candidate.target_id = encoded.at("target_id").get<std::uint64_t>();
        candidate.rng_state = encoded.at("rng_state").get<std::uint64_t>();
        candidate.seeker_mode = encoded.at("seeker_mode").get<int>();
        candidate.autopilot_order = encoded.at("autopilot_order").get<int>();
#define EF_DECODE_DOUBLE(name)                                                                     \
    if (!decode_f64_bits(encoded.at(#name), &candidate.name)) return false;
        EF_P4B_MISSILE_DOUBLE_FIELDS(EF_DECODE_DOUBLE)
#undef EF_DECODE_DOUBLE
#define EF_DECODE_BOOL(name) candidate.name = encoded.at(#name).get<bool>();
        EF_P4B_MISSILE_BOOL_FIELDS(EF_DECODE_BOOL)
#undef EF_DECODE_BOOL
#define EF_DECODE_STRING(name) candidate.name = encoded.at(#name).get<std::string>();
        EF_P4B_MISSILE_STRING_FIELDS(EF_DECODE_STRING)
#undef EF_DECODE_STRING
#define EF_DECODE_VECTOR(name)                                                                     \
    if (!decode_f64_vector(encoded.at(#name), &candidate.name)) return false;
        EF_P4B_MISSILE_VECTOR_FIELDS(EF_DECODE_VECTOR)
#undef EF_DECODE_VECTOR

        const auto &ekf_state = encoded.at("ekf_state");
        if (!only_object_keys(ekf_state, {"initialized", "last_predict_time_s", "x", "P"}) ||
            ekf_state.size() != 4 || !ekf_state.at("x").is_array() ||
            ekf_state.at("x").size() != std::size(candidate.ekf_state.x) ||
            !ekf_state.at("P").is_array() ||
            ekf_state.at("P").size() != std::size(candidate.ekf_state.P)) {
            return false;
        }
        candidate.ekf_state.initialized = ekf_state.at("initialized").get<bool>();
        if (!decode_f64_bits(ekf_state.at("last_predict_time_s"),
                             &candidate.ekf_state.last_predict_time_s)) {
            return false;
        }
        for (std::size_t i = 0; i < std::size(candidate.ekf_state.x); ++i) {
            if (!decode_f64_bits(ekf_state.at("x").at(i), &candidate.ekf_state.x[i])) {
                return false;
            }
        }
        for (std::size_t i = 0; i < std::size(candidate.ekf_state.P); ++i) {
            if (!decode_f64_bits(ekf_state.at("P").at(i), &candidate.ekf_state.P[i])) {
                return false;
            }
        }
        const auto &params = encoded.at("ekf_params");
        if (!only_object_keys(params,
                              {"process_noise_sigma_a", "maneuver_tau_s", "meas_noise_angle_rad",
                               "meas_noise_range_m", "track_memory_timeout_s"}) ||
            params.size() != 5) {
            return false;
        }
#define EF_DECODE_EKF_PARAM(name)                                                                  \
    if (!decode_f64_bits(params.at(#name), &candidate.ekf_params.name)) return false;
        EF_DECODE_EKF_PARAM(process_noise_sigma_a)
        EF_DECODE_EKF_PARAM(maneuver_tau_s)
        EF_DECODE_EKF_PARAM(meas_noise_angle_rad)
        EF_DECODE_EKF_PARAM(meas_noise_range_m)
        EF_DECODE_EKF_PARAM(track_memory_timeout_s)
#undef EF_DECODE_EKF_PARAM
        const auto &warhead = encoded.at("warhead_profile");
        if (!warhead.is_object() ||
            warhead.size() != encode_missile(Missile{}).at("warhead_profile").size()) {
            return false;
        }
        candidate.warhead_profile.family = warhead.at("family").get<std::string>();
#define EF_DECODE_WARHEAD_DOUBLE(name)                                                             \
    if (!decode_f64_bits(warhead.at(#name), &candidate.warhead_profile.name)) return false;
        EF_DECODE_WARHEAD_DOUBLE(mass_kg)
        EF_DECODE_WARHEAD_DOUBLE(lethal_radius_m)
        EF_DECODE_WARHEAD_DOUBLE(damage_scalar)
        EF_DECODE_WARHEAD_DOUBLE(explosive_mass_kg)
        EF_DECODE_WARHEAD_DOUBLE(case_mass_kg)
        EF_DECODE_WARHEAD_DOUBLE(gurney_constant_mps)
        EF_DECODE_WARHEAD_DOUBLE(fragment_mass_kg)
        EF_DECODE_WARHEAD_DOUBLE(fragment_count)
        EF_DECODE_WARHEAD_DOUBLE(projection_radius_fraction)
        EF_DECODE_WARHEAD_DOUBLE(projection_min_radius_m)
        EF_DECODE_WARHEAD_DOUBLE(projection_max_radius_m)
        EF_DECODE_WARHEAD_DOUBLE(projection_min_effect_scale)
        EF_DECODE_WARHEAD_DOUBLE(projection_max_effect_scale)
        EF_DECODE_WARHEAD_DOUBLE(projection_falloff_exponent)
#undef EF_DECODE_WARHEAD_DOUBLE
        candidate.warhead_profile.projection_max_projected_hitboxes =
            warhead.at("projection_max_projected_hitboxes").get<std::uint32_t>();
        candidate.warhead_profile.synthetic = warhead.at("synthetic").get<bool>();
        candidate.warhead_profile.damage_scalar_synthetic =
            warhead.at("damage_scalar_synthetic").get<bool>();
        candidate.warhead_profile.provenance = warhead.at("provenance").get<std::string>();
        const auto &fuze = encoded.at("fuze_profile");
        if (!fuze.is_object() ||
            fuze.size() != encode_missile(Missile{}).at("fuze_profile").size()) {
            return false;
        }
        candidate.fuze_profile.type = fuze.at("type").get<std::string>();
        if (!decode_f64_bits(fuze.at("trigger_radius_m"),
                             &candidate.fuze_profile.trigger_radius_m) ||
            !decode_f64_bits(fuze.at("delay_s"), &candidate.fuze_profile.delay_s) ||
            !decode_f64_bits(fuze.at("reliability"), &candidate.fuze_profile.reliability)) {
            return false;
        }
        candidate.fuze_profile.trigger_logic = fuze.at("trigger_logic").get<std::string>();
        candidate.fuze_profile.coverage_profile = fuze.at("coverage_profile").get<std::string>();
        candidate.fuze_profile.synthetic = fuze.at("synthetic").get<bool>();
        candidate.fuze_profile.provenance = fuze.at("provenance").get<std::string>();
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *missile = std::move(candidate);
    return true;
}

nlohmann::json encode_double_map(const std::unordered_map<std::string, double> &values) {
    nlohmann::json encoded = nlohmann::json::object();
    for (const auto &[key, value] : values) {
        encoded[key] = f64_bits(value);
    }
    return encoded;
}

bool decode_double_map(const nlohmann::json &encoded,
                       std::unordered_map<std::string, double> *values) {
    if (values == nullptr || !encoded.is_object()) {
        return false;
    }
    std::unordered_map<std::string, double> candidate;
    for (const auto &[key, element] : encoded.items()) {
        double value = 0.0;
        if (!decode_f64_bits(element, &value)) {
            return false;
        }
        candidate.emplace(key, value);
    }
    *values = std::move(candidate);
    return true;
}

nlohmann::json encode_nested_double_map(
    const std::unordered_map<std::string, std::unordered_map<std::string, double>> &values) {
    nlohmann::json encoded = nlohmann::json::object();
    for (const auto &[key, value] : values) {
        encoded[key] = encode_double_map(value);
    }
    return encoded;
}

bool decode_nested_double_map(
    const nlohmann::json &encoded,
    std::unordered_map<std::string, std::unordered_map<std::string, double>> *values) {
    if (values == nullptr || !encoded.is_object()) {
        return false;
    }
    std::unordered_map<std::string, std::unordered_map<std::string, double>> candidate;
    for (const auto &[key, element] : encoded.items()) {
        std::unordered_map<std::string, double> nested;
        if (!decode_double_map(element, &nested)) {
            return false;
        }
        candidate.emplace(key, std::move(nested));
    }
    *values = std::move(candidate);
    return true;
}

nlohmann::json encode_system_health(const SystemHealth &health) {
    return {{"schema", "system-health.v2"}, {"systems", encode_double_map(health.systems)}};
}

bool decode_system_health(const nlohmann::json &encoded, SystemHealth *health) {
    return health != nullptr && encoded.is_object() && encoded.size() == 2 &&
           only_object_keys(encoded, {"schema", "systems"}) && encoded.contains("systems") &&
           encoded.value("schema", "") == "system-health.v2" &&
           decode_double_map(encoded.value("systems", nlohmann::json{}), &health->systems);
}

nlohmann::json encode_component_damage(const ComponentDamageState &damage) {
    nlohmann::json pending = nlohmann::json::array();
    for (const auto &effect : damage.pending_dependency_effects) {
        pending.push_back({
            {"target_system", effect.target_system},
            {"edge_type", effect.edge_type},
            {"remaining_delay_s", f64_bits(effect.remaining_delay_s)},
            {"availability", f64_bits(effect.availability)},
            {"impulse", f64_bits(effect.impulse)},
            {"effective_scale", f64_bits(effect.effective_scale)},
            {"source_availability", f64_bits(effect.source_availability)},
            {"direction", effect.direction},
            {"provenance", effect.provenance},
        });
    }
    return {
        {"schema", "component-damage-state.v2"},
        {"component_integrity", encode_double_map(damage.component_integrity)},
        {"component_redundancy_group", damage.component_redundancy_group},
        {"component_system", damage.component_system},
        {"component_redundancy_weight", encode_double_map(damage.component_redundancy_weight)},
        {"component_failure_mode_severity",
         encode_nested_double_map(damage.component_failure_mode_severity)},
        {"component_primary_failure_mode", damage.component_primary_failure_mode},
        {"redundancy_group_availability", encode_double_map(damage.redundancy_group_availability)},
        {"redundancy_group_member_count", damage.redundancy_group_member_count},
        {"redundancy_group_failed_count", damage.redundancy_group_failed_count},
        {"pending_dependency_effects", std::move(pending)},
        {"has_fire_suppression_components", damage.has_fire_suppression_components},
    };
}

bool decode_component_damage(const nlohmann::json &encoded, ComponentDamageState *damage) {
    if (damage == nullptr || !encoded.is_object() ||
        encoded.value("schema", "") != "component-damage-state.v2" ||
        encoded.size() != encode_component_damage(ComponentDamageState{}).size()) {
        return false;
    }
    ComponentDamageState candidate;
    try {
        if (!decode_double_map(encoded.at("component_integrity"), &candidate.component_integrity) ||
            !decode_double_map(encoded.at("component_redundancy_weight"),
                               &candidate.component_redundancy_weight) ||
            !decode_nested_double_map(encoded.at("component_failure_mode_severity"),
                                      &candidate.component_failure_mode_severity) ||
            !decode_double_map(encoded.at("redundancy_group_availability"),
                               &candidate.redundancy_group_availability)) {
            return false;
        }
        candidate.component_redundancy_group =
            encoded.at("component_redundancy_group")
                .get<decltype(candidate.component_redundancy_group)>();
        candidate.component_system =
            encoded.at("component_system").get<decltype(candidate.component_system)>();
        candidate.component_primary_failure_mode =
            encoded.at("component_primary_failure_mode")
                .get<decltype(candidate.component_primary_failure_mode)>();
        candidate.redundancy_group_member_count =
            encoded.at("redundancy_group_member_count")
                .get<decltype(candidate.redundancy_group_member_count)>();
        candidate.redundancy_group_failed_count =
            encoded.at("redundancy_group_failed_count")
                .get<decltype(candidate.redundancy_group_failed_count)>();
        const auto &pending = encoded.at("pending_dependency_effects");
        if (!pending.is_array()) {
            return false;
        }
        for (const auto &element : pending) {
            if (!element.is_object() || element.size() != 9) {
                return false;
            }
            ComponentDamageState::PendingDependencyEffect effect;
            effect.target_system = element.at("target_system").get<std::string>();
            effect.edge_type = element.at("edge_type").get<std::string>();
            if (!decode_f64_bits(element.at("remaining_delay_s"), &effect.remaining_delay_s) ||
                !decode_f64_bits(element.at("availability"), &effect.availability) ||
                !decode_f64_bits(element.at("impulse"), &effect.impulse) ||
                !decode_f64_bits(element.at("effective_scale"), &effect.effective_scale) ||
                !decode_f64_bits(element.at("source_availability"), &effect.source_availability)) {
                return false;
            }
            effect.direction = element.at("direction").get<std::string>();
            effect.provenance = element.at("provenance").get<std::string>();
            candidate.pending_dependency_effects.push_back(std::move(effect));
        }
        candidate.has_fire_suppression_components =
            encoded.at("has_fire_suppression_components").get<bool>();
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *damage = std::move(candidate);
    return true;
}

nlohmann::json encode_damage_dependency(const DamageComponentDependency &dependency) {
    return {{"system", dependency.system},
            {"target_system", dependency.target_system},
            {"edge_type", dependency.edge_type},
            {"scale", f64_bits(dependency.scale)},
            {"threshold", f64_bits(dependency.threshold)},
            {"delay_s", f64_bits(dependency.delay_s)},
            {"direction", dependency.direction},
            {"provenance", dependency.provenance}};
}

bool decode_damage_dependency(const nlohmann::json &encoded,
                              DamageComponentDependency *dependency) {
    if (dependency == nullptr || !encoded.is_object() || encoded.size() != 8) {
        return false;
    }
    try {
        dependency->system = encoded.at("system").get<std::string>();
        dependency->target_system = encoded.at("target_system").get<std::string>();
        dependency->edge_type = encoded.at("edge_type").get<std::string>();
        dependency->direction = encoded.at("direction").get<std::string>();
        dependency->provenance = encoded.at("provenance").get<std::string>();
        return decode_f64_bits(encoded.at("scale"), &dependency->scale) &&
               decode_f64_bits(encoded.at("threshold"), &dependency->threshold) &&
               decode_f64_bits(encoded.at("delay_s"), &dependency->delay_s);
    } catch (const nlohmann::json::exception &) {
        return false;
    }
}

nlohmann::json encode_damage_component(const DamageComponent &component) {
    nlohmann::json dependencies = nlohmann::json::array();
    for (const auto &dependency : component.dependencies) {
        dependencies.push_back(encode_damage_dependency(dependency));
    }
    nlohmann::json axes = nlohmann::json::array();
    for (const auto &axis : component.geometry_axes) {
        axes.push_back({f64_bits(axis[0]), f64_bits(axis[1]), f64_bits(axis[2])});
    }
    nlohmann::json vertices = nlohmann::json::array();
    for (const auto &vertex : component.geometry_vertices_m) {
        vertices.push_back({f64_bits(vertex[0]), f64_bits(vertex[1]), f64_bits(vertex[2])});
    }
    return {
        {"name", component.name},
        {"system", component.system},
        {"redundancy_group_id", component.redundancy_group_id},
        {"dependencies", std::move(dependencies)},
        {"offset_x", f64_bits(component.offset_x)},
        {"offset_y", f64_bits(component.offset_y)},
        {"offset_z", f64_bits(component.offset_z)},
        {"dim_l", f64_bits(component.dim_l)},
        {"dim_w", f64_bits(component.dim_w)},
        {"dim_h", f64_bits(component.dim_h)},
        {"armor_mm", f64_bits(component.armor_mm)},
        {"threshold_scale", f64_bits(component.threshold_scale)},
        {"geometry_primitive", component.geometry_primitive},
        {"geometry_source_ref", component.geometry_source_ref},
        {"geometry_source_region_id", component.geometry_source_region_id},
        {"geometry_surface_component_id", component.geometry_surface_component_id},
        {"geometry_axes", std::move(axes)},
        {"geometry_half_extents_m",
         {f64_bits(component.geometry_half_extents_m[0]),
          f64_bits(component.geometry_half_extents_m[1]),
          f64_bits(component.geometry_half_extents_m[2])}},
        {"geometry_thin_axis", component.geometry_thin_axis},
        {"geometry_nominal_thickness_m", f64_bits(component.geometry_nominal_thickness_m)},
        {"geometry_vertices_m", std::move(vertices)},
        {"mechanism_threshold_scales", encode_double_map(component.mechanism_threshold_scales)},
        {"failure_mode_weights", encode_double_map(component.failure_mode_weights)},
        {"redundancy_group", f64_bits(component.redundancy_group)},
        {"redundancy_weight", f64_bits(component.redundancy_weight)},
        {"critical", component.critical},
    };
}

bool decode_triplet(const nlohmann::json &encoded, std::array<double, 3> *values) {
    if (values == nullptr || !encoded.is_array() || encoded.size() != 3) {
        return false;
    }
    return decode_f64_bits(encoded.at(0), &(*values)[0]) &&
           decode_f64_bits(encoded.at(1), &(*values)[1]) &&
           decode_f64_bits(encoded.at(2), &(*values)[2]);
}

bool decode_damage_component(const nlohmann::json &encoded, DamageComponent *component) {
    if (component == nullptr || !encoded.is_object() ||
        encoded.size() != encode_damage_component(DamageComponent{}).size()) {
        return false;
    }
    DamageComponent candidate;
    try {
        candidate.name = encoded.at("name").get<std::string>();
        candidate.system = encoded.at("system").get<std::string>();
        candidate.redundancy_group_id = encoded.at("redundancy_group_id").get<std::string>();
        const auto &dependencies = encoded.at("dependencies");
        if (!dependencies.is_array()) {
            return false;
        }
        for (const auto &element : dependencies) {
            DamageComponentDependency dependency;
            if (!decode_damage_dependency(element, &dependency)) {
                return false;
            }
            candidate.dependencies.push_back(std::move(dependency));
        }
#define EF_DECODE_DAMAGE_DOUBLE(name)                                                              \
    if (!decode_f64_bits(encoded.at(#name), &candidate.name)) return false;
        EF_DECODE_DAMAGE_DOUBLE(offset_x)
        EF_DECODE_DAMAGE_DOUBLE(offset_y)
        EF_DECODE_DAMAGE_DOUBLE(offset_z)
        EF_DECODE_DAMAGE_DOUBLE(dim_l)
        EF_DECODE_DAMAGE_DOUBLE(dim_w)
        EF_DECODE_DAMAGE_DOUBLE(dim_h)
        EF_DECODE_DAMAGE_DOUBLE(armor_mm)
        EF_DECODE_DAMAGE_DOUBLE(threshold_scale)
        EF_DECODE_DAMAGE_DOUBLE(geometry_nominal_thickness_m)
        EF_DECODE_DAMAGE_DOUBLE(redundancy_group)
        EF_DECODE_DAMAGE_DOUBLE(redundancy_weight)
#undef EF_DECODE_DAMAGE_DOUBLE
        candidate.geometry_primitive = encoded.at("geometry_primitive").get<std::string>();
        candidate.geometry_source_ref = encoded.at("geometry_source_ref").get<std::string>();
        candidate.geometry_source_region_id =
            encoded.at("geometry_source_region_id").get<std::string>();
        candidate.geometry_surface_component_id =
            encoded.at("geometry_surface_component_id").get<std::string>();
        candidate.geometry_thin_axis = encoded.at("geometry_thin_axis").get<std::string>();
        const auto &axes = encoded.at("geometry_axes");
        if (!axes.is_array() || axes.size() != candidate.geometry_axes.size()) {
            return false;
        }
        for (std::size_t index = 0; index < candidate.geometry_axes.size(); ++index) {
            if (!decode_triplet(axes.at(index), &candidate.geometry_axes[index])) {
                return false;
            }
        }
        if (!decode_triplet(encoded.at("geometry_half_extents_m"),
                            &candidate.geometry_half_extents_m)) {
            return false;
        }
        const auto &vertices = encoded.at("geometry_vertices_m");
        if (!vertices.is_array()) {
            return false;
        }
        for (const auto &element : vertices) {
            std::array<double, 3> vertex{};
            if (!decode_triplet(element, &vertex)) {
                return false;
            }
            candidate.geometry_vertices_m.push_back(vertex);
        }
        if (!decode_double_map(encoded.at("mechanism_threshold_scales"),
                               &candidate.mechanism_threshold_scales) ||
            !decode_double_map(encoded.at("failure_mode_weights"),
                               &candidate.failure_mode_weights)) {
            return false;
        }
        candidate.critical = encoded.at("critical").get<bool>();
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *component = std::move(candidate);
    return true;
}

nlohmann::json encode_hitbox_config(const HitboxConfig &config) {
    nlohmann::json hitboxes = nlohmann::json::array();
    for (const auto &hitbox : config.hitboxes) {
        nlohmann::json components = nlohmann::json::array();
        for (const auto &component : hitbox.components) {
            components.push_back(encode_damage_component(component));
        }
        hitboxes.push_back({
            {"id", hitbox.id},
            {"offset_x", f64_bits(hitbox.offset_x)},
            {"offset_y", f64_bits(hitbox.offset_y)},
            {"offset_z", f64_bits(hitbox.offset_z)},
            {"dim_l", f64_bits(hitbox.dim_l)},
            {"dim_w", f64_bits(hitbox.dim_w)},
            {"dim_h", f64_bits(hitbox.dim_h)},
            {"armor_mm", f64_bits(hitbox.armor_mm)},
            {"protected_systems", hitbox.protected_systems},
            {"components", std::move(components)},
        });
    }
    return {{"schema", "hitbox-config.v2"}, {"hitboxes", std::move(hitboxes)}};
}

bool decode_hitbox_config(const nlohmann::json &encoded, HitboxConfig *config) {
    if (config == nullptr || !encoded.is_object() ||
        encoded.value("schema", "") != "hitbox-config.v2" || encoded.size() != 2) {
        return false;
    }
    HitboxConfig candidate;
    try {
        const auto &hitboxes = encoded.at("hitboxes");
        if (!hitboxes.is_array()) {
            return false;
        }
        for (const auto &element : hitboxes) {
            if (!element.is_object() || element.size() != 10) {
                return false;
            }
            Hitbox hitbox;
            hitbox.id = element.at("id").get<int>();
#define EF_DECODE_HITBOX_DOUBLE(name)                                                              \
    if (!decode_f64_bits(element.at(#name), &hitbox.name)) return false;
            EF_DECODE_HITBOX_DOUBLE(offset_x)
            EF_DECODE_HITBOX_DOUBLE(offset_y)
            EF_DECODE_HITBOX_DOUBLE(offset_z)
            EF_DECODE_HITBOX_DOUBLE(dim_l)
            EF_DECODE_HITBOX_DOUBLE(dim_w)
            EF_DECODE_HITBOX_DOUBLE(dim_h)
            EF_DECODE_HITBOX_DOUBLE(armor_mm)
#undef EF_DECODE_HITBOX_DOUBLE
            hitbox.protected_systems =
                element.at("protected_systems").get<std::vector<std::string>>();
            const auto &components = element.at("components");
            if (!components.is_array()) {
                return false;
            }
            for (const auto &component_value : components) {
                DamageComponent component;
                if (!decode_damage_component(component_value, &component)) {
                    return false;
                }
                hitbox.components.push_back(std::move(component));
            }
            candidate.hitboxes.push_back(std::move(hitbox));
        }
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *config = std::move(candidate);
    return true;
}

nlohmann::json encode_vulnerability_row(const AircraftVulnerabilityEvidenceRow &row) {
    nlohmann::json encoded = nlohmann::json::object();
#define EF_ENCODE_VULNERABILITY_STRING(name) encoded[#name] = row.name;
    EF_P4B_VULNERABILITY_ROW_STRING_FIELDS(EF_ENCODE_VULNERABILITY_STRING)
#undef EF_ENCODE_VULNERABILITY_STRING
#define EF_ENCODE_VULNERABILITY_DOUBLE(name) encoded[#name] = f64_bits(row.name);
    EF_P4B_VULNERABILITY_ROW_DOUBLE_FIELDS(EF_ENCODE_VULNERABILITY_DOUBLE)
#undef EF_ENCODE_VULNERABILITY_DOUBLE
#define EF_ENCODE_VULNERABILITY_BOOL(name) encoded[#name] = row.name;
    EF_P4B_VULNERABILITY_ROW_BOOL_FIELDS(EF_ENCODE_VULNERABILITY_BOOL)
#undef EF_ENCODE_VULNERABILITY_BOOL
    return encoded;
}

bool decode_vulnerability_row(const nlohmann::json &encoded,
                              AircraftVulnerabilityEvidenceRow *row) {
    if (row == nullptr || !encoded.is_object() ||
        encoded.size() != encode_vulnerability_row(AircraftVulnerabilityEvidenceRow{}).size()) {
        return false;
    }
    AircraftVulnerabilityEvidenceRow candidate;
    try {
#define EF_DECODE_VULNERABILITY_STRING(name) candidate.name = encoded.at(#name).get<std::string>();
        EF_P4B_VULNERABILITY_ROW_STRING_FIELDS(EF_DECODE_VULNERABILITY_STRING)
#undef EF_DECODE_VULNERABILITY_STRING
#define EF_DECODE_VULNERABILITY_DOUBLE(name)                                                       \
    if (!decode_f64_bits(encoded.at(#name), &candidate.name)) return false;
        EF_P4B_VULNERABILITY_ROW_DOUBLE_FIELDS(EF_DECODE_VULNERABILITY_DOUBLE)
#undef EF_DECODE_VULNERABILITY_DOUBLE
#define EF_DECODE_VULNERABILITY_BOOL(name) candidate.name = encoded.at(#name).get<bool>();
        EF_P4B_VULNERABILITY_ROW_BOOL_FIELDS(EF_DECODE_VULNERABILITY_BOOL)
#undef EF_DECODE_VULNERABILITY_BOOL
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *row = std::move(candidate);
    return true;
}

nlohmann::json encode_aircraft_vulnerability(const AircraftVulnerabilityProfile &profile) {
    nlohmann::json encoded{{"schema", "aircraft-vulnerability.v2"},
                           {"evidence_rows", nlohmann::json::array()}};
#define EF_ENCODE_PROFILE_STRING(name) encoded[#name] = profile.name;
    EF_P4B_VULNERABILITY_PROFILE_STRING_FIELDS(EF_ENCODE_PROFILE_STRING)
#undef EF_ENCODE_PROFILE_STRING
#define EF_ENCODE_PROFILE_BOOL(name) encoded[#name] = profile.name;
    EF_P4B_VULNERABILITY_PROFILE_BOOL_FIELDS(EF_ENCODE_PROFILE_BOOL)
#undef EF_ENCODE_PROFILE_BOOL
#define EF_ENCODE_PROFILE_DOUBLE(name) encoded[#name] = f64_bits(profile.name);
    EF_P4B_VULNERABILITY_PROFILE_DOUBLE_FIELDS(EF_ENCODE_PROFILE_DOUBLE)
#undef EF_ENCODE_PROFILE_DOUBLE
    for (const auto &row : profile.evidence_rows) {
        encoded["evidence_rows"].push_back(encode_vulnerability_row(row));
    }
    return encoded;
}

bool decode_aircraft_vulnerability(const nlohmann::json &encoded,
                                   AircraftVulnerabilityProfile *profile) {
    if (profile == nullptr || !encoded.is_object() ||
        encoded.value("schema", "") != "aircraft-vulnerability.v2" ||
        encoded.size() != encode_aircraft_vulnerability(AircraftVulnerabilityProfile{}).size()) {
        return false;
    }
    AircraftVulnerabilityProfile candidate;
    try {
#define EF_DECODE_PROFILE_STRING(name) candidate.name = encoded.at(#name).get<std::string>();
        EF_P4B_VULNERABILITY_PROFILE_STRING_FIELDS(EF_DECODE_PROFILE_STRING)
#undef EF_DECODE_PROFILE_STRING
#define EF_DECODE_PROFILE_BOOL(name) candidate.name = encoded.at(#name).get<bool>();
        EF_P4B_VULNERABILITY_PROFILE_BOOL_FIELDS(EF_DECODE_PROFILE_BOOL)
#undef EF_DECODE_PROFILE_BOOL
#define EF_DECODE_PROFILE_DOUBLE(name)                                                             \
    if (!decode_f64_bits(encoded.at(#name), &candidate.name)) return false;
        EF_P4B_VULNERABILITY_PROFILE_DOUBLE_FIELDS(EF_DECODE_PROFILE_DOUBLE)
#undef EF_DECODE_PROFILE_DOUBLE
        const auto &rows = encoded.at("evidence_rows");
        if (!rows.is_array()) {
            return false;
        }
        for (const auto &element : rows) {
            AircraftVulnerabilityEvidenceRow row;
            if (!decode_vulnerability_row(element, &row)) {
                return false;
            }
            candidate.evidence_rows.push_back(std::move(row));
        }
    } catch (const nlohmann::json::exception &) {
        return false;
    }
    *profile = std::move(candidate);
    return true;
}

bool scalar_entity_reference_field(std::string_view field) {
    static const std::set<std::string_view> fields{
        "active_helo_entity_id",
        "assignee_id",
        "assigned_target_id",
        "assigned_target_source_id",
        "attacker_id",
        "embarked_helo_entity_id",
        "engagement_authority_grantor_id",
        "engagement_authority_holder_id",
        "entity_id",
        "entity_ref",
        "element_id",
        "ground_commander_id",
        "issuer_id",
        "lead_aircraft_id",
        "msg_recipient",
        "partner_entity_id",
        "receiver_id",
        "recovery_base_id",
        "recovery_site_id",
        "reference_entity_id",
        "sender_id",
        "source_id",
        "supported_node_id",
        "supporting_node_id",
        "tactical_unit_id",
        "target_id",
        "target_receiver_id",
    };
    return fields.contains(field);
}

bool action_message_arg_is_entity_reference(const nlohmann::json &value) {
    if (!value.is_object() || !value.contains("msg_type") ||
        !value.at("msg_type").is_number_integer()) {
        return false;
    }
    const auto message_type = static_cast<CommMsgType>(value.at("msg_type").get<int>());
    switch (message_type) {
    case CommMsgType::REP_TALLY:
    case CommMsgType::REP_VISUAL:
    case CommMsgType::REP_BLIND:
    case CommMsgType::REP_ENGAGED:
    case CommMsgType::REP_SPLASH:
    case CommMsgType::ReportContact:
        return true;
    default:
        return false;
    }
}

bool vector_entity_reference_field(std::string_view field) {
    return field == "detected_radar_ids" || field == "locking_radar_ids";
}

bool encode_entity_references(nlohmann::json &value,
                              const std::unordered_map<std::uint64_t, std::string> &entity_keys,
                              std::string_view field = {},
                              std::string *unresolved_detail = nullptr) {
    const auto encode_scalar = [&entity_keys, unresolved_detail](nlohmann::json &candidate,
                                                                 bool require_remap,
                                                                 std::string_view reference_field) {
        if (!candidate.is_number_unsigned() && !candidate.is_number_integer()) {
            return true;
        }
        const auto raw = candidate.get<std::uint64_t>();
        if (raw == 0) {
            return true;
        }
        if (const auto found = entity_keys.find(raw); found != entity_keys.end()) {
            candidate = nlohmann::json{{"$entity", found->second}};
            return true;
        }
        if (require_remap && unresolved_detail != nullptr && unresolved_detail->empty()) {
            // Name the offending field and raw id.  A fail-closed reference
            // guard is only actionable if it says which owner surface holds
            // the reference that escaped the logical-identity table.
            *unresolved_detail = std::string(reference_field) + "=" + std::to_string(raw);
        }
        return false;
    };
    if (scalar_entity_reference_field(field)) {
        // Every declared entity-bearing scalar must be remapped through the
        // logical-identity table. Preserving an unknown source-local ECS id
        // would let a target resolve it to an unrelated entity (or silently
        // retain a dangling reference), violating generation/logical binding.
        return encode_scalar(value, true, field);
    }
    if (vector_entity_reference_field(field)) {
        if (!value.is_array()) {
            throw std::runtime_error("entity-reference vector is not an array in the ECS snapshot");
        }
        for (auto &element : value) {
            if (!encode_scalar(element, true, field)) {
                return false;
            }
        }
        return true;
    }
    if (value.is_array()) {
        for (auto &element : value) {
            if (!encode_entity_references(element, entity_keys, {}, unresolved_detail)) {
                return false;
            }
        }
    } else if (value.is_object()) {
        const bool remap_action_message_arg = action_message_arg_is_entity_reference(value);
        for (auto &[key, element] : value.items()) {
            // ActionCommand.msg_arg is a typed compatibility payload: only
            // target-bearing message kinds carry an ECS entity reference.
            // Status, azimuth, threat and other message kinds retain their
            // numeric argument as a logical scalar.
            if (key == "msg_arg" && !remap_action_message_arg) {
                continue;
            }
            if (key == "msg_arg" && remap_action_message_arg) {
                if (!encode_scalar(element, true, key)) {
                    return false;
                }
                continue;
            }
            if (!encode_entity_references(element, entity_keys, key, unresolved_detail)) {
                return false;
            }
        }
    }
    return true;
}

bool decode_entity_references(
    nlohmann::json &value, const std::unordered_map<std::string, std::uint64_t> &target_entities) {
    if (value.is_object() && value.size() == 1 && value.contains("$entity")) {
        if (!value.at("$entity").is_string()) {
            return false;
        }
        const auto found = target_entities.find(value.at("$entity").get_ref<const std::string &>());
        if (found == target_entities.end()) {
            return false;
        }
        value = found->second;
        return true;
    }
    if (value.is_array()) {
        for (auto &element : value) {
            if (!decode_entity_references(element, target_entities)) {
                return false;
            }
        }
    } else if (value.is_object()) {
        for (auto &[key, element] : value.items()) {
            static_cast<void>(key);
            if (!decode_entity_references(element, target_entities)) {
                return false;
            }
        }
    }
    return true;
}

std::string identity_text(const RuntimeIdentity128 &identity) {
    return std::to_string(identity.high) + ":" + std::to_string(identity.low);
}

std::string
transaction_id(std::string_view transaction_namespace, const RuntimeStateTransferProfile &profile,
               const RuntimeIncarnationRef &source_slot, const RuntimeStateCensusEntry &entry,
               const RuntimeIdentity128 &candidate_identity, std::string_view payload_sha256) {
    const std::string material =
        std::string(transaction_namespace) + "|" + profile.profile_id + "|" +
        std::to_string(profile.profile_generation) + "|" + profile.source_plan_sha256 + "|" +
        profile.target_plan_sha256 + "|" + identity_text(source_slot.host.host_id) + "|" +
        identity_text(source_slot.host.boot_id) + "|" +
        std::to_string(source_slot.incarnation_epoch) + "|" +
        std::string(runtime_state_category_name(entry.category)) + "|" +
        std::to_string(entry.step_sequence) + "|" + std::to_string(entry.barrier_sequence) + "|" +
        identity_text(candidate_identity) + "|" + std::string(payload_sha256);
    const std::vector<std::uint8_t> material_bytes(material.begin(), material.end());
    return runtime_state_payload_sha256(material_bytes);
}

std::string replay_evidence(std::string_view label, std::string_view payload_sha256,
                            const RuntimeEpisodeCoordinatorSnapshot &barrier) {
    const std::string material = std::string(label) + "|" + std::string(payload_sha256) + "|" +
                                 std::to_string(barrier.step_sequence) + "|" +
                                 std::to_string(barrier.barrier_sequence);
    return runtime_state_payload_sha256(bytes(material));
}

std::string explicit_policy_payload(SimulationKernel &kernel, RuntimeStateCategory category,
                                    const RuntimeStateOwnerExportContext &context) {
    const auto &barrier = context.barrier_snapshot;
    std::ostringstream output;
    switch (category) {
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        output << "python-mirror-rederive.v2\n"
               << "disposition=rederive\n"
               << "source_authority=native-ecs-command-episode\n"
               << "target_action=discard-and-rebuild\n"
               << "cache_transfer=forbidden\n"
               << "resolved_plan_sha256=" << kernel.resolved_composition_sha256() << '\n'
               << "source_step_sequence=" << barrier.step_sequence << '\n'
               << "source_barrier_sequence=" << barrier.barrier_sequence << '\n';
        break;
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
        output << "backend-resource-rederive.v2\n"
               << "disposition=rederive\n"
               << "backend_profile_id="
               << runtime::backend_profiles::kBackendProfileIdCpuExactReference << '\n'
               << "raw_handle_transfer=forbidden\n"
               << "target_action=rehydrate-from-closed-plan\n"
               << "source_release=host-draining-after-publication\n"
               << "resolved_plan_sha256=" << kernel.resolved_composition_sha256() << '\n'
               << "source_step_sequence=" << barrier.step_sequence << '\n'
               << "source_barrier_sequence=" << barrier.barrier_sequence << '\n';
        break;
    case RuntimeStateCategory::InFlightRequestsResults:
        if (!context.cooperative_cancellation_acknowledged) {
            throw std::runtime_error(
                "in-flight drain receipt requires host cancellation acknowledgement");
        }
        output << "in-flight-drain.v2\n"
               << "disposition=drain\n"
               << "truth_mutating_remaining=0\n"
               << "read_only_result_leases=" << context.source_read_only_result_leases << '\n'
               << "late_result_policy=source-slot-fenced-drain\n"
               << "cancellation_acknowledged=1\n"
               << "source_step_sequence=" << barrier.step_sequence << '\n'
               << "source_barrier_sequence=" << barrier.barrier_sequence << '\n';
        break;
    case RuntimeStateCategory::ExternalSideEffects:
        output << "side-effect-outbox.v2\n"
               << "disposition=not-applicable\n"
               << "external_receipt_count=0\n"
               << "policy=no-external-outbox-owned-by-simulation-kernel\n";
        break;
    case RuntimeStateCategory::DiagnosticsTelemetry:
        output << "telemetry-rederive.v2\n"
               << "disposition=rederive\n"
               << "continuity=reset-at-target\n"
               << "resolved_plan_sha256=" << kernel.resolved_composition_sha256() << '\n'
               << "source_step_sequence=" << barrier.step_sequence << '\n'
               << "source_barrier_sequence=" << barrier.barrier_sequence << '\n';
        break;
    default:
        throw std::runtime_error("state category has no explicit policy payload");
    }
    return output.str();
}

struct StagedImport {
    SimulationKernel *kernel = nullptr;
    RuntimeStateCategory category = RuntimeStateCategory::CompositionProviderSystemGraph;
    std::vector<std::uint8_t> source_payload;
    std::vector<std::uint8_t> before_payload;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
    std::size_t source_read_only_result_leases = 0;
    bool cooperative_cancellation_acknowledged = false;
    bool episode_barrier_validated = false;
    RuntimeEpisodeCoordinatorSnapshot episode_barrier;
    std::function<bool()> rederive_python_caches;
    std::function<std::vector<std::uint8_t>()> snapshot_python_caches;
    std::function<bool(const std::vector<std::uint8_t> &)> rollback_python_caches;
    std::function<RuntimeStateOwnerImportTransactionPhase(const std::vector<std::uint8_t> &)>
        recover_python_caches;
    bool python_caches_applied = false;
};

struct DecodedRngState {
    std::uint64_t draw_position = 0;
    std::mt19937 engine;
};

struct DecodedClockState {
    double world_time = 0.0;
    double time_step = 0.0;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
};

bool is_lower_hex_sha256(std::string_view value) {
    return value.size() == 64 && std::all_of(value.begin(), value.end(), [](char character) {
               return (character >= '0' && character <= '9') ||
                      (character >= 'a' && character <= 'f');
           });
}

bool parse_prefixed_uint64(std::string_view line, std::string_view prefix, std::uint64_t *value) {
    if (value == nullptr || !line.starts_with(prefix)) {
        return false;
    }
    const std::string_view encoded = line.substr(prefix.size());
    const auto parsed = std::from_chars(encoded.data(), encoded.data() + encoded.size(), *value);
    return parsed.ec == std::errc{} && parsed.ptr == encoded.data() + encoded.size();
}

std::vector<std::string> policy_lines(std::string_view encoded) {
    std::istringstream input{std::string(encoded)};
    std::vector<std::string> lines;
    for (std::string line; std::getline(input, line);) {
        lines.push_back(std::move(line));
    }
    return lines;
}

bool decode_rederive_policy(std::string_view encoded, std::string_view header,
                            const std::vector<std::string_view> &fixed_lines,
                            std::uint64_t expected_step_sequence,
                            std::uint64_t expected_barrier_sequence) {
    const auto lines = policy_lines(encoded);
    const std::size_t plan_index = 1 + fixed_lines.size();
    if (lines.size() != plan_index + 3 || lines.front() != header) {
        return false;
    }
    for (std::size_t index = 0; index < fixed_lines.size(); ++index) {
        if (lines[index + 1] != fixed_lines[index]) {
            return false;
        }
    }
    const auto &plan = lines[plan_index];
    if (!plan.starts_with("resolved_plan_sha256=") ||
        !is_lower_hex_sha256(
            std::string_view(plan).substr(std::string_view("resolved_plan_sha256=").size()))) {
        return false;
    }
    std::uint64_t decoded_step = 0;
    std::uint64_t decoded_barrier = 0;
    return parse_prefixed_uint64(lines[plan_index + 1], "source_step_sequence=", &decoded_step) &&
           parse_prefixed_uint64(lines[plan_index + 2],
                                 "source_barrier_sequence=", &decoded_barrier) &&
           decoded_step == expected_step_sequence && decoded_barrier == expected_barrier_sequence;
}

bool decode_in_flight_policy(std::string_view encoded, std::size_t expected_read_only_result_leases,
                             std::uint64_t expected_step_sequence,
                             std::uint64_t expected_barrier_sequence) {
    const auto lines = policy_lines(encoded);
    if (lines.size() != 8 || lines[0] != "in-flight-drain.v2" || lines[1] != "disposition=drain" ||
        lines[2] != "truth_mutating_remaining=0" ||
        lines[4] != "late_result_policy=source-slot-fenced-drain" ||
        lines[5] != "cancellation_acknowledged=1") {
        return false;
    }
    std::uint64_t read_only_result_leases = 0;
    std::uint64_t step_sequence = 0;
    std::uint64_t barrier_sequence = 0;
    return parse_prefixed_uint64(lines[3], "read_only_result_leases=", &read_only_result_leases) &&
           read_only_result_leases == expected_read_only_result_leases &&
           parse_prefixed_uint64(lines[6], "source_step_sequence=", &step_sequence) &&
           parse_prefixed_uint64(lines[7], "source_barrier_sequence=", &barrier_sequence) &&
           step_sequence == expected_step_sequence && barrier_sequence == expected_barrier_sequence;
}

bool decode_rng_state(std::string_view encoded, DecodedRngState *decoded) {
    if (decoded == nullptr) {
        return false;
    }
    std::istringstream input{std::string(encoded)};
    std::string header;
    DecodedRngState candidate;
    if (!std::getline(input, header) || header != "rng.v2" || !(input >> candidate.draw_position) ||
        !(input >> candidate.engine)) {
        return false;
    }
    input >> std::ws;
    if (!input.eof()) {
        return false;
    }
    *decoded = std::move(candidate);
    return true;
}

bool decode_clock_state(std::string_view encoded, DecodedClockState *decoded) {
    if (decoded == nullptr) {
        return false;
    }
    std::istringstream input{std::string(encoded)};
    std::string header;
    DecodedClockState candidate;
    if (!std::getline(input, header) || header != "clock.v2" ||
        !(input >> candidate.world_time >> candidate.time_step >> candidate.step_sequence >>
          candidate.barrier_sequence) ||
        !std::isfinite(candidate.world_time) || candidate.world_time < 0.0 ||
        !std::isfinite(candidate.time_step) || candidate.time_step <= 0.0 ||
        candidate.barrier_sequence == 0) {
        return false;
    }
    input >> std::ws;
    if (!input.eof()) {
        return false;
    }
    *decoded = candidate;
    return true;
}

bool decode_episode_barrier(std::string_view encoded, RuntimeEpisodeCoordinatorSnapshot *decoded) {
    if (decoded == nullptr) {
        return false;
    }
    std::istringstream input{std::string(encoded)};
    std::string header;
    unsigned int phase = 0;
    RuntimeEpisodeCoordinatorSnapshot candidate;
    if (!std::getline(input, header) || header != "episode-barrier.v2" ||
        !(input >> candidate.episode.world.incarnation.host.host_id.high >>
          candidate.episode.world.incarnation.host.host_id.low >>
          candidate.episode.world.incarnation.host.boot_id.high >>
          candidate.episode.world.incarnation.host.boot_id.low >>
          candidate.episode.world.incarnation.incarnation_epoch >>
          candidate.episode.world.world_slot >> candidate.episode.world.world_generation >>
          candidate.episode.episode_id.high >> candidate.episode.episode_id.low >>
          candidate.episode.episode_generation >> phase >> candidate.step_sequence >>
          candidate.barrier_sequence >> candidate.snapshot_id.high >> candidate.snapshot_id.low >>
          candidate.snapshot_sha256)) {
        return false;
    }
    input >> std::ws;
    if (!input.eof() ||
        phase != static_cast<unsigned int>(RuntimeEpisodePhase::ReplacementBarrier) ||
        !candidate.episode.well_formed() || candidate.barrier_sequence == 0 ||
        !candidate.snapshot_id.well_formed() || !is_lower_hex_sha256(candidate.snapshot_sha256)) {
        return false;
    }
    candidate.phase = RuntimeEpisodePhase::ReplacementBarrier;
    *decoded = std::move(candidate);
    return true;
}

} // namespace

std::string SimulationKernelStateOwnerBridge::serialize_world(SimulationKernel &kernel) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_export_world");
    // Register transfer reflection lazily so the ordinary simulation path
    // keeps its stable entity-id allocation. State-transfer admission owns
    // this additional Flecs schema surface and is the first path that needs
    // it.
    register_state_transfer_component_reflection(kernel.ecs);
    // Flecs' table JSON writer on this pinned version emits raw ChildOf pair
    // expressions that are not valid JSON.  Detach mutable hierarchy edges
    // while serializing, then restore them before returning; the transfer ABI
    // carries the validated logical edges in `child_of` below.
    std::vector<std::pair<ecs_entity_t, ecs_entity_t>> detached_child_of;
    kernel.ecs.query<SimObject>().each([&](flecs::entity entity, const SimObject &) {
        const ecs_entity_t parent = ecs_get_target(kernel.ecs.c_ptr(), entity.id(), EcsChildOf, 0);
        if (parent != 0) {
            detached_child_of.emplace_back(entity.id(), parent);
        }
    });
    // Query callbacks execute with table storage locked. Apply the temporary
    // relation changes only after enumeration has completed.
    for (const auto &[child, parent] : detached_child_of) {
        ecs_remove_id(kernel.ecs.c_ptr(), child, ecs_pair(EcsChildOf, parent));
    }
    const auto restore_detached_child_of = [&]() {
        for (const auto &[child, parent] : detached_child_of) {
            if (ecs_is_alive(kernel.ecs.c_ptr(), child) &&
                ecs_is_alive(kernel.ecs.c_ptr(), parent)) {
                ecs_add_id(kernel.ecs.c_ptr(), child, ecs_pair(EcsChildOf, parent));
            }
        }
    };
    ecs_query_desc_t query_descriptor{};
    query_descriptor.terms[0].id = kernel.ecs.id<SimObject>();
    ecs_query_t *query = ecs_query_init(kernel.ecs.c_ptr(), &query_descriptor);
    if (query == nullptr) {
        restore_detached_child_of();
        throw std::runtime_error("Flecs SimObject query creation failed");
    }
    ecs_iter_t iterator = ecs_query_iter(kernel.ecs.c_ptr(), query);
    ecs_iter_to_json_desc_t descriptor{};
    descriptor.serialize_entity_ids = true;
    descriptor.serialize_values = true;
    descriptor.serialize_table = true;
    char *json = ecs_iter_to_json(&iterator, &descriptor);
    ecs_query_fini(query);
    restore_detached_child_of();
    if (json == nullptr) {
        throw std::runtime_error("Flecs world serialization failed");
    }
    std::string output(json);
    ecs_os_free(json);
    auto document = nlohmann::json::parse(output);
    std::vector<std::string> unreflected_components;
    if (document.contains("results") && document.at("results").is_array()) {
        auto &results = document.at("results");
        std::unordered_map<std::uint64_t, std::string> entity_keys;
        entity_keys.reserve(results.size());
        nlohmann::json child_of = nlohmann::json::array();
        for (auto &result : results) {
            // Flecs JSON emits the entity index, not its generation. Resolve
            // the live generation before querying components/relations or
            // matching native references after a compensated delete/recreate.
            const std::uint64_t local_entity_id =
                ecs_get_alive(kernel.ecs.c_ptr(), result.value("id", std::uint64_t{0}));
            if (local_entity_id == 0) {
                throw std::runtime_error("Flecs SimObject snapshot has no stable identity seed");
            }
            std::string logical_name = result.value("name", "");
            if (logical_name.empty() || logical_name.starts_with('#')) {
                logical_name = "p4b-simobject-" + std::to_string(local_entity_id);
            }
            if (!entity_keys.emplace(local_entity_id, logical_name).second) {
                throw std::runtime_error("Flecs SimObject snapshot contains a duplicate entity id");
            }
            result["id"] = local_entity_id;
            result["name"] = std::move(logical_name);
        }
        // Flecs includes relation pairs in table serialization.  Keep the
        // transfer format strict and explicit by carrying only ChildOf edges
        // between transferred SimObjects in a dedicated logical-identity map;
        // non-hierarchical pairs remain unsupported rather than being silently
        // dropped.
        for (auto &result : results) {
            const auto local_entity_id = result.at("id").get<std::uint64_t>();
            const auto parent_id =
                ecs_get_target(kernel.ecs.c_ptr(), local_entity_id, EcsChildOf, 0);
            const ecs_type_t *type = ecs_get_type(kernel.ecs.c_ptr(), local_entity_id);
            for (int32_t index = 0; type != nullptr && index < type->count; ++index) {
                const ecs_id_t id = type->array[index];
                if (ecs_id_is_pair(id) && ECS_PAIR_FIRST(id) != EcsChildOf &&
                    id != ecs_pair(ecs_id(EcsIdentifier), EcsName)) {
                    throw std::runtime_error(
                        "ECS snapshot contains an unsupported non-hierarchical pair");
                }
            }
            if (parent_id != 0) {
                const auto parent = entity_keys.find(parent_id);
                if (parent == entity_keys.end()) {
                    throw std::runtime_error(
                        "ECS snapshot ChildOf parent is outside transfer closure");
                }
                child_of.push_back({{"child", result.at("name")}, {"parent", parent->second}});
            }
            if (result.contains("pairs") && result.at("pairs").is_array() &&
                !result.at("pairs").empty() && parent_id == 0) {
                throw std::runtime_error("ECS snapshot contains an unsupported pair on " +
                                         std::to_string(local_entity_id) + ": " +
                                         result.at("pairs").dump());
            }
            // Restore applies the validated logical relation after all entity
            // components exist, so Flecs pair spellings never become part of
            // the public snapshot ABI.
            result.erase("pairs");
        }
        for (auto &result : results) {
            if (!result.contains("components") || !result.at("components").is_object()) {
                throw std::runtime_error("Flecs SimObject snapshot is missing its component map");
            }
            std::vector<std::string> derived_identity_components;
            const std::uint64_t local_entity_id = result.at("id").get<std::uint64_t>();
            for (auto &[component_name, component_value] : result.at("components").items()) {
                if (component_name == "(Identifier,Name)" ||
                    component_name == "(flecs.core.Identifier,flecs.core.Name)") {
                    derived_identity_components.push_back(component_name);
                    continue;
                }
                if (component_name == "Missile" && component_value.is_null()) {
                    const auto *missile = kernel.ecs.entity(local_entity_id).get<Missile>();
                    if (missile == nullptr) {
                        throw std::runtime_error(
                            "Flecs Missile component disappeared during snapshot");
                    }
                    component_value = encode_missile(*missile);
                    continue;
                }
                if (component_name == "SystemHealth" && component_value.is_null()) {
                    const auto *health = kernel.ecs.entity(local_entity_id).get<SystemHealth>();
                    if (health == nullptr) {
                        throw std::runtime_error(
                            "Flecs SystemHealth component disappeared during snapshot");
                    }
                    component_value = encode_system_health(*health);
                    continue;
                }
                if (component_name == "ComponentDamageState" && component_value.is_null()) {
                    const auto *damage =
                        kernel.ecs.entity(local_entity_id).get<ComponentDamageState>();
                    if (damage == nullptr) {
                        throw std::runtime_error(
                            "Flecs ComponentDamageState disappeared during snapshot");
                    }
                    component_value = encode_component_damage(*damage);
                    continue;
                }
                if (component_name == "HitboxConfig" && component_value.is_null()) {
                    const auto *config = kernel.ecs.entity(local_entity_id).get<HitboxConfig>();
                    if (config == nullptr) {
                        throw std::runtime_error("Flecs HitboxConfig disappeared during snapshot");
                    }
                    component_value = encode_hitbox_config(*config);
                    continue;
                }
                if (component_name == "AircraftVulnerabilityProfile" && component_value.is_null()) {
                    const auto *profile =
                        kernel.ecs.entity(local_entity_id).get<AircraftVulnerabilityProfile>();
                    if (profile == nullptr) {
                        throw std::runtime_error(
                            "Flecs AircraftVulnerabilityProfile disappeared during snapshot");
                    }
                    component_value = encode_aircraft_vulnerability(*profile);
                    continue;
                }
                if (component_value.is_null()) {
                    unreflected_components.push_back(component_name);
                }
            }
            for (const auto &component_name : derived_identity_components) {
                result.at("components").erase(component_name);
            }
            std::string unresolved_detail;
            if (!encode_entity_references(result.at("components"), entity_keys, {},
                                          &unresolved_detail)) {
                throw std::runtime_error("ECS snapshot contains an unresolved entity reference (" +
                                         unresolved_detail + ") on entity '" +
                                         result.value("name", "") + "'");
            }
            result.erase("id");
        }
        std::sort(results.begin(), results.end(), [](const auto &lhs, const auto &rhs) {
            const std::string lhs_name = lhs.value("name", "");
            const std::string rhs_name = rhs.value("name", "");
            if (lhs_name != rhs_name) {
                return lhs_name < rhs_name;
            }
            return lhs.dump() < rhs.dump();
        });
        std::sort(child_of.begin(), child_of.end(), [](const auto &lhs, const auto &rhs) {
            if (lhs.at("parent") != rhs.at("parent")) {
                return lhs.at("parent") < rhs.at("parent");
            }
            return lhs.at("child") < rhs.at("child");
        });
        document["child_of"] = std::move(child_of);
    }
    if (!unreflected_components.empty()) {
        std::sort(unreflected_components.begin(), unreflected_components.end());
        unreflected_components.erase(
            std::unique(unreflected_components.begin(), unreflected_components.end()),
            unreflected_components.end());
        std::ostringstream detail;
        detail << "Flecs components are not reflected for durable state transfer:";
        for (const auto &component : unreflected_components) {
            detail << ' ' << component;
        }
        throw std::runtime_error(detail.str());
    }
    return document.dump();
}

bool validate_component_payload(ecs_world_t *world, std::string_view component_name,
                                const nlohmann::json &decoded_value) {
    if (world == nullptr) {
        return false;
    }
    if (component_name == "Missile") {
        Missile value{};
        return decode_missile(decoded_value, &value);
    }
    if (component_name == "SystemHealth") {
        SystemHealth value;
        return decode_system_health(decoded_value, &value);
    }
    if (component_name == "ComponentDamageState") {
        ComponentDamageState value;
        return decode_component_damage(decoded_value, &value);
    }
    if (component_name == "HitboxConfig") {
        HitboxConfig value;
        return decode_hitbox_config(decoded_value, &value);
    }
    if (component_name == "AircraftVulnerabilityProfile") {
        AircraftVulnerabilityProfile value;
        return decode_aircraft_vulnerability(decoded_value, &value);
    }
    const std::string name(component_name);
    const ecs_entity_t component_id = ecs_lookup(world, name.c_str());
    const ecs_type_info_t *type_info =
        component_id == 0 ? nullptr : ecs_get_type_info(world, component_id);
    if (type_info == nullptr || type_info->size == 0 || decoded_value.is_null()) {
        return false;
    }
    void *candidate = ecs_value_new(world, component_id);
    if (candidate == nullptr) {
        return false;
    }
    ecs_from_json_desc_t descriptor{};
    descriptor.strict = true;
    const std::string value_json = flecs_json_value(decoded_value);
    const char *end =
        ecs_ptr_from_json(world, component_id, candidate, value_json.c_str(), &descriptor);
    bool valid = end != nullptr;
    if (valid) {
        while (*end != '\0' && std::isspace(static_cast<unsigned char>(*end))) {
            ++end;
        }
        valid = *end == '\0';
    }
    if (ecs_value_free(world, component_id, candidate) != 0) {
        valid = false;
    }
    return valid;
}

bool SimulationKernelStateOwnerBridge::restore_world(SimulationKernel &kernel,
                                                     const std::vector<std::uint8_t> &payload) {
    // Validate and stage the complete document before mutating the live ECS.
    // A defensive pre-image lets the fault-injection edges below restore the
    // exact source world if Flecs rejects a mutation after deletion/creation.
    static thread_local bool rollback_in_progress = false;
    const bool rollback_enabled = !rollback_in_progress;
    std::vector<std::uint8_t> before_payload;
    if (rollback_enabled) {
        try {
            before_payload = bytes(serialize_world(kernel));
        } catch (...) {
            return false;
        }
    }
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_restore_world");
    const bool restored = [&]() {
        const std::string json = text(payload);
        nlohmann::json document;
        try {
            document = nlohmann::json::parse(json);
        } catch (const nlohmann::json::exception &) {
            return false;
        }
        if (!only_object_keys(document, {"results", "child_of"}) || !document.contains("results") ||
            !document.at("results").is_array() || !document.contains("child_of") ||
            !document.at("child_of").is_array()) {
            return false;
        }
        std::unordered_map<std::string, std::uint64_t> logical_entities;
        logical_entities.reserve(document.at("results").size());
        std::uint64_t logical_entity_id = 1;
        for (const auto &result : document.at("results")) {
            if (!only_object_keys(result, {"name", "tags", "pairs", "components"}) ||
                !result.contains("name") || !result.at("name").is_string() ||
                result.at("name").get_ref<const std::string &>().empty() ||
                !result.contains("components") || !result.at("components").is_object() ||
                !result.contains("tags") || !result.at("tags").is_array() ||
                (result.contains("pairs") &&
                 (!result.at("pairs").is_array() || !result.at("pairs").empty()))) {
                return false;
            }
            const bool sim_object_tagged =
                std::any_of(result.at("tags").begin(), result.at("tags").end(),
                            [](const auto &tag) { return tag.is_string() && tag == "SimObject"; });
            if (!sim_object_tagged) {
                return false;
            }
            if (!logical_entities
                     .emplace(result.at("name").get_ref<const std::string &>(), logical_entity_id++)
                     .second) {
                return false;
            }
            // Restoring the transferred SimObject set must not silently reuse or
            // mutate a static/database entity that merely shares a logical name.
            // Such an entity is outside the snapshot pre-image and therefore
            // cannot be compensated by the rollback serializer.
            const auto existing =
                kernel.ecs.lookup(result.at("name").get_ref<const std::string &>().c_str());
            if (existing != 0 && !kernel.ecs.entity(existing).has<SimObject>()) {
                return false;
            }
        }
        std::unordered_map<std::string, std::string> child_parents;
        if (document.contains("child_of")) {
            for (const auto &relation : document.at("child_of")) {
                if (!only_object_keys(relation, {"child", "parent"}) ||
                    !relation.contains("child") || !relation.contains("parent") ||
                    !relation.at("child").is_string() || !relation.at("parent").is_string() ||
                    !logical_entities.contains(relation.at("child").get<std::string>()) ||
                    !logical_entities.contains(relation.at("parent").get<std::string>())) {
                    return false;
                }
                const auto child = relation.at("child").get<std::string>();
                const auto parent = relation.at("parent").get<std::string>();
                if (child == parent || !child_parents.emplace(child, parent).second) {
                    return false;
                }
            }
            for (const auto &[start, unused] : child_parents) {
                static_cast<void>(unused);
                std::set<std::string> seen;
                std::string current = start;
                for (;;) {
                    const auto found = child_parents.find(current);
                    if (found == child_parents.end()) {
                        break;
                    }
                    if (!seen.insert(current).second) {
                        return false;
                    }
                    current = found->second;
                }
            }
        }
        for (const auto &result : document.at("results")) {
            if (result.contains("tags")) {
                for (const auto &tag : result.at("tags")) {
                    if (!tag.is_string()) {
                        return false;
                    }
                    const ecs_entity_t tag_id =
                        ecs_lookup(kernel.ecs.c_ptr(), tag.get_ref<const std::string &>().c_str());
                    if (tag_id == 0 || !ecs_id_is_tag(kernel.ecs.c_ptr(), tag_id)) {
                        return false;
                    }
                }
            }
            for (const auto &[component_name, component_value] : result.at("components").items()) {
                auto decoded_value = component_value;
                if (!decode_entity_references(decoded_value, logical_entities) ||
                    !validate_component_payload(kernel.ecs.c_ptr(), component_name,
                                                decoded_value)) {
                    return false;
                }
            }
        }
        kernel.ecs.delete_with<SimObject>();
        std::vector<flecs::entity> entities;
        entities.reserve(document.at("results").size());
        std::unordered_map<std::string, std::uint64_t> target_entities;
        target_entities.reserve(document.at("results").size());
        for (auto &result : document.at("results")) {
            if (!result.contains("name") || !result.at("name").is_string() ||
                result.at("name").get_ref<const std::string &>().empty()) {
                return false;
            }
            const auto &name = result.at("name").get_ref<const std::string &>();
            auto entity = kernel.ecs.entity(name.c_str());
            if (!target_entities.emplace(name, entity.id()).second) {
                return false;
            }
            entities.push_back(entity);
        }
        ecs_from_json_desc_t descriptor{};
        descriptor.strict = true;
        for (std::size_t index = 0; index < entities.size(); ++index) {
            const auto &result = document.at("results").at(index);
            const auto entity = entities[index];
            if (result.contains("tags")) {
                if (!result.at("tags").is_array()) {
                    return false;
                }
                for (const auto &tag : result.at("tags")) {
                    if (!tag.is_string()) {
                        return false;
                    }
                    const ecs_entity_t tag_id =
                        ecs_lookup(kernel.ecs.c_ptr(), tag.get_ref<const std::string &>().c_str());
                    if (tag_id == 0 || !ecs_id_is_tag(kernel.ecs.c_ptr(), tag_id)) {
                        return false;
                    }
                    ecs_add_id(kernel.ecs.c_ptr(), entity.id(), tag_id);
                }
            }
            if (!result.contains("components") || !result.at("components").is_object()) {
                return false;
            }
            for (const auto &[component_name, component_value] : result.at("components").items()) {
                auto decoded_value = component_value;
                if (!decode_entity_references(decoded_value, target_entities)) {
                    return false;
                }
                if (component_name == "Missile") {
                    Missile missile{};
                    if (!decode_missile(decoded_value, &missile)) {
                        return false;
                    }
                    entity.set<Missile>(missile);
                    continue;
                }
                if (component_name == "SystemHealth") {
                    SystemHealth health;
                    if (!decode_system_health(decoded_value, &health)) {
                        return false;
                    }
                    entity.set<SystemHealth>(health);
                    continue;
                }
                if (component_name == "ComponentDamageState") {
                    ComponentDamageState damage;
                    if (!decode_component_damage(decoded_value, &damage)) {
                        return false;
                    }
                    entity.set<ComponentDamageState>(damage);
                    continue;
                }
                if (component_name == "HitboxConfig") {
                    HitboxConfig config;
                    if (!decode_hitbox_config(decoded_value, &config)) {
                        return false;
                    }
                    entity.set<HitboxConfig>(config);
                    continue;
                }
                if (component_name == "AircraftVulnerabilityProfile") {
                    AircraftVulnerabilityProfile profile;
                    if (!decode_aircraft_vulnerability(decoded_value, &profile)) {
                        return false;
                    }
                    entity.set<AircraftVulnerabilityProfile>(profile);
                    continue;
                }
                const ecs_entity_t component_id =
                    ecs_lookup(kernel.ecs.c_ptr(), component_name.c_str());
                const ecs_type_info_t *type_info =
                    component_id == 0 ? nullptr
                                      : ecs_get_type_info(kernel.ecs.c_ptr(), component_id);
                if (type_info == nullptr || type_info->size == 0 || component_value.is_null()) {
                    return false;
                }
                void *destination = ecs_ensure_id(kernel.ecs.c_ptr(), entity.id(), component_id);
                if (destination == nullptr) {
                    return false;
                }
                // Flecs' JSON expression reader interprets exponent notation such
                // as 1e-6 as an arithmetic expression on this supported version.
                // Expand floating-point values to exact fixed notation before the
                // strict decode so source values remain bit-representable.
                const std::string value_json = flecs_json_value(decoded_value);
                const char *end = ecs_ptr_from_json(kernel.ecs.c_ptr(), component_id, destination,
                                                    value_json.c_str(), &descriptor);
                if (end == nullptr) {
                    return false;
                }
                while (*end != '\0' && std::isspace(static_cast<unsigned char>(*end))) {
                    ++end;
                }
                if (*end != '\0') {
                    return false;
                }
                ecs_modified_id(kernel.ecs.c_ptr(), entity.id(), component_id);
            }
        }
        if (document.contains("child_of")) {
            for (const auto &relation : document.at("child_of")) {
                const auto child =
                    entities.at(logical_entities.at(relation.at("child").get<std::string>()) - 1);
                const auto parent =
                    entities.at(logical_entities.at(relation.at("parent").get<std::string>()) - 1);
                child.child_of(parent);
            }
        }
        kernel.world_state_mutated_ = true;
        return true;
    }();
    if (!restored && rollback_enabled) {
        rollback_in_progress = true;
        lock.unlock();
        try {
            (void)restore_world(kernel, before_payload);
        } catch (...) {
            // Keep the original failure; the host will quarantine the owner
            // if the compensating restore cannot be proven.
        }
        rollback_in_progress = false;
    }
    return restored;
}

std::string SimulationKernelStateOwnerBridge::serialize_rng(SimulationKernel &kernel) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_export_rng");
    std::ostringstream output;
    output << "rng.v2\n" << kernel.rng_draw_position_ << '\n' << kernel.rng;
    return output.str();
}

bool SimulationKernelStateOwnerBridge::restore_rng(SimulationKernel &kernel,
                                                   const std::vector<std::uint8_t> &payload) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_restore_rng");
    DecodedRngState restored;
    if (!decode_rng_state(text(payload), &restored)) {
        return false;
    }
    kernel.rng = restored.engine;
    kernel.rng_draw_position_ = restored.draw_position;
    kernel.world_state_mutated_ = true;
    return true;
}

std::string SimulationKernelStateOwnerBridge::serialize_clock(SimulationKernel &kernel,
                                                              std::uint64_t step_sequence,
                                                              std::uint64_t barrier_sequence) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_export_clock");
    const ecs_world_info_t *info = ecs_get_world_info(kernel.ecs.c_ptr());
    const double world_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    std::ostringstream output;
    output.precision(std::numeric_limits<double>::max_digits10);
    output << "clock.v2\n"
           << world_time << '\n'
           << kernel.time_step << '\n'
           << step_sequence << '\n'
           << barrier_sequence << '\n';
    return output.str();
}

bool SimulationKernelStateOwnerBridge::restore_clock(SimulationKernel &kernel,
                                                     const std::vector<std::uint8_t> &payload) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_restore_clock");
    DecodedClockState restored;
    if (!decode_clock_state(text(payload), &restored)) {
        return false;
    }
    ecs_reset_clock(kernel.ecs.c_ptr());
    if (restored.world_time > 0.0) {
        ecs_frame_begin(kernel.ecs.c_ptr(), static_cast<ecs_ftime_t>(restored.world_time));
        ecs_frame_end(kernel.ecs.c_ptr());
    }
    kernel.time_step = restored.time_step;
    kernel.world_state_mutated_ = true;
    return true;
}

std::string SimulationKernelStateOwnerBridge::serialize_episode_barrier(
    const RuntimeEpisodeCoordinatorSnapshot &barrier) {
    if (barrier.phase != RuntimeEpisodePhase::ReplacementBarrier ||
        !barrier.episode.well_formed() || barrier.barrier_sequence == 0 ||
        !barrier.snapshot_id.well_formed() || !is_lower_hex_sha256(barrier.snapshot_sha256)) {
        throw std::runtime_error("episode owner requires a well-formed host replacement barrier");
    }
    std::ostringstream output;
    output << "episode-barrier.v2\n"
           << barrier.episode.world.incarnation.host.host_id.high << '\n'
           << barrier.episode.world.incarnation.host.host_id.low << '\n'
           << barrier.episode.world.incarnation.host.boot_id.high << '\n'
           << barrier.episode.world.incarnation.host.boot_id.low << '\n'
           << barrier.episode.world.incarnation.incarnation_epoch << '\n'
           << barrier.episode.world.world_slot << '\n'
           << barrier.episode.world.world_generation << '\n'
           << barrier.episode.episode_id.high << '\n'
           << barrier.episode.episode_id.low << '\n'
           << barrier.episode.episode_generation << '\n'
           << static_cast<unsigned int>(barrier.phase) << '\n'
           << barrier.step_sequence << '\n'
           << barrier.barrier_sequence << '\n'
           << barrier.snapshot_id.high << '\n'
           << barrier.snapshot_id.low << '\n'
           << barrier.snapshot_sha256 << '\n';
    return output.str();
}

std::string SimulationKernelStateOwnerBridge::serialize_composition(SimulationKernel &kernel) {
    return std::string("composition.v2\n") + kernel.requested_composition_sha256() + "\n" +
           kernel.resolved_composition_sha256() + "\n" +
           kernel.executable_composition_graph_sha256() + "\n";
}

const std::set<std::string_view> &delayed_component_owners() {
    static const std::set<std::string_view> components{
        "PendingMovementCommand", "PendingActionCommand", "PendingMissionCommand",
        "MissionCommandPendingQueue", "ComponentDamageState"};
    return components;
}

const std::set<std::string_view> &command_component_owners() {
    static const std::set<std::string_view> components{
        "MovementCommand", "ActionCommand", "MissionCommandControlState",
        "MissionCommand",  "CommandLink",   "CommandLag",
        "LaggedCommand",   "PilotAction",   "TaskOrder",
        "LeaderIntent",    "PilotReport",   "PilotWeaponReleaseState"};
    return components;
}

const std::set<std::string_view> &episode_component_owners() {
    static const std::set<std::string_view> components{"Score",
                                                       "Health",
                                                       "GroundState",
                                                       "PlatformDamageState",
                                                       "AircraftDamageState",
                                                       "StructuralBreakupState",
                                                       "Lifetime"};
    return components;
}

std::string component_subset_schema(RuntimeStateCategory category) {
    switch (category) {
    case RuntimeStateCategory::DelayedEventsQueues:
        return "delayed-owner.v2";
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return "command-owner.v2";
    case RuntimeStateCategory::EpisodeRewardTermination:
        return "episode-owner.v3";
    default:
        throw std::runtime_error("state category has no component subset schema");
    }
}

const std::set<std::string_view> &component_subset_owners(RuntimeStateCategory category) {
    switch (category) {
    case RuntimeStateCategory::DelayedEventsQueues:
        return delayed_component_owners();
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return command_component_owners();
    case RuntimeStateCategory::EpisodeRewardTermination:
        return episode_component_owners();
    default:
        throw std::runtime_error("state category has no component subset owner");
    }
}

std::string serialize_component_subset(SimulationKernel &kernel, RuntimeStateCategory category,
                                       std::uint64_t step_sequence,
                                       std::uint64_t barrier_sequence) {
    auto document =
        nlohmann::json::parse(SimulationKernelStateOwnerBridge::serialize_world(kernel));
    const auto &owners = component_subset_owners(category);
    for (auto &result : document.at("results")) {
        auto &components = result.at("components");
        for (auto iterator = components.begin(); iterator != components.end();) {
            if (!owners.contains(iterator.key())) {
                iterator = components.erase(iterator);
            } else {
                ++iterator;
            }
        }
        result.erase("tags");
    }
    // Component-subset owners intentionally carry only their selected
    // components; hierarchy closure belongs to the ECS truth owner.
    document.erase("child_of");
    document["owner_schema"] = component_subset_schema(category);
    document["step_sequence"] = step_sequence;
    document["barrier_sequence"] = barrier_sequence;
    return document.dump();
}

bool decode_component_subset_metadata(std::string_view payload, RuntimeStateCategory category,
                                      std::uint64_t expected_step_sequence,
                                      std::uint64_t expected_barrier_sequence);

std::string serialize_episode_owner(SimulationKernel &kernel,
                                    const RuntimeEpisodeCoordinatorSnapshot &barrier) {
    auto document = nlohmann::json::parse(
        serialize_component_subset(kernel, RuntimeStateCategory::EpisodeRewardTermination,
                                   barrier.step_sequence, barrier.barrier_sequence));
    document["episode_barrier"] =
        SimulationKernelStateOwnerBridge::serialize_episode_barrier(barrier);
    return document.dump();
}

bool decode_episode_owner(std::string_view payload, const RuntimeStateCensusEntry &entry,
                          RuntimeEpisodeCoordinatorSnapshot *barrier) {
    if (barrier == nullptr ||
        !decode_component_subset_metadata(payload, RuntimeStateCategory::EpisodeRewardTermination,
                                          entry.step_sequence, entry.barrier_sequence)) {
        return false;
    }
    try {
        const auto document = nlohmann::json::parse(payload);
        return document.contains("episode_barrier") && document.at("episode_barrier").is_string() &&
               decode_episode_barrier(document.at("episode_barrier").get_ref<const std::string &>(),
                                      barrier);
    } catch (const nlohmann::json::exception &) {
        return false;
    }
}

bool decode_component_subset_metadata(std::string_view payload, RuntimeStateCategory category,
                                      std::uint64_t expected_step_sequence,
                                      std::uint64_t expected_barrier_sequence) {
    try {
        const auto document = nlohmann::json::parse(payload);
        const bool episode = category == RuntimeStateCategory::EpisodeRewardTermination;
        const bool keys_valid =
            episode ? only_object_keys(document, {"results", "owner_schema", "step_sequence",
                                                  "barrier_sequence", "episode_barrier"})
                    : only_object_keys(document, {"results", "owner_schema", "step_sequence",
                                                  "barrier_sequence"});
        return keys_valid && document.size() == (episode ? 5 : 4) && document.contains("results") &&
               document.at("results").is_array() &&
               document.value("owner_schema", "") == component_subset_schema(category) &&
               document.value("step_sequence", std::uint64_t{0}) == expected_step_sequence &&
               document.value("barrier_sequence", std::uint64_t{0}) == expected_barrier_sequence;
    } catch (const nlohmann::json::exception &) {
        return false;
    }
}

bool restore_component_subset(SimulationKernel &kernel, RuntimeStateCategory category,
                              const std::vector<std::uint8_t> &payload,
                              std::uint64_t expected_step_sequence,
                              std::uint64_t expected_barrier_sequence) {
    static thread_local bool rollback_in_progress = false;
    const bool rollback_enabled = !rollback_in_progress;
    std::vector<std::uint8_t> before_payload;
    if (rollback_enabled) {
        try {
            before_payload = bytes(serialize_component_subset(
                kernel, category, expected_step_sequence, expected_barrier_sequence));
        } catch (...) {
            return false;
        }
    }
    bool restored = false;
    try {
        restored = [&]() {
            auto lease = kernel.acquire_world_lease();
            auto &ecs = lease.world();
            const std::string encoded = text(payload);
            if (!decode_component_subset_metadata(encoded, category, expected_step_sequence,
                                                  expected_barrier_sequence)) {
                return false;
            }
            const auto document = nlohmann::json::parse(encoded);
            const auto &owners = component_subset_owners(category);
            std::unordered_map<std::string, std::uint64_t> target_entities;
            for (const auto &result : document.at("results")) {
                if (!only_object_keys(result, {"name", "pairs", "components"}) ||
                    !result.contains("name") || !result.at("name").is_string() ||
                    !result.contains("components") || !result.at("components").is_object() ||
                    (result.contains("pairs") && !result.at("pairs").empty())) {
                    return false;
                }
                for (auto iterator = result.at("components").begin();
                     iterator != result.at("components").end(); ++iterator) {
                    if (!owners.contains(iterator.key())) {
                        return false;
                    }
                }
                const auto &name = result.at("name").get_ref<const std::string &>();
                const auto entity = ecs.lookup(name.c_str());
                if (!entity.is_valid() || !entity.has<SimObject>() ||
                    !target_entities.emplace(name, entity.id()).second) {
                    return false;
                }
            }
            ecs_from_json_desc_t descriptor{};
            descriptor.strict = true;
            for (const auto &result : document.at("results")) {
                const auto &name = result.at("name").get_ref<const std::string &>();
                const auto entity = ecs.entity(target_entities.at(name));
                const auto &components = result.at("components");
                for (const auto component_name : owners) {
                    const ecs_entity_t component_id =
                        ecs_lookup(ecs.c_ptr(), std::string(component_name).c_str());
                    if (component_id == 0) {
                        return false;
                    }
                    if (!components.contains(std::string(component_name))) {
                        ecs_remove_id(ecs.c_ptr(), entity.id(), component_id);
                        continue;
                    }
                    auto decoded_value = components.at(std::string(component_name));
                    if (!decode_entity_references(decoded_value, target_entities)) {
                        return false;
                    }
                    if (component_name == "ComponentDamageState") {
                        ComponentDamageState damage;
                        if (!decode_component_damage(decoded_value, &damage)) {
                            return false;
                        }
                        entity.set<ComponentDamageState>(damage);
                        continue;
                    }
                    const ecs_type_info_t *type_info = ecs_get_type_info(ecs.c_ptr(), component_id);
                    void *destination = ecs_ensure_id(ecs.c_ptr(), entity.id(), component_id);
                    if (type_info == nullptr || type_info->size == 0 || destination == nullptr) {
                        return false;
                    }
                    const std::string value_json = flecs_json_value(decoded_value);
                    const char *end = ecs_ptr_from_json(ecs.c_ptr(), component_id, destination,
                                                        value_json.c_str(), &descriptor);
                    if (end == nullptr) {
                        return false;
                    }
                    while (*end != '\0' && std::isspace(static_cast<unsigned char>(*end))) {
                        ++end;
                    }
                    if (*end != '\0') {
                        return false;
                    }
                    ecs_modified_id(ecs.c_ptr(), entity.id(), component_id);
                }
            }
            return true;
        }();
    } catch (...) {
        restored = false;
    }
    if (!restored && rollback_enabled) {
        rollback_in_progress = true;
        try {
            (void)restore_component_subset(kernel, category, before_payload, expected_step_sequence,
                                           expected_barrier_sequence);
        } catch (...) {
        }
        rollback_in_progress = false;
    }
    return restored;
}

std::vector<std::uint8_t> export_category_payload(SimulationKernel &kernel,
                                                  RuntimeStateCategory category,
                                                  const RuntimeStateOwnerExportContext &context) {
    const auto &barrier = context.barrier_snapshot;
    switch (category) {
    case RuntimeStateCategory::CompositionProviderSystemGraph:
        return bytes(SimulationKernelStateOwnerBridge::serialize_composition(kernel));
    case RuntimeStateCategory::EcsComponentTruth:
        return bytes(SimulationKernelStateOwnerBridge::serialize_world(kernel));
    case RuntimeStateCategory::RngState:
        return bytes(SimulationKernelStateOwnerBridge::serialize_rng(kernel));
    case RuntimeStateCategory::ClockCadence:
        return bytes(SimulationKernelStateOwnerBridge::serialize_clock(
            kernel, barrier.step_sequence, barrier.barrier_sequence));
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return bytes(serialize_component_subset(kernel, category, barrier.step_sequence,
                                                barrier.barrier_sequence));
    case RuntimeStateCategory::EpisodeRewardTermination:
        return bytes(serialize_episode_owner(kernel, barrier));
    case RuntimeStateCategory::PythonLoaderControllerCaches:
    case RuntimeStateCategory::BackendDeviceAllocationsLeases:
    case RuntimeStateCategory::InFlightRequestsResults:
    case RuntimeStateCategory::ExternalSideEffects:
    case RuntimeStateCategory::DiagnosticsTelemetry:
        return bytes(explicit_policy_payload(kernel, category, context));
    }
    throw std::runtime_error("unsupported state category");
}

bool apply_staged(StagedImport &staged) {
    switch (staged.category) {
    case RuntimeStateCategory::EcsComponentTruth:
        return SimulationKernelStateOwnerBridge::restore_world(*staged.kernel,
                                                               staged.source_payload);
    case RuntimeStateCategory::RngState:
        return SimulationKernelStateOwnerBridge::restore_rng(*staged.kernel, staged.source_payload);
    case RuntimeStateCategory::ClockCadence:
        return SimulationKernelStateOwnerBridge::restore_clock(*staged.kernel,
                                                               staged.source_payload);
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return restore_component_subset(*staged.kernel, staged.category, staged.source_payload,
                                        staged.step_sequence, staged.barrier_sequence);
    case RuntimeStateCategory::EpisodeRewardTermination:
        return staged.episode_barrier_validated &&
               restore_component_subset(*staged.kernel, staged.category, staged.source_payload,
                                        staged.step_sequence, staged.barrier_sequence);
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        if (!staged.rederive_python_caches) {
            staged.python_caches_applied = true;
            return true;
        }
        staged.python_caches_applied = staged.rederive_python_caches();
        return staged.python_caches_applied;
    default:
        return true;
    }
}

bool abort_staged(StagedImport &staged) {
    switch (staged.category) {
    case RuntimeStateCategory::EcsComponentTruth:
        return SimulationKernelStateOwnerBridge::restore_world(*staged.kernel,
                                                               staged.before_payload);
    case RuntimeStateCategory::RngState:
        return SimulationKernelStateOwnerBridge::restore_rng(*staged.kernel, staged.before_payload);
    case RuntimeStateCategory::ClockCadence:
        return SimulationKernelStateOwnerBridge::restore_clock(*staged.kernel,
                                                               staged.before_payload);
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        return restore_component_subset(*staged.kernel, staged.category, staged.before_payload,
                                        staged.step_sequence, staged.barrier_sequence);
    case RuntimeStateCategory::EpisodeRewardTermination:
        return staged.episode_barrier_validated &&
               restore_component_subset(*staged.kernel, staged.category, staged.before_payload,
                                        staged.step_sequence, staged.barrier_sequence);
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        if (staged.rollback_python_caches &&
            !staged.rollback_python_caches(staged.before_payload)) {
            return false;
        }
        staged.python_caches_applied = false;
        return true;
    default:
        return true;
    }
}

RuntimeStateOwnerImportTransactionPhase recover_staged(StagedImport &staged) {
    std::vector<std::uint8_t> current;
    switch (staged.category) {
    case RuntimeStateCategory::EcsComponentTruth:
        current = bytes(SimulationKernelStateOwnerBridge::serialize_world(*staged.kernel));
        break;
    case RuntimeStateCategory::RngState:
        current = bytes(SimulationKernelStateOwnerBridge::serialize_rng(*staged.kernel));
        break;
    case RuntimeStateCategory::ClockCadence:
        current = bytes(SimulationKernelStateOwnerBridge::serialize_clock(
            *staged.kernel, staged.step_sequence, staged.barrier_sequence));
        break;
    case RuntimeStateCategory::DelayedEventsQueues:
    case RuntimeStateCategory::CommandsLinksPendingIntent:
        current = bytes(serialize_component_subset(*staged.kernel, staged.category,
                                                   staged.step_sequence, staged.barrier_sequence));
        break;
    case RuntimeStateCategory::EpisodeRewardTermination:
        current = bytes(serialize_episode_owner(*staged.kernel, staged.episode_barrier));
        break;
    case RuntimeStateCategory::PythonLoaderControllerCaches:
        if (staged.recover_python_caches) {
            return staged.recover_python_caches(staged.before_payload);
        }
        return staged.python_caches_applied ? RuntimeStateOwnerImportTransactionPhase::Committed
                                            : RuntimeStateOwnerImportTransactionPhase::Aborted;
    default:
        return RuntimeStateOwnerImportTransactionPhase::Committed;
    }
    if (current == staged.source_payload) {
        return RuntimeStateOwnerImportTransactionPhase::Committed;
    }
    if (current == staged.before_payload) {
        return RuntimeStateOwnerImportTransactionPhase::Aborted;
    }
    return RuntimeStateOwnerImportTransactionPhase::Ambiguous;
}

std::shared_ptr<RuntimeStateTransferOwnerRegistry>
SimulationKernelStateOwnerBridge::create_registry(SimulationKernelStateOwnerRegistryConfig config) {
    if (config.kernel == nullptr || config.journal == nullptr ||
        config.transaction_namespace.empty() ||
        // A host-bound integration registry must carry both an immutable
        // resource identity and a logical clock sampler.  Host-neutral tests
        // may omit both, but a partially bound registry is rejected.
        config.bound_resource_identity.well_formed() != static_cast<bool>(config.sample_tick) ||
        (config.bound_resource_identity.well_formed() &&
         (!config.rederive_python_caches || !config.snapshot_python_caches ||
          !config.rollback_python_caches || !config.recover_python_caches))) {
        return {};
    }
    std::array<RuntimeStateOwnerAdapterRegistration, kRuntimeStateCategoryCount> registrations{};
    for (std::size_t index = 0; index < registrations.size(); ++index) {
        const auto rule = runtime_state_decoder_replay_matrix()[index];
        auto &registration = registrations[index];
        registration.category = rule.category;
        registration.owner_id = std::string(rule.owner_id);
        registration.schema_id = std::string(rule.schema_id);
        registration.migration_sha256 = std::string(rule.migration_sha256);
        registration.export_state = [kernel = config.kernel, category = rule.category](
                                        const RuntimeStateTransferProfile &profile,
                                        const RuntimeIncarnationRef &source_slot,
                                        const RuntimeStateOwnerExportContext &context) {
            const auto &barrier = context.barrier_snapshot;
            const auto policy = std::find_if(
                profile.rows.begin(), profile.rows.end(),
                [category](const auto &candidate) { return candidate.category == category; });
            if (policy == profile.rows.end()) {
                throw std::runtime_error("state profile category is missing");
            }
            if (category == RuntimeStateCategory::CompositionProviderSystemGraph &&
                kernel->resolved_composition_sha256() != profile.source_plan_sha256) {
                throw std::runtime_error(
                    "source kernel composition does not match the admitted plan");
            }
            if (!barrier.episode.well_formed() ||
                barrier.episode.world.incarnation != source_slot ||
                barrier.episode.world.world_slot != 0 ||
                barrier.phase != RuntimeEpisodePhase::ReplacementBarrier ||
                barrier.step_sequence == 0 || barrier.barrier_sequence == 0) {
                throw std::runtime_error(
                    "owner export is not bound to the quiesced host episode barrier");
            }
            RuntimeStateOwnerArtifact artifact{
                .category = category,
                .schema_id = policy->schema_id,
                .schema_generation = kRuntimeStateTransferContractGeneration,
                .payload = export_category_payload(*kernel, category, context),
            };
            artifact.payload_sha256 = runtime_state_payload_sha256(artifact.payload);
            RuntimeStateCensusEntry entry{
                .category = category,
                .disposition = policy->disposition,
                .owner_id = policy->owner_id,
                .schema_id = policy->schema_id,
                .schema_generation = kRuntimeStateTransferContractGeneration,
                .rng_draw_position =
                    category == RuntimeStateCategory::RngState ? kernel->rng_draw_position_ : 0,
                .step_sequence = barrier.step_sequence,
                .barrier_sequence = barrier.barrier_sequence,
            };
            if (category == RuntimeStateCategory::InFlightRequestsResults) {
                entry.item_count = context.source_read_only_result_leases;
                entry.settled_item_count = context.source_read_only_result_leases;
                entry.sequence_high_watermark = barrier.step_sequence;
            }
            if (policy->disposition == RuntimeStateDisposition::Transfer) {
                entry.state_content_sha256 = artifact.payload_sha256;
                entry.canonical_payload = runtime_state_canonical_payload(entry);
                entry.canonical_payload_sha256 =
                    runtime_state_payload_sha256(entry.canonical_payload);
                entry.semantic_evidence_sha256 = replay_evidence(
                    runtime_state_category_name(category), artifact.payload_sha256, barrier);
            } else if (policy->disposition == RuntimeStateDisposition::Rederive ||
                       policy->disposition == RuntimeStateDisposition::Drain ||
                       policy->disposition == RuntimeStateDisposition::Cancel) {
                entry.semantic_evidence_sha256 = replay_evidence(
                    runtime_state_category_name(category), artifact.payload_sha256, barrier);
            }
            return RuntimeStateOwnerAdapterExport{.census_entry = std::move(entry),
                                                  .artifact = std::move(artifact)};
        };
        registration.migrate_previous = [](const RuntimeStateOwnerArtifact &source) {
            RuntimeStateOwnerArtifact migrated = source;
            migrated.schema_generation = kRuntimeStateTransferContractGeneration;
            // Generation 1 and 2 share the same category byte grammar. The
            // migration is an explicit reader promotion, not a byte rewrite;
            // schema-generation admission still prevents older generations.
            migrated.payload_sha256 = runtime_state_payload_sha256(migrated.payload);
            return migrated;
        };
        registration.import_state = [kernel = config.kernel, journal = config.journal,
                                     transaction_namespace = config.transaction_namespace,
                                     rederive_python_caches = config.rederive_python_caches,
                                     snapshot_python_caches = config.snapshot_python_caches,
                                     rollback_python_caches = config.rollback_python_caches,
                                     recover_python_caches = config.recover_python_caches,
                                     sample_tick = config.sample_tick, category = rule.category](
                                        const RuntimeStateTransferProfile &profile,
                                        const RuntimeIncarnationRef &source_slot,
                                        const RuntimeStateCensusEntry &entry,
                                        const RuntimeStateOwnerArtifact &source_artifact,
                                        const RuntimeStateOwnerArtifact &admitted_artifact,
                                        const RuntimeIdentity128 &candidate_identity) {
            auto staged = std::make_shared<StagedImport>();
            if (category == RuntimeStateCategory::CompositionProviderSystemGraph &&
                kernel->resolved_composition_sha256() != profile.target_plan_sha256) {
                throw std::runtime_error(
                    "target kernel composition does not match the admitted plan");
            }
            staged->kernel = kernel;
            staged->category = category;
            staged->rederive_python_caches = rederive_python_caches;
            staged->snapshot_python_caches = snapshot_python_caches;
            staged->rollback_python_caches = rollback_python_caches;
            staged->recover_python_caches = recover_python_caches;
            staged->source_payload = admitted_artifact.payload;
            staged->step_sequence = entry.step_sequence;
            staged->barrier_sequence = entry.barrier_sequence;
            staged->source_read_only_result_leases = entry.item_count;
            staged->cooperative_cancellation_acknowledged =
                category != RuntimeStateCategory::InFlightRequestsResults ||
                entry.item_count == entry.settled_item_count;
            if (category == RuntimeStateCategory::RngState) {
                DecodedRngState decoded;
                if (!decode_rng_state(text(admitted_artifact.payload), &decoded) ||
                    decoded.draw_position != entry.rng_draw_position) {
                    throw std::runtime_error(
                        "RNG owner payload does not match its census position");
                }
            } else if (category == RuntimeStateCategory::ClockCadence) {
                DecodedClockState decoded;
                if (!decode_clock_state(text(admitted_artifact.payload), &decoded) ||
                    decoded.step_sequence != entry.step_sequence ||
                    decoded.barrier_sequence != entry.barrier_sequence) {
                    throw std::runtime_error(
                        "clock owner payload does not match its native barrier");
                }
            } else if ((category == RuntimeStateCategory::DelayedEventsQueues ||
                        category == RuntimeStateCategory::CommandsLinksPendingIntent) &&
                       !decode_component_subset_metadata(text(admitted_artifact.payload), category,
                                                         entry.step_sequence,
                                                         entry.barrier_sequence)) {
                const auto diagnostic = nlohmann::json::parse(text(admitted_artifact.payload));
                throw std::runtime_error(
                    "component subset owner payload does not match its native barrier: " +
                    std::string(runtime_state_category_name(category)) +
                    " schema=" + diagnostic.value("owner_schema", "<missing>") +
                    " step=" + std::to_string(diagnostic.value("step_sequence", 0ULL)) +
                    " barrier=" + std::to_string(diagnostic.value("barrier_sequence", 0ULL)) +
                    " expected=" + std::to_string(entry.step_sequence) + "/" +
                    std::to_string(entry.barrier_sequence));
            } else if (category == RuntimeStateCategory::EpisodeRewardTermination) {
                RuntimeEpisodeCoordinatorSnapshot decoded;
                if (!decode_episode_owner(text(admitted_artifact.payload), entry, &decoded) ||
                    decoded.step_sequence != entry.step_sequence ||
                    decoded.barrier_sequence != entry.barrier_sequence) {
                    throw std::runtime_error(
                        "episode owner payload does not match its native barrier");
                }
                staged->episode_barrier_validated = true;
                staged->episode_barrier = decoded;
            } else if (category == RuntimeStateCategory::ExternalSideEffects) {
                const auto expected =
                    explicit_policy_payload(*kernel, category,
                                            {.barrier_snapshot = {
                                                 .step_sequence = entry.step_sequence,
                                                 .barrier_sequence = entry.barrier_sequence,
                                             }});
                if (text(admitted_artifact.payload) != expected) {
                    throw std::runtime_error("external side-effect owner payload is not the "
                                             "admitted not-applicable policy");
                }
            } else if (category == RuntimeStateCategory::PythonLoaderControllerCaches &&
                       !decode_rederive_policy(
                           text(admitted_artifact.payload), "python-mirror-rederive.v2",
                           {"disposition=rederive", "source_authority=native-ecs-command-episode",
                            "target_action=discard-and-rebuild", "cache_transfer=forbidden"},
                           entry.step_sequence, entry.barrier_sequence)) {
                throw std::runtime_error(
                    "Python mirror owner payload is not a valid discard-and-rebuild policy");
            } else if (category == RuntimeStateCategory::BackendDeviceAllocationsLeases &&
                       !decode_rederive_policy(
                           text(admitted_artifact.payload), "backend-resource-rederive.v2",
                           {"disposition=rederive", "backend_profile_id=cpu_exact.reference",
                            "raw_handle_transfer=forbidden",
                            "target_action=rehydrate-from-closed-plan",
                            "source_release=host-draining-after-publication"},
                           entry.step_sequence, entry.barrier_sequence)) {
                throw std::runtime_error(
                    "backend resource owner payload is not a valid CPU rehydrate policy");
            } else if (category == RuntimeStateCategory::InFlightRequestsResults &&
                       (entry.item_count != entry.settled_item_count ||
                        !decode_in_flight_policy(text(admitted_artifact.payload), entry.item_count,
                                                 entry.step_sequence, entry.barrier_sequence))) {
                throw std::runtime_error(
                    "in-flight owner payload is not a host-fenced drain receipt");
            } else if (category == RuntimeStateCategory::DiagnosticsTelemetry &&
                       !decode_rederive_policy(
                           text(admitted_artifact.payload), "telemetry-rederive.v2",
                           {"disposition=rederive", "continuity=reset-at-target"},
                           entry.step_sequence, entry.barrier_sequence)) {
                throw std::runtime_error(
                    "telemetry owner payload is not a valid target-rederive policy");
            }
            switch (category) {
            case RuntimeStateCategory::EcsComponentTruth:
                staged->before_payload =
                    bytes(SimulationKernelStateOwnerBridge::serialize_world(*kernel));
                break;
            case RuntimeStateCategory::RngState:
                staged->before_payload =
                    bytes(SimulationKernelStateOwnerBridge::serialize_rng(*kernel));
                break;
            case RuntimeStateCategory::ClockCadence:
                staged->before_payload = bytes(SimulationKernelStateOwnerBridge::serialize_clock(
                    *kernel, entry.step_sequence, entry.barrier_sequence));
                break;
            case RuntimeStateCategory::DelayedEventsQueues:
            case RuntimeStateCategory::CommandsLinksPendingIntent:
                staged->before_payload = bytes(serialize_component_subset(
                    *kernel, category, entry.step_sequence, entry.barrier_sequence));
                break;
            case RuntimeStateCategory::EpisodeRewardTermination:
                staged->before_payload =
                    bytes(serialize_episode_owner(*kernel, staged->episode_barrier));
                break;
            case RuntimeStateCategory::PythonLoaderControllerCaches:
                if (staged->snapshot_python_caches) {
                    staged->before_payload = staged->snapshot_python_caches();
                } else {
                    staged->before_payload =
                        export_category_payload(*kernel, category,
                                                {.barrier_snapshot = {
                                                     .step_sequence = entry.step_sequence,
                                                     .barrier_sequence = entry.barrier_sequence,
                                                 }});
                }
                break;
            default:
                // These rows are target-side no-op/rederive/drain policy
                // owners in the current CPU candidate. Persist their
                // explicit target policy as a non-empty pre-image so a
                // reopen never fabricates an empty rollback identity.
                staged->before_payload =
                    export_category_payload(*kernel, category,
                                            {.barrier_snapshot =
                                                 {
                                                     .step_sequence = entry.step_sequence,
                                                     .barrier_sequence = entry.barrier_sequence,
                                                 },
                                             .source_read_only_result_leases = entry.item_count,
                                             .cooperative_cancellation_acknowledged =
                                                 staged->cooperative_cancellation_acknowledged});
                break;
            }
            std::string candidate_payload_sha256 = admitted_artifact.payload_sha256;
            if (entry.disposition == RuntimeStateDisposition::Rederive) {
                const auto target_payload =
                    export_category_payload(*kernel, category,
                                            {.barrier_snapshot =
                                                 {
                                                     .step_sequence = entry.step_sequence,
                                                     .barrier_sequence = entry.barrier_sequence,
                                                 },
                                             .source_read_only_result_leases = entry.item_count,
                                             .cooperative_cancellation_acknowledged =
                                                 staged->cooperative_cancellation_acknowledged});
                candidate_payload_sha256 = runtime_state_payload_sha256(target_payload);
            }
            auto normalized = entry;
            normalized.schema_generation = kRuntimeStateTransferContractGeneration;
            if (entry.schema_generation != kRuntimeStateTransferContractGeneration) {
                normalized.canonical_payload = runtime_state_canonical_payload(normalized);
                normalized.canonical_payload_sha256 =
                    runtime_state_payload_sha256(normalized.canonical_payload);
            }
            RuntimeStateOwnerObservation observation{
                .category = category,
                .owner_id = entry.owner_id,
                .schema_id = entry.schema_id,
                .schema_generation = kRuntimeStateTransferContractGeneration,
                .source_entry_sha256 = runtime_state_census_entry_sha256(entry),
                .candidate_entry_sha256 = runtime_state_census_entry_sha256(normalized),
                .source_artifact_payload_sha256 = source_artifact.payload_sha256,
                .candidate_artifact_payload_sha256 = candidate_payload_sha256,
                .semantic_replay_sha256 = entry.semantic_evidence_sha256,
                .candidate_resource_identity = candidate_identity,
                .item_count = entry.item_count,
                .settled_item_count = entry.settled_item_count,
                .source_schema_generation = entry.schema_generation,
                .exact_schema_decoded = true,
            };
            const std::string id =
                transaction_id(transaction_namespace, profile, source_slot, entry,
                               candidate_identity, admitted_artifact.payload_sha256);
            // On reopen, recover the original pre-image from the durable
            // WAL record instead of treating the process's current target
            // bytes as a new pre-image.  A third state must remain
            // Ambiguous unless the owner callback can independently prove
            // the outcome.
            if (const auto existing = journal->latest(id);
                existing.status && existing.record &&
                !existing.record->pre_mutation_payload.empty()) {
                staged->before_payload = existing.record->pre_mutation_payload;
            }
            if (staged->before_payload.empty()) {
                throw std::runtime_error("owner import has no durable target pre-mutation image");
            }
            const std::string pre_mutation_sha256 =
                runtime_state_payload_sha256(staged->before_payload);
            auto transaction = std::make_shared<RuntimeDurableOwnerImportTransaction>(
                id, admitted_artifact.payload_sha256, journal,
                RuntimeStateOwnerImportRecoveryCallbacks{
                    .commit = [staged] { return apply_staged(*staged); },
                    .abort = [staged] { return abort_staged(*staged); },
                    .recover = [staged] { return recover_staged(*staged); },
                    .compensate = [staged] { return abort_staged(*staged); },
                    .verify =
                        [staged](RuntimeStateOwnerImportTransactionPhase expected) {
                            return recover_staged(*staged) == expected;
                        },
                    .sample_tick = sample_tick,
                },
                pre_mutation_sha256, staged->before_payload);
            return RuntimeStateOwnerAdapterImport{
                .observation = std::move(observation),
                .transaction = std::move(transaction),
            };
        };
    }
    auto registry = std::make_shared<RuntimeStateOwnerAdapterRegistry>(
        std::move(registrations), config.bound_resource_identity, config.kernel);
    return registry->registration_status() ? registry : nullptr;
}

} // namespace runtime::host::integration
