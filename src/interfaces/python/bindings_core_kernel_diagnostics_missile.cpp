#include "interfaces/python/bindings_core_detail.h"

#include "components/combat/common/missile_guidance_mechanism_profile.h"
#include "components/combat/common/weapon_common.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"

void bind_simulation_kernel_diagnostics_missile_runtime_surface(
    nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("debug_get_embarked_helo", &SimulationKernel::debug_get_embarked_helo,
             "Debug: get embarked helo entity id for a host", nb::arg("entity_id"))
        .def(
            "debug_get_missile_runtime_state",
            [](SimulationKernel &self, uint64_t entity_id) {
                nb::dict out;
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
