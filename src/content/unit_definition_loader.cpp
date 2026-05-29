#include "content/unit_definition_loader.h"

#include <fstream>
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <unordered_map>

namespace fs = std::filesystem;

namespace {

constexpr const char* kVulnerabilityEvidenceSchemaVersion =
    "a2.vulnerability_evidence.v1";
constexpr const char* kVulnerabilitySurrogateValidationManifestSchemaVersion =
    "a2.vulnerability_surrogate_validation.v1";

struct VulnerabilityEvidenceDescriptor {
    std::string dataset_id;
    std::string schema_version;
    std::string target_type;
    std::string weapon_family;
    std::string aspect_bucket;
    std::string closure_bucket;
    std::string miss_distance_bucket;
    std::string calibration_status = "unvalidated";
    std::string source_kind;
    std::string source_ref;
    std::string validation_artifact_ref;
    std::string validation_manifest_schema_version;
    std::string validation_status = "unvalidated";
    std::string validation_artifact_sha256;
    std::string validated_surrogate_model_ref;
    std::string validation_benchmark_ref;
    std::string validation_metrics_ref;
    std::string validation_acceptance_criteria_ref;
    std::string validation_scope_target_type;
    std::string validation_scope_weapon_family;
    std::string validation_scope_aspect_bucket;
    std::string validation_scope_closure_bucket;
    std::string validation_scope_miss_distance_bucket;
    std::string provenance;
    bool effect_scale_authority = false;
    bool component_failure_probability_authority = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    std::vector<AircraftVulnerabilityEvidenceRow> rows;
};

using VulnerabilityEvidenceDescriptorMap =
    std::unordered_map<std::string, VulnerabilityEvidenceDescriptor>;

void parse_optional_evidence_row_number(
    const nlohmann::json& row_json,
    const char* key,
    bool* has_value,
    double* value
) {
    if (!has_value || !value || !row_json.contains(key) || !row_json[key].is_number()) {
        return;
    }
    *has_value = true;
    *value = row_json[key].get<double>();
}

int parse_sensor_type_code(const std::string& type_str) {
    if (type_str == "Visual") return static_cast<int>(SensorType::Visual);
    if (type_str == "Infrared") return static_cast<int>(SensorType::Infrared);
    if (type_str == "Radar") return static_cast<int>(SensorType::Radar);
    if (type_str == "RWR") return static_cast<int>(SensorType::RWR);
    if (type_str == "MIDS") return static_cast<int>(SensorType::MIDS);
    if (type_str == "ESM") return static_cast<int>(SensorType::ESM);
    if (type_str == "Sonar") return static_cast<int>(SensorType::Sonar);
    return static_cast<int>(SensorType::Visual);
}

int parse_sensor_environment_domain_code(const std::string& domain_str) {
    if (domain_str == "SurfaceMaritime") {
        return static_cast<int>(SensorEnvironmentDomain::SurfaceMaritime);
    }
    if (domain_str == "Littoral") {
        return static_cast<int>(SensorEnvironmentDomain::Littoral);
    }
    return static_cast<int>(SensorEnvironmentDomain::Air);
}

NavalWeaponType parse_naval_weapon_type(const std::string& type_str) {
    if (type_str == "vls_sam") return NavalWeaponType::VlsSam;
    if (type_str == "gun_5in") return NavalWeaponType::DeckGun;
    if (type_str == "ciws") return NavalWeaponType::Ciws;
    return NavalWeaponType::Unknown;
}

void parse_aero_tuning_json_fields(const nlohmann::json& src, AeroTuning* out_tuning) {
    if (!out_tuning || !src.is_object()) return;
    AeroTuning tuning = *out_tuning;
    tuning.enabled = src.value("enabled", true);
    tuning.cl_alpha_per_deg = src.value("cl_alpha_per_deg", tuning.cl_alpha_per_deg);
    tuning.cl0 = src.value("cl0", tuning.cl0);
    tuning.cd0_clean = src.value("cd0_clean", tuning.cd0_clean);
    tuning.induced_drag_k = src.value("induced_drag_k", tuning.induced_drag_k);
    tuning.cm_alpha_per_rad = src.value("cm_alpha_per_rad", tuning.cm_alpha_per_rad);
    tuning.cm_q = src.value("cm_q", tuning.cm_q);
    tuning.alpha_stall_clean_deg = src.value("alpha_stall_clean_deg", tuning.alpha_stall_clean_deg);
    tuning.alpha_stall_flaps_full_deg =
        src.value("alpha_stall_flaps_full_deg", tuning.alpha_stall_flaps_full_deg);
    tuning.alpha_peak_offset_deg = src.value("alpha_peak_offset_deg", tuning.alpha_peak_offset_deg);
    tuning.alpha_deep_offset_deg = src.value("alpha_deep_offset_deg", tuning.alpha_deep_offset_deg);
    tuning.cl_peak_clean = src.value("cl_peak_clean", tuning.cl_peak_clean);
    tuning.cl_peak_flaps_full = src.value("cl_peak_flaps_full", tuning.cl_peak_flaps_full);
    tuning.cl_deep_clean = src.value("cl_deep_clean", tuning.cl_deep_clean);
    tuning.cl_deep_flaps_full = src.value("cl_deep_flaps_full", tuning.cl_deep_flaps_full);
    tuning.pitch_break_onset_deg = src.value("pitch_break_onset_deg", tuning.pitch_break_onset_deg);
    tuning.pitch_break_full_deg = src.value("pitch_break_full_deg", tuning.pitch_break_full_deg);
    tuning.pitch_break_cm_nose_down =
        src.value("pitch_break_cm_nose_down", tuning.pitch_break_cm_nose_down);
    tuning.post_stall_damp_floor =
        src.value("post_stall_damp_floor", tuning.post_stall_damp_floor);
    tuning.aoa_rate_pitch_break_gain =
        src.value("aoa_rate_pitch_break_gain", tuning.aoa_rate_pitch_break_gain);

    auto parse_vector = [&](const char* key, std::vector<double>* out_values) {
        if (!out_values || !src.contains(key) || !src[key].is_array()) {
            return;
        }
        out_values->clear();
        for (const auto& value : src[key]) {
            if (!value.is_number()) continue;
            out_values->push_back(value.get<double>());
        }
    };

    parse_vector("mach_breakpoints", &tuning.mach_breakpoints);
    parse_vector("cl_alpha_scale_vs_mach", &tuning.cl_alpha_scale_vs_mach);
    parse_vector("cd0_add_vs_mach", &tuning.cd0_add_vs_mach);
    parse_vector("induced_drag_scale_vs_mach", &tuning.induced_drag_scale_vs_mach);
    parse_vector("cm_alpha_scale_vs_mach", &tuning.cm_alpha_scale_vs_mach);
    parse_vector("stall_alpha_delta_deg_vs_mach", &tuning.stall_alpha_delta_deg_vs_mach);

    *out_tuning = tuning;
}

void parse_engine_tuning_json_fields(const nlohmann::json& src, EngineTuning* out_tuning) {
    if (!out_tuning || !src.is_object()) return;
    EngineTuning tuning = *out_tuning;
    tuning.enabled = src.value("enabled", true);
    tuning.mil_thrust_n = src.value("mil_thrust_n", tuning.mil_thrust_n);
    tuning.ab_thrust_n = src.value("ab_thrust_n", tuning.ab_thrust_n);
    tuning.throttle_ab_threshold =
        src.value("throttle_ab_threshold", tuning.throttle_ab_threshold);
    tuning.throttle_idle_bias = src.value("throttle_idle_bias", tuning.throttle_idle_bias);
    tuning.tau_spool_up_s = src.value("tau_spool_up_s", tuning.tau_spool_up_s);
    tuning.tau_spool_down_s = src.value("tau_spool_down_s", tuning.tau_spool_down_s);
    tuning.tau_ab_light_s = src.value("tau_ab_light_s", tuning.tau_ab_light_s);
    tuning.tau_ab_extinguish_s =
        src.value("tau_ab_extinguish_s", tuning.tau_ab_extinguish_s);
    tuning.ram_rise_gain = src.value("ram_rise_gain", tuning.ram_rise_gain);
    tuning.ram_rise_mach_cap = src.value("ram_rise_mach_cap", tuning.ram_rise_mach_cap);
    tuning.ram_decay_start_mach =
        src.value("ram_decay_start_mach", tuning.ram_decay_start_mach);
    tuning.ram_decay_gain = src.value("ram_decay_gain", tuning.ram_decay_gain);
    tuning.thrust_sigma_exponent =
        src.value("thrust_sigma_exponent", tuning.thrust_sigma_exponent);
    tuning.thrust_theta_exponent =
        src.value("thrust_theta_exponent", tuning.thrust_theta_exponent);
    tuning.tsfc_mil_kg_per_nh =
        src.value("tsfc_mil_kg_per_nh", tuning.tsfc_mil_kg_per_nh);
    tuning.tsfc_ab_kg_per_nh =
        src.value("tsfc_ab_kg_per_nh", tuning.tsfc_ab_kg_per_nh);
    *out_tuning = tuning;
}

void parse_stall_state_json_fields(const nlohmann::json& src, StallState* out_stall) {
    if (!out_stall || !src.is_object()) return;
    StallState stall = *out_stall;
    stall.stall_progress = src.value("stall_progress", stall.stall_progress);
    stall.time_in_stall_s = src.value("time_in_stall_s", stall.time_in_stall_s);
    stall.is_stalled = src.value("is_stalled", stall.is_stalled);
    stall.pitch_break_active = src.value("pitch_break_active", stall.pitch_break_active);
    *out_stall = stall;
}

void parse_sensor_json_fields(
    const nlohmann::json& s,
    Sensor* out_sensor,
    const std::string& default_sensor_type = "Visual"
) {
    if (!out_sensor) return;
    Sensor sensor = *out_sensor;
    sensor.max_range = s.value("max_range", sensor.max_range);
    sensor.fov_deg = s.value("fov_deg", sensor.fov_deg);
    sensor.scan_period = s.value("scan_period", sensor.scan_period);
    sensor.last_scan_time = s.value("last_scan_time", sensor.last_scan_time);
    sensor.detection_prob = s.value("detection_prob", sensor.detection_prob);
    sensor.range_power = s.value("range_power", sensor.range_power);
    sensor.bearing_noise_std = s.value("bearing_noise_std", sensor.bearing_noise_std);
    sensor.range_noise_std = s.value("range_noise_std", sensor.range_noise_std);
    sensor.track_memory_s = s.value("track_memory_s", sensor.track_memory_s);
    sensor.aspect_influence = s.value("aspect_influence", sensor.aspect_influence);
    sensor.doppler_notch_width = s.value("doppler_notch_width", sensor.doppler_notch_width);
    sensor.reference_snr_db = s.value("reference_snr_db", sensor.reference_snr_db);
    sensor.reference_range_m = s.value("reference_range_m", sensor.reference_range_m);
    sensor.reference_rcs_m2 = s.value("reference_rcs_m2", sensor.reference_rcs_m2);
    sensor.pfa = s.value("pfa", sensor.pfa);
    sensor.confirm_hits_m = s.value("confirm_hits_m", sensor.confirm_hits_m);
    sensor.confirm_window_n = s.value("confirm_window_n", sensor.confirm_window_n);
    sensor.velocity_noise_std = s.value("velocity_noise_std", sensor.velocity_noise_std);
    sensor.alpha_beta_alpha = s.value("alpha_beta_alpha", sensor.alpha_beta_alpha);
    sensor.alpha_beta_beta = s.value("alpha_beta_beta", sensor.alpha_beta_beta);
    sensor.antenna_height_m = s.value("antenna_height_m", sensor.antenna_height_m);
    sensor.target_height_bias_m = s.value("target_height_bias_m", sensor.target_height_bias_m);
    sensor.sea_clutter_sensitivity = s.value("sea_clutter_sensitivity", sensor.sea_clutter_sensitivity);
    sensor.sea_state_loss_per_level = s.value("sea_state_loss_per_level", sensor.sea_state_loss_per_level);
    sensor.ducting_gain_factor = s.value("ducting_gain_factor", sensor.ducting_gain_factor);
    sensor.ducting_max_bonus_m = s.value("ducting_max_bonus_m", sensor.ducting_max_bonus_m);
    sensor.bearing_only_min_range_m = s.value("bearing_only_min_range_m", sensor.bearing_only_min_range_m);
    sensor.enforce_radar_horizon = s.value("enforce_radar_horizon", sensor.enforce_radar_horizon);
    sensor.enable_ducting = s.value("enable_ducting", sensor.enable_ducting);
    sensor.sea_clutter_enabled = s.value("sea_clutter_enabled", sensor.sea_clutter_enabled);
    sensor.bearing_only = s.value("bearing_only", sensor.bearing_only);

    sensor.type = parse_sensor_type_code(s.value("type", default_sensor_type));
    sensor.environment_domain =
        parse_sensor_environment_domain_code(s.value("environment_domain", "Air"));

    *out_sensor = sensor;
}

void parse_missile_tuning_json_fields(
    const nlohmann::json& src,
    MissileTuningDefinition* out_tuning
) {
    if (!out_tuning || !src.is_object()) return;
    MissileTuningDefinition tuning = *out_tuning;
    tuning.max_speed = src.value("max_speed", tuning.max_speed);
    tuning.turn_rate = src.value("turn_rate", tuning.turn_rate);
    tuning.fuse_distance = src.value("fuse_distance", tuning.fuse_distance);
    tuning.damage = src.value("damage", tuning.damage);
    tuning.seeker_fov_deg = src.value("seeker_fov_deg", tuning.seeker_fov_deg);
    tuning.seeker_lock_range = src.value("seeker_lock_range", tuning.seeker_lock_range);
    tuning.guidance_delay_s = src.value("guidance_delay_s", tuning.guidance_delay_s);
    tuning.guidance_update_period_s =
        src.value("guidance_update_period_s", tuning.guidance_update_period_s);
    tuning.max_flight_time_s = src.value("max_flight_time_s", tuning.max_flight_time_s);
    tuning.nav_gain = src.value("nav_gain", tuning.nav_gain);
    tuning.sensor_max_range = src.value("sensor_max_range", tuning.sensor_max_range);
    tuning.sensor_fov_deg = src.value("sensor_fov_deg", tuning.sensor_fov_deg);
    tuning.sensor_scan_period = src.value("sensor_scan_period", tuning.sensor_scan_period);
    tuning.sensor_detection_prob =
        src.value("sensor_detection_prob", tuning.sensor_detection_prob);
    tuning.sensor_bearing_noise_std =
        src.value("sensor_bearing_noise_std", tuning.sensor_bearing_noise_std);
    tuning.sensor_range_noise_std =
        src.value("sensor_range_noise_std", tuning.sensor_range_noise_std);
    tuning.sensor_track_memory_s =
        src.value("sensor_track_memory_s", tuning.sensor_track_memory_s);
    tuning.seeker_type = src.value("seeker_type", tuning.seeker_type);
    tuning.seeker_activation_range_m =
        src.value("seeker_activation_range_m", tuning.seeker_activation_range_m);
    tuning.seeker_gimbal_limit_deg =
        src.value("seeker_gimbal_limit_deg", tuning.seeker_gimbal_limit_deg);
    tuning.seeker_ifov_deg = src.value("seeker_ifov_deg", tuning.seeker_ifov_deg);
    tuning.bearing_filter_tau_s =
        src.value("bearing_filter_tau_s", tuning.bearing_filter_tau_s);
    tuning.elevation_filter_tau_s =
        src.value("elevation_filter_tau_s", tuning.elevation_filter_tau_s);
    tuning.range_filter_tau_s = src.value("range_filter_tau_s", tuning.range_filter_tau_s);
    tuning.track_break_time_s = src.value("track_break_time_s", tuning.track_break_time_s);
    tuning.boost_time_s = src.value("boost_time_s", tuning.boost_time_s);
    tuning.sustain_time_s = src.value("sustain_time_s", tuning.sustain_time_s);
    tuning.boost_thrust_n = src.value("boost_thrust_n", tuning.boost_thrust_n);
    tuning.sustain_thrust_n = src.value("sustain_thrust_n", tuning.sustain_thrust_n);
    tuning.reference_area_m2 = src.value("reference_area_m2", tuning.reference_area_m2);
    tuning.cd0_subsonic = src.value("cd0_subsonic", tuning.cd0_subsonic);
    tuning.cd0_supersonic = src.value("cd0_supersonic", tuning.cd0_supersonic);
    tuning.induced_drag_k = src.value("induced_drag_k", tuning.induced_drag_k);
    tuning.propellant_mass_kg = src.value("propellant_mass_kg", tuning.propellant_mass_kg);
    tuning.max_lateral_g = src.value("max_lateral_g", tuning.max_lateral_g);
    tuning.autopilot_tau_s = src.value("autopilot_tau_s", tuning.autopilot_tau_s);
    tuning.max_accel_response_g_per_s =
        src.value("max_accel_response_g_per_s", tuning.max_accel_response_g_per_s);
    tuning.min_launch_range_m = src.value("min_launch_range_m", tuning.min_launch_range_m);
    tuning.max_launch_off_boresight_deg = src.value(
        "max_launch_off_boresight_deg",
        tuning.max_launch_off_boresight_deg
    );
    tuning.lobl_required = src.value("lobl_required", tuning.lobl_required);
    tuning.midcourse_datalink_supported = src.value(
        "midcourse_datalink_supported",
        tuning.midcourse_datalink_supported
    );
    *out_tuning = tuning;
}

std::string normalize_warhead_family(const std::string& raw_type) {
    if (raw_type == "Frag" || raw_type == "Fragmentation" || raw_type == "blast_fragmentation") {
        return "blast_fragmentation";
    }
    if (raw_type == "ContinuousRod" || raw_type == "continuous_rod") {
        return "continuous_rod";
    }
    if (raw_type == "HitToKill" || raw_type == "hit_to_kill") {
        return "hit_to_kill";
    }
    if (raw_type == "Blast" || raw_type == "blast") {
        return "blast";
    }
    return raw_type.empty() ? "blast_fragmentation" : raw_type;
}

std::string normalize_fuze_type(const std::string& raw_type) {
    if (raw_type == "RadarProximity" || raw_type == "radar_proximity" ||
        raw_type == "RFProximity" || raw_type == "rf_proximity") {
        return "radar_proximity";
    }
    if (raw_type == "LaserProximity" || raw_type == "laser_proximity") {
        return "laser_proximity";
    }
    if (raw_type == "Contact" || raw_type == "impact" || raw_type == "contact") {
        return "contact";
    }
    if (raw_type == "Timed" || raw_type == "time" || raw_type == "timed") {
        return "timed";
    }
    if (raw_type == "Proximity" || raw_type == "proximity") {
        return "proximity";
    }
    return raw_type.empty() ? "proximity" : raw_type;
}

double synthetic_damage_from_warhead_mass(double mass_kg) {
    if (!std::isfinite(mass_kg) || mass_kg <= 0.0) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    return std::clamp(mass_kg * 9.0, 40.0, 320.0);
}

void parse_fuze_json_fields(
    const nlohmann::json& src,
    MissileTuningDefinition* out_tuning
) {
    if (!out_tuning || !src.is_object()) return;
    FuzeProfile profile = out_tuning->fuze_profile;
    profile.type = normalize_fuze_type(src.value("type", profile.type));
    if (src.contains("trigger_radius_m") && src["trigger_radius_m"].is_number()) {
        profile.trigger_radius_m = src["trigger_radius_m"].get<double>();
    } else if (src.contains("trigger_radius") && src["trigger_radius"].is_number()) {
        profile.trigger_radius_m = src["trigger_radius"].get<double>();
    } else if (src.contains("radius_m") && src["radius_m"].is_number()) {
        profile.trigger_radius_m = src["radius_m"].get<double>();
    }
    profile.delay_s = src.value("delay_s", profile.delay_s);
    profile.reliability = std::clamp(src.value("reliability", profile.reliability), 0.0, 1.0);
    profile.synthetic = src.value("synthetic", false);
    profile.provenance = src.value("provenance", "authored_fuze_profile");

    out_tuning->fuze_profile = profile;
    out_tuning->has_fuze_profile = true;
    if (std::isfinite(profile.trigger_radius_m)) {
        out_tuning->fuse_distance = profile.trigger_radius_m;
    }
}

void parse_warhead_json_fields(
    const nlohmann::json& src,
    MissileTuningDefinition* out_tuning
) {
    if (!out_tuning || !src.is_object()) return;
    WarheadProfile profile = out_tuning->warhead_profile;
    profile.family = normalize_warhead_family(src.value("type", profile.family));
    profile.mass_kg = src.value("mass_kg", profile.mass_kg);
    profile.lethal_radius_m = src.value("lethal_radius", profile.lethal_radius_m);
    if (src.contains("damage") && src["damage"].is_number()) {
        profile.damage_scalar = src["damage"].get<double>();
        profile.damage_scalar_synthetic = false;
    } else if (!std::isfinite(profile.damage_scalar)) {
        profile.damage_scalar = synthetic_damage_from_warhead_mass(profile.mass_kg);
        profile.damage_scalar_synthetic = true;
    }
    profile.synthetic = src.value("synthetic", false);
    profile.provenance = src.value(
        "provenance",
        profile.damage_scalar_synthetic
            ? "warhead_mass_synthetic_damage_scalar"
            : "authored_warhead_profile");

    out_tuning->warhead_profile = profile;
    out_tuning->has_warhead_profile = true;
    if (std::isfinite(profile.lethal_radius_m)) {
        out_tuning->fuse_distance = profile.lethal_radius_m;
    }
    if (std::isfinite(profile.damage_scalar)) {
        out_tuning->damage = profile.damage_scalar;
    }

    if (!out_tuning->has_fuze_profile && std::isfinite(profile.lethal_radius_m)) {
        out_tuning->fuze_profile =
            make_synthetic_fuze_profile(profile.lethal_radius_m, "warhead_lethal_radius_fuze_compat");
        out_tuning->has_fuze_profile = true;
    }
}

Sonar make_default_sonar_definition() {
    Sonar sonar{};
    sonar.max_range_m = 25000.0;
    sonar.scan_period_s = 5.0;
    sonar.last_scan_time_s = -1.0;
    sonar.detection_threshold_db = 6.0;
    sonar.track_memory_s = 20.0;
    sonar.bearing_noise_std_deg = 2.5;
    sonar.range_noise_std_m = 750.0;
    sonar.directivity_gain_db = 3.0;
    sonar.self_noise_per_speed_db = 1.2;
    sonar.ambient_noise_db = 72.0;
    sonar.source_level_reference_db = 118.0;
    sonar.source_level_speed_factor_db = 1.6;
    sonar.transmission_loss_alpha_db_per_km = 0.08;
    sonar.layer_break_penalty_db = 4.0;
    sonar.convergence_zone_bonus_m = 0.0;
    sonar.baffle_exclusion_deg = 40.0;
    sonar.ownship_quieting_speed_mps = 5.0;
    sonar.active_ping_source_level_db = 210.0;
    sonar.confirm_hits_m = 2;
    sonar.confirm_window_n = 3;
    sonar.mode = static_cast<int>(SonarMode::Passive);
    sonar.passive_only = true;
    sonar.bearing_only = false;
    return sonar;
}

void parse_sonar_json_fields(const nlohmann::json& s, Sonar* out_sonar) {
    if (!out_sonar || !s.is_object()) return;
    Sonar sonar = *out_sonar;
    sonar.max_range_m = s.value("max_range_m", sonar.max_range_m);
    sonar.scan_period_s = s.value("scan_period_s", sonar.scan_period_s);
    sonar.last_scan_time_s = s.value("last_scan_time_s", sonar.last_scan_time_s);
    sonar.detection_threshold_db = s.value("detection_threshold_db", sonar.detection_threshold_db);
    sonar.track_memory_s = s.value("track_memory_s", sonar.track_memory_s);
    sonar.bearing_noise_std_deg = s.value("bearing_noise_std_deg", sonar.bearing_noise_std_deg);
    sonar.range_noise_std_m = s.value("range_noise_std_m", sonar.range_noise_std_m);
    sonar.directivity_gain_db = s.value("directivity_gain_db", sonar.directivity_gain_db);
    sonar.self_noise_per_speed_db = s.value("self_noise_per_speed_db", sonar.self_noise_per_speed_db);
    sonar.ambient_noise_db = s.value("ambient_noise_db", sonar.ambient_noise_db);
    sonar.source_level_reference_db = s.value("source_level_reference_db", sonar.source_level_reference_db);
    sonar.source_level_speed_factor_db = s.value("source_level_speed_factor_db", sonar.source_level_speed_factor_db);
    sonar.transmission_loss_alpha_db_per_km =
        s.value("transmission_loss_alpha_db_per_km", sonar.transmission_loss_alpha_db_per_km);
    sonar.layer_break_penalty_db = s.value("layer_break_penalty_db", sonar.layer_break_penalty_db);
    sonar.convergence_zone_bonus_m = s.value("convergence_zone_bonus_m", sonar.convergence_zone_bonus_m);
    sonar.baffle_exclusion_deg = s.value("baffle_exclusion_deg", sonar.baffle_exclusion_deg);
    sonar.ownship_quieting_speed_mps = s.value("ownship_quieting_speed_mps", sonar.ownship_quieting_speed_mps);
    sonar.active_ping_source_level_db =
        s.value("active_ping_source_level_db", sonar.active_ping_source_level_db);
    sonar.confirm_hits_m = s.value("confirm_hits_m", sonar.confirm_hits_m);
    sonar.confirm_window_n = s.value("confirm_window_n", sonar.confirm_window_n);
    sonar.passive_only = s.value("passive_only", sonar.passive_only);
    sonar.bearing_only = s.value("bearing_only", sonar.bearing_only);
    const std::string mode_str = s.value("mode", sonar.passive_only ? "Passive" : "Active");
    sonar.mode = static_cast<int>(mode_str == "Active" ? SonarMode::Active : SonarMode::Passive);
    *out_sonar = sonar;
}

bool parse_unit_type(const std::string& value, UnitType* out_type) {
    if (!out_type) return false;
    // spdlog::info("Parsing unit type: '{}'", value);
    if (value == "Aircraft") { *out_type = UnitType::Aircraft; return true; }
    if (value == "Ship") { *out_type = UnitType::Ship; return true; }
    if (value == "Missile") { *out_type = UnitType::Missile; return true; }
    if (value == "Facility") { *out_type = UnitType::Facility; return true; }
    if (value == "C2Node") { *out_type = UnitType::C2Node; return true; }
    if (value == "Sensor") { *out_type = UnitType::Sensor; return true; }
    if (value == "Engine") { *out_type = UnitType::Engine; return true; }
    if (value == "EWSuite") { *out_type = UnitType::EWSuite; return true; }
    if (value == "RCSProfile") { *out_type = UnitType::RCSProfile; return true; }
    if (value == "Submarine") { *out_type = UnitType::Submarine; return true; }
    if (value == "Ground") { *out_type = UnitType::Ground; return true; }
    *out_type = UnitType::Unknown;
    return false;
}

bool validation_status_is_passed(const std::string& status) {
    return status == "validated" || status == "passed";
}

bool validated_physics_surrogate_has_auditable_manifest(
    const VulnerabilityEvidenceDescriptor& descriptor
) {
    if (descriptor.validation_artifact_ref.empty() ||
        descriptor.validation_manifest_schema_version !=
            kVulnerabilitySurrogateValidationManifestSchemaVersion ||
        !validation_status_is_passed(descriptor.validation_status) ||
        descriptor.validation_artifact_sha256.empty() ||
        descriptor.validated_surrogate_model_ref.empty() ||
        descriptor.validation_benchmark_ref.empty() ||
        descriptor.validation_metrics_ref.empty() ||
        descriptor.validation_acceptance_criteria_ref.empty()) {
        return false;
    }
    return descriptor.validation_scope_target_type == descriptor.target_type &&
        descriptor.validation_scope_weapon_family == descriptor.weapon_family &&
        descriptor.validation_scope_aspect_bucket == descriptor.aspect_bucket &&
        descriptor.validation_scope_closure_bucket == descriptor.closure_bucket &&
        descriptor.validation_scope_miss_distance_bucket ==
            descriptor.miss_distance_bucket;
}

bool vulnerability_evidence_descriptor_has_authoritative_source(
    const VulnerabilityEvidenceDescriptor& descriptor
) {
    if (descriptor.source_kind == "external_calibration_dataset") {
        return true;
    }
    if (descriptor.source_kind == "validated_physics_surrogate") {
        return validated_physics_surrogate_has_auditable_manifest(descriptor);
    }
    return false;
}

bool vulnerability_evidence_descriptor_is_calibrated_match(
    const VulnerabilityEvidenceDescriptorMap* descriptors,
    const AircraftVulnerabilityProfile& profile,
    const std::string& target_type
) {
    if (!descriptors || profile.evidence_dataset_ref.empty()) {
        return false;
    }
    if (profile.synthetic || !profile.calibrated ||
        profile.calibration_status != "calibrated") {
        return false;
    }
    const auto descriptor_it = descriptors->find(profile.evidence_dataset_ref);
    if (descriptor_it == descriptors->end()) {
        return false;
    }

    const VulnerabilityEvidenceDescriptor& descriptor = descriptor_it->second;
    if (descriptor.target_type != target_type) {
        return false;
    }
    if (descriptor.calibration_status != "calibrated") {
        return false;
    }
    if (descriptor.schema_version != kVulnerabilityEvidenceSchemaVersion ||
        descriptor.source_ref.empty() ||
        descriptor.provenance.empty()) {
        return false;
    }
    if (descriptor.weapon_family.empty() ||
        descriptor.aspect_bucket.empty() ||
        descriptor.closure_bucket.empty() ||
        descriptor.miss_distance_bucket.empty()) {
        return false;
    }
    return vulnerability_evidence_descriptor_has_authoritative_source(descriptor);
}

const VulnerabilityEvidenceDescriptor* find_vulnerability_evidence_descriptor(
    const VulnerabilityEvidenceDescriptorMap* descriptors,
    const AircraftVulnerabilityProfile& profile
) {
    if (!descriptors || profile.evidence_dataset_ref.empty()) {
        return nullptr;
    }
    const auto descriptor_it = descriptors->find(profile.evidence_dataset_ref);
    if (descriptor_it == descriptors->end()) {
        return nullptr;
    }
    return &descriptor_it->second;
}

void copy_vulnerability_descriptor_metadata(
    const VulnerabilityEvidenceDescriptor* descriptor,
    AircraftVulnerabilityProfile* profile
) {
    if (!descriptor || !profile) {
        return;
    }
    profile->evidence_schema_version = descriptor->schema_version;
    profile->evidence_source_kind = descriptor->source_kind;
    profile->evidence_source_ref = descriptor->source_ref;
    profile->evidence_validation_artifact_ref =
        descriptor->validation_artifact_ref;
    profile->evidence_validation_manifest_schema_version =
        descriptor->validation_manifest_schema_version;
    profile->evidence_validation_status = descriptor->validation_status;
    profile->evidence_validation_artifact_sha256 =
        descriptor->validation_artifact_sha256;
    profile->evidence_validated_surrogate_model_ref =
        descriptor->validated_surrogate_model_ref;
    profile->evidence_validation_benchmark_ref =
        descriptor->validation_benchmark_ref;
    profile->evidence_validation_metrics_ref =
        descriptor->validation_metrics_ref;
    profile->evidence_validation_acceptance_criteria_ref =
        descriptor->validation_acceptance_criteria_ref;
}

bool vulnerability_row_matches_descriptor(
    const AircraftVulnerabilityEvidenceRow& row,
    const VulnerabilityEvidenceDescriptor& descriptor
) {
    return row.weapon_family == descriptor.weapon_family &&
        row.aspect_bucket == descriptor.aspect_bucket &&
        row.closure_bucket == descriptor.closure_bucket &&
        row.miss_distance_bucket == descriptor.miss_distance_bucket;
}

bool vulnerability_row_has_authority_metadata(
    const AircraftVulnerabilityEvidenceRow& row
) {
    return !row.row_id.empty() &&
        !row.source_ref.empty() &&
        !row.provenance.empty();
}

void copy_authoritative_vulnerability_rows(
    const VulnerabilityEvidenceDescriptor* descriptor,
    AircraftVulnerabilityProfile* profile
) {
    if (!descriptor || !profile || !profile->evidence_dataset_valid ||
        (!descriptor->effect_scale_authority &&
         !descriptor->component_failure_probability_authority)) {
        return;
    }

    for (const AircraftVulnerabilityEvidenceRow& row : descriptor->rows) {
        if (vulnerability_row_matches_descriptor(row, *descriptor) &&
            vulnerability_row_has_authority_metadata(row)) {
            profile->evidence_rows.push_back(row);
        }
    }
    profile->effect_scale_authority =
        descriptor->effect_scale_authority &&
        !profile->evidence_rows.empty();
    profile->component_failure_probability_authority =
        descriptor->component_failure_probability_authority &&
        !profile->evidence_rows.empty();
}

} // namespace

