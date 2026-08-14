#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_tasking(nb::module_ &m) {
    nb::class_<MissionCommandSharedCoreDirective>(m, "MissionCommandSharedCoreDirective")
        .def(nb::init<>())
        .def_rw("cmd_heading_deg", &MissionCommandSharedCoreDirective::cmd_heading_deg)
        .def_rw("cmd_altitude_m", &MissionCommandSharedCoreDirective::cmd_altitude_m)
        .def_rw("cmd_speed_mps", &MissionCommandSharedCoreDirective::cmd_speed_mps)
        .def_rw("command_code", &MissionCommandSharedCoreDirective::command_code)
        .def_rw("route_ref_id", &MissionCommandSharedCoreDirective::route_ref_id)
        .def_rw("roe_state", &MissionCommandSharedCoreDirective::roe_state)
        .def_rw("engagement_authority_holder_id",
                &MissionCommandSharedCoreDirective::engagement_authority_holder_id)
        .def_rw("engagement_authority_grantor_id",
                &MissionCommandSharedCoreDirective::engagement_authority_grantor_id)
        .def_rw("assigned_target_id", &MissionCommandSharedCoreDirective::assigned_target_id)
        .def_rw("threat_state", &MissionCommandSharedCoreDirective::threat_state)
        .def_rw("assigned_target_track_id",
                &MissionCommandSharedCoreDirective::assigned_target_track_id)
        .def_rw("assigned_target_source_id",
                &MissionCommandSharedCoreDirective::assigned_target_source_id)
        .def_rw("assigned_target_snapshot_time_s",
                &MissionCommandSharedCoreDirective::assigned_target_snapshot_time_s)
        .def_rw("authorization_to_fire", &MissionCommandSharedCoreDirective::authorization_to_fire)
        .def_rw("active", &MissionCommandSharedCoreDirective::active);

    nb::class_<MissionCommandAir::RecoveryDirective>(m, "MissionCommandAirRecoveryDirective")
        .def(nb::init<>())
        .def_rw("recovery_base_id", &MissionCommandAir::RecoveryDirective::recovery_base_id)
        .def_rw("recovery_runway_id", &MissionCommandAir::RecoveryDirective::recovery_runway_id)
        .def_rw("recovery_approach_type",
                &MissionCommandAir::RecoveryDirective::recovery_approach_type);

    nb::class_<MissionCommandAir::TakeoffDirective>(m, "MissionCommandAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw("takeoff_procedure_id", &MissionCommandAir::TakeoffDirective::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &MissionCommandAir::TakeoffDirective::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &MissionCommandAir::TakeoffDirective::takeoff_interval_s)
        .def_rw("runway_slot_id", &MissionCommandAir::TakeoffDirective::runway_slot_id);

    nb::class_<MissionCommandAir::FormationDirective>(m, "MissionCommandAirFormationDirective")
        .def(nb::init<>())
        .def_rw("formation_id", &MissionCommandAir::FormationDirective::formation_id)
        .def_rw("form_offset_x", &MissionCommandAir::FormationDirective::form_offset_x)
        .def_rw("form_offset_y", &MissionCommandAir::FormationDirective::form_offset_y)
        .def_rw("form_offset_z", &MissionCommandAir::FormationDirective::form_offset_z);

    nb::class_<MissionCommandNaval::StationingDirective>(m,
                                                         "MissionCommandNavalStationingDirective")
        .def(nb::init<>())
        .def_rw("reference_entity_id",
                &MissionCommandNaval::StationingDirective::reference_entity_id)
        .def_rw("station_radius_m", &MissionCommandNaval::StationingDirective::station_radius_m)
        .def_rw("station_bearing_deg",
                &MissionCommandNaval::StationingDirective::station_bearing_deg);

    nb::class_<MissionCommandNaval::EmbarkedHeloDirective>(
        m, "MissionCommandNavalEmbarkedHeloDirective")
        .def(nb::init<>())
        .def_rw("embarked_helo_entity_id",
                &MissionCommandNaval::EmbarkedHeloDirective::embarked_helo_entity_id)
        .def_rw("launch_helo", &MissionCommandNaval::EmbarkedHeloDirective::launch_helo)
        .def_rw("recover_helo", &MissionCommandNaval::EmbarkedHeloDirective::recover_helo)
        .def_rw("relay_oth_targeting",
                &MissionCommandNaval::EmbarkedHeloDirective::relay_oth_targeting);

    nb::class_<LeaderIntentAir::RecoveryDirective>(m, "LeaderIntentAirRecoveryDirective")
        .def(nb::init<>())
        .def_rw("recovery_base_id", &LeaderIntentAir::RecoveryDirective::recovery_base_id)
        .def_rw("recovery_runway_id", &LeaderIntentAir::RecoveryDirective::recovery_runway_id)
        .def_rw("recovery_approach_type",
                &LeaderIntentAir::RecoveryDirective::recovery_approach_type);

    nb::class_<LeaderIntentAir::TakeoffDirective>(m, "LeaderIntentAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw("takeoff_procedure_id", &LeaderIntentAir::TakeoffDirective::takeoff_procedure_id)
        .def_rw("takeoff_clearance_id", &LeaderIntentAir::TakeoffDirective::takeoff_clearance_id)
        .def_rw("takeoff_interval_s", &LeaderIntentAir::TakeoffDirective::takeoff_interval_s)
        .def_rw("runway_slot_id", &LeaderIntentAir::TakeoffDirective::runway_slot_id);

    nb::class_<LeaderIntentAir::FormationDirective>(m, "LeaderIntentAirFormationDirective")
        .def(nb::init<>())
        .def_rw("formation_id", &LeaderIntentAir::FormationDirective::formation_id)
        .def_rw("form_offset_x", &LeaderIntentAir::FormationDirective::form_offset_x)
        .def_rw("form_offset_y", &LeaderIntentAir::FormationDirective::form_offset_y)
        .def_rw("form_offset_z", &LeaderIntentAir::FormationDirective::form_offset_z);

    nb::class_<LeaderIntentNaval::CommandAuthorityDirective>(
        m, "LeaderIntentNavalCommandAuthorityDirective")
        .def(nb::init<>())
        .def_rw("warfare_role_code",
                &LeaderIntentNaval::CommandAuthorityDirective::warfare_role_code)
        .def_rw("officer_in_tactical_command",
                &LeaderIntentNaval::CommandAuthorityDirective::officer_in_tactical_command);

    nb::class_<PilotReportNaval::CommandAuthorityDirective>(
        m, "PilotReportNavalCommandAuthorityDirective")
        .def(nb::init<>())
        .def_rw("warfare_role_code",
                &PilotReportNaval::CommandAuthorityDirective::warfare_role_code)
        .def_rw("officer_in_tactical_command",
                &PilotReportNaval::CommandAuthorityDirective::officer_in_tactical_command);

    // Binding-coverage note: MissionCommandMaintainedBatchContract/
    // TaskOrderMaintainedBatchContract/
    // LeaderIntentMaintainedBatchContract/PilotReportMaintainedBatchContract header
    // field blocks are schema-owned (tools/maintenance/dto_schema), but each of these
    // four bindings has long registered every field except its own trailing
    // ground_static_task/ground_static_status field (a pre-existing binding-surface
    // omission; TaskOrder's omitted field stays reachable through the
    // task_order_maintained_ground_static_task free function). That never-bound
    // field is preserved here as-is (parity baseline) instead of being
    // macro-expanded from the same X-macro as the header block.
    nb::class_<MissionCommandMaintainedBatchContract>(m, "MissionCommandMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &MissionCommandMaintainedBatchContract::shared_core)
        .def_rw("air_recovery", &MissionCommandMaintainedBatchContract::air_recovery)
        .def_rw("air_takeoff", &MissionCommandMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &MissionCommandMaintainedBatchContract::air_formation)
        .def_rw("naval_stationing", &MissionCommandMaintainedBatchContract::naval_stationing)
        .def_rw("naval_embarked_helo", &MissionCommandMaintainedBatchContract::naval_embarked_helo);

    nb::class_<TaskOrderMaintainedBatchContract>(m, "TaskOrderMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &TaskOrderMaintainedBatchContract::shared_core)
        .def_rw("air_tasking_identity", &TaskOrderMaintainedBatchContract::air_tasking_identity)
        .def_rw("air_stationing", &TaskOrderMaintainedBatchContract::air_stationing)
        .def_rw("air_recovery", &TaskOrderMaintainedBatchContract::air_recovery)
        .def_rw("air_takeoff", &TaskOrderMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &TaskOrderMaintainedBatchContract::air_formation)
        .def_rw("naval_command_authority",
                &TaskOrderMaintainedBatchContract::naval_command_authority)
        .def_rw("naval_stationing", &TaskOrderMaintainedBatchContract::naval_stationing);

    nb::class_<LeaderIntentMaintainedBatchContract>(m, "LeaderIntentMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &LeaderIntentMaintainedBatchContract::shared_core)
        .def_rw("phase_id", &LeaderIntentMaintainedBatchContract::phase_id)
        .def_rw("element_phase_id", &LeaderIntentMaintainedBatchContract::element_phase_id)
        .def_rw("air_recovery", &LeaderIntentMaintainedBatchContract::air_recovery)
        .def_rw("formation_mode_id", &LeaderIntentMaintainedBatchContract::formation_mode_id)
        .def_rw("join_required_flag", &LeaderIntentMaintainedBatchContract::join_required_flag)
        .def_rw("rejoin_required_flag", &LeaderIntentMaintainedBatchContract::rejoin_required_flag)
        .def_rw("air_takeoff", &LeaderIntentMaintainedBatchContract::air_takeoff)
        .def_rw("air_formation", &LeaderIntentMaintainedBatchContract::air_formation)
        .def_rw("naval_command_authority",
                &LeaderIntentMaintainedBatchContract::naval_command_authority);

    nb::class_<PilotReportMaintainedBatchContract>(m, "PilotReportMaintainedBatchContract")
        .def(nb::init<>())
        .def_rw("shared_core", &PilotReportMaintainedBatchContract::shared_core)
        .def_rw("air", &PilotReportMaintainedBatchContract::air)
        .def_rw("naval_command_authority",
                &PilotReportMaintainedBatchContract::naval_command_authority);

    m.def(
        "mission_command_maintained_batch_contract",
        [](const MissionCommand &command) {
            return mission_command_maintained_batch_contract(command);
        },
        nb::arg("command"));
    m.def(
        "leader_intent_maintained_batch_contract",
        [](const LeaderIntent &intent) { return leader_intent_maintained_batch_contract(intent); },
        nb::arg("intent"));
    m.def(
        "pilot_report_maintained_batch_contract",
        [](const PilotReport &report) { return pilot_report_maintained_batch_contract(report); },
        nb::arg("report"));
}
