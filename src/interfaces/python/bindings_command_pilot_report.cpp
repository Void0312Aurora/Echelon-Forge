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

void bind_command_pilot_report(nb::module_ &m) {
    nb::class_<PilotReportCore>(m, "PilotReportCore")
        .def(nb::init<>())
        .def_rw("report_type", &PilotReportCore::report_type)
        .def_rw("sender_id", &PilotReportCore::sender_id)
        .def_rw("task_id", &PilotReportCore::task_id)
        .def_rw("service_profile", &PilotReportCore::service_profile)
        .def_rw("task_family", &PilotReportCore::task_family)
        .def_rw("tactical_unit_type", &PilotReportCore::tactical_unit_type)
        .def_rw("tactical_unit_id", &PilotReportCore::tactical_unit_id)
        .def_rw("task_group_id", &PilotReportCore::task_group_id)
        .def_rw("role_code", &PilotReportCore::role_code)
        .def_rw("coordination_mode", &PilotReportCore::coordination_mode)
        .def_rw("timestamp_s", &PilotReportCore::timestamp_s)
        .def_rw("status_value", &PilotReportCore::status_value)
        .def_rw("entity_ref", &PilotReportCore::entity_ref)
        .def_rw("location_x_m", &PilotReportCore::location_x_m)
        .def_rw("location_y_m", &PilotReportCore::location_y_m)
        .def_rw("location_z_m", &PilotReportCore::location_z_m)
        .def_rw("active", &PilotReportCore::active);

    nb::class_<PilotReportAir>(m, "PilotReportAir")
        .def(nb::init<>())
        .def_rw("element_id", &PilotReportAir::element_id)
        .def_rw("phase_id", &PilotReportAir::phase_id)
        .def_rw("formation_role_id", &PilotReportAir::formation_role_id)
        .def_rw("formation_error_m", &PilotReportAir::formation_error_m)
        .def_rw("bearing_error_deg", &PilotReportAir::bearing_error_deg)
        .def_rw("closure_mps", &PilotReportAir::closure_mps)
        .def_rw("separation_m", &PilotReportAir::separation_m);

    nb::class_<PilotReportNaval>(m, "PilotReportNaval")
        .def(nb::init<>())
        .def_rw("warfare_role_code", &PilotReportNaval::warfare_role_code)
        .def_rw("officer_in_tactical_command", &PilotReportNaval::officer_in_tactical_command);

    nb::class_<PilotReportGround::StaticStatusDirective>(m,
                                                         "PilotReportGroundStaticStatusDirective")
        .def(nb::init<>())
        .def_rw("ground_status_phase",
                &PilotReportGround::StaticStatusDirective::ground_status_phase)
        .def_rw("ground_task_mode", &PilotReportGround::StaticStatusDirective::ground_task_mode)
        .def_rw("objective_area_id", &PilotReportGround::StaticStatusDirective::objective_area_id)
        .def_rw("objective_node_id", &PilotReportGround::StaticStatusDirective::objective_node_id)
        .def_rw("ground_commander_id",
                &PilotReportGround::StaticStatusDirective::ground_commander_id)
        .def_rw("tactical_cadence_hz",
                &PilotReportGround::StaticStatusDirective::tactical_cadence_hz)
        .def_rw("readiness_ratio", &PilotReportGround::StaticStatusDirective::readiness_ratio);

    nb::class_<PilotReportGround>(m, "PilotReportGround")
        .def(nb::init<>())
        .def_rw("ground_status_phase", &PilotReportGround::ground_status_phase)
        .def_rw("ground_task_mode", &PilotReportGround::ground_task_mode)
        .def_rw("objective_area_id", &PilotReportGround::objective_area_id)
        .def_rw("objective_node_id", &PilotReportGround::objective_node_id)
        .def_rw("ground_commander_id", &PilotReportGround::ground_commander_id)
        .def_rw("tactical_cadence_hz", &PilotReportGround::tactical_cadence_hz)
        .def_rw("readiness_ratio", &PilotReportGround::readiness_ratio);

    nb::class_<PilotReport>(m, "PilotReport")
        .def(nb::init<>())
        .def_rw("report_type", &PilotReport::report_type)
        .def_rw("sender_id", &PilotReport::sender_id)
        .def_rw("task_id", &PilotReport::task_id)
        .def_rw("service_profile", &PilotReport::service_profile)
        .def_rw("task_family", &PilotReport::task_family)
        .def_rw("tactical_unit_type", &PilotReport::tactical_unit_type)
        .def_rw("tactical_unit_id", &PilotReport::tactical_unit_id)
        .def_rw("task_group_id", &PilotReport::task_group_id)
        .def_rw("role_code", &PilotReport::role_code)
        .def_rw("warfare_role_code", &PilotReport::warfare_role_code)
        .def_rw("ground_status_phase", &PilotReport::ground_status_phase)
        .def_rw("ground_task_mode", &PilotReport::ground_task_mode)
        .def_rw("coordination_mode", &PilotReport::coordination_mode)
        .def_rw("officer_in_tactical_command", &PilotReport::officer_in_tactical_command)
        .def_rw("objective_area_id", &PilotReport::objective_area_id)
        .def_rw("objective_node_id", &PilotReport::objective_node_id)
        .def_rw("ground_commander_id", &PilotReport::ground_commander_id)
        .def_rw("element_id", &PilotReport::element_id)
        .def_rw("phase_id", &PilotReport::phase_id)
        .def_rw("formation_role_id", &PilotReport::formation_role_id)
        .def_rw("timestamp_s", &PilotReport::timestamp_s)
        .def_rw("status_value", &PilotReport::status_value)
        .def_rw("entity_ref", &PilotReport::entity_ref)
        .def_rw("location_x_m", &PilotReport::location_x_m)
        .def_rw("location_y_m", &PilotReport::location_y_m)
        .def_rw("location_z_m", &PilotReport::location_z_m)
        .def_rw("formation_error_m", &PilotReport::formation_error_m)
        .def_rw("bearing_error_deg", &PilotReport::bearing_error_deg)
        .def_rw("closure_mps", &PilotReport::closure_mps)
        .def_rw("separation_m", &PilotReport::separation_m)
        .def_rw("tactical_cadence_hz", &PilotReport::tactical_cadence_hz)
        .def_rw("readiness_ratio", &PilotReport::readiness_ratio)
        .def_rw("active", &PilotReport::active);

    m.def(
        "pilot_report_shared_core",
        [](nb::handle report_obj) {
            auto &report = nb::cast<PilotReport &>(report_obj);
            return nb::inst_reference(nb::type<PilotReportCore>(),
                                      &pilot_report_shared_core(report), report_obj);
        },
        nb::arg("report"));
    m.def(
        "pilot_report_air_owner_slice",
        [](nb::handle report_obj) {
            auto &report = nb::cast<PilotReport &>(report_obj);
            return nb::inst_reference(nb::type<PilotReportAir>(),
                                      &pilot_report_air_owner_slice(report), report_obj);
        },
        nb::arg("report"));
    m.def(
        "pilot_report_naval_owner_slice",
        [](nb::handle report_obj) {
            auto &report = nb::cast<PilotReport &>(report_obj);
            return nb::inst_reference(nb::type<PilotReportNaval>(),
                                      &pilot_report_naval_owner_slice(report), report_obj);
        },
        nb::arg("report"));
    m.def(
        "pilot_report_ground_owner_slice",
        [](nb::handle report_obj) {
            auto &report = nb::cast<PilotReport &>(report_obj);
            return nb::inst_reference(nb::type<PilotReportGround>(),
                                      &pilot_report_ground_owner_slice(report), report_obj);
        },
        nb::arg("report"));
    m.def(
        "pilot_report_ground_static_status_directive",
        [](const PilotReport &report) {
            return pilot_report_ground_static_status_directive(report);
        },
        nb::arg("report"));
}
