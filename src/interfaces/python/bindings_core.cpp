#include "interfaces/python/binding_utils.h"

#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <flecs.h>
#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/combat/common/missile_guidance_mechanism_profile.h"
#include "components/combat/common/weapon_common.h"
#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/legacy_command_bridge.h"
#include "components/physics/dynamics.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/physics/control_surface.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/ew.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/systems/track_management.h"
#include "components/visual/visual_sensor.h"
#include "core/engine/simulation_kernel.h"
#include "core/interfaces/observation.h"
#include "core/interfaces/unit_data.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {
const char *default_unit_name_for(UnitType type) {
    switch (type) {
    case UnitType::Aircraft:
        return "Aircraft";
    case UnitType::Ship:
        return "Ship";
    case UnitType::Submarine:
        return "Submarine";
    case UnitType::Ground:
        return "Ground_Platoon_MVP";
    case UnitType::Missile:
        return "Missile";
    case UnitType::Facility:
        return "Facility";
    case UnitType::C2Node:
        return "AWACS";
    default:
        throw std::invalid_argument(
            "Unsupported UnitType for spawn_unit (use type_name string instead)");
    }
}

struct SensorDebugView {
    double max_range = 0.0;
    double detection_prob = 0.0;
    double reference_snr_db = 0.0;
    double reference_range_m = 0.0;
    double reference_rcs_m2 = 0.0;
    double pfa = 0.0;
    int confirm_hits_m = 0;
    int confirm_window_n = 0;
    double bearing_noise_std = 0.0;
    double range_noise_std = 0.0;
    double velocity_noise_std = 0.0;
    double alpha_beta_alpha = 0.0;
    double alpha_beta_beta = 0.0;
    double range_power = 0.0;
    double track_memory_s = 0.0;
    int type = 0;
};

struct TrackDebugView {
    uint64_t id = 0;
    uint64_t entity_id = 0;
    int status = 0;
    int usability = 0;
    int source = 0;
    int classification = 0;
    double quality = 0.0;
    double confidence = 0.0;
    bool iff_known = false;
    double classification_confidence = 0.0;
    double time_since_update = 0.0;
    double last_local_update_time = -1.0;
    double last_datalink_update_time = -1.0;
    int confirm_hit_count = 0;
    int confirm_miss_count = 0;
    int confirm_window_progress = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double range = 0.0;
    double azimuth = 0.0;
    double elevation = 0.0;
};

struct FlightDynamicsDebugView {
    double max_speed = 0.0;
    double max_turn_rate = 0.0;
    double max_accel = 0.0;
    double max_climb_rate = 0.0;
    double max_g = 0.0;
    double alpha_dot_dps = 0.0;
    double stall_progress = 0.0;
    bool is_stalled = false;
    bool pitch_break_active = false;
    double time_in_stall_s = 0.0;
    double throttle_command = 0.0;
    double throttle_state = 0.0;
    double ab_state = 0.0;
    bool afterburner_active = false;
    double current_tsfc = 0.0;
    double current_thrust_n = 0.0;
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double fuel_leak_rate_kg_s = 0.0;
    double elevator_cmd = 0.0;
    double aileron_cmd = 0.0;
    double rudder_cmd = 0.0;
    double elevator_deflection = 0.0;
    double aileron_deflection = 0.0;
    double rudder_deflection = 0.0;
};

