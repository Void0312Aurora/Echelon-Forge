// Scenario-settings owner codec: the environment settings and missile tuning a
// scenario applies to a SimulationKernel through setters. Loaded content
// (terrain raster, Arnis bundles, unit definitions) is a separate owner.
//
// Every double travels as the hex of its IEEE-754 bits, so NaN "unset" values
// and the sign of zero survive. Unknown or missing keys reject the payload.
// The field tables must list every member of their struct; the state transfer
// contract test compares them, and pins this file's codec digest.

#include "simulation_kernel_state_owner_adapters.h"

#include "core/engine/simulation_kernel.h"
#include "core/engine/simulation_kernel_missile_tuning.h"
#include "core/interfaces/environment_model.h"

#include <nlohmann/json.hpp>

#include <bit>
#include <charconv>
#include <cstdint>
#include <initializer_list>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// clang-format off
#define EF_SCENARIO_MISSILE_TUNING_DOUBLE_FIELDS(X)                                                \
    X(max_speed) X(turn_rate) X(fuse_distance) X(damage) X(seeker_fov_deg)                         \
    X(seeker_lock_range) X(guidance_delay_s) X(guidance_update_period_s) X(max_flight_time_s)      \
    X(nav_gain) X(target_tracker_alpha) X(target_tracker_beta) X(target_tracker_gamma)             \
    X(sensor_max_range) X(sensor_fov_deg) X(sensor_scan_period) X(sensor_detection_prob)           \
    X(sensor_bearing_noise_std) X(sensor_range_noise_std) X(sensor_track_memory_s)                 \
    X(seeker_activation_range_m) X(seeker_gimbal_limit_deg) X(seeker_ifov_deg)                     \
    X(bearing_filter_tau_s) X(elevation_filter_tau_s) X(range_filter_tau_s)                        \
    X(track_break_time_s) X(boost_time_s) X(sustain_time_s) X(boost_thrust_n)                      \
    X(sustain_thrust_n) X(reference_area_m2) X(cd0_subsonic) X(cd0_supersonic)                     \
    X(induced_drag_k) X(propellant_mass_kg) X(max_lateral_g) X(autopilot_tau_s)                    \
    X(autopilot_damping) X(max_accel_response_g_per_s) X(mach_transonic_start)                     \
    X(mach_transonic_end) X(cd0_power_on_ratio) X(min_launch_range_m)                              \
    X(max_launch_off_boresight_deg) X(apn_target_accel_gain) X(seeker_decoy_rejection)             \
    X(seeker_resolution_cell_m)
#define EF_SCENARIO_MISSILE_TUNING_INT_FIELDS(X)                                                   \
    X(pn_los_rate_source) X(target_kinematics_estimator) X(capture_guidance_mode)                  \
    X(seeker_type) X(autopilot_order)
#define EF_SCENARIO_MISSILE_TUNING_VECTOR_FIELDS(X)                                                \
    X(cd0_mach_breakpoints) X(cd0_mach_values) X(induced_drag_k_mach_breakpoints)                  \
    X(induced_drag_k_mach_values)
#define EF_SCENARIO_MISSILE_TUNING_BOOL_FIELDS(X)                                                  \
    X(lobl_required) X(midcourse_datalink_supported) X(use_kalman_seeker)                          \
    X(has_warhead_profile) X(has_fuze_profile)
#define EF_SCENARIO_WARHEAD_STRING_FIELDS(X)                                                       \
    X(family) X(fragment_angular_distribution) X(continuous_rod_spatial_model) X(provenance)
