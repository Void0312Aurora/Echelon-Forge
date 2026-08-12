#include "interfaces/python/bindings_core_detail.h"

#include <stdexcept>

#include "components/command/legacy_command_bridge.h"

namespace {
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
} // namespace

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
