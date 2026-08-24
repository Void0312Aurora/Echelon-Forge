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

void bind_command_leader_intent(nb::module_ &m) {
    nb::class_<LeaderIntentCore>(m, "LeaderIntentCore")
        .def(nb::init<>())
        .def_rw("service_profile", &LeaderIntentCore::service_profile)
        .def_rw("task_family", &LeaderIntentCore::task_family)
        .def_rw("tactical_unit_type", &LeaderIntentCore::tactical_unit_type)
        .def_rw("tactical_unit_id", &LeaderIntentCore::tactical_unit_id)
        .def_rw("task_group_id", &LeaderIntentCore::task_group_id)
        .def_rw("role_code", &LeaderIntentCore::role_code)
        .def_rw("coordination_mode", &LeaderIntentCore::coordination_mode)
        .def_rw("relative_slot_code", &LeaderIntentCore::relative_slot_code)
        .def_rw("recovery_site_id", &LeaderIntentCore::recovery_site_id)
        .def_rw("command_code", &LeaderIntentCore::command_code)
        .def_rw("cmd_heading_deg", &LeaderIntentCore::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &LeaderIntentCore::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &LeaderIntentCore::cmd_speed_mps)
        .def_rw("roe_state", &LeaderIntentCore::roe_state)
        .def_rw("engagement_authority_holder_id", &LeaderIntentCore::engagement_authority_holder_id)
        .def_rw("engagement_authority_grantor_id",
                &LeaderIntentCore::engagement_authority_grantor_id)
        .def_rw("assigned_target_id", &LeaderIntentCore::assigned_target_id)
        .def_rw("threat_state", &LeaderIntentCore::threat_state)
        .def_rw("assigned_target_track_id", &LeaderIntentCore::assigned_target_track_id)
        .def_rw("assigned_target_source_id", &LeaderIntentCore::assigned_target_source_id)
        .def_rw("assigned_target_snapshot_time_s",
                &LeaderIntentCore::assigned_target_snapshot_time_s)
        .def_rw("authorization_to_fire", &LeaderIntentCore::authorization_to_fire)
        .def_rw("active", &LeaderIntentCore::active);

    nb::class_<LeaderIntentAir>(m, "LeaderIntentAir")
        .def(nb::init<>())
        .def_rw("phase_id", &LeaderIntentAir::phase_id)
        .def_rw("element_phase_id", &LeaderIntentAir::element_phase_id)
        .def_rw("route_ref_id", &LeaderIntentAir::route_ref_id)
        .def_rw("recovery_base_id", &LeaderIntentAir::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntentAir::recovery_runway_id)
        .def_rw("recovery_approach_type", &LeaderIntentAir::recovery_approach_type)
        .def_rw("takeoff_procedure_id", &LeaderIntentAir::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &LeaderIntentAir::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &LeaderIntentAir::takeoff_interval_s)
        .def_rw("runway_slot_id", &LeaderIntentAir::runway_slot_id)
        .def_rw("formation_id", &LeaderIntentAir::formation_id)
        .def_rw("form_offset_x", &LeaderIntentAir::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntentAir::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntentAir::form_offset_z)
        .def_rw("formation_mode_id", &LeaderIntentAir::formation_mode_id)
        .def_rw("join_required_flag", &LeaderIntentAir::join_required_flag)
        .def_rw("rejoin_required_flag", &LeaderIntentAir::rejoin_required_flag)
        .def_rw("split_flag", &LeaderIntentAir::split_flag)
        .def_rw("support_anchor_x_m", &LeaderIntentAir::support_anchor_x_m)
        .def_rw("support_anchor_y_m", &LeaderIntentAir::support_anchor_y_m)
        .def_rw("support_slot_offset_x_m", &LeaderIntentAir::support_slot_offset_x_m)
        .def_rw("support_slot_offset_y_m", &LeaderIntentAir::support_slot_offset_y_m)
        .def_rw("wingman_command_mode", &LeaderIntentAir::wingman_command_mode)
        .def_rw("approach_armed", &LeaderIntentAir::approach_armed)
        .def_rw("commit_to_land", &LeaderIntentAir::commit_to_land)
        .def_rw("abort_flag", &LeaderIntentAir::abort_flag);

    nb::class_<LeaderIntentNaval>(m, "LeaderIntentNaval")
        .def(nb::init<>())
        .def_rw("warfare_role_code", &LeaderIntentNaval::warfare_role_code)
        .def_rw("officer_in_tactical_command", &LeaderIntentNaval::officer_in_tactical_command);

    nb::class_<LeaderIntentGround::StaticStatusDirective>(m,
                                                          "LeaderIntentGroundStaticStatusDirective")
        .def(nb::init<>())
        .def_rw("ground_status_phase",
                &LeaderIntentGround::StaticStatusDirective::ground_status_phase)
        .def_rw("ground_task_mode", &LeaderIntentGround::StaticStatusDirective::ground_task_mode)
        .def_rw("objective_area_id", &LeaderIntentGround::StaticStatusDirective::objective_area_id)
        .def_rw("objective_node_id", &LeaderIntentGround::StaticStatusDirective::objective_node_id)
        .def_rw("ground_commander_id",
                &LeaderIntentGround::StaticStatusDirective::ground_commander_id)
        .def_rw("tactical_cadence_hz",
                &LeaderIntentGround::StaticStatusDirective::tactical_cadence_hz);

    nb::class_<LeaderIntentGround>(m, "LeaderIntentGround")
        .def(nb::init<>())
        .def_rw("ground_status_phase", &LeaderIntentGround::ground_status_phase)
        .def_rw("ground_task_mode", &LeaderIntentGround::ground_task_mode)
        .def_rw("objective_area_id", &LeaderIntentGround::objective_area_id)
        .def_rw("objective_node_id", &LeaderIntentGround::objective_node_id)
        .def_rw("ground_commander_id", &LeaderIntentGround::ground_commander_id)
        .def_rw("tactical_cadence_hz", &LeaderIntentGround::tactical_cadence_hz);

    nb::class_<LeaderIntent>(m, "LeaderIntent")
        .def(nb::init<>())
        .def_rw("phase_id", &LeaderIntent::phase_id)
        .def_rw("element_phase_id", &LeaderIntent::element_phase_id)
        .def_rw("service_profile", &LeaderIntent::service_profile)
        .def_rw("task_family", &LeaderIntent::task_family)
        .def_rw("tactical_unit_type", &LeaderIntent::tactical_unit_type)
        .def_rw("tactical_unit_id", &LeaderIntent::tactical_unit_id)
        .def_rw("task_group_id", &LeaderIntent::task_group_id)
        .def_rw("role_code", &LeaderIntent::role_code)
        .def_rw("warfare_role_code", &LeaderIntent::warfare_role_code)
        .def_rw("ground_status_phase", &LeaderIntent::ground_status_phase)
        .def_rw("ground_task_mode", &LeaderIntent::ground_task_mode)
        .def_rw("coordination_mode", &LeaderIntent::coordination_mode)
        .def_rw("relative_slot_code", &LeaderIntent::relative_slot_code)
        .def_rw("recovery_site_id", &LeaderIntent::recovery_site_id)
        .def_rw("officer_in_tactical_command", &LeaderIntent::officer_in_tactical_command)
        .def_rw("objective_area_id", &LeaderIntent::objective_area_id)
        .def_rw("objective_node_id", &LeaderIntent::objective_node_id)
        .def_rw("ground_commander_id", &LeaderIntent::ground_commander_id)
        .def_rw("command_code", &LeaderIntent::command_code)
        .def_rw("route_ref_id", &LeaderIntent::route_ref_id)
        .def_rw("recovery_base_id", &LeaderIntent::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntent::recovery_runway_id)
        .def_rw("recovery_approach_type", &LeaderIntent::recovery_approach_type)
        .def_rw("takeoff_procedure_id", &LeaderIntent::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &LeaderIntent::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &LeaderIntent::takeoff_interval_s)
        .def_rw("runway_slot_id", &LeaderIntent::runway_slot_id)
        .def_rw("cmd_heading_deg", &LeaderIntent::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &LeaderIntent::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &LeaderIntent::cmd_speed_mps)
        .def_rw("formation_id", &LeaderIntent::formation_id)
        .def_rw("form_offset_x", &LeaderIntent::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntent::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntent::form_offset_z)
        .def_rw("roe_state", &LeaderIntent::roe_state)
        .def_rw("engagement_authority_holder_id", &LeaderIntent::engagement_authority_holder_id)
        .def_rw("engagement_authority_grantor_id", &LeaderIntent::engagement_authority_grantor_id)
        .def_rw("assigned_target_id", &LeaderIntent::assigned_target_id)
        .def_rw("threat_state", &LeaderIntent::threat_state)
        .def_rw("assigned_target_track_id", &LeaderIntent::assigned_target_track_id)
        .def_rw("assigned_target_source_id", &LeaderIntent::assigned_target_source_id)
        .def_rw("assigned_target_snapshot_time_s", &LeaderIntent::assigned_target_snapshot_time_s)
        .def_rw("authorization_to_fire", &LeaderIntent::authorization_to_fire)
        .def_rw("formation_mode_id", &LeaderIntent::formation_mode_id)
        .def_rw("join_required_flag", &LeaderIntent::join_required_flag)
        .def_rw("rejoin_required_flag", &LeaderIntent::rejoin_required_flag)
        .def_rw("split_flag", &LeaderIntent::split_flag)
        .def_rw("support_anchor_x_m", &LeaderIntent::support_anchor_x_m)
        .def_rw("support_anchor_y_m", &LeaderIntent::support_anchor_y_m)
        .def_rw("support_slot_offset_x_m", &LeaderIntent::support_slot_offset_x_m)
        .def_rw("support_slot_offset_y_m", &LeaderIntent::support_slot_offset_y_m)
        .def_rw("wingman_command_mode", &LeaderIntent::wingman_command_mode)
        .def_rw("approach_armed", &LeaderIntent::approach_armed)
        .def_rw("commit_to_land", &LeaderIntent::commit_to_land)
        .def_rw("abort_flag", &LeaderIntent::abort_flag)
        .def_rw("tactical_cadence_hz", &LeaderIntent::tactical_cadence_hz)
        .def_rw("active", &LeaderIntent::active);

    m.def(
        "leader_intent_shared_core",
        [](nb::handle intent_obj) {
            auto &intent = nb::cast<LeaderIntent &>(intent_obj);
            return nb::inst_reference(nb::type<LeaderIntentCore>(),
                                      &leader_intent_shared_core(intent), intent_obj);
        },
        nb::arg("intent"));
    m.def(
        "leader_intent_air_owner_slice",
        [](nb::handle intent_obj) {
            auto &intent = nb::cast<LeaderIntent &>(intent_obj);
            return nb::inst_reference(nb::type<LeaderIntentAir>(),
                                      &leader_intent_air_owner_slice(intent), intent_obj);
        },
        nb::arg("intent"));
    m.def(
        "leader_intent_naval_owner_slice",
        [](nb::handle intent_obj) {
            auto &intent = nb::cast<LeaderIntent &>(intent_obj);
            return nb::inst_reference(nb::type<LeaderIntentNaval>(),
                                      &leader_intent_naval_owner_slice(intent), intent_obj);
        },
        nb::arg("intent"));
    m.def(
        "leader_intent_ground_owner_slice",
        [](nb::handle intent_obj) {
            auto &intent = nb::cast<LeaderIntent &>(intent_obj);
            return nb::inst_reference(nb::type<LeaderIntentGround>(),
                                      &leader_intent_ground_owner_slice(intent), intent_obj);
        },
        nb::arg("intent"));
    m.def(
        "leader_intent_ground_static_status_directive",
        [](const LeaderIntent &intent) {
            return leader_intent_ground_static_status_directive(intent);
        },
        nb::arg("intent"));
}