// Helper to parse a single JSON object (unit definition)
bool parse_unit_json(
    const nlohmann::json& entry,
    UnitDefinition& def,
    std::string* error,
    const VulnerabilityEvidenceDescriptorMap* vulnerability_descriptors = nullptr
) {
    if (!entry.contains("type") || !entry["type"].is_string()) {
        if (error) *error = "Unit entry missing string 'type'.";
        return false;
    }

    std::string type_str = entry["type"].get<std::string>();
    if (!parse_unit_type(type_str, &def.type) || def.type == UnitType::Unknown) {
        if (error) *error = "Unknown unit type: " + type_str;
        return false;
    }

    def.name = entry.value("name", type_str);
    def.mass_kg = entry.value("mass_kg", 0.0);
    def.has_stall_state = false;
    def.stall_state = {};
    def.has_missile_tuning = false;
    def.missile_tuning = {};


    if (entry.contains("engine_ref")) {
        def.engine_ref = entry["engine_ref"].get<std::string>();
    }

    if (entry.contains("engine")) {
        const auto& e = entry["engine"];
        def.engine_data.mil_thrust_n = e.value("mil_thrust_n", 0.0);
        def.engine_data.ab_thrust_n = e.value("ab_thrust_n", 0.0);
        def.engine_data.sfc_mil = e.value("sfc_mil", 0.0);
        def.engine_data.sfc_ab = e.value("sfc_ab", 0.0);
        def.engine_data.bypass_ratio = e.value("bypass_ratio", 0.0);
        if (e.contains("tuning") && e["tuning"].is_object()) {
            def.engine_data.has_tuning = true;
            def.engine_data.tuning = flight_dynamics::default_engine_tuning();
            parse_engine_tuning_json_fields(e["tuning"], &def.engine_data.tuning);
        }
    }
    def.engine_data.mil_thrust_n = entry.value("mil_thrust_n", def.engine_data.mil_thrust_n);
    def.engine_data.ab_thrust_n = entry.value("ab_thrust_n", def.engine_data.ab_thrust_n);
    def.engine_data.sfc_mil = entry.value("sfc_mil", def.engine_data.sfc_mil);
    def.engine_data.sfc_ab = entry.value("sfc_ab", def.engine_data.sfc_ab);
    def.engine_data.bypass_ratio = entry.value("bypass_ratio", def.engine_data.bypass_ratio);
    if (entry.contains("engine_tuning") && entry["engine_tuning"].is_object()) {
        def.engine_data.has_tuning = true;
        if (!def.engine_data.tuning.enabled) {
            def.engine_data.tuning = flight_dynamics::default_engine_tuning();
        }
        parse_engine_tuning_json_fields(entry["engine_tuning"], &def.engine_data.tuning);
    }

    if (entry.contains("hardpoints") && entry["hardpoints"].is_array()) {
        for (const auto& hp_json : entry["hardpoints"]) {
            Hardpoint hp;
            hp.station_id = hp_json.value("station_id", 0);
            hp.capacity_kg = hp_json.value("capacity_kg", 0.0);
            if (hp_json.contains("type") && hp_json["type"].is_array()) {
                for (const auto& t : hp_json["type"]) {
                    hp.supported_types.push_back(t.get<std::string>());
                }
            }
            def.hardpoints.push_back(hp);
        }
    }

    if (entry.contains("default_loadout") && entry["default_loadout"].is_object()) {
        for (auto& [key, val] : entry["default_loadout"].items()) {
            def.default_loadout[std::stoi(key)] = val.get<std::string>();
        }
    }

    def.health = {100.0, 100.0};
    if (entry.contains("health")) {
        const auto& h = entry["health"];
        def.health.current_hp = h.value("current_hp", def.health.current_hp);
        def.health.max_hp = h.value("max_hp", def.health.max_hp);
    }

    def.has_sensor = false;
    def.sensor = make_unit_definition_default_sensor();
    def.mounted_sensors.mounts.clear();
    def.has_sonar = false;
    def.sonar = make_default_sonar_definition();
    def.mounted_sonars.mounts.clear();
    
    if (entry.contains("sensor_ref")) {
        def.sensor_ref = entry["sensor_ref"].get<std::string>();
        // Note: We don't set has_sensor=true here yet, because the sensor isn't inline.
        // The factory will handle the assembly.
    }
    if (entry.contains("sensor_refs") && entry["sensor_refs"].is_array()) {
        for (const auto& sensor_ref_json : entry["sensor_refs"]) {
            if (!sensor_ref_json.is_string()) continue;
            def.sensor_refs.push_back(sensor_ref_json.get<std::string>());
        }
    } else if (entry.contains("sensor")) {
        def.has_sensor = true;
        const auto& s = entry["sensor"];
        const std::string default_sensor_type =
            (def.type == UnitType::Aircraft || def.type == UnitType::C2Node)
                ? "Radar"
                : "Radar";
        parse_sensor_json_fields(s, &def.sensor, default_sensor_type);
    } else if (entry.contains("has_sensor")) {
        def.has_sensor = entry.value("has_sensor", def.has_sensor);
    }

    if (entry.contains("mounted_sensors") && entry["mounted_sensors"].is_array()) {
        for (const auto& mount_json : entry["mounted_sensors"]) {
            if (!mount_json.is_object()) continue;
            SensorMount mount{};
            mount.label = mount_json.value("label", "");
            mount.sensor = make_unit_definition_default_sensor();
            if (mount_json.contains("sensor") && mount_json["sensor"].is_object()) {
                parse_sensor_json_fields(mount_json["sensor"], &mount.sensor, "Radar");
            }
            def.mounted_sensors.mounts.push_back(mount);
        }
    }

    if (entry.contains("sonar") && entry["sonar"].is_object()) {
        def.has_sonar = true;
        parse_sonar_json_fields(entry["sonar"], &def.sonar);
    }
    if (entry.contains("mounted_sonars") && entry["mounted_sonars"].is_array()) {
        for (const auto& mount_json : entry["mounted_sonars"]) {
            if (!mount_json.is_object()) continue;
            SonarMount mount{};
            mount.label = mount_json.value("label", "");
            mount.sonar = make_default_sonar_definition();
            if (mount_json.contains("sonar") && mount_json["sonar"].is_object()) {
                parse_sonar_json_fields(mount_json["sonar"], &mount.sonar);
            }
            def.mounted_sonars.mounts.push_back(mount);
        }
    }

    def.has_flight_model = entry.value("has_flight_model", false);
    def.flight_model = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    if (entry.contains("flight_model")) {
        def.has_flight_model = true;
        const auto& fm = entry["flight_model"];
        def.flight_model.max_speed = fm.value("max_speed", def.flight_model.max_speed);
        def.flight_model.min_speed = fm.value("min_speed", def.flight_model.min_speed);
        def.flight_model.max_turn_rate = fm.value("max_turn_rate", def.flight_model.max_turn_rate);
        def.flight_model.max_accel = fm.value("max_accel", def.flight_model.max_accel);
        def.flight_model.max_climb_rate = fm.value("max_climb_rate", def.flight_model.max_climb_rate);
        def.flight_model.max_g = fm.value("max_g", def.flight_model.max_g);
        def.flight_model.min_g = fm.value("min_g", -3.0); // Default to -3.0
        
        def.flight_model.takeoff_speed = fm.value("takeoff_speed", 80.0);
        def.flight_model.landing_speed = fm.value("landing_speed", 70.0);
        def.flight_model.taxi_turn_rate = fm.value("taxi_turn_rate", 15.0);
    }

    def.has_landing_gear = entry.value("has_landing_gear", false);
    def.landing_gear = {false, 0.02, 3.0, 2.0, 1.0, false, 5.0}; // Default Paved Only
    if (entry.contains("landing_gear")) {
        def.has_landing_gear = true;
        const auto& lg = entry["landing_gear"];
        def.landing_gear.can_use_unpaved = lg.value("can_use_unpaved", def.landing_gear.can_use_unpaved);
        def.landing_gear.rolling_friction_coeff = lg.value("rolling_friction_coeff", def.landing_gear.rolling_friction_coeff);
        def.landing_gear.max_load_factor = lg.value("max_load_factor", def.landing_gear.max_load_factor);
        def.landing_gear.contact_height_m = lg.value("contact_height_m", def.landing_gear.contact_height_m);
    }

    def.has_score = entry.value("has_score", true);
    def.score = {0.0, 0, 0, 0};
    if (entry.contains("score")) {
        const auto& sc = entry["score"];
        def.score.total_reward = sc.value("total_reward", def.score.total_reward);
        def.score.missiles_fired = sc.value("missiles_fired", def.score.missiles_fired);
        def.score.hits_landed = sc.value("hits_landed", def.score.hits_landed);
        def.score.kills_confirmed = sc.value("kills_confirmed", def.score.kills_confirmed);
    }

    if (entry.contains("airframe")) {
        const auto& af = entry["airframe"];
        def.airframe.empty_mass_kg = af.value("empty_mass_kg", 0.0);
        def.airframe.max_fuel_kg = af.value("max_fuel_kg", 0.0);
        def.airframe.drag_coefficient = af.value("drag_coefficient", 0.02);
        def.airframe.reference_area = af.value("reference_area", 27.0);
        
        def.airframe.length_m = af.value("length_m", 15.0);
        def.airframe.wingspan_m = af.value("wingspan_m", 10.0);
        def.airframe.height_m = af.value("height_m", 5.0);
        def.airframe.configuration = af.value("configuration", "Conventional");
        if (af.contains("tuning") && af["tuning"].is_object()) {
            def.airframe.has_tuning = true;
            def.airframe.tuning = flight_dynamics::default_aero_tuning();
            parse_aero_tuning_json_fields(af["tuning"], &def.airframe.tuning);
        }
    }
    if (entry.contains("aero_tuning") && entry["aero_tuning"].is_object()) {
        def.airframe.has_tuning = true;
        if (!def.airframe.tuning.enabled) {
            def.airframe.tuning = flight_dynamics::default_aero_tuning();
        }
        parse_aero_tuning_json_fields(entry["aero_tuning"], &def.airframe.tuning);
    }
    if (entry.contains("stall_state") && entry["stall_state"].is_object()) {
        def.has_stall_state = true;
        parse_stall_state_json_fields(entry["stall_state"], &def.stall_state);
    }

    def.has_ship_platform = false;
    def.ship_platform = {};
    if (entry.contains("ship_platform") && entry["ship_platform"].is_object()) {
        def.has_ship_platform = true;
        const auto& sp = entry["ship_platform"];
        def.ship_platform.displacement_light_kg =
            sp.value("displacement_light_kg", def.ship_platform.displacement_light_kg);
        def.ship_platform.displacement_full_load_kg =
            sp.value("displacement_full_load_kg", def.ship_platform.displacement_full_load_kg);
        def.ship_platform.length_m = sp.value("length_m", def.ship_platform.length_m);
        def.ship_platform.beam_m = sp.value("beam_m", def.ship_platform.beam_m);
        def.ship_platform.draft_m = sp.value("draft_m", def.ship_platform.draft_m);
        def.ship_platform.height_above_waterline_m =
            sp.value("height_above_waterline_m", def.ship_platform.height_above_waterline_m);
        def.ship_platform.max_speed_mps = sp.value("max_speed_mps", def.ship_platform.max_speed_mps);
        def.ship_platform.economical_speed_mps =
            sp.value("economical_speed_mps", def.ship_platform.economical_speed_mps);
        def.ship_platform.range_nm = sp.value("range_nm", def.ship_platform.range_nm);
        def.ship_platform.range_speed_mps = sp.value("range_speed_mps", def.ship_platform.range_speed_mps);
        def.ship_platform.max_accel_mps2 =
            sp.value("max_accel_mps2", def.ship_platform.max_accel_mps2);
        def.ship_platform.max_decel_mps2 =
            sp.value("max_decel_mps2", def.ship_platform.max_decel_mps2);
        def.ship_platform.max_turn_rate_deg_s =
            sp.value("max_turn_rate_deg_s", def.ship_platform.max_turn_rate_deg_s);
        def.ship_platform.low_speed_turn_factor =
            sp.value("low_speed_turn_factor", def.ship_platform.low_speed_turn_factor);
        def.ship_platform.steerageway_speed_mps =
            sp.value("steerageway_speed_mps", def.ship_platform.steerageway_speed_mps);
        def.ship_platform.sea_state = sp.value("sea_state", def.ship_platform.sea_state);
        def.ship_platform.wave_heading_deg =
            sp.value("wave_heading_deg", def.ship_platform.wave_heading_deg);
        def.ship_platform.wave_period_s =
            sp.value("wave_period_s", def.ship_platform.wave_period_s);
        def.ship_platform.max_roll_deg_sea_state_6 =
            sp.value("max_roll_deg_sea_state_6", def.ship_platform.max_roll_deg_sea_state_6);
        def.ship_platform.max_pitch_deg_sea_state_6 =
            sp.value("max_pitch_deg_sea_state_6", def.ship_platform.max_pitch_deg_sea_state_6);
        def.ship_platform.added_resistance_fraction_sea_state_6 = sp.value(
            "added_resistance_fraction_sea_state_6",
            def.ship_platform.added_resistance_fraction_sea_state_6
        );
        def.ship_platform.crew = sp.value("crew", def.ship_platform.crew);
    }

    def.has_submarine_platform = false;
    def.submarine_platform = {};
    if (entry.contains("submarine_platform") && entry["submarine_platform"].is_object()) {
        def.has_submarine_platform = true;
        const auto& sp = entry["submarine_platform"];
        def.submarine_platform.submerged_displacement_kg =
            sp.value("submerged_displacement_kg", def.submarine_platform.submerged_displacement_kg);
        def.submarine_platform.length_m = sp.value("length_m", def.submarine_platform.length_m);
        def.submarine_platform.beam_m = sp.value("beam_m", def.submarine_platform.beam_m);
        def.submarine_platform.draft_m = sp.value("draft_m", def.submarine_platform.draft_m);
        def.submarine_platform.max_speed_submerged_mps =
            sp.value("max_speed_submerged_mps", def.submarine_platform.max_speed_submerged_mps);
        def.submarine_platform.quiet_speed_mps =
            sp.value("quiet_speed_mps", def.submarine_platform.quiet_speed_mps);
        def.submarine_platform.max_accel_mps2 =
            sp.value("max_accel_mps2", def.submarine_platform.max_accel_mps2);
        def.submarine_platform.max_decel_mps2 =
            sp.value("max_decel_mps2", def.submarine_platform.max_decel_mps2);
        def.submarine_platform.max_turn_rate_deg_s =
            sp.value("max_turn_rate_deg_s", def.submarine_platform.max_turn_rate_deg_s);
        def.submarine_platform.max_depth_rate_mps =
            sp.value("max_depth_rate_mps", def.submarine_platform.max_depth_rate_mps);
        def.submarine_platform.nominal_patrol_depth_m =
            sp.value("nominal_patrol_depth_m", def.submarine_platform.nominal_patrol_depth_m);
        def.submarine_platform.max_operating_depth_m =
            sp.value("max_operating_depth_m", def.submarine_platform.max_operating_depth_m);
        def.submarine_platform.acoustic_stealth_bias_db =
            sp.value("acoustic_stealth_bias_db", def.submarine_platform.acoustic_stealth_bias_db);
        def.submarine_platform.self_noise_per_speed_db =
            sp.value("self_noise_per_speed_db", def.submarine_platform.self_noise_per_speed_db);
        def.submarine_platform.crew = sp.value("crew", def.submarine_platform.crew);
    }

    def.has_naval_stores = false;
    def.naval_stores = {};
    if (entry.contains("naval_stores") && entry["naval_stores"].is_object()) {
        def.has_naval_stores = true;
        const auto& stores = entry["naval_stores"];
        def.naval_stores.fuel_units_current =
            stores.value("fuel_units_current", def.naval_stores.fuel_units_current);
        def.naval_stores.fuel_units_max =
            stores.value("fuel_units_max", def.naval_stores.fuel_units_max);
        def.naval_stores.missile_units_current =
            stores.value("missile_units_current", def.naval_stores.missile_units_current);
        def.naval_stores.missile_units_max =
            stores.value("missile_units_max", def.naval_stores.missile_units_max);
        def.naval_stores.dry_cargo_units_current =
            stores.value("dry_cargo_units_current", def.naval_stores.dry_cargo_units_current);
        def.naval_stores.dry_cargo_units_max =
            stores.value("dry_cargo_units_max", def.naval_stores.dry_cargo_units_max);
        def.naval_stores.can_receive_underway =
            stores.value("can_receive_underway", def.naval_stores.can_receive_underway);
        def.naval_stores.can_provide_underway =
            stores.value("can_provide_underway", def.naval_stores.can_provide_underway);
    }

    def.has_naval_logistics = false;
    def.naval_logistics = {};
    if (entry.contains("naval_logistics") && entry["naval_logistics"].is_object()) {
        def.has_naval_logistics = true;
        const auto& logistics = entry["naval_logistics"];
        def.naval_logistics.underway_replenishment_enabled = logistics.value(
            "underway_replenishment_enabled",
            def.naval_logistics.underway_replenishment_enabled
        );
        def.naval_logistics.min_separation_m =
            logistics.value("min_separation_m", def.naval_logistics.min_separation_m);
        def.naval_logistics.max_separation_m =
            logistics.value("max_separation_m", def.naval_logistics.max_separation_m);
        def.naval_logistics.max_relative_speed_mps = logistics.value(
            "max_relative_speed_mps",
            def.naval_logistics.max_relative_speed_mps
        );
        def.naval_logistics.transfer_rate_fuel_units_per_s = logistics.value(
            "transfer_rate_fuel_units_per_s",
            def.naval_logistics.transfer_rate_fuel_units_per_s
        );
        def.naval_logistics.transfer_rate_missile_units_per_s = logistics.value(
            "transfer_rate_missile_units_per_s",
            def.naval_logistics.transfer_rate_missile_units_per_s
        );
        def.naval_logistics.transfer_rate_dry_cargo_units_per_s = logistics.value(
            "transfer_rate_dry_cargo_units_per_s",
            def.naval_logistics.transfer_rate_dry_cargo_units_per_s
        );
    }

    def.has_naval_weapon_system = false;
    def.naval_weapon_system.mounts.clear();
    if (entry.contains("naval_weapon_system") && entry["naval_weapon_system"].is_object()) {
        const auto& nws = entry["naval_weapon_system"];
        if (nws.contains("mounts") && nws["mounts"].is_array()) {
            def.has_naval_weapon_system = true;
            for (const auto& mount_json : nws["mounts"]) {
                if (!mount_json.is_object()) continue;
                NavalWeaponMountDefinition mount{};
                mount.mount_id = mount_json.value("mount_id", "");
                mount.weapon_type = parse_naval_weapon_type(mount_json.value("weapon_type", ""));
                mount.ready_count = mount_json.value("ready_count", 0);
                mount.max_ready_count = mount_json.value("max_ready_count", mount.ready_count);
                mount.ammo_per_shot = mount_json.value("ammo_per_shot", 1);
                mount.cooldown_s = mount_json.value("cooldown_s", 0.0);
                mount.last_fire_time = mount_json.value("last_fire_time", -1.0);
                mount.engagement_range_m = mount_json.value("engagement_range_m", 0.0);
                mount.projectile_speed_mps = mount_json.value("projectile_speed_mps", 0.0);
                mount.hit_probability = mount_json.value("hit_probability", 0.0);
                mount.damage_per_hit = mount_json.value("damage_per_hit", 0.0);
                mount.consumes_ready_count = mount_json.value("consumes_ready_count", true);
                mount.can_intercept_missiles = mount_json.value("can_intercept_missiles", false);
                mount.fire_control_channel = mount_json.value("fire_control_channel", "");
                mount.target_domain = mount_json.value("target_domain", "");
                mount.provenance_note = mount_json.value("provenance_note", "");
                def.naval_weapon_system.mounts.push_back(mount);
            }
        }
    }

    def.has_embarked_air_ops = false;
    def.embarked_air_ops = {};
    if (entry.contains("embarked_air_ops") && entry["embarked_air_ops"].is_object()) {
        def.has_embarked_air_ops = true;
        const auto& ops = entry["embarked_air_ops"];
        def.embarked_air_ops.helo_unit_name =
            ops.value("helo_unit_name", def.embarked_air_ops.helo_unit_name);
        def.embarked_air_ops.launch_altitude_m =
            ops.value("launch_altitude_m", def.embarked_air_ops.launch_altitude_m);
        def.embarked_air_ops.launch_offset_forward_m =
            ops.value("launch_offset_forward_m", def.embarked_air_ops.launch_offset_forward_m);
        def.embarked_air_ops.launch_offset_starboard_m =
            ops.value("launch_offset_starboard_m", def.embarked_air_ops.launch_offset_starboard_m);
        def.embarked_air_ops.recover_range_m =
            ops.value("recover_range_m", def.embarked_air_ops.recover_range_m);
        def.embarked_air_ops.relay_refresh_s =
            ops.value("relay_refresh_s", def.embarked_air_ops.relay_refresh_s);
        def.embarked_air_ops.enabled = ops.value("enabled", true);
        def.embarked_air_ops.relay_oth_targeting =
            ops.value("relay_oth_targeting", def.embarked_air_ops.relay_oth_targeting);
    }

    if (entry.contains("damage_model") && entry["damage_model"].is_object()) {
        const auto& dm = entry["damage_model"];
        if (dm.contains("hitboxes") && dm["hitboxes"].is_array()) {
            int hb_idx = 0;
            for (const auto& hb_json : dm["hitboxes"]) {
                Hitbox hb;
                hb.id = hb_idx++;
                
                if (hb_json.contains("offset") && hb_json["offset"].is_array() && hb_json["offset"].size() >= 3) {
                     hb.offset_x = hb_json["offset"][0];
                     hb.offset_y = hb_json["offset"][1];
                     hb.offset_z = hb_json["offset"][2];
                }
                
                if (hb_json.contains("size") && hb_json["size"].is_array() && hb_json["size"].size() >= 3) {
                     hb.dim_l = hb_json["size"][0];
                     hb.dim_w = hb_json["size"][1];
                     hb.dim_h = hb_json["size"][2];
                }
                
                hb.armor_mm = hb_json.value("armor", 0.0);
                
                if (hb_json.contains("systems") && hb_json["systems"].is_array()) {
                    for (const auto& sys : hb_json["systems"]) {
                        hb.protected_systems.push_back(sys.get<std::string>());
                    }
                }
                if (hb_json.contains("components") && hb_json["components"].is_array()) {
                    for (const auto& component_json : hb_json["components"]) {
                        if (!component_json.is_object()) {
                            continue;
                        }
                        DamageComponent component{};
                        component.name = component_json.value("name", "");
                        component.system = component_json.value("system", component.name);
                        component.redundancy_group_id =
                            component_json.value("redundancy_group_id", "");
                        if (component_json.contains("dependencies") &&
                            component_json["dependencies"].is_array()) {
                            for (const auto& dependency_json : component_json["dependencies"]) {
                                DamageComponentDependency dependency{};
                                if (dependency_json.is_string()) {
                                    dependency.system = dependency_json.get<std::string>();
                                    dependency.target_system = dependency.system;
                                } else if (dependency_json.is_object()) {
                                    dependency.target_system =
                                        dependency_json.value("target_system",
                                            dependency_json.value("system", ""));
                                    dependency.system =
                                        dependency_json.value("system", dependency.target_system);
                                    if (dependency.target_system.empty()) {
                                        dependency.target_system = dependency.system;
                                    }
                                    dependency.scale =
                                        dependency_json.value("scale", dependency.scale);
                                    dependency.edge_type =
                                        dependency_json.value("edge_type", dependency.edge_type);
                                    dependency.threshold =
                                        dependency_json.value("threshold", dependency.threshold);
                                    dependency.delay_s =
                                        dependency_json.value("delay_s", dependency.delay_s);
                                    dependency.direction =
                                        dependency_json.value("direction", dependency.direction);
                                    dependency.provenance =
                                        dependency_json.value("provenance", dependency.provenance);
                                }
                                if (dependency.system.empty()) {
                                    dependency.system = dependency.target_system;
                                }
                                if (dependency.target_system.empty()) {
                                    dependency.target_system = dependency.system;
                                }
                                if (dependency.system.empty() && dependency.target_system.empty()) {
                                    continue;
                                }
                                component.dependencies.push_back(dependency);
                            }
                        }
                        if (component.system.empty()) {
                            continue;
                        }
                        if (component_json.contains("offset") &&
                            component_json["offset"].is_array() &&
                            component_json["offset"].size() >= 3) {
                            component.offset_x = component_json["offset"][0];
                            component.offset_y = component_json["offset"][1];
                            component.offset_z = component_json["offset"][2];
                        } else {
                            component.offset_x = hb.offset_x;
                            component.offset_y = hb.offset_y;
                            component.offset_z = hb.offset_z;
                        }
                        if (component_json.contains("size") &&
                            component_json["size"].is_array() &&
                            component_json["size"].size() >= 3) {
                            component.dim_l = component_json["size"][0];
                            component.dim_w = component_json["size"][1];
                            component.dim_h = component_json["size"][2];
                        } else {
                            component.dim_l = hb.dim_l;
                            component.dim_w = hb.dim_w;
                            component.dim_h = hb.dim_h;
                        }
                        component.armor_mm = component_json.value("armor", hb.armor_mm);
                        component.threshold_scale =
                            component_json.value("threshold_scale", component.threshold_scale);
                        if (component_json.contains("mechanism_thresholds") &&
                            component_json["mechanism_thresholds"].is_object()) {
                            for (const auto& [family, value] :
                                 component_json["mechanism_thresholds"].items()) {
                                if (value.is_number()) {
                                    component.mechanism_threshold_scales[family] =
                                        value.get<double>();
                                }
                            }
                        }
                        component.redundancy_group =
                            component_json.value("redundancy_group", component.redundancy_group);
                        component.redundancy_weight =
                            component_json.value("redundancy_weight", component.redundancy_weight);
                        component.critical = component_json.value("critical", component.critical);
                        hb.components.push_back(component);
                    }
                }
                def.damage_model.hitboxes.push_back(hb);
            }
        }
        def.has_aircraft_vulnerability = false;
        def.aircraft_vulnerability = {};
        if (dm.contains("vulnerability") && dm["vulnerability"].is_object()) {
            const auto& vuln = dm["vulnerability"];
            def.has_aircraft_vulnerability = true;
            def.aircraft_vulnerability.synthetic =
                vuln.value("synthetic", def.aircraft_vulnerability.synthetic);
            def.aircraft_vulnerability.calibrated =
                vuln.value("calibrated", def.aircraft_vulnerability.calibrated);
            def.aircraft_vulnerability.pk_authority =
                vuln.value("pk_authority", def.aircraft_vulnerability.pk_authority);
            def.aircraft_vulnerability.deterministic_fuze_authority =
                vuln.value(
                    "deterministic_fuze_authority",
                    def.aircraft_vulnerability.deterministic_fuze_authority);
            def.aircraft_vulnerability.provenance =
                vuln.value("provenance", def.aircraft_vulnerability.provenance);
            def.aircraft_vulnerability.evidence_dataset_ref =
                vuln.value("evidence_dataset_ref", def.aircraft_vulnerability.evidence_dataset_ref);
            def.aircraft_vulnerability.calibration_status =
                vuln.value("calibration_status", def.aircraft_vulnerability.calibration_status);
            const bool requested_pk_authority = def.aircraft_vulnerability.pk_authority;
            const bool requested_deterministic_fuze_authority =
                def.aircraft_vulnerability.deterministic_fuze_authority;
            const VulnerabilityEvidenceDescriptor* descriptor =
                find_vulnerability_evidence_descriptor(
                    vulnerability_descriptors,
                    def.aircraft_vulnerability);
            def.aircraft_vulnerability.evidence_dataset_valid =
                vulnerability_evidence_descriptor_is_calibrated_match(
                    vulnerability_descriptors,
                    def.aircraft_vulnerability,
                    def.name);
            copy_vulnerability_descriptor_metadata(
                descriptor,
                &def.aircraft_vulnerability);
            if (!aircraft_vulnerability_has_calibrated_evidence(def.aircraft_vulnerability)) {
                def.aircraft_vulnerability.effect_scale_authority = false;
                def.aircraft_vulnerability.component_failure_probability_authority = false;
                def.aircraft_vulnerability.pk_authority = false;
                def.aircraft_vulnerability.deterministic_fuze_authority = false;
            } else {
                def.aircraft_vulnerability.pk_authority =
                    requested_pk_authority &&
                    descriptor &&
                    descriptor->pk_authority;
                def.aircraft_vulnerability.deterministic_fuze_authority =
                    requested_deterministic_fuze_authority &&
                    descriptor &&
                    descriptor->deterministic_fuze_authority;
                copy_authoritative_vulnerability_rows(
                    descriptor,
                    &def.aircraft_vulnerability);
            }
            def.aircraft_vulnerability.blast_scale =
                vuln.value("blast_scale", def.aircraft_vulnerability.blast_scale);
            def.aircraft_vulnerability.fragmentation_scale =
                vuln.value("fragmentation_scale", def.aircraft_vulnerability.fragmentation_scale);
            def.aircraft_vulnerability.continuous_rod_scale =
                vuln.value("continuous_rod_scale", def.aircraft_vulnerability.continuous_rod_scale);
            def.aircraft_vulnerability.hit_to_kill_scale =
                vuln.value("hit_to_kill_scale", def.aircraft_vulnerability.hit_to_kill_scale);
            def.aircraft_vulnerability.nose_aspect_scale =
                vuln.value("nose_aspect_scale", def.aircraft_vulnerability.nose_aspect_scale);
            def.aircraft_vulnerability.beam_aspect_scale =
                vuln.value("beam_aspect_scale", def.aircraft_vulnerability.beam_aspect_scale);
            def.aircraft_vulnerability.tail_aspect_scale =
                vuln.value("tail_aspect_scale", def.aircraft_vulnerability.tail_aspect_scale);
            def.aircraft_vulnerability.high_closure_scale =
                vuln.value("high_closure_scale", def.aircraft_vulnerability.high_closure_scale);
            def.aircraft_vulnerability.low_closure_scale =
                vuln.value("low_closure_scale", def.aircraft_vulnerability.low_closure_scale);
            def.aircraft_vulnerability.near_miss_scale =
                vuln.value("near_miss_scale", def.aircraft_vulnerability.near_miss_scale);
            def.aircraft_vulnerability.direct_hit_scale =
                vuln.value("direct_hit_scale", def.aircraft_vulnerability.direct_hit_scale);
        }
    }

    def.has_ammo = entry.value("has_ammo", false);
    def.ammo = {0, 0};
    if (entry.contains("ammo")) {
        def.has_ammo = true;
        const auto& ammo = entry["ammo"];
        def.ammo.missiles_remaining = ammo.value("missiles_remaining", def.ammo.missiles_remaining);
        def.ammo.max_missiles = ammo.value("max_missiles", def.ammo.max_missiles);
    }

    if (def.type == UnitType::Missile) {
        def.has_missile_tuning = true;
        auto& missile_tuning = def.missile_tuning;
        missile_tuning.max_speed = def.flight_model.max_speed;
        missile_tuning.turn_rate = def.flight_model.max_turn_rate;
        missile_tuning.max_lateral_g = def.flight_model.max_g;

        if (entry.contains("missile_tuning") && entry["missile_tuning"].is_object()) {
            parse_missile_tuning_json_fields(entry["missile_tuning"], &missile_tuning);
        }
        if (entry.contains("guidance") && entry["guidance"].is_object()) {
            const auto& guidance = entry["guidance"];
            parse_missile_tuning_json_fields(guidance, &missile_tuning);

            const std::string guidance_type = guidance.value("type", "");
            if (missile_tuning.seeker_type < 0) {
                if (guidance_type == "IR" || guidance_type == "Infrared") {
                    missile_tuning.seeker_type = static_cast<int>(SensorType::Infrared);
                } else if (guidance_type == "ActiveRadar" || guidance_type == "Radar") {
                    missile_tuning.seeker_type = static_cast<int>(SensorType::Radar);
                }
            }

            missile_tuning.seeker_lock_range =
                guidance.value("active_seek_range", missile_tuning.seeker_lock_range);
            missile_tuning.sensor_max_range =
                guidance.value("sensor_max_range", missile_tuning.sensor_max_range);
            missile_tuning.max_launch_off_boresight_deg =
                guidance.value("off_boresight_cap", missile_tuning.max_launch_off_boresight_deg);
            missile_tuning.min_launch_range_m =
                guidance.value("min_launch_range_m", missile_tuning.min_launch_range_m);
            missile_tuning.midcourse_datalink_supported = guidance.value(
                "midcourse_datalink_supported",
                missile_tuning.midcourse_datalink_supported
            );
            missile_tuning.lobl_required = guidance.value(
                "lobl_required",
                missile_tuning.lobl_required
            );
        }
        if (entry.contains("warhead") && entry["warhead"].is_object()) {
            parse_warhead_json_fields(entry["warhead"], &missile_tuning);
        }
        if (entry.contains("fuze") && entry["fuze"].is_object()) {
            parse_fuze_json_fields(entry["fuze"], &missile_tuning);
        }
        if (entry.contains("fuse") && entry["fuse"].is_object()) {
            parse_fuze_json_fields(entry["fuse"], &missile_tuning);
        }
        if (entry.contains("sensor") && entry["sensor"].is_object()) {
            Sensor missile_sensor = make_unit_definition_default_sensor();
            const std::string default_sensor_type =
                missile_tuning.seeker_type == static_cast<int>(SensorType::Infrared)
                    ? "Infrared"
                    : "Radar";
            parse_sensor_json_fields(entry["sensor"], &missile_sensor, default_sensor_type);
            def.has_sensor = true;
            def.sensor = missile_sensor;
            missile_tuning.sensor_max_range =
                entry["sensor"].value("max_range", missile_tuning.sensor_max_range);
            missile_tuning.sensor_fov_deg =
                entry["sensor"].value("fov_deg", missile_tuning.sensor_fov_deg);
            missile_tuning.sensor_scan_period =
                entry["sensor"].value("scan_period", missile_tuning.sensor_scan_period);
            missile_tuning.sensor_detection_prob =
                entry["sensor"].value("detection_prob", missile_tuning.sensor_detection_prob);
            missile_tuning.sensor_bearing_noise_std =
                entry["sensor"].value("bearing_noise_std", missile_tuning.sensor_bearing_noise_std);
            missile_tuning.sensor_range_noise_std =
                entry["sensor"].value("range_noise_std", missile_tuning.sensor_range_noise_std);
            missile_tuning.sensor_track_memory_s =
                entry["sensor"].value("track_memory_s", missile_tuning.sensor_track_memory_s);
            if (missile_tuning.seeker_type < 0) {
                missile_tuning.seeker_type = def.sensor.type;
            }
        } else if (missile_tuning.seeker_type >= 0 || std::isfinite(missile_tuning.sensor_max_range)) {
            def.has_sensor = true;
        }
    }

    def.has_command_link = entry.value("has_command_link", false);
    def.command_link = {0.0, 0.0};
    if (entry.contains("command_link")) {
        def.has_command_link = true;
        const auto& link = entry["command_link"];
        def.command_link.latency_s = link.value("latency_s", def.command_link.latency_s);
        def.command_link.drop_prob = link.value("drop_prob", def.command_link.drop_prob);
    }

    def.has_data_link = entry.value("has_data_link", false);
    def.data_link_network_id = entry.value("data_link_network_id", 0);
    def.data_link_max_reports_per_update = std::max(0, entry.value("data_link_max_reports_per_update", 16));
    def.data_link_max_messages_per_update = entry.contains("data_link_max_messages_per_update")
        ? std::max(0, entry.value("data_link_max_messages_per_update", def.data_link_max_reports_per_update))
        : def.data_link_max_reports_per_update;

    if (entry.contains("rwr") && entry["rwr"].is_object()) {
        const auto& rwr = entry["rwr"];
        def.rwr_data.sensitivity_dbm = rwr.value("sensitivity_dbm", def.rwr_data.sensitivity_dbm);
    }

    if (entry.contains("jammer") && entry["jammer"].is_object()) {
        const auto& jammer = entry["jammer"];
        def.jammer_data.is_active = jammer.value("is_active", def.jammer_data.is_active);
        def.jammer_data.power_watts = jammer.value("power_watts", def.jammer_data.power_watts);
        def.jammer_data.bandwidth_mhz = jammer.value("bandwidth_mhz", def.jammer_data.bandwidth_mhz);
        def.jammer_data.effective_angle = jammer.value("effective_angle", def.jammer_data.effective_angle);
        const std::string jammer_type = jammer.value("type", "NoiseBarrage");
        if (jammer_type == "NoiseSpot") {
            def.jammer_data.type = JammingType::NoiseSpot;
        } else if (jammer_type == "DeceptionDRFM") {
            def.jammer_data.type = JammingType::DeceptionDRFM;
        } else {
            def.jammer_data.type = JammingType::NoiseBarrage;
        }
    }

    if (entry.contains("countermeasures") && entry["countermeasures"].is_object()) {
        const auto& cms = entry["countermeasures"];
        def.cms_data.chaff_count = cms.value("chaff_count", def.cms_data.chaff_count);
        def.cms_data.flare_count = cms.value("flare_count", def.cms_data.flare_count);
        def.cms_data.release_interval = cms.value("release_interval", def.cms_data.release_interval);
        def.cms_data.last_release_time = cms.value("last_release_time", def.cms_data.last_release_time);
        def.cms_data.auto_mode = cms.value("auto_mode", def.cms_data.auto_mode);
    }

    if (entry.contains("esm") && entry["esm"].is_object()) {
        const auto& esm = entry["esm"];
        def.has_esm_data = true;
        def.esm_data.sensitivity_dbm = esm.value("sensitivity_dbm", def.esm_data.sensitivity_dbm);
        def.esm_data.max_detection_range_m =
            esm.value("max_detection_range_m", def.esm_data.max_detection_range_m);
        def.esm_data.classify_emitters =
            esm.value("classify_emitters", def.esm_data.classify_emitters);
    }

    return true;
}

