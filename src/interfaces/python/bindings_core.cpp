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
#include "components/combat/weapon.h"
#include "components/command/command_link.h"
#include "components/physics/dynamics.h"
#include "components/physics/flight_dynamics_tuning.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
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
const char* default_unit_name_for(UnitType type) {
    switch (type) {
        case UnitType::Aircraft:
            return "Aircraft";
        case UnitType::Ship:
            return "Ship";
        case UnitType::Submarine:
            return "Submarine";
        case UnitType::Missile:
            return "Missile";
        case UnitType::Facility:
            return "Facility";
        case UnitType::C2Node:
            return "AWACS";
        default:
            throw std::invalid_argument("Unsupported UnitType for spawn_unit (use type_name string instead)");
    }
}

struct SensorDebugView {
    double reference_snr_db = 0.0;
    double reference_range_m = 0.0;
    double reference_rcs_m2 = 0.0;
    double pfa = 0.0;
    int confirm_hits_m = 0;
    int confirm_window_n = 0;
    double velocity_noise_std = 0.0;
    double alpha_beta_alpha = 0.0;
    double alpha_beta_beta = 0.0;
    double range_power = 0.0;
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
};

SensorDebugView make_sensor_debug_view(const Sensor& sensor) {
    SensorDebugView out{};
    out.reference_snr_db = sensor.reference_snr_db;
    out.reference_range_m = sensor.reference_range_m;
    out.reference_rcs_m2 = sensor.reference_rcs_m2;
    out.pfa = sensor.pfa;
    out.confirm_hits_m = sensor.confirm_hits_m;
    out.confirm_window_n = sensor.confirm_window_n;
    out.velocity_noise_std = sensor.velocity_noise_std;
    out.alpha_beta_alpha = sensor.alpha_beta_alpha;
    out.alpha_beta_beta = sensor.alpha_beta_beta;
    out.range_power = sensor.range_power;
    out.type = sensor.type;
    return out;
}

