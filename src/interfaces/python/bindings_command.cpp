#include "interfaces/python/binding_utils.h"

#include "components/command/common/comm_message.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/systems/comm.h"
#include "components/tasking/air/air_tasking_enums.h"
#include "components/tasking/common/core_tasking_enums.h"
#include "components/tasking/ground/ground_tasking_enums.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/naval/naval_tasking_enums.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "runtime/contracts/world_batch_contracts.h"

void bind_command(nb::module_& m) {
    nb::enum_<CommMsgType>(m, "CommMsgType")
        .value("None", CommMsgType::None)
        .value("REP_WILCO", CommMsgType::REP_WILCO)
        .value("REP_ROGER", CommMsgType::REP_ROGER)
        .value("REP_UNABLE", CommMsgType::REP_UNABLE)
        .value("REP_CANT_DO", CommMsgType::REP_CANT_DO)
        .value("STATUS_FUEL", CommMsgType::STATUS_FUEL)
        .value("STATUS_AMMO", CommMsgType::STATUS_AMMO)
        .value("STATUS_DAMAGE", CommMsgType::STATUS_DAMAGE)
        .value("STATUS_POS", CommMsgType::STATUS_POS)
        .value("REP_TALLY", CommMsgType::REP_TALLY)
        .value("REP_VISUAL", CommMsgType::REP_VISUAL)
        .value("REP_BLIND", CommMsgType::REP_BLIND)
        .value("REP_SPIKE", CommMsgType::REP_SPIKE)
        .value("REP_FAILED_SORT", CommMsgType::REP_FAILED_SORT)
        .value("REP_ENGAGED", CommMsgType::REP_ENGAGED)
        .value("REP_SPLASH", CommMsgType::REP_SPLASH)
        .value("REP_DEFENDING", CommMsgType::REP_DEFENDING)
        .value("REP_ON_STATION", CommMsgType::REP_ON_STATION)
        .value("REP_FENCE_IN", CommMsgType::REP_FENCE_IN)
        .value("REP_FENCE_OUT", CommMsgType::REP_FENCE_OUT)
        .value("REP_RTB", CommMsgType::REP_RTB)
        .value("WARN_FLAMEOUT", CommMsgType::WARN_FLAMEOUT)
        .value("WARN_BINGO", CommMsgType::WARN_BINGO)
        .value("WARN_LAUNCH", CommMsgType::WARN_LAUNCH)
        .value("ACK_WILCO", CommMsgType::ACK_WILCO)
        .value("ACK_ROGER", CommMsgType::ACK_ROGER)
        .value("ACK_UNABLE", CommMsgType::ACK_UNABLE)
        .value("ACK_CANT_DO", CommMsgType::ACK_CANT_DO)
        .value("ReportContact", CommMsgType::ReportContact)
        .value("ReportTrack", CommMsgType::ReportTrack)
        .value("AssignTask", CommMsgType::AssignTask)
        .value("StatusUpdate", CommMsgType::StatusUpdate)
        .value("RequestSupport", CommMsgType::RequestSupport)
        .value("REP_JOINED", CommMsgType::REP_JOINED)
        .value("REP_REJOINING", CommMsgType::REP_REJOINING)
        .value("REP_FORM_LOST", CommMsgType::REP_FORM_LOST)
        .value("REP_UNABLE_FORM", CommMsgType::REP_UNABLE_FORM)
        .value("REP_SUPPORTING", CommMsgType::REP_SUPPORTING)
        .value("WARN_SEPARATION", CommMsgType::WARN_SEPARATION)
        .export_values();

    nb::enum_<TaskType>(m, "TaskType")
        .value("Idle", TaskType::Idle)
        .value("Scramble", TaskType::Scramble)
        .value("CAP", TaskType::CAP)
        .value("RTB", TaskType::RTB)
        .value("RecoverLand", TaskType::RecoverLand)
        .value("CAPMission", TaskType::CAPMission);

    nb::enum_<StationType>(m, "StationType")
        .value("Orbit", StationType::Orbit)
        .value("Racetrack", StationType::Racetrack)
        .value("RouteCAP", StationType::RouteCAP);

    nb::enum_<NavalStationType>(m, "NavalStationType")
        .value("Unspecified", NavalStationType::Unspecified)
        .value("Screen", NavalStationType::Screen)
        .value("Support", NavalStationType::Support)
        .value("PatrolStation", NavalStationType::PatrolStation)
        .value("ReplenishmentTrack", NavalStationType::ReplenishmentTrack);

    nb::enum_<LeaderPhase>(m, "LeaderPhase")
        .value("Idle", LeaderPhase::Idle)
        .value("Scramble", LeaderPhase::Scramble)
        .value("Takeoff", LeaderPhase::Takeoff)
        .value("Departure", LeaderPhase::Departure)
        .value("TransitToStation", LeaderPhase::TransitToStation)
        .value("EstablishCAP", LeaderPhase::EstablishCAP)
        .value("OnStation", LeaderPhase::OnStation)
        .value("Reposition", LeaderPhase::Reposition)
        .value("RTB", LeaderPhase::RTB)
        .value("ApproachArmed", LeaderPhase::ApproachArmed)
        .value("LandingFinal", LeaderPhase::LandingFinal)
        .value("Rollout", LeaderPhase::Rollout)
        .value("Abort", LeaderPhase::Abort);

    nb::enum_<RecoveryApproachType>(m, "RecoveryApproachType")
        .value("None", RecoveryApproachType::None)
        .value("StraightIn", RecoveryApproachType::StraightIn)
        .value("ILS", RecoveryApproachType::ILS)
        .value("Visual", RecoveryApproachType::Visual)
        .value("Overhead", RecoveryApproachType::Overhead)
        .value("TACAN", RecoveryApproachType::TACAN);

    nb::enum_<ServiceProfile>(m, "ServiceProfile")
        .value("Unspecified", ServiceProfile::Unspecified)
        .value("AirForce", ServiceProfile::AirForce)
        .value("Army", ServiceProfile::Army)
        .value("Navy", ServiceProfile::Navy)
        .value("MarineCorps", ServiceProfile::MarineCorps);

    nb::enum_<TaskFamily>(m, "TaskFamily")
        .value("Unspecified", TaskFamily::Unspecified)
        .value("Transit", TaskFamily::Transit)
        .value("Patrol", TaskFamily::Patrol)
        .value("Escort", TaskFamily::Escort)
        .value("Intercept", TaskFamily::Intercept)
        .value("Attack", TaskFamily::Attack)
        .value("Defend", TaskFamily::Defend)
        .value("Recover", TaskFamily::Recover)
        .value("Withdraw", TaskFamily::Withdraw);

    nb::enum_<GroundTaskMode>(m, "GroundTaskMode")
        .value("Unspecified", GroundTaskMode::Unspecified)
        .value("HoldStatic", GroundTaskMode::HoldStatic)
        .value("OccupyStatic", GroundTaskMode::OccupyStatic)
        .value("SupportStatic", GroundTaskMode::SupportStatic);

    nb::enum_<GroundStatusPhase>(m, "GroundStatusPhase")
        .value("Unspecified", GroundStatusPhase::Unspecified)
        .value("Assigned", GroundStatusPhase::Assigned)
        .value("Preparing", GroundStatusPhase::Preparing)
        .value("HoldingStatic", GroundStatusPhase::HoldingStatic)
        .value("OccupyingStatic", GroundStatusPhase::OccupyingStatic)
        .value("SupportingStatic", GroundStatusPhase::SupportingStatic)
        .value("Complete", GroundStatusPhase::Complete);

    nb::enum_<NavalWarfareRole>(m, "NavalWarfareRole")
        .value("Unspecified", NavalWarfareRole::Unspecified)
        .value("ScreenCommander", NavalWarfareRole::ScreenCommander)
        .value("SurfaceActionCommander", NavalWarfareRole::SurfaceActionCommander)
        .value("AirDefenseCommander", NavalWarfareRole::AirDefenseCommander)
        .value("SeaControlCommander", NavalWarfareRole::SeaControlCommander)
        .value("LogisticsCoordinator", NavalWarfareRole::LogisticsCoordinator);

    nb::enum_<TacticalUnitType>(m, "TacticalUnitType")
        .value("Unspecified", TacticalUnitType::Unspecified)
        .value("Platform", TacticalUnitType::Platform)
        .value("TacticalUnit", TacticalUnitType::TacticalUnit)
        .value("MissionPackage", TacticalUnitType::MissionPackage)
        .value("CommandNode", TacticalUnitType::CommandNode);

    nb::enum_<CommandRelationship>(m, "CommandRelationship")
        .value("None", CommandRelationship::None)
        .value("COCOM", CommandRelationship::COCOM)
        .value("OPCON", CommandRelationship::OPCON)
        .value("TACON", CommandRelationship::TACON)
        .value("Support", CommandRelationship::Support)
        .value("ADCON", CommandRelationship::ADCON)
        .value("CoordinatingAuthority", CommandRelationship::CoordinatingAuthority)
        .value("DIRLAUTH", CommandRelationship::DIRLAUTH);

    nb::enum_<AuthorityScope>(m, "AuthorityScope")
        .value("Unspecified", AuthorityScope::Unspecified)
        .value("Strategic", AuthorityScope::Strategic)
        .value("Operational", AuthorityScope::Operational)
        .value("Tactical", AuthorityScope::Tactical)
        .value("Execution", AuthorityScope::Execution);

    nb::enum_<AssigneeKind>(m, "AssigneeKind")
        .value("Aircraft", AssigneeKind::Aircraft)
        .value("Element", AssigneeKind::Element)
        .value("Package", AssigneeKind::Package);

    nb::enum_<FormationRole>(m, "FormationRole")
        .value("Unspecified", FormationRole::Unspecified)
        .value("ElementLead", FormationRole::ElementLead)
        .value("Wingman", FormationRole::Wingman);

    nb::enum_<WingmanSlot>(m, "WingmanSlot")
        .value("Unspecified", WingmanSlot::Unspecified)
        .value("Left", WingmanSlot::Left)
        .value("Right", WingmanSlot::Right)
        .value("Trail", WingmanSlot::Trail);

    nb::enum_<FormationMode>(m, "FormationMode")
        .value("Unspecified", FormationMode::Unspecified)
        .value("Prejoin", FormationMode::Prejoin)
        .value("Joining", FormationMode::Joining)
        .value("Cruise", FormationMode::Cruise)
        .value("CAP", FormationMode::CAP)
        .value("Rejoin", FormationMode::Rejoin)
        .value("Recover", FormationMode::Recover)
        .value("SplitAbort", FormationMode::SplitAbort);

    nb::enum_<WingmanCommandMode>(m, "WingmanCommandMode")
        .value("None", WingmanCommandMode::None)
        .value("HoldSlot", WingmanCommandMode::HoldSlot)
        .value("Rejoin", WingmanCommandMode::Rejoin)
        .value("OffsetLeft", WingmanCommandMode::OffsetLeft)
        .value("OffsetRight", WingmanCommandMode::OffsetRight)
        .value("Trail", WingmanCommandMode::Trail)
        .value("Support", WingmanCommandMode::Support)
        .value("AbortForm", WingmanCommandMode::AbortForm);

    nb::enum_<CoordinationMode>(m, "CoordinationMode")
        .value("Unspecified", CoordinationMode::Unspecified)
        .value("Independent", CoordinationMode::Independent)
        .value("Attached", CoordinationMode::Attached)
        .value("Follow", CoordinationMode::Follow)
        .value("Support", CoordinationMode::Support)
        .value("Screen", CoordinationMode::Screen)
        .value("Rejoin", CoordinationMode::Rejoin)
        .value("Recover", CoordinationMode::Recover)
        .value("Detached", CoordinationMode::Detached);

    nb::enum_<TakeoffProcedureType>(m, "TakeoffProcedureType")
        .value("Unspecified", TakeoffProcedureType::Unspecified)
        .value("SingleShip", TakeoffProcedureType::SingleShip)
        .value("Interval", TakeoffProcedureType::Interval)
        .value("Wing", TakeoffProcedureType::Wing);

    nb::enum_<TakeoffClearanceState>(m, "TakeoffClearanceState")
        .value("Unspecified", TakeoffClearanceState::Unspecified)
        .value("HoldShort", TakeoffClearanceState::HoldShort)
        .value("LineUpAndWait", TakeoffClearanceState::LineUpAndWait)
        .value("ClearedForTakeoff", TakeoffClearanceState::ClearedForTakeoff)
        .value("Rolling", TakeoffClearanceState::Rolling)
        .value("Airborne", TakeoffClearanceState::Airborne)
        .value("Abort", TakeoffClearanceState::Abort);

    nb::enum_<RunwaySlotPosition>(m, "RunwaySlotPosition")
        .value("Unspecified", RunwaySlotPosition::Unspecified)
        .value("Center", RunwaySlotPosition::Center)
        .value("Left", RunwaySlotPosition::Left)
        .value("Right", RunwaySlotPosition::Right);

    nb::class_<CommPacket>(m, "CommPacket")
        .def(nb::init<>())
        .def_rw("sender_id", &CommPacket::sender_id)
        .def_rw("target_receiver_id", &CommPacket::target_receiver_id)
        .def_rw("type", &CommPacket::type)
        .def_rw("entity_ref", &CommPacket::entity_ref)
        .def_rw("location_x", &CommPacket::location_x)
        .def_rw("location_y", &CommPacket::location_y)
        .def_rw("location_z", &CommPacket::location_z)
        .def_rw("value", &CommPacket::value)
        .def_rw("status_code", &CommPacket::status_code)
        .def_rw("timestamp", &CommPacket::timestamp);

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
        .def_rw(
            "officer_in_tactical_command",
            &PilotReportNaval::officer_in_tactical_command
        );

    nb::class_<PilotReportGround::StaticStatusDirective>(
        m,
        "PilotReportGroundStaticStatusDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "ground_status_phase",
            &PilotReportGround::StaticStatusDirective::ground_status_phase
        )
        .def_rw(
            "ground_task_mode",
            &PilotReportGround::StaticStatusDirective::ground_task_mode
        )
        .def_rw(
            "objective_area_id",
            &PilotReportGround::StaticStatusDirective::objective_area_id
        )
        .def_rw(
            "objective_node_id",
            &PilotReportGround::StaticStatusDirective::objective_node_id
        )
        .def_rw(
            "ground_commander_id",
            &PilotReportGround::StaticStatusDirective::ground_commander_id
        )
        .def_rw(
            "tactical_cadence_hz",
            &PilotReportGround::StaticStatusDirective::tactical_cadence_hz
        )
        .def_rw(
            "readiness_ratio",
            &PilotReportGround::StaticStatusDirective::readiness_ratio
        );

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
            auto& report = nb::cast<PilotReport&>(report_obj);
            return nb::inst_reference(
                nb::type<PilotReportCore>(),
                &pilot_report_shared_core(report),
                report_obj
            );
        },
        nb::arg("report")
    );
    m.def(
        "pilot_report_air_owner_slice",
        [](nb::handle report_obj) {
            auto& report = nb::cast<PilotReport&>(report_obj);
            return nb::inst_reference(
                nb::type<PilotReportAir>(),
                &pilot_report_air_owner_slice(report),
                report_obj
            );
        },
        nb::arg("report")
    );
    m.def(
        "pilot_report_naval_owner_slice",
        [](nb::handle report_obj) {
            auto& report = nb::cast<PilotReport&>(report_obj);
            return nb::inst_reference(
                nb::type<PilotReportNaval>(),
                &pilot_report_naval_owner_slice(report),
                report_obj
            );
        },
        nb::arg("report")
    );
    m.def(
        "pilot_report_ground_owner_slice",
        [](nb::handle report_obj) {
            auto& report = nb::cast<PilotReport&>(report_obj);
            return nb::inst_reference(
                nb::type<PilotReportGround>(),
                &pilot_report_ground_owner_slice(report),
                report_obj
            );
        },
        nb::arg("report")
    );
    m.def(
        "pilot_report_ground_static_status_directive",
        [](const PilotReport& report) {
            return pilot_report_ground_static_status_directive(report);
        },
        nb::arg("report")
    );

    // Bind PilotAction
    nb::class_<PilotAction>(m, "PilotAction")
        .def(nb::init<>())
        .def_rw("stick_pitch", &PilotAction::stick_pitch)
        .def_rw("stick_roll", &PilotAction::stick_roll)
        .def_rw("rudder", &PilotAction::rudder)
        .def_rw("throttle", &PilotAction::throttle)
        .def_rw("gear_handle", &PilotAction::gear_handle)
        .def_rw("flaps", &PilotAction::flaps)
        .def_rw("speedbrake", &PilotAction::speedbrake)
        .def_rw("brake", &PilotAction::brake)
        .def_rw("brake_left", &PilotAction::brake_left)
        .def_rw("brake_right", &PilotAction::brake_right)
        .def_rw("radar_active", &PilotAction::radar_active)
        .def_rw("radar_scan_az", &PilotAction::radar_scan_az)
        .def_rw("radar_scan_el", &PilotAction::radar_scan_el)
        .def_rw("tms_up", &PilotAction::tms_up)
        .def_rw("master_arm", &PilotAction::master_arm)
        .def_rw("fire_weapon", &PilotAction::fire_weapon)
        .def_rw("fire_gun", &PilotAction::fire_gun)
        .def_rw("weapon_select_id", &PilotAction::weapon_select_id)
        .def_rw("jettison_emergency", &PilotAction::jettison_emergency)
        .def_rw("program_chaff", &PilotAction::program_chaff)
        .def_rw("program_flare", &PilotAction::program_flare)
        .def_rw("active", &PilotAction::active);

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
        .def_rw(
            "assigned_target_snapshot_time_s",
            &MissionCommand::assigned_target_snapshot_time_s
        )
        .def_rw("authorization_to_fire", &MissionCommand::authorization_to_fire)
        .def_rw("active", &MissionCommand::active);

    nb::class_<MissionCommandGround::StaticTaskDirective>(
        m,
        "MissionCommandGroundStaticTaskDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "ground_task_mode",
            &MissionCommandGround::StaticTaskDirective::ground_task_mode
        )
        .def_rw(
            "objective_area_id",
            &MissionCommandGround::StaticTaskDirective::objective_area_id
        )
        .def_rw(
            "objective_node_id",
            &MissionCommandGround::StaticTaskDirective::objective_node_id
        )
        .def_rw(
            "ground_commander_id",
            &MissionCommandGround::StaticTaskDirective::ground_commander_id
        )
        .def_rw(
            "tactical_cadence_hz",
            &MissionCommandGround::StaticTaskDirective::tactical_cadence_hz
        );

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
            auto& command = nb::cast<MissionCommand&>(command_obj);
            return nb::inst_reference(
                nb::type<MissionCommandGround>(),
                &mission_command_ground_owner_slice(command),
                command_obj
            );
        },
        nb::arg("command")
    );
    m.def(
        "mission_command_ground_static_task_directive",
        [](const MissionCommand& command) {
            return mission_command_ground_static_task_directive(command);
        },
        nb::arg("command")
    );

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
        .def_rw(
            "recovery_runway_id",
            &TaskOrderAir::RecoveryDirective::recovery_runway_id
        )
        .def_rw(
            "recovery_approach_type",
            &TaskOrderAir::RecoveryDirective::recovery_approach_type
        );

    nb::class_<TaskOrderAir::TakeoffDirective>(m, "TaskOrderAirTakeoffDirective")
        .def(nb::init<>())
        .def_rw(
            "takeoff_procedure_id",
            &TaskOrderAir::TakeoffDirective::takeoff_procedure_id
        )
        .def_rw(
            "takeoff_clearance_id",
            &TaskOrderAir::TakeoffDirective::takeoff_clearance_id
        )
        .def_rw(
            "takeoff_interval_s",
            &TaskOrderAir::TakeoffDirective::takeoff_interval_s
        )
        .def_rw("runway_slot_id", &TaskOrderAir::TakeoffDirective::runway_slot_id);

    nb::class_<TaskOrderAirTaskingIdentityDirective>(
        m,
        "TaskOrderAirTaskingIdentityDirective"
    )
        .def(nb::init<>())
        .def_rw("task_type", &TaskOrderAirTaskingIdentityDirective::task_type)
        .def_rw("element_id", &TaskOrderAirTaskingIdentityDirective::element_id)
        .def_rw("package_id", &TaskOrderAirTaskingIdentityDirective::package_id)
        .def_rw(
            "lead_aircraft_id",
            &TaskOrderAirTaskingIdentityDirective::lead_aircraft_id
        );

    nb::class_<TaskOrderAirStationingDirective>(
        m,
        "TaskOrderAirStationingDirective"
    )
        .def(nb::init<>())
        .def_rw("anchor_x_m", &TaskOrderAirStationingDirective::anchor_x_m)
        .def_rw("anchor_y_m", &TaskOrderAirStationingDirective::anchor_y_m)
        .def_rw("anchor_z_m", &TaskOrderAirStationingDirective::anchor_z_m)
        .def_rw("station_type", &TaskOrderAirStationingDirective::station_type)
        .def_rw(
            "station_radius_m",
            &TaskOrderAirStationingDirective::station_radius_m
        )
        .def_rw(
            "station_leg_length_m",
            &TaskOrderAirStationingDirective::station_leg_length_m
        )
        .def_rw(
            "station_heading_deg",
            &TaskOrderAirStationingDirective::station_heading_deg
        )
        .def_rw(
            "altitude_block_min_m",
            &TaskOrderAirStationingDirective::altitude_block_min_m
        )
        .def_rw(
            "altitude_block_max_m",
            &TaskOrderAirStationingDirective::altitude_block_max_m
        )
        .def_rw(
            "target_altitude_m",
            &TaskOrderAirStationingDirective::target_altitude_m
        )
        .def_rw("speed_min_mps", &TaskOrderAirStationingDirective::speed_min_mps)
        .def_rw("speed_max_mps", &TaskOrderAirStationingDirective::speed_max_mps)
        .def_rw(
            "target_speed_mps",
            &TaskOrderAirStationingDirective::target_speed_mps
        )
        .def_rw(
            "entry_condition_code",
            &TaskOrderAirStationingDirective::entry_condition_code
        )
        .def_rw(
            "exit_condition_code",
            &TaskOrderAirStationingDirective::exit_condition_code
        )
        .def_rw(
            "on_station_time_s",
            &TaskOrderAirStationingDirective::on_station_time_s
        )
        .def_rw(
            "fuel_bingo_override_kg",
            &TaskOrderAirStationingDirective::fuel_bingo_override_kg
        );

    nb::class_<TaskOrderAirFormationDirective>(
        m,
        "TaskOrderAirFormationDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "formation_template_id",
            &TaskOrderAirFormationDirective::formation_template_id
        )
        .def_rw(
            "formation_contract_id",
            &TaskOrderAirFormationDirective::formation_contract_id
        )
        .def_rw(
            "formation_role_id",
            &TaskOrderAirFormationDirective::formation_role_id
        )
        .def_rw("wingman_slot_id", &TaskOrderAirFormationDirective::wingman_slot_id)
        .def_rw("join_policy_id", &TaskOrderAirFormationDirective::join_policy_id)
        .def_rw(
            "rejoin_policy_id",
            &TaskOrderAirFormationDirective::rejoin_policy_id
        )
        .def_rw(
            "mutual_support_mode",
            &TaskOrderAirFormationDirective::mutual_support_mode
        )
        .def_rw(
            "support_sector_id",
            &TaskOrderAirFormationDirective::support_sector_id
        );

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

    nb::class_<TaskOrderNaval::CommandAuthorityDirective>(
        m,
        "TaskOrderNavalCommandAuthorityDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "warfare_role_code",
            &TaskOrderNaval::CommandAuthorityDirective::warfare_role_code
        )
        .def_rw(
            "officer_in_tactical_command",
            &TaskOrderNaval::CommandAuthorityDirective::officer_in_tactical_command
        );

    nb::class_<TaskOrderNaval>(m, "TaskOrderNaval")
        .def(nb::init<>())
        .def_rw("warfare_role_code", &TaskOrderNaval::warfare_role_code)
        .def_rw(
            "officer_in_tactical_command",
            &TaskOrderNaval::officer_in_tactical_command
        )
        .def_rw("naval_station_type", &TaskOrderNaval::naval_station_type);

    nb::class_<TaskOrderGround::StaticTaskDirective>(
        m,
        "TaskOrderGroundStaticTaskDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "ground_task_mode",
            &TaskOrderGround::StaticTaskDirective::ground_task_mode
        )
        .def_rw(
            "objective_area_id",
            &TaskOrderGround::StaticTaskDirective::objective_area_id
        )
        .def_rw(
            "objective_node_id",
            &TaskOrderGround::StaticTaskDirective::objective_node_id
        )
        .def_rw(
            "ground_commander_id",
            &TaskOrderGround::StaticTaskDirective::ground_commander_id
        )
        .def_rw(
            "tactical_cadence_hz",
            &TaskOrderGround::StaticTaskDirective::tactical_cadence_hz
        );

    nb::class_<TaskOrderGround>(m, "TaskOrderGround")
        .def(nb::init<>())
        .def_rw("ground_task_mode", &TaskOrderGround::ground_task_mode)
        .def_rw("objective_area_id", &TaskOrderGround::objective_area_id)
        .def_rw("objective_node_id", &TaskOrderGround::objective_node_id)
        .def_rw("ground_commander_id", &TaskOrderGround::ground_commander_id)
        .def_rw("tactical_cadence_hz", &TaskOrderGround::tactical_cadence_hz);

    nb::class_<TaskOrderNavalStationingDirective>(
        m,
        "TaskOrderNavalStationingDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "naval_station_type",
            &TaskOrderNavalStationingDirective::naval_station_type
        );

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

    m.def(
        "task_order_shared_core",
        [](nb::handle order_obj) {
            auto& order = nb::cast<TaskOrder&>(order_obj);
            return nb::inst_reference(
                nb::type<TaskOrderCore>(),
                &task_order_shared_core(order),
                order_obj
            );
        },
        nb::arg("order")
    );
    m.def(
        "task_order_shared_core_directive",
        [](const TaskOrder& order) { return task_order_shared_core_directive(order); },
        nb::arg("order")
    );
    m.def(
        "task_order_air_owner_slice",
        [](nb::handle order_obj) {
            auto& order = nb::cast<TaskOrder&>(order_obj);
            return nb::inst_reference(
                nb::type<TaskOrderAir>(),
                &task_order_air_owner_slice(order),
                order_obj
            );
        },
        nb::arg("order")
    );
    m.def(
        "task_order_naval_owner_slice",
        [](nb::handle order_obj) {
            auto& order = nb::cast<TaskOrder&>(order_obj);
            return nb::inst_reference(
                nb::type<TaskOrderNaval>(),
                &task_order_naval_owner_slice(order),
                order_obj
            );
        },
        nb::arg("order")
    );
    m.def(
        "task_order_ground_owner_slice",
        [](nb::handle order_obj) {
            auto& order = nb::cast<TaskOrder&>(order_obj);
            return nb::inst_reference(
                nb::type<TaskOrderGround>(),
                &task_order_ground_owner_slice(order),
                order_obj
            );
        },
        nb::arg("order")
    );
    m.def(
        "task_order_air_recovery_directive",
        [](const TaskOrder& order) { return task_order_air_recovery_directive(order); },
        nb::arg("order")
    );
    m.def(
        "task_order_air_tasking_identity_directive",
        [](const TaskOrder& order) {
            return task_order_air_tasking_identity_directive(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_air_stationing_directive",
        [](const TaskOrder& order) {
            return task_order_air_stationing_directive(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_air_takeoff_directive",
        [](const TaskOrder& order) { return task_order_air_takeoff_directive(order); },
        nb::arg("order")
    );
    m.def(
        "task_order_air_formation_directive",
        [](const TaskOrder& order) {
            return task_order_air_formation_directive(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_naval_command_authority",
        [](const TaskOrder& order) { return task_order_naval_command_authority(order); },
        nb::arg("order")
    );
    m.def(
        "task_order_naval_stationing_directive",
        [](const TaskOrder& order) {
            return task_order_naval_stationing_directive(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_ground_static_task_directive",
        [](const TaskOrder& order) {
            return task_order_ground_static_task_directive(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_maintained_batch_contract",
        [](const TaskOrder& order) {
            return task_order_maintained_batch_contract(order);
        },
        nb::arg("order")
    );
    m.def(
        "task_order_compatibility_shell_from_maintained_batch_contract",
        [](nb::handle contract_obj) {
            const auto& contract =
                nb::cast<const TaskOrderMaintainedBatchContract&>(contract_obj);
            return task_order_compatibility_shell_from_maintained_batch_contract(
                contract
            );
        },
        nb::arg("contract")
    );
    m.def(
        "apply_task_order_maintained_batch_contract_to_compatibility_shell",
        [](nb::handle order_obj, nb::handle contract_obj) {
            auto& order = nb::cast<TaskOrder&>(order_obj);
            const auto& contract =
                nb::cast<const TaskOrderMaintainedBatchContract&>(contract_obj);
            apply_task_order_maintained_batch_contract_to_compatibility_shell(
                order,
                contract
            );
        },
        nb::arg("order"),
        nb::arg("contract")
    );
    m.def(
        "task_order_maintained_air_tasking_identity",
        [](nb::handle contract_obj) {
            auto& contract = nb::cast<TaskOrderMaintainedBatchContract&>(
                contract_obj
            );
            return nb::inst_reference(
                nb::type<TaskOrderAirTaskingIdentityDirective>(),
                &contract.air_tasking_identity,
                contract_obj
            );
        },
        nb::arg("contract")
    );
    m.def(
        "task_order_maintained_air_stationing",
        [](nb::handle contract_obj) {
            auto& contract = nb::cast<TaskOrderMaintainedBatchContract&>(
                contract_obj
            );
            return nb::inst_reference(
                nb::type<TaskOrderAirStationingDirective>(),
                &contract.air_stationing,
                contract_obj
            );
        },
        nb::arg("contract")
    );
    m.def(
        "task_order_maintained_air_formation",
        [](nb::handle contract_obj) {
            auto& contract = nb::cast<TaskOrderMaintainedBatchContract&>(
                contract_obj
            );
            return nb::inst_reference(
                nb::type<TaskOrderAirFormationDirective>(),
                &contract.air_formation,
                contract_obj
            );
        },
        nb::arg("contract")
    );
    m.def(
        "task_order_maintained_naval_stationing",
        [](nb::handle contract_obj) {
            auto& contract = nb::cast<TaskOrderMaintainedBatchContract&>(
                contract_obj
            );
            return nb::inst_reference(
                nb::type<TaskOrderNavalStationingDirective>(),
                &contract.naval_stationing,
                contract_obj
            );
        },
        nb::arg("contract")
    );
    m.def(
        "task_order_maintained_ground_static_task",
        [](nb::handle contract_obj) {
            auto& contract = nb::cast<TaskOrderMaintainedBatchContract&>(
                contract_obj
            );
            return nb::inst_reference(
                nb::type<TaskOrderGround::StaticTaskDirective>(),
                &contract.ground_static_task,
                contract_obj
            );
        },
        nb::arg("contract")
    );

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
        .def_rw(
            "engagement_authority_holder_id",
            &LeaderIntentCore::engagement_authority_holder_id
        )
        .def_rw(
            "engagement_authority_grantor_id",
            &LeaderIntentCore::engagement_authority_grantor_id
        )
        .def_rw("assigned_target_id", &LeaderIntentCore::assigned_target_id)
        .def_rw("threat_state", &LeaderIntentCore::threat_state)
        .def_rw("assigned_target_track_id", &LeaderIntentCore::assigned_target_track_id)
        .def_rw("assigned_target_source_id", &LeaderIntentCore::assigned_target_source_id)
        .def_rw(
            "assigned_target_snapshot_time_s",
            &LeaderIntentCore::assigned_target_snapshot_time_s
        )
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
        .def_rw(
            "officer_in_tactical_command",
            &LeaderIntentNaval::officer_in_tactical_command
        );

    nb::class_<LeaderIntentGround::StaticStatusDirective>(
        m,
        "LeaderIntentGroundStaticStatusDirective"
    )
        .def(nb::init<>())
        .def_rw(
            "ground_status_phase",
            &LeaderIntentGround::StaticStatusDirective::ground_status_phase
        )
        .def_rw(
            "ground_task_mode",
            &LeaderIntentGround::StaticStatusDirective::ground_task_mode
        )
        .def_rw(
            "objective_area_id",
            &LeaderIntentGround::StaticStatusDirective::objective_area_id
        )
        .def_rw(
            "objective_node_id",
            &LeaderIntentGround::StaticStatusDirective::objective_node_id
        )
        .def_rw(
            "ground_commander_id",
            &LeaderIntentGround::StaticStatusDirective::ground_commander_id
        )
        .def_rw(
            "tactical_cadence_hz",
            &LeaderIntentGround::StaticStatusDirective::tactical_cadence_hz
        );

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
        .def_rw(
            "assigned_target_snapshot_time_s",
            &LeaderIntent::assigned_target_snapshot_time_s
        )
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
            auto& intent = nb::cast<LeaderIntent&>(intent_obj);
            return nb::inst_reference(
                nb::type<LeaderIntentCore>(),
                &leader_intent_shared_core(intent),
                intent_obj
            );
        },
        nb::arg("intent")
    );
    m.def(
        "leader_intent_air_owner_slice",
        [](nb::handle intent_obj) {
            auto& intent = nb::cast<LeaderIntent&>(intent_obj);
            return nb::inst_reference(
                nb::type<LeaderIntentAir>(),
                &leader_intent_air_owner_slice(intent),
                intent_obj
            );
        },
        nb::arg("intent")
    );
    m.def(
        "leader_intent_naval_owner_slice",
        [](nb::handle intent_obj) {
            auto& intent = nb::cast<LeaderIntent&>(intent_obj);
            return nb::inst_reference(
                nb::type<LeaderIntentNaval>(),
                &leader_intent_naval_owner_slice(intent),
                intent_obj
            );
        },
        nb::arg("intent")
    );
    m.def(
        "leader_intent_ground_owner_slice",
        [](nb::handle intent_obj) {
            auto& intent = nb::cast<LeaderIntent&>(intent_obj);
            return nb::inst_reference(
                nb::type<LeaderIntentGround>(),
                &leader_intent_ground_owner_slice(intent),
                intent_obj
            );
        },
        nb::arg("intent")
    );
    m.def(
        "leader_intent_ground_static_status_directive",
        [](const LeaderIntent& intent) {
            return leader_intent_ground_static_status_directive(intent);
        },
        nb::arg("intent")
    );
}
