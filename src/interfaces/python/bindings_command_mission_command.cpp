#include "interfaces/python/bindings_command_detail.h"

#include "components/command/common/comm_message.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/systems/comm.h"
#include "components/domains/air/tasking/air_tasking_enums.h"
#include "components/tasking/common/core_tasking_enums.h"
#include "components/domains/ground/tasking/ground_tasking_enums.h"
#include "components/tasking/leader_intent.h"
#include "components/domains/naval/tasking/naval_tasking_enums.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "runtime/contracts/world_batch_contracts.h"

void bind_command_mission_command(nb::module_ &m) {
    // Bind MissionCommand
    nb::class_<MissionCommand>(m, "MissionCommand")
        .def(nb::init<>())
        .def_rw("cmd_heading_deg", &MissionCommand::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &MissionCommand::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &MissionCommand::cmd_speed_mps)
        .def_rw("command_code", &MissionCommand::command_code)
        .def_rw("route_ref_id", &MissionCommand::route_ref_id)
        .def_rw("reference_entity_id", &MissionCommand::reference_entity_id)
        .def_rw("station_radius_m", &MissionCommand::station_radius_m)
        .def_rw("station_bearing_deg", &MissionCommand::station_bearing_deg)
        .def_rw("embarked_helo_entity_id", &MissionCommand::embarked_helo_entity_id)
        .def_rw("launch_helo", &MissionCommand::launch_helo)
        .def_rw("recover_helo", &MissionCommand::recover_helo)
        .def_rw("relay_oth_targeting", &MissionCommand::relay_oth_targeting)
        .def_rw("ground_task_mode", &MissionCommand::ground_task_mode)
        .def_rw("objective_area_id", &MissionCommand::objective_area_id)
        .def_rw("objective_node_id", &MissionCommand::objective_node_id)
        .def_rw("ground_commander_id", &MissionCommand::ground_commander_id)
        .def_rw("tactical_cadence_hz", &MissionCommand::tactical_cadence_hz)
        .def_rw("recovery_base_id", &MissionCommand::recovery_base_id)
        .def_rw("recovery_runway_id", &MissionCommand::recovery_runway_id)
        .def_rw("recovery_approach_type", &MissionCommand::recovery_approach_type)
        .def_rw("takeoff_procedure_id", &MissionCommand::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &MissionCommand::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &MissionCommand::takeoff_interval_s)
        .def_rw("runway_slot_id", &MissionCommand::runway_slot_id)
        .def_rw("formation_id", &MissionCommand::formation_id)
        .def_rw("form_offset_x", &MissionCommand::form_offset_x)
        .def_rw("form_offset_y", &MissionCommand::form_offset_y)
        .def_rw("form_offset_z", &MissionCommand::form_offset_z)
        .def_rw("roe_state", &MissionCommand::roe_state)
        .def_rw("engagement_authority_holder_id", &MissionCommand::engagement_authority_holder_id)
        .def_rw("engagement_authority_grantor_id", &MissionCommand::engagement_authority_grantor_id)
        .def_rw("assigned_target_id", &MissionCommand::assigned_target_id)
        .def_rw("threat_state", &MissionCommand::threat_state)
        .def_rw("assigned_target_track_id", &MissionCommand::assigned_target_track_id)
        .def_rw("assigned_target_source_id", &MissionCommand::assigned_target_source_id)
        .def_rw("assigned_target_snapshot_time_s", &MissionCommand::assigned_target_snapshot_time_s)
        .def_rw("authorization_to_fire", &MissionCommand::authorization_to_fire)
        .def_rw("active", &MissionCommand::active);

    nb::class_<MissionCommandGround::StaticTaskDirective>(m,
                                                          "MissionCommandGroundStaticTaskDirective")
        .def(nb::init<>())
        .def_rw("ground_task_mode", &MissionCommandGround::StaticTaskDirective::ground_task_mode)
        .def_rw("objective_area_id", &MissionCommandGround::StaticTaskDirective::objective_area_id)
        .def_rw("objective_node_id", &MissionCommandGround::StaticTaskDirective::objective_node_id)
        .def_rw("ground_commander_id",
                &MissionCommandGround::StaticTaskDirective::ground_commander_id)
        .def_rw("tactical_cadence_hz",
                &MissionCommandGround::StaticTaskDirective::tactical_cadence_hz);

    nb::class_<MissionCommandGround>(m, "MissionCommandGround")
        .def(nb::init<>())
        .def_rw("ground_task_mode", &MissionCommandGround::ground_task_mode)
        .def_rw("objective_area_id", &MissionCommandGround::objective_area_id)
        .def_rw("objective_node_id", &MissionCommandGround::objective_node_id)
        .def_rw("ground_commander_id", &MissionCommandGround::ground_commander_id)
        .def_rw("tactical_cadence_hz", &MissionCommandGround::tactical_cadence_hz);

    m.def(
        "mission_command_ground_owner_slice",
        [](nb::handle command_obj) {
            auto &command = nb::cast<MissionCommand &>(command_obj);
            return nb::inst_reference(nb::type<MissionCommandGround>(),
                                      &mission_command_ground_owner_slice(command), command_obj);
        },
        nb::arg("command"));
    m.def(
        "mission_command_ground_static_task_directive",
        [](const MissionCommand &command) {
            return mission_command_ground_static_task_directive(command);
        },
        nb::arg("command"));
}