#define EF_SCENARIO_WARHEAD_DOUBLE_FIELDS(X)                                                       \
    X(mass_kg) X(lethal_radius_m) X(damage_scalar) X(explosive_mass_kg) X(case_mass_kg)            \
    X(gurney_constant_mps) X(fragment_mass_kg) X(fragment_count)                                   \
    X(fragment_polar_concentration) X(fragment_isotropic_fraction)                                 \
    X(fragment_azimuthal_modulation) X(fragment_azimuthal_phase_deg)                               \
    X(continuous_rod_band_half_angle_deg) X(continuous_rod_azimuthal_phase_deg)                    \
    X(projection_radius_fraction) X(projection_min_radius_m) X(projection_max_radius_m)            \
    X(projection_min_effect_scale) X(projection_curve_floor_effect_scale)                          \
    X(projection_max_effect_scale) X(projection_falloff_exponent)
#define EF_SCENARIO_WARHEAD_UINT32_FIELDS(X)                                                       \
    X(fragment_azimuthal_lobes) X(continuous_rod_azimuthal_samples)                                \
    X(continuous_rod_polar_samples) X(projection_max_projected_hitboxes)
#define EF_SCENARIO_WARHEAD_BOOL_FIELDS(X)                                                         \
    X(projection_near_field_floor_enabled) X(synthetic) X(damage_scalar_synthetic)
#define EF_SCENARIO_FUZE_STRING_FIELDS(X)                                                          \
    X(type) X(trigger_logic) X(coverage_profile) X(provenance)
#define EF_SCENARIO_FUZE_DOUBLE_FIELDS(X) X(trigger_radius_m) X(delay_s) X(reliability)
#define EF_SCENARIO_FUZE_BOOL_FIELDS(X) X(synthetic)

// Exact key count of each encoded object; a payload with more or fewer keys
// is rejected.
#define EF_COUNT(name) +1
constexpr std::size_t kWarheadKeyCount =
    0 EF_SCENARIO_WARHEAD_STRING_FIELDS(EF_COUNT) EF_SCENARIO_WARHEAD_UINT32_FIELDS(EF_COUNT)
        EF_SCENARIO_WARHEAD_BOOL_FIELDS(EF_COUNT) EF_SCENARIO_WARHEAD_DOUBLE_FIELDS(EF_COUNT);
constexpr std::size_t kFuzeKeyCount =
    0 EF_SCENARIO_FUZE_STRING_FIELDS(EF_COUNT) EF_SCENARIO_FUZE_BOOL_FIELDS(EF_COUNT)
        EF_SCENARIO_FUZE_DOUBLE_FIELDS(EF_COUNT);
// The tables plus the two profiles and explicit_overrides.
constexpr std::size_t kMissileTuningKeyCount =
    3 EF_SCENARIO_MISSILE_TUNING_INT_FIELDS(EF_COUNT)
        EF_SCENARIO_MISSILE_TUNING_BOOL_FIELDS(EF_COUNT)
            EF_SCENARIO_MISSILE_TUNING_DOUBLE_FIELDS(EF_COUNT)
                EF_SCENARIO_MISSILE_TUNING_VECTOR_FIELDS(EF_COUNT);
#undef EF_COUNT
// clang-format on

namespace runtime::host::integration {

namespace {

using Json = nlohmann::json;

constexpr std::string_view kScenarioSettingsSchema = "scenario-settings.v1";

std::string f64_hex(double value) {
    constexpr char hex[] = "0123456789abcdef";
    std::uint64_t bits = std::bit_cast<std::uint64_t>(value);
    std::string encoded(16, '0');
    for (std::size_t index = 0; index < encoded.size(); ++index) {
        encoded[encoded.size() - index - 1] = hex[bits & 0xfU];
        bits >>= 4U;
    }
    return encoded;
}

// Lower-case, exactly 16 digits, so every value has one encoding.
double f64_from(const Json &encoded) {
    const auto &text = encoded.get_ref<const std::string &>();
    if (text.size() != 16 || text.find_first_not_of("0123456789abcdef") != std::string::npos) {
        throw std::runtime_error("scenario settings double is not 16 lower-case hex digits");
    }
    std::uint64_t bits = 0;
    const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), bits, 16);
    if (error != std::errc{} || end != text.data() + text.size()) {
        throw std::runtime_error("scenario settings double is malformed");
    }
    return std::bit_cast<double>(bits);
}