bool load_file(
    const std::string& path,
    std::vector<UnitDefinition>& out_definitions,
    std::string* error,
    const VulnerabilityEvidenceDescriptorMap* vulnerability_descriptors = nullptr
) {
    std::ifstream file(path);
    if (!file.is_open()) {
        if (error) *error = "Failed to open unit definition file: " + path;
        return false;
    }

    nlohmann::json root;
    try {
        file >> root;
    } catch (const std::exception& ex) {
        if (error) *error = std::string("Failed to parse JSON: ") + ex.what();
        return false;
    }

    // Support both single object and array "units"
    // Case 1: Root is array (legacy units_demo.json structure inside "units" key)
    if (root.contains("units") && root["units"].is_array()) {
        for (const auto& entry : root["units"]) {
            UnitDefinition def{};
            if (parse_unit_json(entry, def, error, vulnerability_descriptors)) {
                out_definitions.push_back(def);
            } else {
                return false;
            }
        }
    } 
    // Case 2: Root IS the unit object (single file per unit)
    else if (root.contains("name") && root.contains("type")) {
        UnitDefinition def{};
        if (parse_unit_json(root, def, error, vulnerability_descriptors)) {
            out_definitions.push_back(def);
        } else {
            return false;
        }
    } else {
        if (error) *error = "Invalid unit definition JSON: expected 'units' array or a single unit object.";
        return false;
    }
    
    return true;
}

