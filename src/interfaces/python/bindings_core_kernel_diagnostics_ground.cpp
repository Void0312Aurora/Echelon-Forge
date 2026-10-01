#include "interfaces/python/bindings_core_detail.h"

#include <tuple>

// Ground native-probe surface.
//
// These bindings serve the single-soldier native probe and its Gymnasium adapter
// (`python/rl/ground/native_probe.py`), whose authority is `native_probe_only`: they
// are tooling for the bounded Ground slice, not maintained SimulationKernel API and
// not a production training entry point. They stay on the diagnostics side of the
// WP22 quarantine split, with every name on the explicit native-probe allowlist,
// until a reviewed Ground owner package promotes a facade/contract replacement.
void bind_simulation_kernel_diagnostics_ground_native_probe_surface(
    nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("load_arnis_terrain_bundle", &SimulationKernel::load_arnis_terrain_bundle,
             "Load a verified Arnis continuous raster bundle directory", nb::arg("bundle_root"))
        .def("load_arnis_field_overlay", &SimulationKernel::load_arnis_field_overlay,
             "Load a metadata-only Arnis field overlay", nb::arg("overlay_path"))
        .def(
            "get_ground_terrain_observation",
            [](SimulationKernel &self, double x, double y) {
                const auto sample = self.get_ground_terrain_observation(x, y);
                return std::make_tuple(sample[0], sample[1], sample[2], sample[3], sample[4]);
            },
            "Get native Ground terrain observation as (elevation, surface_type, friction, "
            "roughness, vegetation_density)",
            nb::arg("x"), nb::arg("y"))
        .def("get_ground_slope_deg", &SimulationKernel::get_ground_slope_deg,
             "Get bounded native Ground terrain slope in degrees", nb::arg("x"), nb::arg("y"))
        .def(
            "get_ground_movement_effect_observation",
            [](SimulationKernel &self, double x, double y, int stance_code) {
                const auto sample = self.get_ground_movement_effect_observation(x, y, stance_code);
                return std::make_tuple(sample[0], sample[1], sample[2], sample[3], sample[4],
                                       sample[5], sample[6], sample[7]);
            },
            "Get native Ground movement effects as (surface, slope_deg, vegetation_density, "
            "surface_multiplier, slope_multiplier, vegetation_multiplier, stance_multiplier, "
            "combined_multiplier)",
            nb::arg("x"), nb::arg("y"), nb::arg("stance_code"))
        .def(
            "get_ground_field_semantic_observation",
            [](SimulationKernel &self, double x, double y) {
                const auto sample = self.get_ground_field_semantic_observation(x, y);
                return std::make_tuple(sample[0], sample[1], sample[2], sample[3], sample[4],
                                       sample[5], sample[6]);
            },
            "Get metadata-only Ground field semantics as (configured, tree_distance, "
            "tree_bearing, settlement_distance, settlement_bearing, in_tree_line, "
            "in_settlement)",
            nb::arg("x"), nb::arg("y"))
        .def(
            "get_ground_transition_observation",
            [](SimulationKernel &self, double from_x, double from_y, double to_x, double to_y) {
                const auto sample =
                    self.get_ground_transition_observation(from_x, from_y, to_x, to_y);
                return std::make_tuple(sample[0], sample[1], sample[2], sample[3], sample[4],
                                       sample[5], sample[6]);
            },
            "Get native Ground transition as (configured, passable, destination_surface, "
            "water_blocked, obstacle_blocked, bridge_admitted, distance_m)",
            nb::arg("from_x"), nb::arg("from_y"), nb::arg("to_x"), nb::arg("to_y"))
        .def(
            "get_ground_transition_movement_observation",
            [](SimulationKernel &self, double from_x, double from_y, double to_x, double to_y,
               int stance_code) {
                const auto sample = self.get_ground_transition_movement_observation(
                    from_x, from_y, to_x, to_y, stance_code);
                return std::make_tuple(sample[0], sample[1], sample[2], sample[3], sample[4],
                                       sample[5], sample[6], sample[7], sample[8], sample[9]);
            },
            "Get native Ground transition plus sampled movement effects as (configured, passable, "
            "destination_surface, water_blocked, obstacle_blocked, bridge_admitted, distance_m, "
            "minimum_combined_multiplier, average_combined_multiplier, sample_count)",
            nb::arg("from_x"), nb::arg("from_y"), nb::arg("to_x"), nb::arg("to_y"),
            nb::arg("stance_code"))
        .def("fire_ground_weapon", &SimulationKernel::fire_ground_weapon,
             "Fire a bounded ground direct-fire weapon at a tracked ground target",
             nb::arg("attacker_id"), nb::arg("target_id"), nb::arg("weapon_type_code"))
        .def("fire_ground_weapon_from_mission_command",
             &SimulationKernel::fire_ground_weapon_from_mission_command,
             "Fire the bounded ground weapon at an authorized mission-command target",
             nb::arg("attacker_id"))
        .def("get_ground_weapon_state", &SimulationKernel::get_ground_weapon_state,
             "Get bounded ground weapon state [present, selected_type, ammo, max_ammo, damage, "
             "range, hit_probability, cooldown_remaining]",
             nb::arg("entity_id"));
}
