#include "interfaces/python/bindings_core_detail.h"

#include <string>
#include <vector>

#include "components/combat/common/weapon_common.h"
#include "core/engine/simulation_kernel_missile_tuning.h"

void bind_core_weapon_profiles(nb::module_ &m) {
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
        .def_prop_rw(
            "midcourse_datalink_supported",
            [](const MissileTuning &self) { return self.midcourse_datalink_supported; },
            [](MissileTuning &self, bool value) { self.set_midcourse_datalink_override(value); })
        .def_prop_rw(
            "use_kalman_seeker", [](const MissileTuning &self) { return self.use_kalman_seeker; },
            [](MissileTuning &self, bool value) { self.set_kalman_seeker_override(value); })
        .def_rw("warhead_profile", &MissileTuning::warhead_profile)
        .def_rw("has_warhead_profile", &MissileTuning::has_warhead_profile)
        .def_rw("fuze_profile", &MissileTuning::fuze_profile)
        .def_rw("has_fuze_profile", &MissileTuning::has_fuze_profile);
}