void bind_simulation_kernel_maintained_surface(nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_introspection_surface(nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_legacy_compatibility_debug_surface(
    nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_override_surface(nb::class_<SimulationKernel> &kernel);

flecs::entity diagnostics_legacy_binding_entity_quarantine_lookup(SimulationKernel &self,
                                                                  uint64_t entity_id) {
    // WP22-R3 quarantine marker: raw entity binding access must stay localized
    // to diagnostics/legacy helpers instead of widening the maintained surface.
    return self.get_world().entity(entity_id);
}

void diagnostics_mark_read_only_snapshot(nb::dict &out, const char *diagnostics_surface_kind,
                                         const char *runtime_owner_kind) {
    out["diagnostics_only"] = true;
    out["quarantined_surface"] = true;
    out["read_only_snapshot"] = true;
    out["maintained_truth"] = false;
    out["diagnostics_quarantine_marker"] = "WP22-R1-2";
    out["diagnostics_surface_kind"] = diagnostics_surface_kind;
    out["runtime_owner_kind"] = runtime_owner_kind;
}

void diagnostics_quarantined_legacy_movement_bridge_write(flecs::entity e,
                                                          double target_heading_deg,
                                                          double target_speed_mps,
                                                          double target_altitude_m, bool active) {
    // WP22-R1-2 quarantine marker: legacy debug writes must stay bridge-only
    // and must never become maintained command truth or direct component writes.
    if (active) {
        set_compatibility_autopilot_movement_command(e, target_heading_deg, target_speed_mps,
                                                     target_altitude_m);
        return;
    }
    deactivate_compatibility_movement_command(e);
}

SensorDebugView make_sensor_debug_view(const Sensor &sensor) {
    SensorDebugView out{};
    out.max_range = sensor.max_range;
    out.detection_prob = sensor.detection_prob;
    out.reference_snr_db = sensor.reference_snr_db;
    out.reference_range_m = sensor.reference_range_m;
    out.reference_rcs_m2 = sensor.reference_rcs_m2;
    out.pfa = sensor.pfa;
    out.confirm_hits_m = sensor.confirm_hits_m;
    out.confirm_window_n = sensor.confirm_window_n;
    out.bearing_noise_std = sensor.bearing_noise_std;
    out.range_noise_std = sensor.range_noise_std;
    out.velocity_noise_std = sensor.velocity_noise_std;
    out.alpha_beta_alpha = sensor.alpha_beta_alpha;
    out.alpha_beta_beta = sensor.alpha_beta_beta;
    out.range_power = sensor.range_power;
    out.track_memory_s = sensor.track_memory_s;
    out.type = sensor.type;
    return out;
}

TrackDebugView make_track_debug_view(const SystemTrack &track) {
    TrackDebugView out{};
    out.id = track.track_id;
    out.entity_id = track.entity_id;
    out.status = static_cast<int>(track.status);
    out.usability = static_cast<int>(track_usability_for(track));
    out.source = static_cast<int>(track.main_source);
    out.classification = static_cast<int>(track.classification);
    out.quality = track.quality;
    out.confidence = track.confidence;
    out.iff_known = track.iff_known;
    out.classification_confidence = track.classification_confidence;
    out.time_since_update = track.time_since_update;
    out.last_local_update_time = track.last_local_update_time;
    out.last_datalink_update_time = track.last_datalink_update_time;
    out.confirm_hit_count = track.confirm_hit_count;
    out.confirm_miss_count = track.confirm_miss_count;
    out.confirm_window_progress = track.confirm_window_progress;
    out.x = track.x;
    out.y = track.y;
    out.z = track.z;
    out.vx = track.vx;
    out.vy = track.vy;
    out.vz = track.vz;
    out.range = track.range;
    out.azimuth = track.azimuth;
    out.elevation = track.elevation;
    return out;
}
} // namespace

void bind_core(nb::module_ &m) {
    nb::enum_<Side>(m, "Side")
        .value("Blue", Side::Blue)
        .value("Red", Side::Red)
        .value("Neutral", Side::Neutral)
        .value("Unknown", Side::Unknown)
        .export_values();

    nb::class_<RWREvent>(m, "RWREvent")
        .def_ro("source_id", &RWREvent::source_id)
        .def_ro("bearing", &RWREvent::bearing)
        .def_ro("signal_strength", &RWREvent::signal_strength)
        .def_ro("is_lock", &RWREvent::is_lock)
        .def_ro("is_launch", &RWREvent::is_launch);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Submarine", UnitType::Submarine)
        .value("Ground", UnitType::Ground)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility)
        .value("C2Node", UnitType::C2Node);

    nb::enum_<SensorType>(m, "SensorType")
        .value("Visual", SensorType::Visual)
        .value("Infrared", SensorType::Infrared)
        .value("Radar", SensorType::Radar)
        .value("RWR", SensorType::RWR)
        .value("MIDS", SensorType::MIDS)
        .value("ESM", SensorType::ESM)
        .value("Sonar", SensorType::Sonar);

    // Bind InstrumentState
    nb::class_<InstrumentState>(m, "InstrumentState")
        .def(nb::init<>())
        .def_rw("alt_baro", &InstrumentState::alt_baro_m)
        .def_rw("alt_radar", &InstrumentState::alt_radar_m)
        .def_rw("ias", &InstrumentState::ias_mps)
        .def_rw("mach", &InstrumentState::mach)
        .def_rw("vvi", &InstrumentState::vvi_mps)
        .def_rw("pitch", &InstrumentState::pitch_deg)
        .def_rw("roll", &InstrumentState::roll_deg)
        .def_rw("heading", &InstrumentState::heading_deg)
        .def_rw("aoa", &InstrumentState::aoa_deg)
        .def_rw("beta", &InstrumentState::beta_deg)
        .def_rw("g_load", &InstrumentState::g_load_normal)
        .def_rw("g_load_axial", &InstrumentState::g_load_axial)
        .def_rw("p", &InstrumentState::p_deg_s)
        .def_rw("q", &InstrumentState::q_deg_s)
        .def_rw("r", &InstrumentState::r_deg_s)
        .def_rw("engine_rpm", &InstrumentState::engine_rpm_pct)
        .def_rw("engine_temp", &InstrumentState::engine_temp_c)
        .def_rw("fuel_flow", &InstrumentState::fuel_flow_kg_h)
        .def_rw("throttle_pos", &InstrumentState::throttle_pos)
        .def_rw("fuel_internal", &InstrumentState::fuel_internal_kg)
        .def_rw("fuel_external", &InstrumentState::fuel_external_kg)
        .def_rw("gear_pos", &InstrumentState::gear_pos)
        .def_rw("flaps_pos", &InstrumentState::flaps_pos)
        .def_rw("speedbrake_pos", &InstrumentState::speedbrake_pos)
        .def_rw("master_arm", &InstrumentState::master_arm)
        .def_rw("oat", &InstrumentState::oat_c)
        .def_rw("cmd_heading", &InstrumentState::cmd_heading_deg)
        .def_rw("cmd_alt", &InstrumentState::cmd_alt_m)
        .def_rw("cmd_speed", &InstrumentState::cmd_speed_mps)
        .def_rw("rwr_active", &InstrumentState::rwr_active)
        .def_rw("missiles_remaining", &InstrumentState::missiles_remaining)
        // EGI / Navigation
        .def_rw("lat", &InstrumentState::lat_deg)
        .def_rw("lon", &InstrumentState::lon_deg)
        .def_rw("vn", &InstrumentState::vn_mps)
        .def_rw("ve", &InstrumentState::ve_mps)
        .def_rw("vd", &InstrumentState::vd_mps)
        .def_rw("ground_speed", &InstrumentState::ground_speed_mps)
        .def_rw("ground_track", &InstrumentState::ground_track_deg)
        .def_rw("wind_speed", &InstrumentState::wind_speed_mps)
        .def_rw("wind_dir", &InstrumentState::wind_dir_deg)
        .def_rw("gps_available", &InstrumentState::gps_available)
        .def_rw("position_uncertainty", &InstrumentState::position_uncertainty_m)
        // Internal physics (for reward, not observation)
        .def_rw("gear_stress", &InstrumentState::gear_stress)
        .def_rw("gear_collapsed", &InstrumentState::gear_collapsed)
        .def_rw("on_runway", &InstrumentState::on_runway);

    // Bind EGI
    nb::class_<EGI>(m, "EGI")
        .def(nb::init<>())
        .def_rw("lat", &EGI::lat_deg)
        .def_rw("lon", &EGI::lon_deg)
        .def_rw("alt_baro", &EGI::alt_baro_m)
        .def_rw("alt_radar", &EGI::alt_radar_m)
        .def_rw("vn", &EGI::vn_mps)
        .def_rw("ve", &EGI::ve_mps)
        .def_rw("vd", &EGI::vd_mps)
        .def_rw("heading", &EGI::heading_deg)
        .def_rw("pitch", &EGI::pitch_deg)
        .def_rw("roll", &EGI::roll_deg)
        .def_rw("wind_speed", &EGI::wind_speed_mps)
        .def_rw("wind_dir", &EGI::wind_dir_deg)
        .def_rw("drift_lat", &EGI::drift_lat_m)
        .def_rw("drift_lon", &EGI::drift_lon_m)
        .def_rw("drift_alt", &EGI::drift_alt_m)
        .def_rw("pos_uncertainty", &EGI::position_uncertainty_m)
        .def_rw("time_since_fix", &EGI::time_since_last_gps_fix)
        .def_rw("gps_avail", &EGI::gps_available);

    nb::class_<WarheadProfile>(m, "WarheadProfile")
        .def(nb::init<>())
        .def_rw("family", &WarheadProfile::family)
        .def_rw("mass_kg", &WarheadProfile::mass_kg)
        .def_rw("lethal_radius_m", &WarheadProfile::lethal_radius_m)
        .def_rw("damage_scalar", &WarheadProfile::damage_scalar)
        .def_rw("explosive_mass_kg", &WarheadProfile::explosive_mass_kg)
        .def_rw("case_mass_kg", &WarheadProfile::case_mass_kg)
        .def_rw("gurney_constant_mps", &WarheadProfile::gurney_constant_mps)
        .def_rw("fragment_mass_kg", &WarheadProfile::fragment_mass_kg)
        .def_rw("fragment_count", &WarheadProfile::fragment_count)
        .def_rw("projection_radius_fraction", &WarheadProfile::projection_radius_fraction)
        .def_rw("projection_min_radius_m", &WarheadProfile::projection_min_radius_m)
        .def_rw("projection_max_radius_m", &WarheadProfile::projection_max_radius_m)
        .def_rw("projection_min_effect_scale", &WarheadProfile::projection_min_effect_scale)
        .def_rw("projection_max_effect_scale", &WarheadProfile::projection_max_effect_scale)
        .def_rw("projection_falloff_exponent", &WarheadProfile::projection_falloff_exponent)
        .def_rw("projection_max_projected_hitboxes",
                &WarheadProfile::projection_max_projected_hitboxes)
        .def_rw("synthetic", &WarheadProfile::synthetic)
        .def_rw("damage_scalar_synthetic", &WarheadProfile::damage_scalar_synthetic)
        .def_rw("provenance", &WarheadProfile::provenance);

    nb::class_<FuzeProfile>(m, "FuzeProfile")
        .def(nb::init<>())
        .def_rw("type", &FuzeProfile::type)
        .def_rw("trigger_radius_m", &FuzeProfile::trigger_radius_m)
        .def_rw("delay_s", &FuzeProfile::delay_s)
        .def_rw("reliability", &FuzeProfile::reliability)
        .def_rw("trigger_logic", &FuzeProfile::trigger_logic)
        .def_rw("coverage_profile", &FuzeProfile::coverage_profile)
        .def_rw("synthetic", &FuzeProfile::synthetic)
        .def_rw("provenance", &FuzeProfile::provenance);

    // Bind MissileTuning
    nb::class_<MissileTuning>(m, "MissileTuning")
        .def(nb::init<>())
        .def_rw("max_speed", &MissileTuning::max_speed)
        .def_rw("turn_rate", &MissileTuning::turn_rate)
        .def_rw("fuse_distance", &MissileTuning::fuse_distance)
        .def_rw("damage", &MissileTuning::damage)
        .def_rw("seeker_fov_deg", &MissileTuning::seeker_fov_deg)
        .def_rw("seeker_lock_range", &MissileTuning::seeker_lock_range)
        .def_rw("guidance_delay_s", &MissileTuning::guidance_delay_s)
        .def_rw("guidance_update_period_s", &MissileTuning::guidance_update_period_s)
        .def_rw("max_flight_time_s", &MissileTuning::max_flight_time_s)
        .def_rw("nav_gain", &MissileTuning::nav_gain)
        .def_rw("apn_target_accel_gain", &MissileTuning::apn_target_accel_gain)
        .def_rw("autopilot_damping", &MissileTuning::autopilot_damping)
        .def_prop_rw(
            "autopilot_order", [](const MissileTuning &self) { return self.autopilot_order; },
            [](MissileTuning &self, int value) { self.set_autopilot_order_override(value); })
        .def_rw("mach_transonic_start", &MissileTuning::mach_transonic_start)
        .def_rw("mach_transonic_end", &MissileTuning::mach_transonic_end)
        .def_rw("cd0_power_on_ratio", &MissileTuning::cd0_power_on_ratio)
        .def_rw("sensor_max_range", &MissileTuning::sensor_max_range)
        .def_rw("sensor_fov_deg", &MissileTuning::sensor_fov_deg)
        .def_rw("sensor_scan_period", &MissileTuning::sensor_scan_period)
        .def_rw("sensor_detection_prob", &MissileTuning::sensor_detection_prob)
        .def_rw("sensor_bearing_noise_std", &MissileTuning::sensor_bearing_noise_std)
        .def_rw("sensor_range_noise_std", &MissileTuning::sensor_range_noise_std)
        .def_rw("sensor_track_memory_s", &MissileTuning::sensor_track_memory_s)
        .def_rw("seeker_type", &MissileTuning::seeker_type)
        .def_rw("seeker_activation_range_m", &MissileTuning::seeker_activation_range_m)
        .def_rw("seeker_gimbal_limit_deg", &MissileTuning::seeker_gimbal_limit_deg)
        .def_rw("seeker_ifov_deg", &MissileTuning::seeker_ifov_deg)
        .def_rw("bearing_filter_tau_s", &MissileTuning::bearing_filter_tau_s)
        .def_rw("elevation_filter_tau_s", &MissileTuning::elevation_filter_tau_s)
        .def_rw("range_filter_tau_s", &MissileTuning::range_filter_tau_s)
        .def_rw("track_break_time_s", &MissileTuning::track_break_time_s)
        .def_rw("boost_time_s", &MissileTuning::boost_time_s)
        .def_rw("sustain_time_s", &MissileTuning::sustain_time_s)
        .def_rw("boost_thrust_n", &MissileTuning::boost_thrust_n)
        .def_rw("sustain_thrust_n", &MissileTuning::sustain_thrust_n)
        .def_rw("reference_area_m2", &MissileTuning::reference_area_m2)
        .def_rw("cd0_subsonic", &MissileTuning::cd0_subsonic)
        .def_rw("cd0_supersonic", &MissileTuning::cd0_supersonic)
        .def_rw("induced_drag_k", &MissileTuning::induced_drag_k)
        .def_rw("cd0_mach_breakpoints", &MissileTuning::cd0_mach_breakpoints)
        .def_rw("cd0_mach_values", &MissileTuning::cd0_mach_values)
        .def_rw("induced_drag_k_mach_breakpoints", &MissileTuning::induced_drag_k_mach_breakpoints)
        .def_rw("induced_drag_k_mach_values", &MissileTuning::induced_drag_k_mach_values)
        .def_rw("propellant_mass_kg", &MissileTuning::propellant_mass_kg)
        .def_rw("max_lateral_g", &MissileTuning::max_lateral_g)
        .def_rw("autopilot_tau_s", &MissileTuning::autopilot_tau_s)
        .def_rw("max_accel_response_g_per_s", &MissileTuning::max_accel_response_g_per_s)
        .def_rw("min_launch_range_m", &MissileTuning::min_launch_range_m)
        .def_rw("max_launch_off_boresight_deg", &MissileTuning::max_launch_off_boresight_deg)
        .def_prop_rw(
            "lobl_required", [](const MissileTuning &self) { return self.lobl_required; },
            [](MissileTuning &self, bool value) { self.set_lobl_required_override(value); })
        .def_prop_rw("midcourse_datalink_supported",
                     [](const MissileTuning &self) {
                         return self.midcourse_datalink_supported;
                     },
                     [](MissileTuning &self, bool value) {
                         self.set_midcourse_datalink_override(value);
                     })
        .def_prop_rw(
            "use_kalman_seeker", [](const MissileTuning &self) { return self.use_kalman_seeker; },
            [](MissileTuning &self, bool value) { self.set_kalman_seeker_override(value); })
        .def_rw("warhead_profile", &MissileTuning::warhead_profile)
        .def_rw("has_warhead_profile", &MissileTuning::has_warhead_profile)
        .def_rw("fuze_profile", &MissileTuning::fuze_profile)
        .def_rw("has_fuze_profile", &MissileTuning::has_fuze_profile);

    nb::class_<UnitData>(m, "UnitData")
        .def_ro("id", &UnitData::id)
        .def_ro("side", &UnitData::side)
        .def_ro("type", &UnitData::type)
        .def_ro("x", &UnitData::x)
        .def_ro("y", &UnitData::y)
        .def_ro("z", &UnitData::z)
        .def_ro("heading", &UnitData::heading);

    nb::class_<Detection>(m, "Detection")
        .def(nb::init<>())
        .def_rw("target_id", &Detection::target_id)
        .def_rw("range", &Detection::range)
        .def_rw("bearing", &Detection::bearing)
        .def_rw("elevation", &Detection::elevation)
        .def_rw("closing_speed", &Detection::closing_speed)
        .def_rw("signal_strength", &Detection::signal_strength)
        .def_rw("snr_db", &Detection::snr_db)
        .def_rw("detection_prob_used", &Detection::detection_prob_used)
        .def_rw("measured_vr", &Detection::measured_vr)
        .def_rw("sensor_type", &Detection::sensor_type)
        .def_rw("local_sensor_hit", &Detection::local_sensor_hit)
        .def_rw("timestamp", &Detection::timestamp);

    nb::class_<TrackData>(m, "TrackData")
        .def_ro("id", &TrackData::id)
        .def_ro("range", &TrackData::range)
        .def_ro("azimuth", &TrackData::azimuth)
        .def_ro("elevation", &TrackData::elevation)
        .def_ro("closing_speed", &TrackData::closing_speed)
        .def_ro("time_since_update", &TrackData::time_since_update)
        .def_ro("source", &TrackData::source)
        .def_ro("classification", &TrackData::classification)
        .def_ro("status", &TrackData::status)
        .def_ro("quality", &TrackData::quality)
        .def_ro("confidence", &TrackData::confidence)
        .def_ro("usability", &TrackData::usability)
        .def_ro("iff_known", &TrackData::iff_known)
        .def_ro("classification_confidence", &TrackData::classification_confidence);

    nb::class_<SensorDebugView>(m, "SensorDebugView")
        .def_ro("max_range", &SensorDebugView::max_range)
        .def_ro("detection_prob", &SensorDebugView::detection_prob)
        .def_ro("reference_snr_db", &SensorDebugView::reference_snr_db)
        .def_ro("reference_range_m", &SensorDebugView::reference_range_m)
        .def_ro("reference_rcs_m2", &SensorDebugView::reference_rcs_m2)
        .def_ro("pfa", &SensorDebugView::pfa)
        .def_ro("confirm_hits_m", &SensorDebugView::confirm_hits_m)
        .def_ro("confirm_window_n", &SensorDebugView::confirm_window_n)
        .def_ro("bearing_noise_std", &SensorDebugView::bearing_noise_std)
        .def_ro("range_noise_std", &SensorDebugView::range_noise_std)
        .def_ro("velocity_noise_std", &SensorDebugView::velocity_noise_std)
        .def_ro("alpha_beta_alpha", &SensorDebugView::alpha_beta_alpha)
        .def_ro("alpha_beta_beta", &SensorDebugView::alpha_beta_beta)
        .def_ro("range_power", &SensorDebugView::range_power)
        .def_ro("track_memory_s", &SensorDebugView::track_memory_s)
        .def_ro("type", &SensorDebugView::type);

    nb::class_<TrackDebugView>(m, "TrackDebugView")
        .def_ro("id", &TrackDebugView::id)
        .def_ro("entity_id", &TrackDebugView::entity_id)
        .def_ro("status", &TrackDebugView::status)
        .def_ro("usability", &TrackDebugView::usability)
        .def_ro("source", &TrackDebugView::source)
        .def_ro("classification", &TrackDebugView::classification)
        .def_ro("quality", &TrackDebugView::quality)
        .def_ro("confidence", &TrackDebugView::confidence)
        .def_ro("iff_known", &TrackDebugView::iff_known)
        .def_ro("classification_confidence", &TrackDebugView::classification_confidence)
        .def_ro("time_since_update", &TrackDebugView::time_since_update)
        .def_ro("last_local_update_time", &TrackDebugView::last_local_update_time)
        .def_ro("last_datalink_update_time", &TrackDebugView::last_datalink_update_time)
        .def_ro("confirm_hit_count", &TrackDebugView::confirm_hit_count)
        .def_ro("confirm_miss_count", &TrackDebugView::confirm_miss_count)
        .def_ro("confirm_window_progress", &TrackDebugView::confirm_window_progress)
        .def_ro("x", &TrackDebugView::x)
        .def_ro("y", &TrackDebugView::y)
        .def_ro("z", &TrackDebugView::z)
        .def_ro("vx", &TrackDebugView::vx)
        .def_ro("vy", &TrackDebugView::vy)
        .def_ro("vz", &TrackDebugView::vz)
        .def_ro("range", &TrackDebugView::range)
        .def_ro("azimuth", &TrackDebugView::azimuth)
        .def_ro("elevation", &TrackDebugView::elevation);

    nb::class_<FlightDynamicsDebugView>(m, "FlightDynamicsDebugView")
        .def_ro("max_speed", &FlightDynamicsDebugView::max_speed)
        .def_ro("max_turn_rate", &FlightDynamicsDebugView::max_turn_rate)
        .def_ro("max_accel", &FlightDynamicsDebugView::max_accel)
        .def_ro("max_climb_rate", &FlightDynamicsDebugView::max_climb_rate)
        .def_ro("max_g", &FlightDynamicsDebugView::max_g)
        .def_ro("alpha_dot_dps", &FlightDynamicsDebugView::alpha_dot_dps)
        .def_ro("stall_progress", &FlightDynamicsDebugView::stall_progress)
        .def_ro("is_stalled", &FlightDynamicsDebugView::is_stalled)
        .def_ro("pitch_break_active", &FlightDynamicsDebugView::pitch_break_active)
        .def_ro("time_in_stall_s", &FlightDynamicsDebugView::time_in_stall_s)
        .def_ro("throttle_command", &FlightDynamicsDebugView::throttle_command)
        .def_ro("throttle_state", &FlightDynamicsDebugView::throttle_state)
        .def_ro("ab_state", &FlightDynamicsDebugView::ab_state)
        .def_ro("afterburner_active", &FlightDynamicsDebugView::afterburner_active)
        .def_ro("current_tsfc", &FlightDynamicsDebugView::current_tsfc)
        .def_ro("current_thrust_n", &FlightDynamicsDebugView::current_thrust_n)
        .def_ro("mil_thrust_n", &FlightDynamicsDebugView::mil_thrust_n)
        .def_ro("ab_thrust_n", &FlightDynamicsDebugView::ab_thrust_n)
        .def_ro("fuel_leak_rate_kg_s", &FlightDynamicsDebugView::fuel_leak_rate_kg_s)
        .def_ro("elevator_cmd", &FlightDynamicsDebugView::elevator_cmd)
        .def_ro("aileron_cmd", &FlightDynamicsDebugView::aileron_cmd)
        .def_ro("rudder_cmd", &FlightDynamicsDebugView::rudder_cmd)
        .def_ro("elevator_deflection", &FlightDynamicsDebugView::elevator_deflection)
        .def_ro("aileron_deflection", &FlightDynamicsDebugView::aileron_deflection)
        .def_ro("rudder_deflection", &FlightDynamicsDebugView::rudder_deflection);

    nb::class_<AgentObservation>(m, "AgentObservation")
        .def_ro("sim_time", &AgentObservation::sim_time)
        .def_ro("id", &AgentObservation::id)
        .def_ro("x", &AgentObservation::x)
        .def_ro("y", &AgentObservation::y)
        .def_ro("z", &AgentObservation::z)
        .def_ro("vx", &AgentObservation::vx)
        .def_ro("vy", &AgentObservation::vy)
        .def_ro("vz", &AgentObservation::vz)
        .def_ro("heading", &AgentObservation::heading)
        .def_ro("pitch", &AgentObservation::pitch)
        .def_ro("roll", &AgentObservation::roll)
        .def_ro("speed", &AgentObservation::speed)
        .def_ro("health", &AgentObservation::health)
        .def_ro("contacts", &AgentObservation::contacts)
        .def_ro("rwr_warnings", &AgentObservation::rwr_warnings)
        .def_ro("missiles_remaining", &AgentObservation::missiles_remaining)
        .def_ro("can_fire", &AgentObservation::can_fire)
        .def_ro("gear_state", &AgentObservation::gear_state)
        .def_ro("throttle", &AgentObservation::throttle)
        .def_ro("total_reward", &AgentObservation::total_reward);

    nb::class_<RecentEngagementEvents>(m, "RecentEngagementEvents")
        .def(nb::init<>())
        .def_rw("launch_events", &RecentEngagementEvents::launch_events)
        .def_rw("effects_events", &RecentEngagementEvents::effects_events)
        .def_rw("nearest_approach_events", &RecentEngagementEvents::nearest_approach_events)
        .def_rw("fuze_evaluation_events", &RecentEngagementEvents::fuze_evaluation_events)
        .def_rw("warhead_mechanism_events", &RecentEngagementEvents::warhead_mechanism_events)
        .def_rw("spatial_coverage_events", &RecentEngagementEvents::spatial_coverage_events)
        .def_rw("component_load_events", &RecentEngagementEvents::component_load_events)
        .def_rw("component_damage_events", &RecentEngagementEvents::component_damage_events)
        .def_rw("platform_consequence_events", &RecentEngagementEvents::platform_consequence_events)
        .def_rw("structural_breakup_events", &RecentEngagementEvents::structural_breakup_events)
        .def_rw("lifecycle_transition_events", &RecentEngagementEvents::lifecycle_transition_events)
        .def_rw("training_projection_events", &RecentEngagementEvents::training_projection_events)
        .def_rw("damage_reports", &RecentEngagementEvents::damage_reports)
        .def_rw("diagnostics_traces", &RecentEngagementEvents::diagnostics_traces);

    nb::class_<SimulationKernel> simulation_kernel(m, "SimulationKernel");
    simulation_kernel.def(nb::init<>());

    // Maintained SimulationKernel API surface unless a narrower guard marker
    // below explicitly quarantines a diagnostics-only or legacy binding.
    bind_simulation_kernel_maintained_surface(simulation_kernel);
    // Diagnostics-only introspection surface. Keep additions explicit in the
    // WP22-E binding guard allowlist instead of widening maintained API by default.
    bind_simulation_kernel_diagnostics_introspection_surface(simulation_kernel);
    // Legacy compatibility debug surface. This remains quarantined until the
    // movement-command retirement stream owns a replacement or deletion path.
    bind_simulation_kernel_legacy_compatibility_debug_surface(simulation_kernel);
    // Diagnostics override surface. These helpers intentionally bypass the
    // maintained API contract and must stay on an explicit allowlist.
    bind_simulation_kernel_diagnostics_override_surface(simulation_kernel);
}

namespace {
void bind_simulation_kernel_maintained_surface(nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("get_instrument_state", &SimulationKernel::get_instrument_state,
             "Get the instrument state for a unit", nb::arg("entity_id"))
        .def("get_egi_state", &SimulationKernel::get_egi_state, "Get the EGI state for a unit",
             nb::arg("entity_id"))
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"),
             "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step,
             "Get the fixed time step in seconds")
        .def("set_time_step", &SimulationKernel::set_time_step,
             "Set the fixed time step in seconds")
        .def("shutdown", &SimulationKernel::shutdown, "Release simulation kernel resources")
        .def(
            "load_unit_definitions",
            [](SimulationKernel &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok) {
                    spdlog::warn("Failed to load unit definitions: {}", error);
                }
                return ok;
            },
            "Load unit definitions from JSON", nb::arg("path"))
        .def("clear_zones", &SimulationKernel::clear_zones, "Clear all environment zones")
        .def("add_zone", &SimulationKernel::add_zone, "Add a new environment zone", nb::arg("name"),
             nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"), nb::arg("heading"),
             nb::arg("surface_type"))
        .def("set_wind", &SimulationKernel::set_wind,
             "Set global wind (speed m/s, dir_from_deg NAV, shear m/s per km)",
             nb::arg("speed_mps"), nb::arg("dir_from_deg"), nb::arg("shear_mps_per_km") = 0.0)
        .def("set_maritime_state", &SimulationKernel::set_maritime_state,
             "Set global maritime state (sea state, wave heading deg NAV, wave period s)",
             nb::arg("sea_state"), nb::arg("wave_heading_deg") = 0.0,
             nb::arg("wave_period_s") = 8.0)
        .def("clear_maritime_state", &SimulationKernel::clear_maritime_state,
             "Clear global maritime override so platform defaults can apply again")
        .def(
            "get_maritime_state",
            [](SimulationKernel &self) {
                const auto state = self.get_maritime_state();
                return std::make_tuple(state.sea_state, state.wave_heading_deg,
                                       state.wave_period_s);
            },
            "Get global maritime state as (sea_state, wave_heading_deg, wave_period_s)")
        .def("set_terrain_type", &SimulationKernel::set_terrain_type,
             "Set terrain profile ('flat' or explicit compatibility profiles: 'legacy', 'hill', "
             "'gaussian_hill', 'mountain')",
             nb::arg("terrain_type"))
        .def(
            "spawn_unit",
            [](SimulationKernel &self, Side side, const std::string &type, double x, double y,
               double z, double heading, double pitch, double roll, double vx, double vy,
               double vz) {
                auto e = self.spawn_unit(side, type, x, y, z, heading, pitch, roll, vx, vy, vz);
                return e.id();
            },
            "Spawn a unit by name with orientation and return its Entity ID", nb::arg("side"),
            nb::arg("type_name"), nb::arg("x"), nb::arg("y"), nb::arg("z"),
            nb::arg("heading") = 0.0, nb::arg("pitch") = 0.0, nb::arg("roll") = 0.0,
            nb::arg("vx") = 0.0, nb::arg("vy") = 0.0, nb::arg("vz") = 0.0)
        .def(
            "spawn_unit",
            [](SimulationKernel &self, Side side, UnitType type, double x, double y, double z,
               double heading, double pitch, double roll, double vx, double vy, double vz) {
                auto e = self.spawn_unit(side, default_unit_name_for(type), x, y, z, heading, pitch,
                                         roll, vx, vy, vz);
                return e.id();
            },
            "Spawn a default unit for the given UnitType with orientation and return its Entity ID",
            nb::arg("side"), nb::arg("type"), nb::arg("x"), nb::arg("y"), nb::arg("z"),
            nb::arg("heading") = 0.0, nb::arg("pitch") = 0.0, nb::arg("roll") = 0.0,
            nb::arg("vx") = 0.0, nb::arg("vy") = 0.0, nb::arg("vz") = 0.0)
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"),
             nb::arg("altitude_m"))
        .def("set_stick_command", &SimulationKernel::set_unit_stick_command, "Set stick inputs",
             nb::arg("entity_id"), nb::arg("stick_roll"), nb::arg("stick_pitch"),
             nb::arg("throttle"), nb::arg("gear_down") = true)
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"), nb::arg("turn_rate_cmd"), nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"), nb::arg("fire_cmd"), nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false, nb::arg("jettison_tanks") = false)
        .def("set_action_space_config", &SimulationKernel::set_action_space_config,
             "Override action mapping scales for a unit", nb::arg("entity_id"),
             nb::arg("max_turn_rate_deg_s"), nb::arg("max_accel_mps2"),
             nb::arg("max_climb_rate_mps"), nb::arg("min_speed_mps"), nb::arg("max_speed_mps"),
             nb::arg("min_alt_m"), nb::arg("max_alt_m"))
        .def("set_pilot_action", &SimulationKernel::set_pilot_action,
             "Set raw pilot inputs (stick, throttle, etc) for Digital Pilot", nb::arg("entity_id"),
             nb::arg("action"))
        .def("set_mission_command", &SimulationKernel::set_mission_command,
             "Set high-level mission intent for Digital Pilot", nb::arg("entity_id"),
             nb::arg("command"))
        .def("set_task_order", &SimulationKernel::set_task_order,
             "Set the C2 task order for the entity", nb::arg("entity_id"), nb::arg("task_order"))
        .def("set_leader_intent", &SimulationKernel::set_leader_intent,
             "Set the leader-layer intent for the entity", nb::arg("entity_id"),
             nb::arg("leader_intent"))
        .def("set_pilot_report", &SimulationKernel::set_pilot_report,
             "Store the latest pilot report for the entity", nb::arg("entity_id"),
             nb::arg("pilot_report"))
        .def("set_command_lag", &SimulationKernel::set_command_lag,
             "Override command lag time constants for a unit", nb::arg("entity_id"),
             nb::arg("heading_tau_s"), nb::arg("speed_tau_s"), nb::arg("altitude_tau_s"))
        .def("set_command_link", &SimulationKernel::set_command_link,
             "Set command link latency/drop probability", nb::arg("entity_id"),
             nb::arg("latency_s"), nb::arg("drop_prob"))
        .def("set_unit_ammo", &SimulationKernel::set_unit_ammo, "Override unit ammo counts",
             nb::arg("entity_id"), nb::arg("missiles_remaining"), nb::arg("max_missiles"))
        .def("set_weapon_cooldown", &SimulationKernel::set_weapon_cooldown,
             "Override unit weapon cooldown state", nb::arg("entity_id"), nb::arg("cooldown_s"),
             nb::arg("last_fire_time"))
        .def(
            "fire_missile",
            [](SimulationKernel &self, uint64_t attacker_id, uint64_t target_id) {
                auto e = self.fire_missile(attacker_id, target_id);
                return e.id();
            },
            "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        .def("fire_naval_weapon", &SimulationKernel::fire_naval_weapon,
             "Fire a naval weapon mount type at target", nb::arg("attacker_id"),
             nb::arg("target_id"), nb::arg("weapon_type_code"))
        .def("export_recent_engagement_events", &SimulationKernel::export_recent_engagement_events,
             "Export recently captured engagement events")
        .def(
            "get_unit_position",
            [](SimulationKernel &self, uint64_t entity_id) {
                auto p = self.get_unit_position(entity_id);
                return std::make_tuple(p[0], p[1], p[2]);
            },
            "Get unit position (x,y,z)")
        .def(
            "get_unit_velocity",
            [](SimulationKernel &self, uint64_t entity_id) {
                auto v = self.get_unit_velocity(entity_id);
                return std::make_tuple(v[0], v[1], v[2]);
            },
            "Get unit velocity (vx,vy,vz)")
        .def("get_unit_heading", &SimulationKernel::get_unit_heading,
             "Get unit heading in degrees (NAV: 0=North, CW)", nb::arg("entity_id"))
        .def("get_unit_type", &SimulationKernel::get_unit_type, "Get unit type enum value",
             nb::arg("entity_id"))
        .def("is_unit_active", &SimulationKernel::is_unit_active, "Check if unit exists",
             nb::arg("entity_id"))
        .def("get_all_units", &SimulationKernel::get_all_units, "Get all units state")
        .def("get_detections", &SimulationKernel::get_detections, "Get unit sensor contacts")
        .def("get_unit_health", &SimulationKernel::get_unit_health,
             "Get unit health [current, max]")
        .def("get_unit_damage_state", &SimulationKernel::get_unit_damage_state,
             "Get unit damage state [mission, mobility, sensor, survivability]")
        .def("get_unit_fuel", &SimulationKernel::get_unit_fuel, nb::arg("entity_id"),
             "Returns [internal, max_internal, external, max_external]")
        .def("get_task_order", &SimulationKernel::get_task_order, "Get the latest task order",
             nb::arg("entity_id"))
        .def("get_leader_intent", &SimulationKernel::get_leader_intent,
             "Get the latest leader intent", nb::arg("entity_id"))
        .def("get_mission_command", &SimulationKernel::get_mission_command,
             "Get the active mission command", nb::arg("entity_id"))
        .def("get_pilot_report", &SimulationKernel::get_pilot_report, "Get the latest pilot report",
             nb::arg("entity_id"))
        .def("get_agent_observation", &SimulationKernel::get_agent_observation,
             "Get complete agent observation")
        .def(
            "get_visual_observation",
            [](SimulationKernel &self, uint64_t entity_id) {
                size_t shape[3] = {
                    static_cast<size_t>(arb::ARB_HEIGHT),
                    static_cast<size_t>(arb::ARB_WIDTH),
                    static_cast<size_t>(arb::ARB_CHANNELS),
                };
                return visual_tensor_to_numpy<nb::shape<static_cast<size_t>(arb::ARB_HEIGHT),
                                                        static_cast<size_t>(arb::ARB_WIDTH),
                                                        static_cast<size_t>(arb::ARB_CHANNELS)>>(
                    self.get_visual_observation(entity_id), 3, shape);
            },
            "Get ARB visual observation [H, W, C] tensor", nb::arg("entity_id"))
        .def(
            "get_visual_observation_downsampled",
            [](SimulationKernel &self, uint64_t entity_id, int factor) {
                const int downsample = factor > 1 ? factor : 1;
                auto downsampled = self.get_visual_observation_downsampled(entity_id, downsample);
                size_t shape[3] = {
                    static_cast<size_t>(arb::ARB_HEIGHT / downsample),
                    static_cast<size_t>(arb::ARB_WIDTH / downsample),
                    static_cast<size_t>(arb::ARB_CHANNELS),
                };
                return visual_tensor_to_numpy<
                    nb::shape<nb::any, nb::any, static_cast<size_t>(arb::ARB_CHANNELS)>>(
                    std::move(downsampled), 3, shape);
            },
            "Get ARB visual observation [H/f, W/f, C] tensor", nb::arg("entity_id"),
            nb::arg("factor"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, nb::arg("entity_id"),
             nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"));
}

void bind_simulation_kernel_diagnostics_introspection_surface(
    nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("debug_apply_proximity_hit", &SimulationKernel::debug_apply_proximity_hit,
             "Testing helper: apply one synthetic proximity hit to a target",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("damage"),
             nb::arg("fuse_distance"))
        .def("debug_apply_local_proximity_hit", &SimulationKernel::debug_apply_local_proximity_hit,
             "Testing helper: apply one synthetic proximity hit at a target-body local point",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("local_forward_m"),
             nb::arg("local_right_m"), nb::arg("local_up_m"), nb::arg("damage"),
             nb::arg("fuse_distance"))
        .def("debug_apply_profiled_local_proximity_hit",
             &SimulationKernel::debug_apply_profiled_local_proximity_hit,
             "Testing helper: apply one synthetic local proximity hit with an explicit warhead "
             "profile",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("local_forward_m"),
             nb::arg("local_right_m"), nb::arg("local_up_m"), nb::arg("warhead_profile"))
        .def("debug_apply_profiled_local_proximity_hit_with_velocity",
             &SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity,
             "Testing helper: apply one synthetic local proximity hit with warhead profile and "
             "missile velocity",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("local_forward_m"),
             nb::arg("local_right_m"), nb::arg("local_up_m"), nb::arg("warhead_profile"),
             nb::arg("missile_vx_mps"), nb::arg("missile_vy_mps"), nb::arg("missile_vz_mps"))
        .def("debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude",
             &SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude,
             "Testing helper: apply one synthetic local proximity hit with explicit missile "
             "velocity and detonation attitude",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("local_forward_m"),
             nb::arg("local_right_m"), nb::arg("local_up_m"), nb::arg("warhead_profile"),
             nb::arg("missile_vx_mps"), nb::arg("missile_vy_mps"), nb::arg("missile_vz_mps"),
             nb::arg("detonation_heading_deg"), nb::arg("detonation_pitch_deg"),
             nb::arg("detonation_roll_deg"))
        .def(
            "get_sensor_debug_view",
            [](SimulationKernel &self, uint64_t entity_id) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return SensorDebugView{};
                }
                const Sensor *sensor = e.get<Sensor>();
                if (!sensor) {
                    return SensorDebugView{};
                }
                return make_sensor_debug_view(*sensor);
            },
            "Get current runtime sensor tuning fields", nb::arg("entity_id"))
        .def(
            "get_track_debug_view",
            [](SimulationKernel &self, uint64_t entity_id) {
                std::vector<TrackDebugView> out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const TrackDatabase *db = e.get<TrackDatabase>();
                if (!db) {
                    return out;
                }
                out.reserve(db->tracks.size());
                for (const auto &track : db->tracks) {
                    out.push_back(make_track_debug_view(track));
                }
                return out;
            },
            "Get confirmed/coasted runtime track debug view", nb::arg("entity_id"))
        .def(
            "get_tentative_track_debug_view",
            [](SimulationKernel &self, uint64_t entity_id) {
                std::vector<TrackDebugView> out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const TrackDatabase *db = e.get<TrackDatabase>();
                if (!db) {
                    return out;
                }
                out.reserve(db->tentative_tracks.size());
                for (const auto &track : db->tentative_tracks) {
                    out.push_back(make_track_debug_view(track));
                }
                return out;
            },
            "Get tentative runtime track debug view", nb::arg("entity_id"))
        .def(
            "get_flight_dynamics_debug_view",
            [](SimulationKernel &self, uint64_t entity_id) {
                FlightDynamicsDebugView out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                if (const AeroState *aero = e.get<AeroState>()) {
                    out.alpha_dot_dps = aero->angle_of_attack_rate_dps;
                    out.stall_progress = aero->stall_progress;
                }
                if (const FlightModel *flight_model = e.get<FlightModel>()) {
                    out.max_speed = flight_model->max_speed;
                    out.max_turn_rate = flight_model->max_turn_rate;
                    out.max_accel = flight_model->max_accel;
                    out.max_climb_rate = flight_model->max_climb_rate;
                    out.max_g = flight_model->max_g;
                }
                if (const StallState *stall = e.get<StallState>()) {
                    out.stall_progress = stall->stall_progress;
                    out.is_stalled = stall->is_stalled;
                    out.pitch_break_active = stall->pitch_break_active;
                    out.time_in_stall_s = stall->time_in_stall_s;
                }
                if (const Propulsion *propulsion = e.get<Propulsion>()) {
                    out.mil_thrust_n = propulsion->mil_thrust_n;
                    out.ab_thrust_n = propulsion->ab_thrust_n;
                    out.throttle_command = propulsion->throttle_command;
                    out.throttle_state = propulsion->throttle_state;
                    out.ab_state = propulsion->ab_state;
                    out.afterburner_active = propulsion->afterburner_active;
                    out.current_tsfc = propulsion->current_tsfc;
                    out.current_thrust_n = propulsion->current_thrust_n;
                }
                if (const Mass *mass = e.get<Mass>()) {
                    out.fuel_leak_rate_kg_s = mass->fuel_leak_rate_kg_s;
                }
                if (const ControlSurfaceState *surf = e.get<ControlSurfaceState>()) {
                    out.elevator_cmd = surf->elevator_cmd;
                    out.aileron_cmd = surf->aileron_cmd;
                    out.rudder_cmd = surf->rudder_cmd;
                    out.elevator_deflection = surf->elevator_pos;
                    out.aileron_deflection = surf->aileron_pos;
                    out.rudder_deflection = surf->rudder_pos;
                }
                return out;
            },
            "Get flight-dynamics debug state (AoA-rate, stall, propulsion spool)",
            nb::arg("entity_id"))
        .def("debug_get_aircraft_damage_state", &SimulationKernel::debug_get_aircraft_damage_state,
             "Get aircraft-specific damage overlay [structure, flight_control, hydraulic, "
             "hydraulic_pressure, roll_control, pitch_control, yaw_control, control_asymmetry, "
             "propulsion, fuel, avionics, crew, pilot, mission_crew, command_navigation, fire, "
             "fuel_leak, fuel_imbalance, flammable_fluid, ignition_source, fire_suppression, "
             "smoke_heat, engine_fire_zone, wing_fire_zone, fuselage_fire_zone, mission_fire_zone, "
             "structural_overstress, flutter_exposure, forced_landing, flight_control_kill, "
             "propulsion_kill, crew_kill]",
             nb::arg("entity_id"))
        .def("debug_get_aircraft_vulnerability_evidence_state",
             &SimulationKernel::debug_get_aircraft_vulnerability_evidence_state,
             "Get aircraft vulnerability evidence gate [present, synthetic, calibrated_evidence, "
             "pk_authority, deterministic_fuze_authority, evidence_dataset_valid]",
             nb::arg("entity_id"))
        .def("debug_get_aircraft_vulnerability_authority_state",
             &SimulationKernel::debug_get_aircraft_vulnerability_authority_state,
             "Get aircraft vulnerability authority gate [present, synthetic, calibrated_evidence, "
             "effect_scale_authority, component_failure_probability_authority, pk_authority, "
             "deterministic_fuze_authority, evidence_dataset_valid]",
             nb::arg("entity_id"))
        .def("debug_get_naval_weapon_counts", &SimulationKernel::debug_get_naval_weapon_counts,
             "Get naval weapon counts [mounts, ready_vls, ready_gun, ready_ciws]")
        .def("debug_get_naval_stores", &SimulationKernel::debug_get_naval_stores,
             nb::arg("entity_id"),
             "Debug: get [fuel_cur, fuel_max, missile_cur, missile_max, dry_cur, dry_max]")
        .def("debug_get_logistics_node", &SimulationKernel::debug_get_logistics_node,
             nb::arg("entity_id"),
             "Debug: get [supply_radius, infinite, underway_enabled, min_sep, max_sep, "
             "max_rel_speed, fuel_rate, missile_rate, dry_rate]")
        .def("debug_get_resupply_state", &SimulationKernel::debug_get_resupply_state,
             nb::arg("entity_id"),
             "Debug: get [active, kind, partner_id, stage, time_remaining, is_refueling, "
             "is_rearming]")
        .def("debug_get_data_link_state", &SimulationKernel::debug_get_data_link_state,
             nb::arg("entity_id"),
             "Debug: get [report_budget, message_budget, reports_sent_last, messages_sent_last, "
             "reports_dropped_last, messages_dropped_last, reports_sent_total, "
             "messages_sent_total, reports_dropped_total, messages_dropped_total]")
        .def("debug_get_ground_contact_state", &SimulationKernel::debug_get_ground_contact_state,
             nb::arg("entity_id"),
             "Debug: get [on_ground, terrain_z, lifecycle, impact_h_speed, impact_sink_rate, "
             "impact_severity, gear_stress, gear_collapsed, on_runway]")
        .def("debug_get_last_scan_time", &SimulationKernel::debug_get_last_scan_time,
             "Debug: get sensor last_scan_time")
        .def("debug_get_contact_count", &SimulationKernel::debug_get_contact_count,
             "Debug: get ContactList size")
        .def(
            "debug_get_mass_state", &SimulationKernel::debug_get_mass_state,
            "Debug: get [mass_empty, mass_fuel, mass_stores, mass_total, props_empty, props_total]",
            nb::arg("entity_id"))
        .def(
            "debug_get_pending_movement_command",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const PendingMovementCommand *pending = e.get<PendingMovementCommand>();
                if (!pending) {
                    return out;
                }
                diagnostics_mark_read_only_snapshot(out, "diagnostics_pending_transport_shell",
                                                    "mission_command_control_state");
                out["diagnostics_transport_shell"] = true;
                out["transport_shell_kind"] = "pending_legacy_movement_command";
                out["active"] = pending->active;
                out["deliver_time"] = pending->deliver_time;
                out["command_shell_active"] = pending->command.active;
                out["target_heading"] = pending->command.target_heading;
                out["target_speed"] = pending->command.target_speed;
                out["target_altitude"] = pending->command.target_altitude;
                out["use_stick_control"] = pending->command.use_stick_control;
                // WP22-R1-2: read-only transport shell snapshot, not maintained truth.
                out["state_access_mode"] = "read_only_transport_shell";
                out["transport_shell_truth_owner"] = "typed_control_state_pending_delivery";
                if (const MissionCommandControlState *state = e.get<MissionCommandControlState>()) {
                    out["current_control_state_present"] = true;
                    out["current_control_state_active"] = state->active;
                    out["current_control_target_heading_deg"] = state->target_heading_deg;
                    out["current_control_target_speed_mps"] = state->target_speed_mps;
                    out["current_control_target_altitude_m"] = state->target_altitude_m;
                } else {
                    out["current_control_state_present"] = false;
                }
                return out;
            },
            "Debug diagnostics-only read-only transport shell snapshot for pending legacy movement "
            "command state",
            nb::arg("entity_id"))
        .def(
            "debug_get_pending_action_command",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const PendingActionCommand *pending = e.get<PendingActionCommand>();
                if (!pending) {
                    return out;
                }
                diagnostics_mark_read_only_snapshot(out, "diagnostics_pending_transport_shell",
                                                    "typed_action_delivery");
                out["diagnostics_transport_shell"] = true;
                out["transport_shell_kind"] = "pending_legacy_action_command";
                out["active"] = pending->active;
                out["deliver_time"] = pending->deliver_time;
                out["command_shell_active"] = pending->command.active;
                out["turn_rate_cmd"] = pending->command.turn_rate_cmd;
                out["accel_cmd"] = pending->command.accel_cmd;
                out["climb_rate_cmd"] = pending->command.climb_rate_cmd;
                out["fire_cmd"] = pending->command.fire_cmd;
                out["release_chaff"] = pending->command.release_chaff;
                out["release_flare"] = pending->command.release_flare;
                out["jettison_tanks"] = pending->command.jettison_tanks;
                // WP22-R1-2: read-only transport shell snapshot, not maintained truth.
                out["state_access_mode"] = "read_only_transport_shell";
                out["transport_shell_truth_owner"] = "typed_action_pending_delivery";
                return out;
            },
            "Debug diagnostics-only read-only transport shell snapshot for pending legacy action "
            "command state",
            nb::arg("entity_id"))
        .def(
            "debug_get_pending_mission_command_queue",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                nb::list queued;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    out["queued"] = queued;
                    return out;
                }
                const PendingMissionCommand *pending = e.get<PendingMissionCommand>();
                if (pending) {
                    nb::dict pending_out;
                    pending_out["active"] = pending->active;
                    pending_out["deliver_time"] = pending->deliver_time;
                    pending_out["command_code"] = pending->command.command_code;
                    pending_out["priority"] = mission_command_queue_priority(pending->command);
                    pending_out["target_heading"] = pending->command.cmd_heading_deg;
                    pending_out["target_altitude"] = pending->command.cmd_altitude_m;
                    pending_out["target_speed"] = pending->command.cmd_speed_mps;
                    pending_out["assigned_target_id"] = pending->command.assigned_target_id;
                    pending_out["authorization_to_fire"] = pending->command.authorization_to_fire;
                    out["pending"] = pending_out;
                }
                const MissionCommandPendingQueue *queue = e.get<MissionCommandPendingQueue>();
                if (queue) {
                    out["size"] = queue->size;
                    for (std::size_t i = 0; i < queue->size; ++i) {
                        const auto &entry = queue->entries[i];
                        nb::dict entry_out;
                        entry_out["index"] = i;
                        entry_out["deliver_time"] = entry.deliver_time;
                        entry_out["command_code"] = entry.command.command_code;
                        entry_out["priority"] = mission_command_queue_priority(entry.command);
                        entry_out["target_heading"] = entry.command.cmd_heading_deg;
                        entry_out["target_altitude"] = entry.command.cmd_altitude_m;
                        entry_out["target_speed"] = entry.command.cmd_speed_mps;
                        entry_out["assigned_target_id"] = entry.command.assigned_target_id;
                        entry_out["authorization_to_fire"] = entry.command.authorization_to_fire;
                        queued.append(entry_out);
                    }
                } else {
                    out["size"] = 0;
                }
                out["queued"] = queued;
                return out;
            },
            "Debug: get pending mission command queue state", nb::arg("entity_id"))
        .def("debug_get_embarked_helo", &SimulationKernel::debug_get_embarked_helo,
             "Debug: get embarked helo entity id for a host", nb::arg("entity_id"))
        .def(
            "debug_get_missile_runtime_state",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const Missile *missile = e.get<Missile>();
                const Sensor *sensor = e.get<Sensor>();
                const Mass *mass = e.get<Mass>();
                const MassProperties *mass_properties = e.get<MassProperties>();
                if (!missile) {
                    return out;
                }
                out["max_speed_mps"] = missile->max_speed;
                out["turn_rate_deg_s"] = missile->turn_rate;
                out["fuse_distance_m"] = missile->fuse_distance;
                out["damage"] = missile->damage;
                out["warhead_family"] = missile->warhead_profile.family;
                out["warhead_mass_kg"] = missile->warhead_profile.mass_kg;
                out["warhead_lethal_radius_m"] = missile->warhead_profile.lethal_radius_m;
                out["warhead_damage_scalar"] = missile->warhead_profile.damage_scalar;
                out["warhead_profile_synthetic"] = missile->warhead_profile.synthetic;
                out["warhead_damage_scalar_synthetic"] =
                    missile->warhead_profile.damage_scalar_synthetic;
                out["warhead_explosive_mass_kg"] = missile->warhead_profile.explosive_mass_kg;
                out["warhead_case_mass_kg"] = missile->warhead_profile.case_mass_kg;
                out["warhead_gurney_constant_mps"] = missile->warhead_profile.gurney_constant_mps;
                out["warhead_fragment_mass_kg"] = missile->warhead_profile.fragment_mass_kg;
                out["warhead_fragment_count"] = missile->warhead_profile.fragment_count;
                out["warhead_projection_radius_fraction"] =
                    missile->warhead_profile.projection_radius_fraction;
                out["warhead_projection_min_radius_m"] =
                    missile->warhead_profile.projection_min_radius_m;
                out["warhead_projection_max_radius_m"] =
                    missile->warhead_profile.projection_max_radius_m;
                out["warhead_projection_min_effect_scale"] =
                    missile->warhead_profile.projection_min_effect_scale;
                out["warhead_projection_max_effect_scale"] =
                    missile->warhead_profile.projection_max_effect_scale;
                out["warhead_projection_falloff_exponent"] =
                    missile->warhead_profile.projection_falloff_exponent;
                out["warhead_projection_max_projected_hitboxes"] =
                    missile->warhead_profile.projection_max_projected_hitboxes;
                out["warhead_provenance"] = missile->warhead_profile.provenance;
                out["fuze_type"] = missile->fuze_profile.type;
                out["fuze_trigger_radius_m"] = missile->fuze_profile.trigger_radius_m;
                out["fuze_delay_s"] = missile->fuze_profile.delay_s;
                out["fuze_reliability"] = missile->fuze_profile.reliability;
                out["fuze_trigger_logic"] = missile->fuze_profile.trigger_logic;
                out["fuze_profile_synthetic"] = missile->fuze_profile.synthetic;
                out["fuze_provenance"] = missile->fuze_profile.provenance;
                out["seeker_fov_deg"] = missile->seeker_fov_deg;
                out["seeker_lock_range_m"] = missile->seeker_lock_range;
                out["guidance_delay_s"] = missile->guidance_delay_s;
                out["guidance_update_period_s"] = missile->guidance_update_period_s;
                out["last_guidance_time_s"] = missile->last_guidance_time;
                out["max_flight_time_s"] = missile->max_flight_time_s;
                out["nav_gain"] = missile->nav_gain;
                out["apn_target_accel_gain"] = missile->apn_target_accel_gain;
                out["autopilot_order"] = missile->autopilot_order;
                out["autopilot_damping"] = missile->autopilot_damping;
                out["use_kalman_seeker"] = missile->use_kalman_seeker;
                out["mach_transonic_start"] = missile->guidance_mach_transonic_start;
                out["mach_transonic_end"] = missile->guidance_mach_transonic_end;
                out["cd0_power_on_ratio"] = missile->guidance_cd0_power_on_ratio;
                out["proximity_min_dist_m"] = missile->proximity_min_dist_m;
                out["proximity_min_time_s"] = missile->proximity_min_time_s;
                out["proximity_last_dist_m"] = missile->proximity_last_dist_m;
                out["proximity_min_local_forward_m"] = missile->proximity_min_local_forward_m;
                out["proximity_min_local_right_m"] = missile->proximity_min_local_right_m;
                out["proximity_min_local_up_m"] = missile->proximity_min_local_up_m;
                out["proximity_last_sample_time_s"] = missile->proximity_last_sample_time_s;
                out["proximity_last_missile_x_m"] = missile->proximity_last_missile_x_m;
                out["proximity_last_missile_y_m"] = missile->proximity_last_missile_y_m;
                out["proximity_last_missile_z_m"] = missile->proximity_last_missile_z_m;
                out["proximity_last_target_x_m"] = missile->proximity_last_target_x_m;
                out["proximity_last_target_y_m"] = missile->proximity_last_target_y_m;
                out["proximity_last_target_z_m"] = missile->proximity_last_target_z_m;
                out["proximity_engaged"] = missile->proximity_engaged;
                out["fuze_delay_armed"] = missile->fuze_delay_armed;
                out["fuze_nearest_approach_time_s"] = missile->fuze_nearest_approach_time_s;
                out["fuze_detonation_time_s"] = missile->fuze_detonation_time_s;
                out["fuze_detonation_heading_deg"] = missile->fuze_detonation_heading_deg;
                out["fuze_detonation_pitch_deg"] = missile->fuze_detonation_pitch_deg;
                out["fuze_detonation_roll_deg"] = missile->fuze_detonation_roll_deg;
                out["fuze_quality"] = missile->fuze_quality;
                out["fuze_hit_probability"] = missile->fuze_hit_probability;
                out["fuze_signature_source"] = missile->fuze_signature_source;
                out["fuze_target_signature"] = missile->fuze_target_signature;
                out["fuze_signature_scale"] = missile->fuze_signature_scale;
                out["fuze_effective_reliability"] = missile->fuze_effective_reliability;
                out["fuze_contact_surface_distance_m"] = missile->fuze_contact_surface_distance_m;
                out["fuze_contact_penetration_depth_m"] = missile->fuze_contact_penetration_depth_m;
                out["fuze_contact_surface_tolerance_m"] = missile->fuze_contact_surface_tolerance_m;
                out["fuze_contact_inside_hitbox"] = missile->fuze_contact_inside_hitbox;
                out["fuze_sensor_opportunity_source"] = missile->fuze_sensor_opportunity_source;
                out["fuze_sensor_opportunity_score"] = missile->fuze_sensor_opportunity_score;
                out["fuze_terminal_track_valid"] = missile->fuze_terminal_track_valid;
                out["fuze_target_detected"] = missile->fuze_target_detected;
                out["fuze_target_detection_source"] = missile->fuze_target_detection_source;
                out["fuze_target_detection_confidence"] = missile->fuze_target_detection_confidence;
                out["fuze_target_detection_threshold"] = missile->fuze_target_detection_threshold;
                out["fuze_detonation_point_source"] = missile->fuze_detonation_point_source;
                out["fuze_mechanism_coverage_score"] = missile->fuze_mechanism_coverage_score;
                out["runtime_initialized"] = missile->runtime_initialized;
                out["seeker_has_valid_track"] = missile->seeker_has_valid_track;
                out["seeker_has_range"] = missile->seeker_has_range;
                out["seeker_mode"] = missile->seeker_mode;
                out["filtered_bearing_deg"] = missile->filtered_bearing_deg;
                out["filtered_elevation_deg"] = missile->filtered_elevation_deg;
                out["filtered_range_m"] = missile->filtered_range_m;
                out["filtered_closing_speed_mps"] = missile->filtered_closing_speed_mps;
                out["bearing_rate_deg_s"] = missile->bearing_rate_deg_s;
                out["elevation_rate_deg_s"] = missile->elevation_rate_deg_s;
                out["last_track_time_s"] = missile->last_track_time_s;
                out["track_memory_timeout_s"] = missile->track_memory_timeout_s;
                out["target_kinematics_valid"] = missile->target_kinematics_valid;
                out["target_kinematics_time_s"] = missile->target_kinematics_time_s;
                out["target_track_x_m"] = missile->target_track_x_m;
                out["target_track_y_m"] = missile->target_track_y_m;
                out["target_track_z_m"] = missile->target_track_z_m;
                out["target_track_vx_mps"] = missile->target_track_vx_mps;
                out["target_track_vy_mps"] = missile->target_track_vy_mps;
                out["target_track_vz_mps"] = missile->target_track_vz_mps;
                out["target_track_ax_mps2"] = missile->target_track_ax_mps2;
                out["target_track_ay_mps2"] = missile->target_track_ay_mps2;
                out["target_track_az_mps2"] = missile->target_track_az_mps2;
                out["guidance_lead_time_s"] = missile->guidance_lead_time_s;
                out["guidance_lead_blend"] = missile->guidance_lead_blend;
                out["guidance_apn_lateral_accel_mps2"] = missile->guidance_apn_lateral_accel_mps2;
                out["current_speed_mps"] = missile->current_speed_mps;
                out["commanded_lateral_accel_mps2"] = missile->commanded_lateral_accel_mps2;
                out["commanded_lateral_accel_x_mps2"] = missile->commanded_lateral_accel_x_mps2;
                out["commanded_lateral_accel_y_mps2"] = missile->commanded_lateral_accel_y_mps2;
                out["commanded_lateral_accel_z_mps2"] = missile->commanded_lateral_accel_z_mps2;
                out["achieved_lateral_accel_mps2"] = missile->achieved_lateral_accel_mps2;
                out["burnout_time_s"] = missile->burnout_time_s;
                out["boost_duration_s"] = missile->boost_duration_s;
                out["sustain_duration_s"] = missile->sustain_duration_s;
                out["guidance_bearing_filter_tau_s"] = missile->guidance_bearing_filter_tau_s;
                out["guidance_elevation_filter_tau_s"] = missile->guidance_elevation_filter_tau_s;
                out["guidance_range_filter_tau_s"] = missile->guidance_range_filter_tau_s;
                out["guidance_boost_thrust_n"] = missile->guidance_boost_thrust_n;
                out["guidance_sustain_thrust_n"] = missile->guidance_sustain_thrust_n;
                out["guidance_cd0_subsonic"] = missile->guidance_cd0_subsonic;
                out["guidance_cd0_supersonic"] = missile->guidance_cd0_supersonic;
                out["guidance_induced_drag_k"] = missile->guidance_induced_drag_k;
                out["guidance_cd0_mach_breakpoints"] = missile->guidance_cd0_mach_breakpoints;
                out["guidance_cd0_mach_values"] = missile->guidance_cd0_mach_values;
                out["guidance_induced_drag_k_mach_breakpoints"] =
                    missile->guidance_induced_drag_k_mach_breakpoints;
                out["guidance_induced_drag_k_mach_values"] =
                    missile->guidance_induced_drag_k_mach_values;
                out["guidance_max_lateral_g"] = missile->guidance_max_lateral_g;
                out["guidance_autopilot_tau_s"] = missile->guidance_autopilot_tau_s;
                out["guidance_max_accel_response_g_per_s"] =
                    missile->guidance_max_accel_response_g_per_s;
                out["seeker_activation_range_m"] = missile->seeker_activation_range_m;
                out["midcourse_datalink_supported"] = missile->midcourse_datalink_supported;
                out["terminal_seeker_active"] = missile->terminal_seeker_active;
                const MissileGuidanceMechanismProfile *mechanism_profile =
                    e.get<MissileGuidanceMechanismProfile>();
                out["guidance_mechanism_profile_active"] =
                    mechanism_profile && mechanism_profile->active;
                if (mechanism_profile) {
                    out["guidance_mechanism_capture_mode"] = mechanism_profile->capture_mode;
                    out["guidance_mechanism_pn_mode"] = mechanism_profile->pn_mode;
                    out["guidance_mechanism_lead_mode"] = mechanism_profile->lead_mode;
                    out["guidance_mechanism_kinematics_source"] =
                        mechanism_profile->kinematics_source;
                    out["guidance_mechanism_apn_mode"] = mechanism_profile->apn_mode;
                    out["guidance_target_kinematics_source_used"] =
                        mechanism_profile->target_kinematics_source_used;
                    out["guidance_pn_source_used"] = mechanism_profile->pn_source_used;
                    out["guidance_capture_accel_x_mps2"] = mechanism_profile->capture_accel_x_mps2;
                    out["guidance_capture_accel_y_mps2"] = mechanism_profile->capture_accel_y_mps2;
                    out["guidance_capture_accel_z_mps2"] = mechanism_profile->capture_accel_z_mps2;
                    out["guidance_capture_accel_mps2"] = mechanism_profile->capture_accel_mps2;
                    out["guidance_pn_accel_x_mps2"] = mechanism_profile->pn_accel_x_mps2;
                    out["guidance_pn_accel_y_mps2"] = mechanism_profile->pn_accel_y_mps2;
                    out["guidance_pn_accel_z_mps2"] = mechanism_profile->pn_accel_z_mps2;
                    out["guidance_pn_accel_mps2"] = mechanism_profile->pn_accel_mps2;
                    out["guidance_apn_accel_x_mps2"] = mechanism_profile->apn_accel_x_mps2;
                    out["guidance_apn_accel_y_mps2"] = mechanism_profile->apn_accel_y_mps2;
                    out["guidance_apn_accel_z_mps2"] = mechanism_profile->apn_accel_z_mps2;
                    out["guidance_preclamp_accel_x_mps2"] =
                        mechanism_profile->preclamp_accel_x_mps2;
                    out["guidance_preclamp_accel_y_mps2"] =
                        mechanism_profile->preclamp_accel_y_mps2;
                    out["guidance_preclamp_accel_z_mps2"] =
                        mechanism_profile->preclamp_accel_z_mps2;
                    out["guidance_preclamp_accel_mps2"] = mechanism_profile->preclamp_accel_mps2;
                    out["guidance_postclamp_accel_x_mps2"] =
                        mechanism_profile->postclamp_accel_x_mps2;
                    out["guidance_postclamp_accel_y_mps2"] =
                        mechanism_profile->postclamp_accel_y_mps2;
                    out["guidance_postclamp_accel_z_mps2"] =
                        mechanism_profile->postclamp_accel_z_mps2;
                    out["guidance_postclamp_accel_mps2"] = mechanism_profile->postclamp_accel_mps2;
                    out["guidance_los_rate_x_rad_s"] = mechanism_profile->los_rate_x_rad_s;
                    out["guidance_los_rate_y_rad_s"] = mechanism_profile->los_rate_y_rad_s;
                    out["guidance_los_rate_z_rad_s"] = mechanism_profile->los_rate_z_rad_s;
                    out["guidance_los_rate_rad_s"] = mechanism_profile->los_rate_rad_s;
                    out["guidance_closing_speed_used_mps"] =
                        mechanism_profile->closing_speed_used_mps;
                    out["guidance_achieved_accel_x_mps2"] =
                        mechanism_profile->achieved_accel_x_mps2;
                    out["guidance_achieved_accel_y_mps2"] =
                        mechanism_profile->achieved_accel_y_mps2;
                    out["guidance_achieved_accel_z_mps2"] =
                        mechanism_profile->achieved_accel_z_mps2;
                }
                if (sensor) {
                    out["sensor_max_range_m"] = sensor->max_range;
                    out["sensor_fov_deg"] = sensor->fov_deg;
                    out["sensor_scan_period_s"] = sensor->scan_period;
                    out["sensor_detection_prob"] = sensor->detection_prob;
                    out["sensor_bearing_noise_std"] = sensor->bearing_noise_std;
                    out["sensor_range_noise_std"] = sensor->range_noise_std;
                    out["sensor_track_memory_s"] = sensor->track_memory_s;
                    out["sensor_type"] = sensor->type;
                }
                if (mass) {
                    out["mass_empty_kg"] = mass->empty_mass_kg;
                    out["mass_fuel_kg"] = mass->fuel_mass_kg;
                    out["mass_stores_kg"] = mass->stores_mass_kg;
                    out["mass_total_kg"] = mass->get_total_kg();
                }
                if (mass_properties) {
                    out["reference_area_m2"] = mass_properties->reference_area_m2;
                }
                return out;
            },
            "Debug: get missile runtime guidance state", nb::arg("entity_id"));
}