// The reader consumes exactly these keys and no others.
void require_keys(const Json &object, std::initializer_list<std::string_view> keys) {
    if (!object.is_object() || object.size() != keys.size()) {
        throw std::runtime_error("scenario settings object has missing or unknown keys");
    }
    for (const std::string_view key : keys) {
        if (!object.contains(std::string(key))) {
            throw std::runtime_error("scenario settings object is missing a key");
        }
    }
}

void require_key_count(const Json &object, std::size_t expected) {
    if (!object.is_object() || object.size() != expected) {
        throw std::runtime_error("scenario settings object has missing or unknown keys");
    }
}

Json encode_warhead(const WarheadProfile &profile) {
    Json encoded = Json::object();
#define EF_ENCODE(name) encoded[#name] = profile.name;
    EF_SCENARIO_WARHEAD_STRING_FIELDS(EF_ENCODE)
    EF_SCENARIO_WARHEAD_UINT32_FIELDS(EF_ENCODE)
    EF_SCENARIO_WARHEAD_BOOL_FIELDS(EF_ENCODE)
#undef EF_ENCODE
#define EF_ENCODE_DOUBLE(name) encoded[#name] = f64_hex(profile.name);
    EF_SCENARIO_WARHEAD_DOUBLE_FIELDS(EF_ENCODE_DOUBLE)
#undef EF_ENCODE_DOUBLE
    return encoded;
}

WarheadProfile decode_warhead(const Json &encoded) {
    require_key_count(encoded, kWarheadKeyCount);
    WarheadProfile profile{};
#define EF_DECODE_STRING(name) profile.name = encoded.at(#name).get<std::string>();
    EF_SCENARIO_WARHEAD_STRING_FIELDS(EF_DECODE_STRING)
#undef EF_DECODE_STRING
#define EF_DECODE_UINT32(name) profile.name = encoded.at(#name).get<std::uint32_t>();
    EF_SCENARIO_WARHEAD_UINT32_FIELDS(EF_DECODE_UINT32)
#undef EF_DECODE_UINT32
#define EF_DECODE_BOOL(name) profile.name = encoded.at(#name).get<bool>();
    EF_SCENARIO_WARHEAD_BOOL_FIELDS(EF_DECODE_BOOL)
#undef EF_DECODE_BOOL
#define EF_DECODE_DOUBLE(name) profile.name = f64_from(encoded.at(#name));
    EF_SCENARIO_WARHEAD_DOUBLE_FIELDS(EF_DECODE_DOUBLE)
#undef EF_DECODE_DOUBLE
    return profile;
}

Json encode_fuze(const FuzeProfile &profile) {
    Json encoded = Json::object();
#define EF_ENCODE(name) encoded[#name] = profile.name;
    EF_SCENARIO_FUZE_STRING_FIELDS(EF_ENCODE)
    EF_SCENARIO_FUZE_BOOL_FIELDS(EF_ENCODE)
#undef EF_ENCODE
#define EF_ENCODE_DOUBLE(name) encoded[#name] = f64_hex(profile.name);
    EF_SCENARIO_FUZE_DOUBLE_FIELDS(EF_ENCODE_DOUBLE)
#undef EF_ENCODE_DOUBLE
    return encoded;
}

FuzeProfile decode_fuze(const Json &encoded) {
    require_key_count(encoded, kFuzeKeyCount);
    FuzeProfile profile{};
#define EF_DECODE_STRING(name) profile.name = encoded.at(#name).get<std::string>();
    EF_SCENARIO_FUZE_STRING_FIELDS(EF_DECODE_STRING)
#undef EF_DECODE_STRING
#define EF_DECODE_BOOL(name) profile.name = encoded.at(#name).get<bool>();
    EF_SCENARIO_FUZE_BOOL_FIELDS(EF_DECODE_BOOL)
#undef EF_DECODE_BOOL
#define EF_DECODE_DOUBLE(name) profile.name = f64_from(encoded.at(#name));
    EF_SCENARIO_FUZE_DOUBLE_FIELDS(EF_DECODE_DOUBLE)
#undef EF_DECODE_DOUBLE
    return profile;
}

