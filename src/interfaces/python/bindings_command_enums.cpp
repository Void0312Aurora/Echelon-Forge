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

void bind_command_enums(nb::module_ &m) {
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
        .value("MoveStatic", GroundTaskMode::MoveStatic)
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
}
