#include "interfaces/python/bindings_core_detail.h"

#include <cstddef>

#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"

void bind_simulation_kernel_diagnostics_platform_state_surface(
    nb::class_<SimulationKernel> &kernel) {
    kernel
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
                // read-only transport shell snapshot, not maintained truth.
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
                // read-only transport shell snapshot, not maintained truth.
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
                auto entity_lease =
                    diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                auto e = entity_lease.entity;
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
            "Debug: get pending mission command queue state", nb::arg("entity_id"));
}
