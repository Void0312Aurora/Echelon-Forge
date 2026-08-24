#include "interfaces/python/bindings_core_detail.h"

#include <vector>

#include "components/combat/common/weapon_common.h"
#include "components/physics/dynamics.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/physics/control_surface.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "components/systems/sensor.h"
#include "components/systems/track_management.h"

namespace {
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

void bind_simulation_kernel_diagnostics_hit_and_view_surface(nb::class_<SimulationKernel> &kernel) {
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
            nb::arg("entity_id"));
}