void bind_simulation_kernel_legacy_compatibility_debug_surface(
    nb::class_<SimulationKernel> &kernel) {
    kernel
        .def(
            "debug_set_legacy_movement_command",
            [](SimulationKernel &self, uint64_t entity_id, double target_heading_deg,
               double target_speed_mps, double target_altitude_m, bool active) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    throw std::invalid_argument(
                        "Invalid entity ID for debug_set_legacy_movement_command");
                }
                diagnostics_quarantined_legacy_movement_bridge_write(
                    e, target_heading_deg, target_speed_mps, target_altitude_m, active);
            },
            "Debug quarantined bridge write: sync legacy movement shell through typed "
            "control-state compatibility helper only",
            nb::arg("entity_id"), nb::arg("target_heading_deg"), nb::arg("target_speed_mps"),
            nb::arg("target_altitude_m"), nb::arg("active") = true)
        .def(
            "debug_get_legacy_movement_command",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    return out;
                }
                const MovementCommand *movement = e.get<MovementCommand>();
                if (!movement) {
                    return out;
                }
                diagnostics_mark_read_only_snapshot(out, "diagnostics_legacy_mirror",
                                                    "mission_command_control_state_bridge");
                out["diagnostics_legacy_mirror"] = true;
                out["mirror_kind"] = "legacy_movement_command";
                out["active"] = movement->active;
                out["target_heading"] = movement->target_heading;
                out["target_speed"] = movement->target_speed;
                out["target_altitude"] = movement->target_altitude;
                out["use_stick_control"] = movement->use_stick_control;
                // WP22-R1-2: read-only legacy movement shell mirror, not maintained truth.
                out["state_access_mode"] = "read_only_legacy_mirror";
                out["mirror_truth_owner"] = "typed_control_state_bridge_projection";
                if (const MissionCommandControlState *state = e.get<MissionCommandControlState>()) {
                    out["control_state_present"] = true;
                    out["control_state_active"] = state->active;
                    out["control_target_heading_deg"] = state->target_heading_deg;
                    out["control_target_speed_mps"] = state->target_speed_mps;
                    out["control_target_altitude_m"] = state->target_altitude_m;
                    out["control_lagged_active"] = state->lagged_active;
                    out["control_lagged_heading_deg"] = state->lagged_heading_deg;
                    out["control_lagged_speed_mps"] = state->lagged_speed_mps;
                    out["control_lagged_altitude_m"] = state->lagged_altitude_m;
                } else {
                    out["control_state_present"] = false;
                }
                return out;
            },
            "Debug diagnostics-only read-only legacy movement shell mirror plus typed "
            "control-state bridge snapshot",
            nb::arg("entity_id"));
}