Json encode_f64_vector(const std::vector<double> &values) {
    Json encoded = Json::array();
    for (const double value : values) {
        encoded.push_back(f64_hex(value));
    }
    return encoded;
}

std::vector<double> decode_f64_vector(const Json &encoded) {
    if (!encoded.is_array()) {
        throw std::runtime_error("scenario settings vector is not an array");
    }
    std::vector<double> values;
    values.reserve(encoded.size());
    for (const Json &element : encoded) {
        values.push_back(f64_from(element));
    }
    return values;
}

Json encode_missile_tuning(const MissileTuning &tuning) {
    Json encoded = Json::object();
#define EF_ENCODE(name) encoded[#name] = tuning.name;
    EF_SCENARIO_MISSILE_TUNING_INT_FIELDS(EF_ENCODE)
    EF_SCENARIO_MISSILE_TUNING_BOOL_FIELDS(EF_ENCODE)
#undef EF_ENCODE
#define EF_ENCODE_DOUBLE(name) encoded[#name] = f64_hex(tuning.name);
    EF_SCENARIO_MISSILE_TUNING_DOUBLE_FIELDS(EF_ENCODE_DOUBLE)
#undef EF_ENCODE_DOUBLE
#define EF_ENCODE_VECTOR(name) encoded[#name] = encode_f64_vector(tuning.name);
    EF_SCENARIO_MISSILE_TUNING_VECTOR_FIELDS(EF_ENCODE_VECTOR)
#undef EF_ENCODE_VECTOR
    encoded["warhead_profile"] = encode_warhead(tuning.warhead_profile);
    encoded["fuze_profile"] = encode_fuze(tuning.fuze_profile);
    encoded["explicit_overrides"] = tuning.explicit_overrides;
    return encoded;
}

MissileTuning decode_missile_tuning(const Json &encoded) {
    require_key_count(encoded, kMissileTuningKeyCount);
    MissileTuning tuning{};
#define EF_DECODE_INT(name) tuning.name = encoded.at(#name).get<int>();
    EF_SCENARIO_MISSILE_TUNING_INT_FIELDS(EF_DECODE_INT)
#undef EF_DECODE_INT
#define EF_DECODE_BOOL(name) tuning.name = encoded.at(#name).get<bool>();
    EF_SCENARIO_MISSILE_TUNING_BOOL_FIELDS(EF_DECODE_BOOL)
#undef EF_DECODE_BOOL
#define EF_DECODE_DOUBLE(name) tuning.name = f64_from(encoded.at(#name));
    EF_SCENARIO_MISSILE_TUNING_DOUBLE_FIELDS(EF_DECODE_DOUBLE)
#undef EF_DECODE_DOUBLE
#define EF_DECODE_VECTOR(name) tuning.name = decode_f64_vector(encoded.at(#name));
    EF_SCENARIO_MISSILE_TUNING_VECTOR_FIELDS(EF_DECODE_VECTOR)
#undef EF_DECODE_VECTOR
    tuning.warhead_profile = decode_warhead(encoded.at("warhead_profile"));
    tuning.fuze_profile = decode_fuze(encoded.at("fuze_profile"));
    tuning.explicit_overrides = encoded.at("explicit_overrides").get<std::uint8_t>();
    return tuning;
}

Json encode_zone(const IEnvironmentModel::ZoneSettings &zone) {
    return {
        {"name", zone.name},
        {"center_x", f64_hex(zone.center_x)},
        {"center_y", f64_hex(zone.center_y)},
        {"center_z", f64_hex(zone.center_z)},
        {"width", f64_hex(zone.width)},
        {"length", f64_hex(zone.length)},
        {"heading_deg", f64_hex(zone.heading_deg)},
        {"type", zone.type},
        {"surface", static_cast<int>(zone.surface)},
        {"friction", f64_hex(zone.friction)},
        {"roughness", f64_hex(zone.roughness)},
        {"vegetation_density", f64_hex(zone.vegetation_density)},
        {"runway_heading_deg", f64_hex(zone.runway_heading_deg)},
        {"z_order", zone.z_order},
    };
}