VulnerabilityEvidenceDescriptorMap load_vulnerability_evidence_descriptors(
    const std::string& root_path
) {
    VulnerabilityEvidenceDescriptorMap descriptors;
    const fs::path base_path(root_path);
    if (!fs::is_directory(base_path)) {
        return descriptors;
    }

    const fs::path evidence_dir = base_path / "damage" / "vulnerability_evidence";
    if (!fs::is_directory(evidence_dir)) {
        return descriptors;
    }

    for (const auto& entry : fs::directory_iterator(evidence_dir)) {
        if (!entry.is_regular_file() || entry.path().extension() != ".json") {
            continue;
        }
        try {
            std::ifstream file(entry.path());
            if (!file.is_open()) {
                continue;
            }
            nlohmann::json root;
            file >> root;
            if (!root.is_object()) {
                continue;
            }
            VulnerabilityEvidenceDescriptor descriptor{};
            descriptor.dataset_id = root.value("dataset_id", "");
            descriptor.schema_version = root.value("schema_version", "");
            descriptor.target_type = root.value("target_type", "");
            descriptor.weapon_family =
                normalize_warhead_family(root.value("weapon_family", ""));
            descriptor.aspect_bucket = root.value("aspect_bucket", "");
            descriptor.closure_bucket = root.value("closure_bucket", "");
            descriptor.miss_distance_bucket = root.value("miss_distance_bucket", "");
            descriptor.calibration_status =
                root.value("calibration_status", descriptor.calibration_status);
            descriptor.source_kind = root.value("source_kind", "");
            descriptor.source_ref = root.value("source_ref", "");
            descriptor.validation_artifact_ref =
                root.value("validation_artifact_ref", "");
            if (root.contains("validation_manifest") &&
                root["validation_manifest"].is_object()) {
                const auto& manifest = root["validation_manifest"];
                descriptor.validation_manifest_schema_version =
                    manifest.value("schema_version", "");
                descriptor.validation_status =
                    manifest.value("validation_status", descriptor.validation_status);
                descriptor.validation_artifact_sha256 =
                    manifest.value("validation_artifact_sha256", "");
                descriptor.validated_surrogate_model_ref =
                    manifest.value("validated_surrogate_model_ref", "");
                descriptor.validation_benchmark_ref =
                    manifest.value("validation_benchmark_ref", "");
                descriptor.validation_metrics_ref =
                    manifest.value("validation_metrics_ref", "");
                descriptor.validation_acceptance_criteria_ref =
                    manifest.value("validation_acceptance_criteria_ref", "");
                if (manifest.contains("validation_scope") &&
                    manifest["validation_scope"].is_object()) {
                    const auto& scope = manifest["validation_scope"];
                    descriptor.validation_scope_target_type =
                        scope.value("target_type", "");
                    descriptor.validation_scope_weapon_family =
                        normalize_warhead_family(scope.value("weapon_family", ""));
                    descriptor.validation_scope_aspect_bucket =
                        scope.value("aspect_bucket", "");
                    descriptor.validation_scope_closure_bucket =
                        scope.value("closure_bucket", "");
                    descriptor.validation_scope_miss_distance_bucket =
                        scope.value("miss_distance_bucket", "");
                }
            }
            descriptor.provenance = root.value("provenance", "");
            descriptor.effect_scale_authority =
                root.value("effect_scale_authority", false);
            descriptor.component_failure_probability_authority =
                root.value("component_failure_probability_authority", false);
            descriptor.pk_authority = root.value("pk_authority", false);
            descriptor.deterministic_fuze_authority =
                false;
            if (root.contains("rows") && root["rows"].is_array()) {
                for (const auto& row_json : root["rows"]) {
                    if (!row_json.is_object()) {
                        continue;
                    }
                    AircraftVulnerabilityEvidenceRow row{};
                    row.row_id = row_json.value("row_id", "");
                    row.source_ref = row_json.value("source_ref", "");
                    row.provenance = row_json.value("provenance", "");
                    row.weapon_family = normalize_warhead_family(
                        row_json.value("weapon_family", descriptor.weapon_family));
                    row.aspect_bucket =
                        row_json.value("aspect_bucket", descriptor.aspect_bucket);
                    row.closure_bucket =
                        row_json.value("closure_bucket", descriptor.closure_bucket);
                    row.miss_distance_bucket =
                        row_json.value(
                            "miss_distance_bucket",
                            descriptor.miss_distance_bucket);
                    row.component_name = row_json.value("component_name", "");
                    row.component_system = row_json.value("component_system", "");
                    row.component_redundancy_group_id =
                        row_json.value("component_redundancy_group_id", "");
                    row.family_scale = row_json.value("family_scale", row.family_scale);
                    row.aspect_scale = row_json.value("aspect_scale", row.aspect_scale);
                    row.closure_scale = row_json.value("closure_scale", row.closure_scale);
                    row.miss_distance_scale =
                        row_json.value(
                            "miss_distance_scale",
                            row.miss_distance_scale);
                    row.effect_scale = row_json.value("effect_scale", row.effect_scale);
                    if (row_json.contains("component_failure_probability") &&
                        row_json["component_failure_probability"].is_number()) {
                        row.has_component_failure_probability = true;
                        row.component_failure_probability =
                            row_json["component_failure_probability"].get<double>();
                    }
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_fragment_energy_j",
                        &row.has_min_fragment_energy_j,
                        &row.min_fragment_energy_j);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_fragment_energy_j",
                        &row.has_max_fragment_energy_j,
                        &row.max_fragment_energy_j);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_fragment_areal_density_per_m2",
                        &row.has_min_fragment_areal_density_per_m2,
                        &row.min_fragment_areal_density_per_m2);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_fragment_areal_density_per_m2",
                        &row.has_max_fragment_areal_density_per_m2,
                        &row.max_fragment_areal_density_per_m2);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_penetration_margin",
                        &row.has_min_penetration_margin,
                        &row.min_penetration_margin);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_penetration_margin",
                        &row.has_max_penetration_margin,
                        &row.max_penetration_margin);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_blast_overpressure_kpa",
                        &row.has_min_blast_overpressure_kpa,
                        &row.min_blast_overpressure_kpa);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_blast_overpressure_kpa",
                        &row.has_max_blast_overpressure_kpa,
                        &row.max_blast_overpressure_kpa);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_blast_impulse_kpa_ms",
                        &row.has_min_blast_impulse_kpa_ms,
                        &row.min_blast_impulse_kpa_ms);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_blast_impulse_kpa_ms",
                        &row.has_max_blast_impulse_kpa_ms,
                        &row.max_blast_impulse_kpa_ms);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_blast_scaled_distance_m_kg13",
                        &row.has_min_blast_scaled_distance_m_kg13,
                        &row.min_blast_scaled_distance_m_kg13);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_blast_scaled_distance_m_kg13",
                        &row.has_max_blast_scaled_distance_m_kg13,
                        &row.max_blast_scaled_distance_m_kg13);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_rod_cut_margin",
                        &row.has_min_rod_cut_margin,
                        &row.min_rod_cut_margin);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_rod_cut_margin",
                        &row.has_max_rod_cut_margin,
                        &row.max_rod_cut_margin);
                    parse_optional_evidence_row_number(
                        row_json,
                        "min_surface_incidence_cos",
                        &row.has_min_surface_incidence_cos,
                        &row.min_surface_incidence_cos);
                    parse_optional_evidence_row_number(
                        row_json,
                        "max_surface_incidence_cos",
                        &row.has_max_surface_incidence_cos,
                        &row.max_surface_incidence_cos);
                    descriptor.rows.push_back(row);
                }
            }
            if (descriptor.dataset_id.empty() || descriptor.target_type.empty()) {
                continue;
            }
            descriptors[descriptor.dataset_id] = descriptor;
        } catch (const std::exception& ex) {
            spdlog::warn(
                "Failed to load vulnerability evidence descriptor {}: {}",
                entry.path().string(),
                ex.what());
        }
    }
    return descriptors;
}

bool load_unit_definitions_json(const std::string& path,
                                std::vector<UnitDefinition>& out_definitions,
                                std::string* error) {
    if (fs::is_directory(path)) {
        const fs::path vulnerability_evidence_dir =
            fs::path(path) / "damage" / "vulnerability_evidence";
        const VulnerabilityEvidenceDescriptorMap vulnerability_descriptors =
            load_vulnerability_evidence_descriptors(path);
        // Recursive scan
        for (const auto& entry : fs::recursive_directory_iterator(path)) {
            if (entry.is_regular_file() && entry.path().extension() == ".json") {
                if (entry.path().parent_path() == vulnerability_evidence_dir) {
                    continue;
                }
                if (!load_file(
                        entry.path().string(),
                        out_definitions,
                        error,
                        &vulnerability_descriptors)) {
                    spdlog::warn("Failed to load file {}: {}", entry.path().string(), (error ? *error : "unknown"));
                    // Continue loading others? For now, yes, just warn.
                }
            }
        }
        return true;
    } else {
        return load_file(path, out_definitions, error);
    }
}
