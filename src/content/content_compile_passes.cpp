#include "content/content_compile_passes.h"

#include <iterator>
#include <unordered_set>
#include <utility>

namespace content_compile {
namespace {

// Union of the I52-surveyed recognized top-level keys. Hardcoded here (the draft
// JSON is NOT read at build or run time, per the census red lines):
//   * 54 direct top-level keys read by parse_unit_json
//   * 52 keys read by parse_missile_tuning_json_fields on the top-level entry
//   * 3 semantic present-but-unread keys (ew_suite_ref / rcs / rcs_profile_ref)
// Underscore-prefixed annotation keys (_provenance, _real_world, _ground_schema,
// _deferred_runtime_claims, ...) are accepted separately by the '_' rule.
const std::unordered_set<std::string> &recognized_top_level_keys() {
    static const std::unordered_set<std::string> keys = {
        // --- 54 direct top-level keys (parse_unit_json) ---
        "type",
        "name",
        "mass_kg",
        "engine_ref",
        "engine",
        "mil_thrust_n",
        "ab_thrust_n",
        "sfc_mil",
        "sfc_ab",
        "bypass_ratio",
        "engine_tuning",
        "hardpoints",
        "default_loadout",
        "health",
        "sensor_ref",
        "sensor_refs",
        "sensor",
        "has_sensor",
        "mounted_sensors",
        "sonar",
        "mounted_sonars",
        "has_flight_model",
        "flight_model",
        "has_landing_gear",
        "landing_gear",
        "has_score",
        "score",
        "airframe",
        "aero_tuning",
        "stall_state",
        "ship_platform",
        "submarine_platform",
        "naval_stores",
        "naval_logistics",
        "naval_weapon_system",
        "embarked_air_ops",
        "damage_model",
        "has_ammo",
        "ammo",
        "missile_tuning",
        "guidance",
        "warhead",
        "fuze",
        "fuse",
        "has_command_link",
        "command_link",
        "has_data_link",
        "data_link_network_id",
        "data_link_max_reports_per_update",
        "data_link_max_messages_per_update",
        "rwr",
        "jammer",
        "countermeasures",
        "esm",
        // --- 52 missile-tuning helper keys (parse_missile_tuning_json_fields) ---
        "max_speed",
        "turn_rate",
        "fuse_distance",
        "damage",
        "seeker_fov_deg",
        "seeker_lock_range",
        "guidance_delay_s",
        "guidance_update_period_s",
        "max_flight_time_s",
        "nav_gain",
        "apn_target_accel_gain",
        "sensor_max_range",
        "sensor_fov_deg",
        "sensor_scan_period",
        "sensor_detection_prob",
        "sensor_bearing_noise_std",
        "sensor_range_noise_std",
        "sensor_track_memory_s",
        "seeker_type",
        "seeker_activation_range_m",
        "seeker_gimbal_limit_deg",
        "seeker_ifov_deg",
        "bearing_filter_tau_s",
        "elevation_filter_tau_s",
        "range_filter_tau_s",
        "track_break_time_s",
        "boost_time_s",
        "sustain_time_s",
        "boost_thrust_n",
        "sustain_thrust_n",
        "reference_area_m2",
        "cd0_subsonic",
        "cd0_supersonic",
        "induced_drag_k",
        "cd0_mach_breakpoints",
        "cd0_mach_values",
        "induced_drag_k_mach_breakpoints",
        "induced_drag_k_mach_values",
        "propellant_mass_kg",
        "max_lateral_g",
        "autopilot_tau_s",
        "autopilot_damping",
        "autopilot_order",
        "max_accel_response_g_per_s",
        "mach_transonic_start",
        "mach_transonic_end",
        "cd0_power_on_ratio",
        "min_launch_range_m",
        "max_launch_off_boresight_deg",
        "lobl_required",
        "midcourse_datalink_supported",
        "use_kalman_seeker",
        // --- 3 semantic present-but-unread top-level keys (survey section 3) ---
        "ew_suite_ref",
        "rcs",
        "rcs_profile_ref",
    };
    return keys;
}

} // namespace

bool is_recognized_top_level_key(const std::string &key) {
    // Underscore-annotation convention: provenance/schema notes ignored by parser.
    if (!key.empty() && key.front() == '_') {
        return true;
    }
    const auto &keys = recognized_top_level_keys();
    return keys.find(key) != keys.end();
}

std::vector<ContentDiagnostic> validate_unit_json_entry(const nlohmann::json &entry,
                                                        const std::string &source) {
    std::vector<ContentDiagnostic> diagnostics;
    if (!entry.is_object()) {
        // Non-fatal: the parse pass handles shape rejection; nothing to check.
        return diagnostics;
    }

    std::string unit_name;
    if (entry.contains("name") && entry["name"].is_string()) {
        unit_name = entry["name"].get<std::string>();
    } else if (entry.contains("type") && entry["type"].is_string()) {
        unit_name = entry["type"].get<std::string>();
    }

    for (const auto &item : entry.items()) {
        const std::string &key = item.key();
        if (is_recognized_top_level_key(key)) {
            continue;
        }
        ContentDiagnostic diagnostic;
        diagnostic.severity = ContentDiagnostic::Severity::Warning;
        diagnostic.source = source;
        diagnostic.unit_name = unit_name;
        diagnostic.code = "unknown_top_level_key";
        diagnostic.key = key;
        diagnostic.message =
            "Unrecognized top-level content key '" + key + "' is ignored by the unit loader.";
        diagnostics.push_back(std::move(diagnostic));
    }
    return diagnostics;
}

std::vector<ContentDiagnostic> validate_pass(const std::vector<nlohmann::json> &entries,
                                             const std::string &source) {
    std::vector<ContentDiagnostic> diagnostics;
    for (const auto &entry : entries) {
        std::vector<ContentDiagnostic> entry_diagnostics = validate_unit_json_entry(entry, source);
        diagnostics.insert(diagnostics.end(), std::make_move_iterator(entry_diagnostics.begin()),
                           std::make_move_iterator(entry_diagnostics.end()));
    }
    return diagnostics;
}

DeferredReferenceReport resolve_pass(const std::vector<UnitDefinition> &definitions) {
    // PASS-THROUGH. Cross-reference resolution stays at materialize time in
    // src/models/core/default_unit_factory.h (spawn /
    // build_platform_capability_bundle_template), which resolves these names via
    // definitions_.find(...):
    //   sensor_refs (:712), sensor_ref (:724), engine_ref (:806),
    //   ew_suite_ref (:873), rcs_profile_ref (:896), default_loadout (:763),
    //   embarked_air_ops.helo_unit_name (:1388).
    // This slice does not move that resolution earlier; it only tallies the
    // deferred edges (read-only) and MUST NOT mutate `definitions`.
    DeferredReferenceReport report;
    report.definitions = definitions.size();
    for (const auto &def : definitions) {
        bool has_deferred = false;
        if (!def.sensor_ref.empty()) {
            ++report.sensor_ref;
            has_deferred = true;
        }
        if (!def.sensor_refs.empty()) {
            ++report.sensor_refs;
            has_deferred = true;
        }
        if (!def.engine_ref.empty()) {
            ++report.engine_ref;
            has_deferred = true;
        }
        if (!def.ew_suite_ref.empty()) {
            ++report.ew_suite_ref;
            has_deferred = true;
        }
        if (!def.rcs_profile_ref.empty()) {
            ++report.rcs_profile_ref;
            has_deferred = true;
        }
        if (!def.default_loadout.empty()) {
            ++report.default_loadout;
            has_deferred = true;
        }
        if (!def.embarked_air_ops.helo_unit_name.empty()) {
            ++report.embarked_helo_ref;
            has_deferred = true;
        }
        if (has_deferred) {
            ++report.definitions_with_deferred_refs;
        }
    }
    return report;
}

} // namespace content_compile
