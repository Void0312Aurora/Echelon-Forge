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

void bind_command_task_order(nb::module_ &m) {
    nb::class_<TaskOrderCore>(m, "TaskOrderCore")
        .def(nb::init<>())
        .def_rw("task_id", &TaskOrderCore::task_id)
        .def_rw("service_profile", &TaskOrderCore::service_profile)
        .def_rw("task_family", &TaskOrderCore::task_family)
        .def_rw("tactical_unit_type", &TaskOrderCore::tactical_unit_type)
        .def_rw("priority", &TaskOrderCore::priority)
        .def_rw("issuer_id", &TaskOrderCore::issuer_id)
        .def_rw("assignee_id", &TaskOrderCore::assignee_id)
        .def_rw("command_relationship", &TaskOrderCore::command_relationship)
        .def_rw("authority_scope", &TaskOrderCore::authority_scope)
        .def_rw("parent_node_id", &TaskOrderCore::parent_node_id)
        .def_rw("task_group_id", &TaskOrderCore::task_group_id)
        .def_rw("supported_node_id", &TaskOrderCore::supported_node_id)
        .def_rw("supporting_node_id", &TaskOrderCore::supporting_node_id)
        .def_rw("role_code", &TaskOrderCore::role_code)
        .def_rw("coordination_mode", &TaskOrderCore::coordination_mode)
        .def_rw("relative_slot_code", &TaskOrderCore::relative_slot_code)
        .def_rw("assignee_kind", &TaskOrderCore::assignee_kind)
        .def_rw("recovery_site_id", &TaskOrderCore::recovery_site_id)
        .def_rw("active", &TaskOrderCore::active)
        .def_rw("issue_time_s", &TaskOrderCore::issue_time_s);

    nb::class_<TaskOrderAir::RecoveryDirective>(m, "TaskOrderAirRecoveryDirective")
        .def(nb::init<>())
        .def_rw("recovery_base_id", &TaskOrderAir::RecoveryDirective::recovery_base_id)
        .def_rw("recovery_runway_id", &TaskOrderAir::RecoveryDirective::recovery_runway_id)
        .def_rw("recovery_approach_type", &TaskOrderAir::RecoveryDirective::recovery_approach_type);

    nb::class_<TaskOrderAir::TakeoffDirective>(m, "TaskOrderAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw("takeoff_procedure_id", &TaskOrderAir::TakeoffDirective::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &TaskOrderAir::TakeoffDirective::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &TaskOrderAir::TakeoffDirective::takeoff_interval_s)
        .def_rw("runway_slot_id", &TaskOrderAir::TakeoffDirective::runway_slot_id);

    nb::class_<TaskOrderAirTaskingIdentityDirective>
        task_order_air_tasking_identity_directive_class(m, "TaskOrderAirTaskingIdentityDirective");
    task_order_air_tasking_identity_directive_class.def(nb::init<>());
#define EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(type, name, default_value)              \
    task_order_air_tasking_identity_directive_class.def_rw(                                        \
        #name, &TaskOrderAirTaskingIdentityDirective::name);
#include "runtime/contracts/detail/tasking/task_order_air_tasking_identity_directive.inc"

    nb::class_<TaskOrderAirStationingDirective> task_order_air_stationing_directive_class(
        m, "TaskOrderAirStationingDirective");
    task_order_air_stationing_directive_class.def(nb::init<>());
#define EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(type, name, default_value)                    \
    task_order_air_stationing_directive_class.def_rw(#name, &TaskOrderAirStationingDirective::name);
#include "runtime/contracts/detail/tasking/task_order_air_stationing_directive.inc"

    nb::class_<TaskOrderAirFormationDirective> task_order_air_formation_directive_class(
        m, "TaskOrderAirFormationDirective");
    task_order_air_formation_directive_class.def(nb::init<>());
#define EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(type, name, default_value)                     \
    task_order_air_formation_directive_class.def_rw(#name, &TaskOrderAirFormationDirective::name);
#include "runtime/contracts/detail/tasking/task_order_air_formation_directive.inc"

    nb::class_<TaskOrderAir>(m, "TaskOrderAir")
        .def(nb::init<>())
        .def_rw("task_type", &TaskOrderAir::task_type)
        .def_rw("element_id", &TaskOrderAir::element_id)
        .def_rw("package_id", &TaskOrderAir::package_id)
        .def_rw("lead_aircraft_id", &TaskOrderAir::lead_aircraft_id)
        .def_rw("anchor_x_m", &TaskOrderAir::anchor_x_m)
        .def_rw("anchor_y_m", &TaskOrderAir::anchor_y_m)
        .def_rw("anchor_z_m", &TaskOrderAir::anchor_z_m)
        .def_rw("station_type", &TaskOrderAir::station_type)
        .def_rw("station_radius_m", &TaskOrderAir::station_radius_m)
        .def_rw("station_leg_length_m", &TaskOrderAir::station_leg_length_m)
        .def_rw("station_heading_deg", &TaskOrderAir::station_heading_deg)
        .def_rw("altitude_block_min_m", &TaskOrderAir::altitude_block_min_m)
        .def_rw("altitude_block_max_m", &TaskOrderAir::altitude_block_max_m)
        .def_rw("target_altitude_m", &TaskOrderAir::target_altitude_m)
        .def_rw("speed_min_mps", &TaskOrderAir::speed_min_mps)
        .def_rw("speed_max_mps", &TaskOrderAir::speed_max_mps)
        .def_rw("target_speed_mps", &TaskOrderAir::target_speed_mps)
        .def_rw("entry_condition_code", &TaskOrderAir::entry_condition_code)
        .def_rw("exit_condition_code", &TaskOrderAir::exit_condition_code)
        .def_rw("on_station_time_s", &TaskOrderAir::on_station_time_s)
        .def_rw("fuel_bingo_override_kg", &TaskOrderAir::fuel_bingo_override_kg)
        .def_rw("recovery_base_id", &TaskOrderAir::recovery_base_id)
        .def_rw("recovery_runway_id", &TaskOrderAir::recovery_runway_id)
        .def_rw("recovery_approach_type", &TaskOrderAir::recovery_approach_type)
        .def_rw("takeoff_procedure_id", &TaskOrderAir::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &TaskOrderAir::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &TaskOrderAir::takeoff_interval_s)
        .def_rw("runway_slot_id", &TaskOrderAir::runway_slot_id)
        .def_rw("formation_template_id", &TaskOrderAir::formation_template_id)
        .def_rw("formation_contract_id", &TaskOrderAir::formation_contract_id)
        .def_rw("formation_role_id", &TaskOrderAir::formation_role_id)
        .def_rw("wingman_slot_id", &TaskOrderAir::wingman_slot_id)
        .def_rw("join_policy_id", &TaskOrderAir::join_policy_id)
        .def_rw("rejoin_policy_id", &TaskOrderAir::rejoin_policy_id)
        .def_rw("mutual_support_mode", &TaskOrderAir::mutual_support_mode)
        .def_rw("support_sector_id", &TaskOrderAir::support_sector_id);

    nb::class_<TaskOrderNaval::CommandAuthorityDirective>(m,
                                                          "TaskOrderNavalCommandAuthorityDirective")
        .def(nb::init<>())
        .def_rw("warfare_role_code", &TaskOrderNaval::CommandAuthorityDirective::warfare_role_code)
        .def_rw("officer_in_tactical_command",
                &TaskOrderNaval::CommandAuthorityDirective::officer_in_tactical_command);

    nb::class_<TaskOrderNaval>(m, "TaskOrderNaval")
        .def(nb::init<>())
        .def_rw("warfare_role_code", &TaskOrderNaval::warfare_role_code)
        .def_rw("officer_in_tactical_command", &TaskOrderNaval::officer_in_tactical_command)
        .def_rw("naval_station_type", &TaskOrderNaval::naval_station_type);

    nb::class_<TaskOrderGround::StaticTaskDirective>(m, "TaskOrderGroundStaticTaskDirective")
        .def(nb::init<>())
        .def_rw("ground_task_mode", &TaskOrderGround::StaticTaskDirective::ground_task_mode)
        .def_rw("objective_area_id", &TaskOrderGround::StaticTaskDirective::objective_area_id)
        .def_rw("objective_node_id", &TaskOrderGround::StaticTaskDirective::objective_node_id)
        .def_rw("ground_commander_id", &TaskOrderGround::StaticTaskDirective::ground_commander_id)
        .def_rw("tactical_cadence_hz", &TaskOrderGround::StaticTaskDirective::tactical_cadence_hz);

    nb::class_<TaskOrderGround>(m, "TaskOrderGround")
        .def(nb::init<>())
        .def_rw("ground_task_mode", &TaskOrderGround::ground_task_mode)
        .def_rw("objective_area_id", &TaskOrderGround::objective_area_id)
        .def_rw("objective_node_id", &TaskOrderGround::objective_node_id)
        .def_rw("ground_commander_id", &TaskOrderGround::ground_commander_id)
        .def_rw("tactical_cadence_hz", &TaskOrderGround::tactical_cadence_hz);

    nb::class_<TaskOrderNavalStationingDirective> task_order_naval_stationing_directive_class(
        m, "TaskOrderNavalStationingDirective");
    task_order_naval_stationing_directive_class.def(nb::init<>());
#define EF_TASK_ORDER_NAVAL_STATIONING_DIRECTIVE_FIELD(type, name, default_value)                  \
    task_order_naval_stationing_directive_class.def_rw(#name,                                      \
                                                       &TaskOrderNavalStationingDirective::name);
#include "runtime/contracts/detail/tasking/task_order_naval_stationing_directive.inc"

    nb::class_<TaskOrder>(m, "TaskOrder")
        .def(nb::init<>())
        .def_rw("task_id", &TaskOrder::task_id)
        .def_rw("task_type", &TaskOrder::task_type)
        .def_rw("service_profile", &TaskOrder::service_profile)
        .def_rw("task_family", &TaskOrder::task_family)
        .def_rw("tactical_unit_type", &TaskOrder::tactical_unit_type)
        .def_rw("priority", &TaskOrder::priority)
        .def_rw("issuer_id", &TaskOrder::issuer_id)
        .def_rw("assignee_id", &TaskOrder::assignee_id)
        .def_rw("command_relationship", &TaskOrder::command_relationship)
        .def_rw("authority_scope", &TaskOrder::authority_scope)
        .def_rw("parent_node_id", &TaskOrder::parent_node_id)
        .def_rw("task_group_id", &TaskOrder::task_group_id)
        .def_rw("supported_node_id", &TaskOrder::supported_node_id)
        .def_rw("supporting_node_id", &TaskOrder::supporting_node_id)
        .def_rw("role_code", &TaskOrder::role_code)
        .def_rw("warfare_role_code", &TaskOrder::warfare_role_code)
        .def_rw("ground_task_mode", &TaskOrder::ground_task_mode)
        .def_rw("coordination_mode", &TaskOrder::coordination_mode)
        .def_rw("relative_slot_code", &TaskOrder::relative_slot_code)
        .def_rw("assignee_kind", &TaskOrder::assignee_kind)
        .def_rw("recovery_site_id", &TaskOrder::recovery_site_id)
        .def_rw("officer_in_tactical_command", &TaskOrder::officer_in_tactical_command)
        .def_rw("objective_area_id", &TaskOrder::objective_area_id)
        .def_rw("objective_node_id", &TaskOrder::objective_node_id)
        .def_rw("ground_commander_id", &TaskOrder::ground_commander_id)
        .def_rw("element_id", &TaskOrder::element_id)
        .def_rw("package_id", &TaskOrder::package_id)
        .def_rw("lead_aircraft_id", &TaskOrder::lead_aircraft_id)
        .def_rw("active", &TaskOrder::active)
        .def_rw("issue_time_s", &TaskOrder::issue_time_s)
        .def_rw("anchor_x_m", &TaskOrder::anchor_x_m)
        .def_rw("anchor_y_m", &TaskOrder::anchor_y_m)
        .def_rw("anchor_z_m", &TaskOrder::anchor_z_m)
        .def_rw("station_type", &TaskOrder::station_type)
        .def_rw("naval_station_type", &TaskOrder::naval_station_type)
        .def_rw("station_radius_m", &TaskOrder::station_radius_m)
        .def_rw("station_leg_length_m", &TaskOrder::station_leg_length_m)
        .def_rw("station_heading_deg", &TaskOrder::station_heading_deg)
        .def_rw("altitude_block_min_m", &TaskOrder::altitude_block_min_m)
        .def_rw("altitude_block_max_m", &TaskOrder::altitude_block_max_m)
        .def_rw("target_altitude_m", &TaskOrder::target_altitude_m)
        .def_rw("speed_min_mps", &TaskOrder::speed_min_mps)
        .def_rw("speed_max_mps", &TaskOrder::speed_max_mps)
        .def_rw("target_speed_mps", &TaskOrder::target_speed_mps)
        .def_rw("entry_condition_code", &TaskOrder::entry_condition_code)
        .def_rw("exit_condition_code", &TaskOrder::exit_condition_code)
        .def_rw("on_station_time_s", &TaskOrder::on_station_time_s)
        .def_rw("fuel_bingo_override_kg", &TaskOrder::fuel_bingo_override_kg)
        .def_rw("recovery_base_id", &TaskOrder::recovery_base_id)
        .def_rw("recovery_runway_id", &TaskOrder::recovery_runway_id)
        .def_rw("recovery_approach_type", &TaskOrder::recovery_approach_type)
        .def_rw("takeoff_procedure_id", &TaskOrder::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &TaskOrder::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &TaskOrder::takeoff_interval_s)
        .def_rw("runway_slot_id", &TaskOrder::runway_slot_id)
        .def_rw("formation_template_id", &TaskOrder::formation_template_id)
        .def_rw("formation_contract_id", &TaskOrder::formation_contract_id)
        .def_rw("formation_role_id", &TaskOrder::formation_role_id)
        .def_rw("wingman_slot_id", &TaskOrder::wingman_slot_id)
        .def_rw("join_policy_id", &TaskOrder::join_policy_id)
        .def_rw("rejoin_policy_id", &TaskOrder::rejoin_policy_id)
        .def_rw("mutual_support_mode", &TaskOrder::mutual_support_mode)
        .def_rw("support_sector_id", &TaskOrder::support_sector_id)
        .def_rw("tactical_cadence_hz", &TaskOrder::tactical_cadence_hz);
}