TrackDebugView make_track_debug_view(const SystemTrack& track) {
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

void bind_core(nb::module_& m) {
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
        .def_rw("propellant_mass_kg", &MissileTuning::propellant_mass_kg)
        .def_rw("max_lateral_g", &MissileTuning::max_lateral_g)
        .def_rw("autopilot_tau_s", &MissileTuning::autopilot_tau_s)
        .def_rw("max_accel_response_g_per_s", &MissileTuning::max_accel_response_g_per_s)
        .def_rw("min_launch_range_m", &MissileTuning::min_launch_range_m)
        .def_rw("max_launch_off_boresight_deg", &MissileTuning::max_launch_off_boresight_deg)
        .def_rw("lobl_required", &MissileTuning::lobl_required)
        .def_rw("midcourse_datalink_supported", &MissileTuning::midcourse_datalink_supported);

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
        .def_ro("reference_snr_db", &SensorDebugView::reference_snr_db)
        .def_ro("reference_range_m", &SensorDebugView::reference_range_m)
        .def_ro("reference_rcs_m2", &SensorDebugView::reference_rcs_m2)
        .def_ro("pfa", &SensorDebugView::pfa)
        .def_ro("confirm_hits_m", &SensorDebugView::confirm_hits_m)
        .def_ro("confirm_window_n", &SensorDebugView::confirm_window_n)
        .def_ro("velocity_noise_std", &SensorDebugView::velocity_noise_std)
        .def_ro("alpha_beta_alpha", &SensorDebugView::alpha_beta_alpha)
        .def_ro("alpha_beta_beta", &SensorDebugView::alpha_beta_beta)
        .def_ro("range_power", &SensorDebugView::range_power)
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
        .def_ro("current_thrust_n", &FlightDynamicsDebugView::current_thrust_n);

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

    nb::class_<SimulationKernel>(m, "SimulationKernel")
        .def(nb::init<>())
        .def("get_instrument_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const InstrumentState* inst = e.get<InstrumentState>();
                if (inst) return *inst;
            }
            return InstrumentState{};
        }, "Get the instrument state for a unit")
        .def("get_egi_state", [](SimulationKernel& self, uint64_t entity_id) {
            auto e = self.get_world().entity(entity_id);
            if (e.is_valid()) {
                const EGI* egi = e.get<EGI>();
                if (egi) return *egi;
            }
            return EGI{};
        }, "Get the EGI state for a unit")
        .def("reset", &SimulationKernel::reset, "Reset the simulation", nb::arg("seed") = 42)
        .def("load_database", &SimulationKernel::load_database, nb::arg("path"), "Load unit definitions from JSON directory")
        .def("step", &SimulationKernel::step, "Advance simulation by one fixed tick")
        .def("get_time_step", &SimulationKernel::get_time_step, "Get the fixed time step in seconds")
        .def("set_time_step", &SimulationKernel::set_time_step, "Set the fixed time step in seconds")
        .def("load_unit_definitions", [](SimulationKernel& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok) {
                spdlog::warn("Failed to load unit definitions: {}", error);
            }
            return ok;
        }, "Load unit definitions from JSON", nb::arg("path"))
        .def("clear_zones", &SimulationKernel::clear_zones, "Clear all environment zones")
        .def("add_zone", &SimulationKernel::add_zone, 
             "Add a new environment zone",
             nb::arg("name"), nb::arg("x"), nb::arg("y"), nb::arg("width"), nb::arg("height"), nb::arg("heading"), nb::arg("surface_type"))
        .def("set_wind", &SimulationKernel::set_wind,
             "Set global wind (speed m/s, dir_from_deg NAV, shear m/s per km)",
             nb::arg("speed_mps"), nb::arg("dir_from_deg"), nb::arg("shear_mps_per_km") = 0.0)
        .def("set_maritime_state", &SimulationKernel::set_maritime_state,
             "Set global maritime state (sea state, wave heading deg NAV, wave period s)",
             nb::arg("sea_state"), nb::arg("wave_heading_deg") = 0.0, nb::arg("wave_period_s") = 8.0)
        .def("clear_maritime_state", &SimulationKernel::clear_maritime_state,
             "Clear global maritime override so platform defaults can apply again")
        .def("get_maritime_state", [](SimulationKernel& self) {
             const auto state = self.get_maritime_state();
             return std::make_tuple(state.sea_state, state.wave_heading_deg, state.wave_period_s);
        }, "Get global maritime state as (sea_state, wave_heading_deg, wave_period_s)")
        .def("set_terrain_type", &SimulationKernel::set_terrain_type,
             "Set terrain profile (e.g. 'flat', 'legacy', 'hill')",
             nb::arg("terrain_type"))
        .def("spawn_unit", [](SimulationKernel& self, Side side, const std::string& type, 
                              double x, double y, double z, 
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            // We return the Entity ID as an integer for MVP
            auto e = self.spawn_unit(side, type, x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a unit by name with orientation and return its Entity ID", 
           nb::arg("side"), nb::arg("type_name"), 
           nb::arg("x"), nb::arg("y"), nb::arg("z"), 
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)
        .def("spawn_unit", [](SimulationKernel& self, Side side, UnitType type,
                              double x, double y, double z,
                              double heading, double pitch, double roll,
                              double vx, double vy, double vz) {
            auto e = self.spawn_unit(side, default_unit_name_for(type), x, y, z, heading, pitch, roll, vx, vy, vz);
            return e.id();
        }, "Spawn a default unit for the given UnitType with orientation and return its Entity ID",
           nb::arg("side"), nb::arg("type"),
           nb::arg("x"), nb::arg("y"), nb::arg("z"),
           nb::arg("heading")=0.0, nb::arg("pitch")=0.0, nb::arg("roll")=0.0,
           nb::arg("vx")=0.0, nb::arg("vy")=0.0, nb::arg("vz")=0.0)

        // Action Interface
        .def("set_command", &SimulationKernel::set_unit_command, "Set movement command for a unit",
             nb::arg("entity_id"), nb::arg("heading_deg"), nb::arg("speed_mps"), nb::arg("altitude_m"))
        .def("set_stick_command", &SimulationKernel::set_unit_stick_command, "Set stick inputs",
             nb::arg("entity_id"), nb::arg("stick_roll"), nb::arg("stick_pitch"), nb::arg("throttle"), nb::arg("gear_down")=true)
        .def("set_action", &SimulationKernel::set_unit_action, "Set normalized action for a unit",
             nb::arg("entity_id"),
             nb::arg("turn_rate_cmd"),
             nb::arg("accel_cmd"),
             nb::arg("climb_rate_cmd"),
             nb::arg("fire_cmd"),
             nb::arg("release_chaff") = false,
             nb::arg("release_flare") = false,
             nb::arg("jettison_tanks") = false)
        .def("set_action_space_config", &SimulationKernel::set_action_space_config, "Override action mapping scales for a unit",
             nb::arg("entity_id"),
             nb::arg("max_turn_rate_deg_s"),
             nb::arg("max_accel_mps2"),
             nb::arg("max_climb_rate_mps"),
             nb::arg("min_speed_mps"),
             nb::arg("max_speed_mps"),
             nb::arg("min_alt_m"),
             nb::arg("max_alt_m"))
        
        // Digital Pilot Bindings
        .def("set_pilot_action", &SimulationKernel::set_pilot_action, 
             "Set raw pilot inputs (stick, throttle, etc) for Digital Pilot",
             nb::arg("entity_id"), nb::arg("action"))
        .def("set_mission_command", &SimulationKernel::set_mission_command,
             "Set high-level mission intent for Digital Pilot",
             nb::arg("entity_id"), nb::arg("command"))
        .def("set_task_order", &SimulationKernel::set_task_order,
             "Set the C2 task order for the entity",
             nb::arg("entity_id"), nb::arg("task_order"))
        .def("set_leader_intent", &SimulationKernel::set_leader_intent,
             "Set the leader-layer intent for the entity",
             nb::arg("entity_id"), nb::arg("leader_intent"))
        .def("set_pilot_report", &SimulationKernel::set_pilot_report,
             "Store the latest pilot report for the entity",
             nb::arg("entity_id"), nb::arg("pilot_report"))

        .def("set_command_lag", &SimulationKernel::set_command_lag, "Override command lag time constants for a unit",
             nb::arg("entity_id"),
             nb::arg("heading_tau_s"),
             nb::arg("speed_tau_s"),
             nb::arg("altitude_tau_s"))
        .def("set_command_link", &SimulationKernel::set_command_link, "Set command link latency/drop probability",
             nb::arg("entity_id"), nb::arg("latency_s"), nb::arg("drop_prob"))
        .def("set_unit_ammo", &SimulationKernel::set_unit_ammo,
             "Override unit ammo counts",
             nb::arg("entity_id"), nb::arg("missiles_remaining"), nb::arg("max_missiles"))
        .def("set_weapon_cooldown", &SimulationKernel::set_weapon_cooldown,
             "Override unit weapon cooldown state",
             nb::arg("entity_id"), nb::arg("cooldown_s"), nb::arg("last_fire_time"))
             
        .def("fire_missile", [](SimulationKernel& self, uint64_t attacker_id, uint64_t target_id) {
             auto e = self.fire_missile(attacker_id, target_id);
             return e.id(); // Return ID just like spawn_unit
        }, "Fire a missile from attacker to target", nb::arg("attacker_id"), nb::arg("target_id"))
        .def("fire_naval_weapon", &SimulationKernel::fire_naval_weapon,
             "Fire a naval weapon mount type at target",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("weapon_type_code"))
        .def("debug_apply_proximity_hit", &SimulationKernel::debug_apply_proximity_hit,
             "Testing helper: apply one synthetic proximity hit to a target",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("damage"), nb::arg("fuse_distance"))
        
        // Helper to get unit position (state observation)
        .def("get_unit_position", [](SimulationKernel& self, uint64_t entity_id) {
             auto p = self.get_unit_position(entity_id);
             return std::make_tuple(p[0], p[1], p[2]);
        }, "Get unit position (x,y,z)")
        .def("get_unit_velocity", [](SimulationKernel& self, uint64_t entity_id) {
             auto v = self.get_unit_velocity(entity_id);
             return std::make_tuple(v[0], v[1], v[2]);
        }, "Get unit velocity (vx,vy,vz)")
        
        // Helper to get unit heading (degrees, NAV convention: 0=North, CW)
        .def("get_unit_heading", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0.0;
             const Transform* t = e.get<Transform>();
             if (t) return t->heading;
             const Velocity* v = e.get<Velocity>();
             if(!v) return 0.0;
             // Math angle: atan2(vy, vx) where 0=East, CCW positive
             double math_rad = std::atan2(v->vy, v->vx);
             double math_deg = math_rad * 180.0 / M_PI;
             // NAV angle: 0=North, CW positive => NAV = 90 - Math
             double nav_deg = 90.0 - math_deg;
             // Normalize to [0, 360)
             while (nav_deg < 0) nav_deg += 360.0;
             while (nav_deg >= 360.0) nav_deg -= 360.0;
             return nav_deg;
        }, "Get unit heading in degrees (NAV: 0=North, CW)")
        
        // Helper to get unit type
        .def("get_unit_type", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             auto e = world.entity(entity_id);
             if(!e.is_valid()) return 0;
             const KeyEntity* k = e.get<KeyEntity>();
             return k ? (int)k->type : 0;
        }, "Get unit type enum value")
        
        // Helper to check if unit is active/alive
        .def("is_unit_active", [](SimulationKernel& self, uint64_t entity_id) {
             flecs::world& world = self.get_world();
             return world.entity(entity_id).is_valid();
        }, "Check if unit exists")
        
        .def("get_all_units", &SimulationKernel::get_all_units, "Get all units state")
        .def("get_detections", &SimulationKernel::get_detections, "Get unit sensor contacts")
        .def("get_sensor_debug_view", [](SimulationKernel& self, uint64_t entity_id) {
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return SensorDebugView{};
             }
             const Sensor* sensor = e.get<Sensor>();
             if (!sensor) {
                 return SensorDebugView{};
             }
             return make_sensor_debug_view(*sensor);
        }, "Get current runtime sensor tuning fields", nb::arg("entity_id"))
        .def("get_track_debug_view", [](SimulationKernel& self, uint64_t entity_id) {
             std::vector<TrackDebugView> out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             const TrackDatabase* db = e.get<TrackDatabase>();
             if (!db) {
                 return out;
             }
             out.reserve(db->tracks.size());
             for (const auto& track : db->tracks) {
                 out.push_back(make_track_debug_view(track));
             }
             return out;
        }, "Get confirmed/coasted runtime track debug view", nb::arg("entity_id"))
        .def("get_tentative_track_debug_view", [](SimulationKernel& self, uint64_t entity_id) {
             std::vector<TrackDebugView> out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             const TrackDatabase* db = e.get<TrackDatabase>();
             if (!db) {
                 return out;
             }
             out.reserve(db->tentative_tracks.size());
             for (const auto& track : db->tentative_tracks) {
                 out.push_back(make_track_debug_view(track));
             }
             return out;
        }, "Get tentative runtime track debug view", nb::arg("entity_id"))
        .def("get_flight_dynamics_debug_view", [](SimulationKernel& self, uint64_t entity_id) {
             FlightDynamicsDebugView out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             if (const AeroState* aero = e.get<AeroState>()) {
                 out.alpha_dot_dps = aero->angle_of_attack_rate_dps;
                 out.stall_progress = aero->stall_progress;
             }
             if (const StallState* stall = e.get<StallState>()) {
                 out.stall_progress = stall->stall_progress;
                 out.is_stalled = stall->is_stalled;
                 out.pitch_break_active = stall->pitch_break_active;
                 out.time_in_stall_s = stall->time_in_stall_s;
             }
             if (const Propulsion* propulsion = e.get<Propulsion>()) {
                 out.throttle_command = propulsion->throttle_command;
                 out.throttle_state = propulsion->throttle_state;
                 out.ab_state = propulsion->ab_state;
                 out.afterburner_active = propulsion->afterburner_active;
                 out.current_tsfc = propulsion->current_tsfc;
                 out.current_thrust_n = propulsion->current_thrust_n;
             }
             return out;
        }, "Get flight-dynamics debug state (AoA-rate, stall, propulsion spool)", nb::arg("entity_id"))
        .def("get_unit_health", &SimulationKernel::get_unit_health, "Get unit health [current, max]")
        .def("get_unit_damage_state", &SimulationKernel::get_unit_damage_state,
             "Get unit damage state [mission, mobility, sensor, survivability]")
        .def("debug_get_naval_weapon_counts", &SimulationKernel::debug_get_naval_weapon_counts,
             "Get naval weapon counts [mounts, ready_vls, ready_gun, ready_ciws]")
        .def("get_unit_fuel", &SimulationKernel::get_unit_fuel, nb::arg("entity_id"),
             "Returns [internal, max_internal, external, max_external]")
        .def("debug_get_naval_stores", &SimulationKernel::debug_get_naval_stores, nb::arg("entity_id"),
             "Debug: get [fuel_cur, fuel_max, missile_cur, missile_max, dry_cur, dry_max]")
        .def("debug_get_logistics_node", &SimulationKernel::debug_get_logistics_node, nb::arg("entity_id"),
             "Debug: get [supply_radius, infinite, underway_enabled, min_sep, max_sep, max_rel_speed, fuel_rate, missile_rate, dry_rate]")
        .def("debug_get_resupply_state", &SimulationKernel::debug_get_resupply_state, nb::arg("entity_id"),
             "Debug: get [active, kind, partner_id, stage, time_remaining, is_refueling, is_rearming]")
        .def("debug_get_data_link_state", &SimulationKernel::debug_get_data_link_state, nb::arg("entity_id"),
             "Debug: get [report_budget, message_budget, reports_sent_last, messages_sent_last, reports_dropped_last, messages_dropped_last, reports_sent_total, messages_sent_total, reports_dropped_total, messages_dropped_total]")
        .def("get_task_order", &SimulationKernel::get_task_order, "Get the latest task order", nb::arg("entity_id"))
        .def("get_leader_intent", &SimulationKernel::get_leader_intent, "Get the latest leader intent", nb::arg("entity_id"))
        .def("get_mission_command", &SimulationKernel::get_mission_command, "Get the active mission command", nb::arg("entity_id"))
        .def("get_pilot_report", &SimulationKernel::get_pilot_report, "Get the latest pilot report", nb::arg("entity_id"))
        .def("get_agent_observation", &SimulationKernel::get_agent_observation, "Get complete agent observation")
        .def("get_visual_observation", [](SimulationKernel& self, uint64_t entity_id) {
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT),
                 static_cast<size_t>(arb::ARB_WIDTH),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     static_cast<size_t>(arb::ARB_HEIGHT),
                     static_cast<size_t>(arb::ARB_WIDTH),
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(self.get_visual_observation(entity_id), 3, shape);
        }, "Get ARB visual observation [H, W, C] tensor", nb::arg("entity_id"))
        .def("get_visual_observation_downsampled", [](SimulationKernel& self, uint64_t entity_id, int factor) {
             const int downsample = factor > 1 ? factor : 1;
             auto downsampled = self.get_visual_observation_downsampled(entity_id, downsample);
             size_t shape[3] = {
                 static_cast<size_t>(arb::ARB_HEIGHT / downsample),
                 static_cast<size_t>(arb::ARB_WIDTH / downsample),
                 static_cast<size_t>(arb::ARB_CHANNELS),
             };
             return visual_tensor_to_numpy<
                 nb::shape<
                     nb::any,
                     nb::any,
                     static_cast<size_t>(arb::ARB_CHANNELS)
                 >
             >(std::move(downsampled), 3, shape);
        }, "Get ARB visual observation [H/f, W/f, C] tensor", nb::arg("entity_id"), nb::arg("factor"))
        .def("get_unit_messages", &SimulationKernel::get_unit_messages, "Get inbox")
        .def("send_message_command", &SimulationKernel::send_message_command, 
             nb::arg("entity_id"), nb::arg("recipient_id"), nb::arg("msg_type"), nb::arg("msg_arg"))
        .def("debug_get_last_scan_time", &SimulationKernel::debug_get_last_scan_time, "Debug: get sensor last_scan_time")
        .def("debug_get_contact_count", &SimulationKernel::debug_get_contact_count, "Debug: get ContactList size")
        .def("debug_get_mass_state", &SimulationKernel::debug_get_mass_state,
             "Debug: get [mass_empty, mass_fuel, mass_stores, mass_total, props_empty, props_total]",
             nb::arg("entity_id"))
        .def("debug_get_pending_movement_command", [](SimulationKernel& self, uint64_t entity_id) {
             nb::dict out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             const PendingMovementCommand* pending = e.get<PendingMovementCommand>();
             if (!pending) {
                 return out;
             }
             out["active"] = pending->active;
             out["deliver_time"] = pending->deliver_time;
             out["target_heading"] = pending->command.target_heading;
             out["target_speed"] = pending->command.target_speed;
             out["target_altitude"] = pending->command.target_altitude;
             out["use_stick_control"] = pending->command.use_stick_control;
             return out;
        }, "Debug: get pending movement command state", nb::arg("entity_id"))
        .def("debug_get_pending_action_command", [](SimulationKernel& self, uint64_t entity_id) {
             nb::dict out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             const PendingActionCommand* pending = e.get<PendingActionCommand>();
             if (!pending) {
                 return out;
             }
             out["active"] = pending->active;
             out["deliver_time"] = pending->deliver_time;
             out["turn_rate_cmd"] = pending->command.turn_rate_cmd;
             out["accel_cmd"] = pending->command.accel_cmd;
             out["climb_rate_cmd"] = pending->command.climb_rate_cmd;
             out["fire_cmd"] = pending->command.fire_cmd;
             out["release_chaff"] = pending->command.release_chaff;
             out["release_flare"] = pending->command.release_flare;
             out["jettison_tanks"] = pending->command.jettison_tanks;
             return out;
        }, "Debug: get pending action command state", nb::arg("entity_id"))
        .def("debug_get_embarked_helo", &SimulationKernel::debug_get_embarked_helo,
             "Debug: get embarked helo entity id for a host",
             nb::arg("entity_id"))
        .def("debug_get_missile_runtime_state", [](SimulationKernel& self, uint64_t entity_id) {
             nb::dict out;
             auto e = self.get_world().entity(entity_id);
             if (!e.is_valid()) {
                 return out;
             }
             const Missile* missile = e.get<Missile>();
             if (!missile) {
                 return out;
             }
             out["p0_runtime_initialized"] = missile->p0_runtime_initialized;
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
             out["current_speed_mps"] = missile->current_speed_mps;
             out["commanded_lateral_accel_mps2"] = missile->commanded_lateral_accel_mps2;
             out["achieved_lateral_accel_mps2"] = missile->achieved_lateral_accel_mps2;
             out["burnout_time_s"] = missile->burnout_time_s;
             return out;
        }, "Debug: get missile runtime guidance state", nb::arg("entity_id"))
        .def("set_contact_list", &SimulationKernel::set_contact_list,
             "Override the ContactList for a unit or missile",
             nb::arg("entity_id"), nb::arg("detections"))
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"))
        .def("get_missile_tuning", &SimulationKernel::get_missile_tuning,
             nb::rv_policy::copy,
             "Get current missile tuning snapshot");
}