IEnvironmentModel::ZoneSettings decode_zone(const Json &encoded) {
    require_keys(encoded, {"name", "center_x", "center_y", "center_z", "width", "length",
                           "heading_deg", "type", "surface", "friction", "roughness",
                           "vegetation_density", "runway_heading_deg", "z_order"});
    const int surface = encoded.at("surface").get<int>();
    if (surface < static_cast<int>(IEnvironmentModel::SurfaceType::Concrete) ||
        surface > static_cast<int>(IEnvironmentModel::SurfaceType::Obstacle)) {
        throw std::runtime_error("scenario settings zone surface is out of range");
    }
    return {
        .name = encoded.at("name").get<std::string>(),
        .center_x = f64_from(encoded.at("center_x")),
        .center_y = f64_from(encoded.at("center_y")),
        .center_z = f64_from(encoded.at("center_z")),
        .width = f64_from(encoded.at("width")),
        .length = f64_from(encoded.at("length")),
        .heading_deg = f64_from(encoded.at("heading_deg")),
        .type = encoded.at("type").get<int>(),
        .surface = static_cast<IEnvironmentModel::SurfaceType>(surface),
        .friction = f64_from(encoded.at("friction")),
        .roughness = f64_from(encoded.at("roughness")),
        .vegetation_density = f64_from(encoded.at("vegetation_density")),
        .runway_heading_deg = f64_from(encoded.at("runway_heading_deg")),
        .z_order = encoded.at("z_order").get<int>(),
    };
}

Json encode_environment(const IEnvironmentModel::Settings &settings) {
    Json zones = Json::array();
    for (const auto &zone : settings.zones) {
        zones.push_back(encode_zone(zone));
    }
    return {
        {"wind_speed_mps", f64_hex(settings.wind_speed_mps)},
        {"wind_dir_from_deg", f64_hex(settings.wind_dir_from_deg)},
        {"wind_shear_mps_per_km", f64_hex(settings.wind_shear_mps_per_km)},
        {"sun_azimuth_deg", f64_hex(settings.sun_azimuth_deg)},
        {"sun_elevation_deg", f64_hex(settings.sun_elevation_deg)},
        {"maritime_configured", settings.maritime_state.configured},
        {"sea_state", f64_hex(settings.maritime_state.sea_state)},
        {"wave_heading_deg", f64_hex(settings.maritime_state.wave_heading_deg)},
        {"wave_period_s", f64_hex(settings.maritime_state.wave_period_s)},
        {"anchor_latitude_deg", f64_hex(settings.geodetic_anchor.latitude_deg)},
        {"anchor_longitude_deg", f64_hex(settings.geodetic_anchor.longitude_deg)},
        {"anchor_height_m", f64_hex(settings.geodetic_anchor.height_m)},
        {"flat_terrain", settings.flat_terrain},
        {"zones", std::move(zones)},
    };
}