void bind_simulation_kernel_diagnostics_override_surface(nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("set_contact_list", &SimulationKernel::set_contact_list,
             "Override the ContactList for a unit or missile", nb::arg("entity_id"),
             nb::arg("detections"))
        .def(
            "debug_set_unit_truth_state",
            [](SimulationKernel &self, uint64_t entity_id, double x_m, double y_m, double z_m,
               double heading_deg, double pitch_deg, double roll_deg, double vx_mps, double vy_mps,
               double vz_mps) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    throw std::invalid_argument("Invalid entity ID for debug_set_unit_truth_state");
                }
                // Diagnostics-only truth override for deterministic runtime tests. Keep this
                // quarantined from the maintained command surface: scripted scenarios use it to
                // remove unrelated platform-control drift while validating weapons behavior.
                e.set<Transform>({x_m, y_m, z_m, heading_deg, pitch_deg, roll_deg});
                e.set<Velocity>({vx_mps, vy_mps, vz_mps});
            },
            "Debug diagnostics-only override of entity transform and velocity truth state",
            nb::arg("entity_id"), nb::arg("x_m"), nb::arg("y_m"), nb::arg("z_m"),
            nb::arg("heading_deg"), nb::arg("pitch_deg"), nb::arg("roll_deg"), nb::arg("vx_mps"),
            nb::arg("vy_mps"), nb::arg("vz_mps"))
        .def(
            "set_missile_guidance_mechanism_profile",
            [](SimulationKernel &self, uint64_t entity_id, int capture_mode, int pn_mode,
               int lead_mode, int kinematics_source, int apn_mode) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                const Missile *missile = e.is_valid() ? e.get<Missile>() : nullptr;
                if (!missile) {
                    throw std::invalid_argument(
                        "Invalid missile entity for set_missile_guidance_mechanism_profile");
                }
                if (missile->last_guidance_time >= 0.0) {
                    throw std::invalid_argument("Missile guidance mechanism profile must be set "
                                                "before the first guidance update");
                }
                if (capture_mode < MissileGuidanceMechanismProfile::kCaptureOff ||
                    capture_mode > MissileGuidanceMechanismProfile::kCaptureOn) {
                    throw std::invalid_argument("capture_mode must be 0 or 1");
                }
                if (pn_mode < MissileGuidanceMechanismProfile::kPnLegacyBodyRates ||
                    pn_mode > MissileGuidanceMechanismProfile::kPnWorldTrackAnalytic) {
                    throw std::invalid_argument("pn_mode must be in [0, 3]");
                }
                if (lead_mode < MissileGuidanceMechanismProfile::kLeadOff ||
                    lead_mode > MissileGuidanceMechanismProfile::kLeadQuadratic) {
                    throw std::invalid_argument("lead_mode must be in [0, 2]");
                }
                if (kinematics_source < MissileGuidanceMechanismProfile::kKinematicsTrack ||
                    kinematics_source >
                        MissileGuidanceMechanismProfile::kKinematicsTruthConstantVelocity) {
                    throw std::invalid_argument("kinematics_source must be 0 or 1");
                }
                if (apn_mode < MissileGuidanceMechanismProfile::kApnOff ||
                    apn_mode > MissileGuidanceMechanismProfile::kApnOn) {
                    throw std::invalid_argument("apn_mode must be 0 or 1");
                }
                MissileGuidanceMechanismProfile profile;
                profile.active = true;
                profile.capture_mode = capture_mode;
                profile.pn_mode = pn_mode;
                profile.lead_mode = lead_mode;
                profile.kinematics_source = kinematics_source;
                profile.apn_mode = apn_mode;
                e.set<MissileGuidanceMechanismProfile>(profile);
            },
            "Attach a diagnostics-only exact guidance mechanism profile before first update",
            nb::arg("entity_id"), nb::arg("capture_mode"), nb::arg("pn_mode"), nb::arg("lead_mode"),
            nb::arg("kinematics_source"), nb::arg("apn_mode"))
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"))
        .def("get_missile_tuning", &SimulationKernel::get_missile_tuning, nb::rv_policy::copy,
             "Get current missile tuning snapshot");
}
} // namespace