IEnvironmentModel::Settings decode_environment(const Json &encoded) {
    require_keys(encoded, {"wind_speed_mps", "wind_dir_from_deg", "wind_shear_mps_per_km",
                           "sun_azimuth_deg", "sun_elevation_deg", "maritime_configured",
                           "sea_state", "wave_heading_deg", "wave_period_s", "anchor_latitude_deg",
                           "anchor_longitude_deg", "anchor_height_m", "flat_terrain", "zones"});
    IEnvironmentModel::Settings settings{
        .wind_speed_mps = f64_from(encoded.at("wind_speed_mps")),
        .wind_dir_from_deg = f64_from(encoded.at("wind_dir_from_deg")),
        .wind_shear_mps_per_km = f64_from(encoded.at("wind_shear_mps_per_km")),
        .sun_azimuth_deg = f64_from(encoded.at("sun_azimuth_deg")),
        .sun_elevation_deg = f64_from(encoded.at("sun_elevation_deg")),
        .maritime_state =
            {
                .configured = encoded.at("maritime_configured").get<bool>(),
                .sea_state = f64_from(encoded.at("sea_state")),
                .wave_heading_deg = f64_from(encoded.at("wave_heading_deg")),
                .wave_period_s = f64_from(encoded.at("wave_period_s")),
            },
        .geodetic_anchor =
            {
                .latitude_deg = f64_from(encoded.at("anchor_latitude_deg")),
                .longitude_deg = f64_from(encoded.at("anchor_longitude_deg")),
                .height_m = f64_from(encoded.at("anchor_height_m")),
            },
        .flat_terrain = encoded.at("flat_terrain").get<bool>(),
    };
    const Json &zones = encoded.at("zones");
    if (!zones.is_array()) {
        throw std::runtime_error("scenario settings zones are not an array");
    }
    settings.zones.reserve(zones.size());
    for (const Json &zone : zones) {
        settings.zones.push_back(decode_zone(zone));
    }
    return settings;
}

bool decode_scenario_settings(const std::vector<std::uint8_t> &payload,
                              IEnvironmentModel::Settings *settings,
                              MissileTuning *tuning) noexcept {
    try {
        const Json document = Json::parse(payload.begin(), payload.end());
        require_keys(document, {"schema", "environment", "missile_tuning"});
        if (document.at("schema").get<std::string>() != kScenarioSettingsSchema) {
            return false;
        }
        *settings = decode_environment(document.at("environment"));
        *tuning = decode_missile_tuning(document.at("missile_tuning"));
        return true;
    } catch (const std::exception &) {
        return false;
    }
}

} // namespace

std::string
SimulationKernelStateOwnerBridge::serialize_scenario_settings(SimulationKernel &kernel) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_export_scenario_settings");
    IEnvironmentModel *environment = kernel.environment_model();
    IEnvironmentModel::Settings settings;
    if (environment == nullptr || !environment->export_settings(&settings)) {
        throw std::runtime_error(
            "scenario settings require an environment provider that exports its settings");
    }
    const Json document{
        {"schema", kScenarioSettingsSchema},
        {"environment", encode_environment(settings)},
        {"missile_tuning", encode_missile_tuning(kernel.missile_tuning_)},
    };
    return document.dump();
}

bool SimulationKernelStateOwnerBridge::scenario_settings_well_formed(
    const std::vector<std::uint8_t> &payload) noexcept {
    IEnvironmentModel::Settings settings;
    MissileTuning tuning;
    return decode_scenario_settings(payload, &settings, &tuning);
}

bool SimulationKernelStateOwnerBridge::restore_scenario_settings(
    SimulationKernel &kernel, const std::vector<std::uint8_t> &payload) {
    auto lock = kernel.acquire_composition_operation();
    kernel.ensure_active("state_transfer_restore_scenario_settings");
    IEnvironmentModel *environment = kernel.environment_model();
    IEnvironmentModel::Settings settings;
    MissileTuning tuning;
    if (environment == nullptr || !decode_scenario_settings(payload, &settings, &tuning)) {
        return false;
    }
    // Decode completely before touching any target state, then apply both.
    IEnvironmentModel::Settings before;
    if (!environment->export_settings(&before)) {
        return false;
    }
    const MissileTuning tuning_before = kernel.missile_tuning_;
    try {
        // Validates before it assigns, so a rejected tuning changes nothing.
        kernel.set_missile_tuning(tuning);
    } catch (const std::exception &) {
        return false;
    }
    if (!environment->restore_settings(settings)) {
        kernel.missile_tuning_ = tuning_before;
        (void)environment->restore_settings(before);
        return false;
    }
    kernel.world_state_mutated_ = true;
    return true;
}

} // namespace runtime::host::integration
