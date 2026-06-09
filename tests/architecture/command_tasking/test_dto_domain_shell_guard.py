from __future__ import annotations

import re
import textwrap
from pathlib import Path

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

MISSION_COMMAND_HEADER = REPO_ROOT / "src" / "components" / "command" / "mission_command.h"
MISSION_COMMAND_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "air" / "mission_command_air.h"
)
MISSION_COMMAND_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "naval" / "mission_command_naval.h"
)
MISSION_COMMAND_GROUND_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "ground" / "mission_command_ground.h"
)
TASK_ORDER_HEADER = REPO_ROOT / "src" / "components" / "tasking" / "task_order.h"
TASK_ORDER_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "air" / "task_order_air.h"
)
TASK_ORDER_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "naval" / "task_order_naval.h"
)
TASK_ORDER_GROUND_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "ground" / "task_order_ground.h"
)
LEADER_INTENT_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "leader_intent.h"
)
LEADER_INTENT_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "air" / "leader_intent_air.h"
)
LEADER_INTENT_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "naval" / "leader_intent_naval.h"
)
LEADER_INTENT_GROUND_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "ground" / "leader_intent_ground.h"
)
PILOT_REPORT_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "pilot_report.h"
)
PILOT_REPORT_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "air" / "pilot_report_air.h"
)
PILOT_REPORT_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "naval" / "pilot_report_naval.h"
)
PILOT_REPORT_GROUND_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "ground" / "pilot_report_ground.h"
)
WORLD_BATCH_CONTRACTS_HEADER = (
    REPO_ROOT / "src" / "runtime" / "contracts" / "world_batch_contracts.h"
)
MISSION_COMMAND_CODEC_CPP = (
    REPO_ROOT / "src" / "core" / "mission" / "episode" / "detail" / "mission_command_codec.cpp"
)
EXECUTION_EPISODE_STATE_CPP = (
    REPO_ROOT / "src" / "core" / "mission" / "episode" / "execution_episode_state.cpp"
)
SHIP_MOTION_SYSTEM_HEADER = REPO_ROOT / "src" / "systems" / "naval" / "ship_motion_system.h"
EMBARKED_AIR_OPS_SYSTEM_HEADER = (
    REPO_ROOT / "src" / "systems" / "naval" / "embarked_air_ops_system.h"
)
BINDINGS_COMMAND_CPP = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_command.cpp"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compile_and_run(source: str):
    return compile_cpp_snippet(source, binary_prefix="command_tasking_dto_domain_shell")


def test_wp22_command_and_tasking_headers_name_compatibility_shells_and_owner_slices() -> None:
    mission_text = _text(MISSION_COMMAND_HEADER)
    task_order_text = _text(TASK_ORDER_HEADER)
    leader_text = _text(LEADER_INTENT_HEADER)
    pilot_text = _text(PILOT_REPORT_HEADER)

    for token in (
        "using MissionCommandCompatibilityTransportShell = MissionCommand;",
        "using MissionCommandSharedCoreOwnerSlice = MissionCommandCore;",
        "inline constexpr bool kMissionCommandCompatibilityTransportShell = true;",
        "inline constexpr bool kMissionCommandSharedCoreOwnedSurface = true;",
        "mission_command_shared_core(",
        "mission_command_shared_core_directive(",
        "mission_command_air_owner_slice(",
        "mission_command_naval_owner_slice(",
        "mission_command_ground_owner_slice(",
        "mission_command_air_recovery_directive(",
        "mission_command_air_takeoff_directive(",
        "mission_command_air_formation_directive(",
        "mission_command_naval_stationing_directive(",
        "mission_command_naval_embarked_helo_directive(",
        "mission_command_ground_static_task_directive(",
    ):
        assert token in mission_text

    for token in (
        "using TaskOrderCompatibilityTransportShell = TaskOrder;",
        "using TaskOrderSharedCoreOwnerSlice = TaskOrderCore;",
        "using TaskOrderSharedCoreDirective = TaskOrderCore;",
        "inline constexpr bool kTaskOrderCompatibilityTransportShell = true;",
        "inline constexpr bool kTaskOrderSharedCoreOwnedSurface = true;",
        "task_order_shared_core(",
        "task_order_shared_core_directive(",
        "task_order_air_owner_slice(",
        "task_order_naval_owner_slice(",
        "task_order_ground_owner_slice(",
        "task_order_air_recovery_directive(",
        "task_order_air_takeoff_directive(",
        "task_order_naval_command_authority(",
        "task_order_ground_static_task_directive(",
    ):
        assert token in task_order_text

    for token in (
        "using LeaderIntentCompatibilityTransportShell = LeaderIntent;",
        "inline constexpr bool kLeaderIntentCompatibilityTransportShell = true;",
        "leader_intent_shared_core(",
        "leader_intent_air_owner_slice(",
        "leader_intent_naval_owner_slice(",
        "leader_intent_ground_owner_slice(",
        "leader_intent_air_recovery_directive(",
        "leader_intent_air_takeoff_directive(",
        "leader_intent_air_formation_directive(",
        "leader_intent_naval_command_authority(",
        "leader_intent_ground_static_status_directive(",
    ):
        assert token in leader_text

    for token in (
        "using PilotReportCompatibilityTransportShell = PilotReport;",
        "inline constexpr bool kPilotReportCompatibilityTransportShell = true;",
        "pilot_report_shared_core(",
        "pilot_report_air_owner_slice(",
        "pilot_report_naval_owner_slice(",
        "pilot_report_ground_owner_slice(",
        "pilot_report_naval_command_authority(",
        "pilot_report_ground_static_status_directive(",
    ):
        assert token in pilot_text


def test_wp22_air_and_naval_slice_headers_mark_named_owner_surfaces() -> None:
    expected_tokens = {
        MISSION_COMMAND_AIR_HEADER: (
            "using MissionCommandAirOwnerSlice = MissionCommandAir;",
            "inline constexpr bool kMissionCommandAirOwnedDomainSlice = true;",
            "struct RecoveryDirective",
            "struct TakeoffDirective",
            "struct FormationDirective",
            "mission_command_air_recovery_directive(",
            "mission_command_air_takeoff_directive(",
            "mission_command_air_formation_directive(",
        ),
        MISSION_COMMAND_NAVAL_HEADER: (
            "using MissionCommandNavalOwnerSlice = MissionCommandNaval;",
            "inline constexpr bool kMissionCommandNavalOwnedDomainSlice = true;",
            "struct StationingDirective",
            "struct EmbarkedHeloDirective",
            "mission_command_naval_stationing_directive(",
            "mission_command_naval_embarked_helo_directive(",
        ),
        MISSION_COMMAND_GROUND_HEADER: (
            "using MissionCommandGroundOwnerSlice = MissionCommandGround;",
            "inline constexpr bool kMissionCommandGroundOwnedDomainSlice = true;",
            "struct StaticTaskDirective",
            "mission_command_ground_static_task_directive(",
            "GroundTaskMode",
            "tactical_cadence_hz",
        ),
        TASK_ORDER_AIR_HEADER: (
            "using TaskOrderAirOwnerSlice = TaskOrderAir;",
            "inline constexpr bool kTaskOrderAirOwnedDomainSlice = true;",
            "struct RecoveryDirective",
            "struct TakeoffDirective",
            "task_order_air_recovery_directive(",
            "task_order_air_takeoff_directive(",
        ),
        TASK_ORDER_NAVAL_HEADER: (
            "using TaskOrderNavalOwnerSlice = TaskOrderNaval;",
            "inline constexpr bool kTaskOrderNavalOwnedDomainSlice = true;",
            "struct CommandAuthorityDirective",
            "task_order_naval_command_authority(",
        ),
        TASK_ORDER_GROUND_HEADER: (
            "using TaskOrderGroundOwnerSlice = TaskOrderGround;",
            "inline constexpr bool kTaskOrderGroundOwnedDomainSlice = true;",
            "struct StaticTaskDirective",
            "task_order_ground_static_task_directive(",
            "GroundTaskMode",
            "tactical_cadence_hz",
        ),
        LEADER_INTENT_AIR_HEADER: (
            "using LeaderIntentAirOwnerSlice = LeaderIntentAir;",
            "inline constexpr bool kLeaderIntentAirOwnedDomainSlice = true;",
            "struct RecoveryDirective",
            "struct TakeoffDirective",
            "struct FormationDirective",
            "leader_intent_air_recovery_directive(",
            "leader_intent_air_takeoff_directive(",
            "leader_intent_air_formation_directive(",
        ),
        LEADER_INTENT_NAVAL_HEADER: (
            "using LeaderIntentNavalOwnerSlice = LeaderIntentNaval;",
            "inline constexpr bool kLeaderIntentNavalOwnedDomainSlice = true;",
            "struct CommandAuthorityDirective",
            "leader_intent_naval_command_authority(",
        ),
        LEADER_INTENT_GROUND_HEADER: (
            "using LeaderIntentGroundOwnerSlice = LeaderIntentGround;",
            "inline constexpr bool kLeaderIntentGroundOwnedDomainSlice = true;",
            "struct StaticStatusDirective",
            "leader_intent_ground_static_status_directive(",
            "GroundStatusPhase",
            "tactical_cadence_hz",
        ),
        PILOT_REPORT_AIR_HEADER: (
            "using PilotReportAirOwnerSlice = PilotReportAir;",
            "inline constexpr bool kPilotReportAirOwnedDomainSlice = true;",
        ),
        PILOT_REPORT_NAVAL_HEADER: (
            "using PilotReportNavalOwnerSlice = PilotReportNaval;",
            "inline constexpr bool kPilotReportNavalOwnedDomainSlice = true;",
            "struct CommandAuthorityDirective",
            "pilot_report_naval_command_authority(",
        ),
        PILOT_REPORT_GROUND_HEADER: (
            "using PilotReportGroundOwnerSlice = PilotReportGround;",
            "inline constexpr bool kPilotReportGroundOwnedDomainSlice = true;",
            "struct StaticStatusDirective",
            "pilot_report_ground_static_status_directive(",
            "GroundStatusPhase",
            "readiness_ratio",
        ),
    }

    for path, tokens in expected_tokens.items():
        text = _text(path)
        for token in tokens:
            assert token in text, f"{path.relative_to(REPO_ROOT)} is missing {token!r}"


def test_wp22_cross_domain_aggregate_shell_allowlist_stays_closed_and_marked() -> None:
    aggregate_pattern = re.compile(
        r"struct\s+(\w+)\s*:\s*(\w+Core),\s*(\w+Air),\s*(\w+Naval),\s*(\w+Ground)\s*\{\s*\};"
    )
    matches: list[tuple[str, str]] = []

    for path in (REPO_ROOT / "src" / "components").rglob("*.h"):
        text = path.read_text(encoding="utf-8")
        for match in aggregate_pattern.finditer(text):
            matches.append((path.relative_to(REPO_ROOT).as_posix(), match.group(1)))

    assert sorted(matches) == [
        ("src/components/command/mission_command.h", "MissionCommand"),
        ("src/components/tasking/leader_intent.h", "LeaderIntent"),
        ("src/components/tasking/pilot_report.h", "PilotReport"),
        ("src/components/tasking/task_order.h", "TaskOrder"),
    ], "new flat cross-domain aggregate shells must stay on the named WP22 compatibility allowlist"

    assert "kMissionCommandCompatibilityTransportShell" in _text(MISSION_COMMAND_HEADER)
    assert "kTaskOrderCompatibilityTransportShell" in _text(TASK_ORDER_HEADER)
    assert "kLeaderIntentCompatibilityTransportShell" in _text(LEADER_INTENT_HEADER)
    assert "kPilotReportCompatibilityTransportShell" in _text(PILOT_REPORT_HEADER)


def test_wp22_world_batch_assignments_keep_aggregate_dtos_as_named_transport_shells() -> None:
    text = _text(WORLD_BATCH_CONTRACTS_HEADER)

    for token in (
        "using shell_type = MissionCommandCompatibilityTransportShell;",
        "using shell_type = LeaderIntentCompatibilityTransportShell;",
        "using shell_type = PilotReportCompatibilityTransportShell;",
        "static constexpr bool kCompatibilityTransportShell =",
        "world_batch_assignment_compatibility_shell(",
    ):
        assert token in text

    assert "WorldMissionCommandAssignment transports only the MissionCommand compatibility shell." in text
    assert "WorldTaskOrderAssignment" not in text
    assert "WorldTaskOrderCompatibilityAssignment" not in text
    assert "using shell_type = TaskOrderCompatibilityTransportShell;" not in text
    assert "WorldLeaderIntentAssignment transports only the LeaderIntent compatibility shell." in text
    assert "WorldPilotReportAssignment transports only the PilotReport compatibility shell." in text
    for forbidden in (
        "struct WorldMissionCommandAssignment {\n    using contract_type",
        "struct WorldLeaderIntentAssignment {\n    using contract_type",
        "struct WorldPilotReportAssignment {\n    using contract_type",
        "WorldMissionCommandAssignment::kMaintainedBatchTruth",
        "WorldLeaderIntentAssignment::kMaintainedBatchTruth",
        "WorldPilotReportAssignment::kMaintainedBatchTruth",
    ):
        assert forbidden not in text


def test_wp24_command_chain_maintained_contracts_are_slice_based_and_shell_assignments_stay_quarantined() -> None:
    text = _text(WORLD_BATCH_CONTRACTS_HEADER)

    for token in (
        "struct MissionCommandMaintainedBatchContract {",
        "using shared_core_owner_slice = MissionCommandSharedCoreOwnerSlice;",
        "using air_owner_slice = MissionCommandAirOwnerSlice;",
        "using naval_owner_slice = MissionCommandNavalOwnerSlice;",
        "using ground_owner_slice = MissionCommandGroundOwnerSlice;",
        "using shared_core_type = MissionCommandSharedCoreDirective;",
        "using air_recovery_type = MissionCommandAir::RecoveryDirective;",
        "using air_takeoff_type = MissionCommandAir::TakeoffDirective;",
        "using air_formation_type = MissionCommandAir::FormationDirective;",
        "using naval_stationing_type = MissionCommandNaval::StationingDirective;",
        "using naval_embarked_helo_type = MissionCommandNaval::EmbarkedHeloDirective;",
        "using ground_static_task_type = MissionCommandGround::StaticTaskDirective;",
        "MissionCommandMaintainedBatchContract is the controlled MissionCommand maintained batch read/write shape.",
        "mission_command_maintained_batch_contract(",
        "mission_command_compatibility_shell_from_maintained_batch_contract(",
        "struct WorldMissionCommandMaintainedAssignment {",
        "WorldMissionCommandMaintainedAssignment transports only the controlled MissionCommand maintained batch contract.",
        "world_mission_command_maintained_batch_contract(",
        "struct LeaderIntentMaintainedBatchContract {",
        "using shared_core_owner_slice = LeaderIntentCore;",
        "using air_owner_slice = LeaderIntentAirOwnerSlice;",
        "using naval_owner_slice = LeaderIntentNavalOwnerSlice;",
        "using ground_owner_slice = LeaderIntentGroundOwnerSlice;",
        "LeaderIntentMaintainedBatchContract is the controlled LeaderIntent maintained batch read/write shape.",
        "leader_intent_maintained_batch_contract(",
        "leader_intent_compatibility_shell_from_maintained_batch_contract(",
        "struct WorldLeaderIntentMaintainedAssignment {",
        "WorldLeaderIntentMaintainedAssignment transports only the controlled LeaderIntent maintained batch contract.",
        "world_leader_intent_maintained_batch_contract(",
        "struct PilotReportMaintainedBatchContract {",
        "using shared_core_owner_slice = PilotReportCore;",
        "using air_owner_slice = PilotReportAirOwnerSlice;",
        "using naval_owner_slice = PilotReportNavalOwnerSlice;",
        "using ground_owner_slice = PilotReportGroundOwnerSlice;",
        "PilotReportMaintainedBatchContract is the controlled PilotReport maintained batch read/write shape.",
        "pilot_report_maintained_batch_contract(",
        "pilot_report_compatibility_shell_from_maintained_batch_contract(",
        "struct WorldPilotReportMaintainedAssignment {",
        "WorldPilotReportMaintainedAssignment transports only the controlled PilotReport maintained batch contract.",
        "world_pilot_report_maintained_batch_contract(",
    ):
        assert token in text

    for forbidden in (
        "MissionCommandCompatibilityTransportShell mission_command{};",
        "MissionCommandCompatibilityTransportShell command{};",
        "LeaderIntentCompatibilityTransportShell leader_intent{};",
        "LeaderIntentCompatibilityTransportShell intent{};",
        "PilotReportCompatibilityTransportShell pilot_report{};",
        "PilotReportCompatibilityTransportShell report{};",
        "struct MissionCommandMaintainedBatchContract :",
        "struct LeaderIntentMaintainedBatchContract :",
        "struct PilotReportMaintainedBatchContract :",
    ):
        assert forbidden not in text


def test_wp22_task_order_maintained_batch_contract_stays_controlled_and_slice_based() -> None:
    text = _text(WORLD_BATCH_CONTRACTS_HEADER)

    for token in (
        "struct TaskOrderMaintainedBatchContract {",
        "using shared_core_owner_slice = TaskOrderSharedCoreOwnerSlice;",
        "using air_owner_slice = TaskOrderAirOwnerSlice;",
        "using naval_owner_slice = TaskOrderNavalOwnerSlice;",
        "using ground_owner_slice = TaskOrderGroundOwnerSlice;",
        "using shared_core_type = TaskOrderSharedCoreDirective;",
        "using air_tasking_identity_type = TaskOrderAirTaskingIdentityDirective;",
        "using air_stationing_type = TaskOrderAirStationingDirective;",
        "using air_recovery_type = TaskOrderAir::RecoveryDirective;",
        "using air_takeoff_type = TaskOrderAir::TakeoffDirective;",
        "using air_formation_type = TaskOrderAirFormationDirective;",
        "using naval_command_authority_type = TaskOrderNaval::CommandAuthorityDirective;",
        "using naval_stationing_type = TaskOrderNavalStationingDirective;",
        "using ground_static_task_type = TaskOrderGround::StaticTaskDirective;",
        "static constexpr bool kMaintainedBatchTruth = true;",
        "shared_core_type shared_core{};",
        "air_tasking_identity_type air_tasking_identity{};",
        "air_stationing_type air_stationing{};",
        "air_recovery_type air_recovery{};",
        "air_takeoff_type air_takeoff{};",
        "air_formation_type air_formation{};",
        "naval_command_authority_type naval_command_authority{};",
        "naval_stationing_type naval_stationing{};",
        "ground_static_task_type ground_static_task{};",
        "TaskOrderMaintainedBatchContract is the controlled TaskOrder maintained batch read/write shape.",
        "task_order_maintained_batch_contract(",
        ".shared_core = task_order_shared_core_directive(order),",
        ".air_tasking_identity = task_order_air_tasking_identity_directive(order),",
        ".air_stationing = task_order_air_stationing_directive(order),",
        ".air_recovery = task_order_air_recovery_directive(order),",
        ".air_takeoff = task_order_air_takeoff_directive(order),",
        ".air_formation = task_order_air_formation_directive(order),",
        ".naval_command_authority = task_order_naval_command_authority(order),",
        ".naval_stationing = task_order_naval_stationing_directive(order),",
        ".ground_static_task = task_order_ground_static_task_directive(order),",
        "struct WorldTaskOrderMaintainedAssignment {",
        "using contract_type = TaskOrderMaintainedBatchContract;",
        "WorldTaskOrderMaintainedAssignment transports only the controlled TaskOrder maintained batch contract.",
        "world_task_order_maintained_batch_contract(",
        "project_world_task_order_maintained_batch_assignment(",
    ):
        assert token in text

    for forbidden in (
        "struct TaskOrderMaintainedBatchContract :",
        "TaskOrderCompatibilityTransportShell order{};",
        "TaskOrder task_order{};",
        "TaskOrderCompatibilityTransportShell task_order{};",
    ):
        assert forbidden not in text


def test_wp22_maintained_episode_consumers_use_owner_slice_directive_helpers() -> None:
    codec_text = _text(MISSION_COMMAND_CODEC_CPP)
    state_text = _text(EXECUTION_EPISODE_STATE_CPP)

    for token in (
        "mission_command_shared_core_directive(command)",
        "mission_command_air_recovery_directive(command)",
        "mission_command_air_takeoff_directive(command)",
        "mission_command_air_formation_directive(command)",
        "mission_command_naval_stationing_directive(command)",
        "mission_command_naval_embarked_helo_directive(command)",
        "mission_command_ground_static_task_directive(command)",
    ):
        assert token in codec_text

    for token in (
        "mission_command_shared_core_directive(lhs)",
        "mission_command_shared_core_directive(rhs)",
        "mission_command_air_recovery_directive(lhs)",
        "mission_command_air_recovery_directive(rhs)",
        "mission_command_air_takeoff_directive(lhs)",
        "mission_command_air_takeoff_directive(rhs)",
        "mission_command_air_formation_directive(lhs)",
        "mission_command_air_formation_directive(rhs)",
        "mission_command_naval_stationing_directive(lhs)",
        "mission_command_naval_stationing_directive(rhs)",
        "mission_command_naval_embarked_helo_directive(lhs)",
        "mission_command_naval_embarked_helo_directive(rhs)",
        "mission_command_ground_static_task_directive(lhs)",
        "mission_command_ground_static_task_directive(rhs)",
    ):
        assert token in state_text

    codec_body = re.search(
        r"void write_mission_command_fields_to_json\(const MissionCommand& command, nlohmann::json\* mission_json\) \{(?P<body>.*?)\n\}",
        codec_text,
        re.S,
    )
    assert codec_body is not None
    for forbidden in (
        "command.cmd_heading_deg",
        "command.cmd_altitude_m",
        "command.cmd_speed_mps",
        "command.command_code",
        "command.route_ref_id",
        "command.reference_entity_id",
        "command.station_radius_m",
        "command.station_bearing_deg",
        "command.embarked_helo_entity_id",
        "command.launch_helo",
        "command.recover_helo",
        "command.relay_oth_targeting",
        "command.ground_task_mode",
        "command.objective_area_id",
        "command.objective_node_id",
        "command.ground_commander_id",
        "command.tactical_cadence_hz",
        "command.recovery_base_id",
        "command.recovery_runway_id",
        "command.recovery_approach_type",
        "command.takeoff_procedure_id",
        "command.takeoff_clearance_id",
        "command.takeoff_interval_s",
        "command.runway_slot_id",
        "command.formation_id",
        "command.form_offset_x",
        "command.form_offset_y",
        "command.form_offset_z",
        "command.roe_state",
        "command.engagement_authority_holder_id",
        "command.engagement_authority_grantor_id",
        "command.assigned_target_id",
        "command.authorization_to_fire",
        "command.active",
    ):
        assert forbidden not in codec_body.group("body")

    equality_body = re.search(
        r"bool mission_commands_equal\(const MissionCommand& lhs, const MissionCommand& rhs\) \{(?P<body>.*?)\n\}",
        state_text,
        re.S,
    )
    assert equality_body is not None
    for forbidden in (
        "lhs.cmd_heading_deg",
        "rhs.cmd_heading_deg",
        "lhs.cmd_altitude_m",
        "rhs.cmd_altitude_m",
        "lhs.cmd_speed_mps",
        "rhs.cmd_speed_mps",
        "lhs.command_code",
        "rhs.command_code",
        "lhs.route_ref_id",
        "rhs.route_ref_id",
        "lhs.reference_entity_id",
        "rhs.reference_entity_id",
        "lhs.station_radius_m",
        "rhs.station_radius_m",
        "lhs.station_bearing_deg",
        "rhs.station_bearing_deg",
        "lhs.embarked_helo_entity_id",
        "rhs.embarked_helo_entity_id",
        "lhs.launch_helo",
        "rhs.launch_helo",
        "lhs.recover_helo",
        "rhs.recover_helo",
        "lhs.relay_oth_targeting",
        "rhs.relay_oth_targeting",
        "lhs.ground_task_mode",
        "rhs.ground_task_mode",
        "lhs.objective_area_id",
        "rhs.objective_area_id",
        "lhs.objective_node_id",
        "rhs.objective_node_id",
        "lhs.ground_commander_id",
        "rhs.ground_commander_id",
        "lhs.tactical_cadence_hz",
        "rhs.tactical_cadence_hz",
        "lhs.recovery_base_id",
        "rhs.recovery_base_id",
        "lhs.recovery_runway_id",
        "rhs.recovery_runway_id",
        "lhs.recovery_approach_type",
        "rhs.recovery_approach_type",
        "lhs.takeoff_procedure_id",
        "rhs.takeoff_procedure_id",
        "lhs.takeoff_clearance_id",
        "rhs.takeoff_clearance_id",
        "lhs.takeoff_interval_s",
        "rhs.takeoff_interval_s",
        "lhs.runway_slot_id",
        "rhs.runway_slot_id",
        "lhs.formation_id",
        "rhs.formation_id",
        "lhs.form_offset_x",
        "rhs.form_offset_x",
        "lhs.form_offset_y",
        "rhs.form_offset_y",
        "lhs.form_offset_z",
        "rhs.form_offset_z",
        "lhs.roe_state",
        "rhs.roe_state",
        "lhs.engagement_authority_holder_id",
        "rhs.engagement_authority_holder_id",
        "lhs.engagement_authority_grantor_id",
        "rhs.engagement_authority_grantor_id",
        "lhs.assigned_target_id",
        "rhs.assigned_target_id",
        "lhs.authorization_to_fire",
        "rhs.authorization_to_fire",
        "lhs.active",
        "rhs.active",
    ):
        assert forbidden not in equality_body.group("body")


def test_wp22_maintained_naval_consumers_use_owner_slice_directive_helpers() -> None:
    ship_motion_text = _text(SHIP_MOTION_SYSTEM_HEADER)
    embarked_air_ops_text = _text(EMBARKED_AIR_OPS_SYSTEM_HEADER)

    ship_station_body = re.search(
        r"inline bool resolve_ship_station_command\((?P<signature>.*?)\) \{(?P<body>.*?)\n\}",
        ship_motion_text,
        re.S,
    )
    assert ship_station_body is not None
    assert "mission_command_naval_stationing_directive(mission_cmd)" in ship_station_body.group("body")
    for forbidden in (
        "mission_cmd.reference_entity_id",
        "mission_cmd.station_radius_m",
        "mission_cmd.station_bearing_deg",
    ):
        assert forbidden not in ship_station_body.group("body")

    assert "mission_command_naval_embarked_helo_directive(*host_mission)" in embarked_air_ops_text
    for forbidden in (
        "host_mission->embarked_helo_entity_id",
        "host_mission->launch_helo",
        "host_mission->recover_helo",
        "host_mission->relay_oth_targeting",
    ):
        assert forbidden not in embarked_air_ops_text


def test_wp22_dto_domain_shell_guard_helpers_compile_without_changing_transport_shapes() -> None:
    source = textwrap.dedent(
        r"""
        #include <type_traits>
        #include "runtime/contracts/world_batch_contracts.h"

        int main() {
            static_assert(kMissionCommandCompatibilityTransportShell);
            static_assert(kTaskOrderCompatibilityTransportShell);
            static_assert(kLeaderIntentCompatibilityTransportShell);
            static_assert(kPilotReportCompatibilityTransportShell);

            static_assert(kTaskOrderSharedCoreOwnedSurface);
            static_assert(kMissionCommandAirOwnedDomainSlice);
            static_assert(kMissionCommandNavalOwnedDomainSlice);
            static_assert(kMissionCommandGroundOwnedDomainSlice);
            static_assert(kTaskOrderAirOwnedDomainSlice);
            static_assert(kTaskOrderNavalOwnedDomainSlice);
            static_assert(kTaskOrderGroundOwnedDomainSlice);
            static_assert(kLeaderIntentAirOwnedDomainSlice);
            static_assert(kLeaderIntentNavalOwnedDomainSlice);
            static_assert(kLeaderIntentGroundOwnedDomainSlice);
            static_assert(kPilotReportAirOwnedDomainSlice);
            static_assert(kPilotReportNavalOwnedDomainSlice);
            static_assert(kPilotReportGroundOwnedDomainSlice);

            static_assert(std::is_same_v<MissionCommandCompatibilityTransportShell, MissionCommand>);
            static_assert(std::is_same_v<MissionCommandSharedCoreOwnerSlice, MissionCommandCore>);
            static_assert(std::is_same_v<TaskOrderCompatibilityTransportShell, TaskOrder>);
            static_assert(std::is_same_v<TaskOrderSharedCoreOwnerSlice, TaskOrderCore>);
            static_assert(std::is_same_v<TaskOrderSharedCoreDirective, TaskOrderCore>);
            static_assert(std::is_same_v<LeaderIntentCompatibilityTransportShell, LeaderIntent>);
            static_assert(std::is_same_v<PilotReportCompatibilityTransportShell, PilotReport>);

            MissionCommand command{};
            TaskOrder order{};
            LeaderIntent intent{};
            PilotReport report{};

            static_assert(std::is_same_v<
                          decltype(mission_command_shared_core(command)),
                          MissionCommandSharedCoreOwnerSlice&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_shared_core_directive(command)),
                          MissionCommandSharedCoreDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_air_owner_slice(command)),
                          MissionCommandAir&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_naval_owner_slice(command)),
                          MissionCommandNaval&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_ground_owner_slice(command)),
                          MissionCommandGround&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_air_recovery_directive(command)),
                          MissionCommandAir::RecoveryDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_air_takeoff_directive(command)),
                          MissionCommandAir::TakeoffDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_air_formation_directive(command)),
                          MissionCommandAir::FormationDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_naval_stationing_directive(command)),
                          MissionCommandNaval::StationingDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_naval_embarked_helo_directive(command)),
                          MissionCommandNaval::EmbarkedHeloDirective>);
            static_assert(std::is_same_v<
                          decltype(mission_command_ground_static_task_directive(command)),
                          MissionCommandGround::StaticTaskDirective>);

            static_assert(std::is_same_v<
                          decltype(task_order_shared_core(order)),
                          TaskOrderSharedCoreOwnerSlice&>);
            static_assert(std::is_same_v<
                          decltype(task_order_shared_core_directive(order)),
                          TaskOrderSharedCoreDirective>);
            static_assert(std::is_same_v<
                          decltype(task_order_air_owner_slice(order)),
                          TaskOrderAir&>);
            static_assert(std::is_same_v<
                          decltype(task_order_naval_owner_slice(order)),
                          TaskOrderNaval&>);
            static_assert(std::is_same_v<
                          decltype(task_order_ground_owner_slice(order)),
                          TaskOrderGround&>);
            static_assert(std::is_same_v<
                          decltype(task_order_air_recovery_directive(order)),
                          TaskOrderAir::RecoveryDirective>);
            static_assert(std::is_same_v<
                          decltype(task_order_air_takeoff_directive(order)),
                          TaskOrderAir::TakeoffDirective>);
            static_assert(std::is_same_v<
                          decltype(task_order_naval_command_authority(order)),
                          TaskOrderNaval::CommandAuthorityDirective>);
            static_assert(std::is_same_v<
                          decltype(task_order_ground_static_task_directive(order)),
                          TaskOrderGround::StaticTaskDirective>);

            static_assert(std::is_same_v<
                          decltype(leader_intent_shared_core(intent)),
                          LeaderIntentCore&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_air_owner_slice(intent)),
                          LeaderIntentAir&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_naval_owner_slice(intent)),
                          LeaderIntentNaval&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_ground_owner_slice(intent)),
                          LeaderIntentGround&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_air_recovery_directive(intent)),
                          LeaderIntentAir::RecoveryDirective>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_air_takeoff_directive(intent)),
                          LeaderIntentAir::TakeoffDirective>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_air_formation_directive(intent)),
                          LeaderIntentAir::FormationDirective>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_naval_command_authority(intent)),
                          LeaderIntentNaval::CommandAuthorityDirective>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_ground_static_status_directive(intent)),
                          LeaderIntentGround::StaticStatusDirective>);

            static_assert(std::is_same_v<
                          decltype(pilot_report_shared_core(report)),
                          PilotReportCore&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_air_owner_slice(report)),
                          PilotReportAir&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_naval_owner_slice(report)),
                          PilotReportNaval&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_ground_owner_slice(report)),
                          PilotReportGround&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_naval_command_authority(report)),
                          PilotReportNaval::CommandAuthorityDirective>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_ground_static_status_directive(report)),
                          PilotReportGround::StaticStatusDirective>);

            command.recovery_base_id = 11;
            command.recovery_runway_id = 12;
            command.takeoff_procedure_id = TakeoffProcedureType::Interval;
            command.takeoff_clearance_id = TakeoffClearanceState::Rolling;
            command.takeoff_interval_s = 13.5;
            command.runway_slot_id = RunwaySlotPosition::Center;
            command.formation_id = 14;
            command.form_offset_x = 1.25;
            command.form_offset_y = 2.5;
            command.form_offset_z = 3.75;
            command.reference_entity_id = 15;
            command.station_radius_m = 1500.0;
            command.station_bearing_deg = 87.0;
            command.embarked_helo_entity_id = 16;
            command.launch_helo = true;
            command.recover_helo = false;
            command.relay_oth_targeting = true;
            command.ground_task_mode = GroundTaskMode::OccupyStatic;
            command.objective_area_id = 17;
            command.objective_node_id = 18;
            command.ground_commander_id = 19;
            command.tactical_cadence_hz = 1.0;

            order.recovery_base_id = 21;
            order.recovery_runway_id = 22;
            order.recovery_approach_type = RecoveryApproachType::StraightIn;
            order.takeoff_procedure_id = TakeoffProcedureType::Wing;
            order.takeoff_clearance_id = TakeoffClearanceState::HoldShort;
            order.takeoff_interval_s = 23.5;
            order.runway_slot_id = RunwaySlotPosition::Right;
            order.warfare_role_code = 24;
            order.officer_in_tactical_command = 25;
            order.task_id = 26;
            order.service_profile = ServiceProfile::Navy;
            order.task_family = TaskFamily::Escort;
            order.authority_scope = AuthorityScope::Operational;
            order.active = true;
            order.ground_task_mode = GroundTaskMode::SupportStatic;
            order.objective_area_id = 27;
            order.objective_node_id = 28;
            order.ground_commander_id = 29;
            order.tactical_cadence_hz = 1.0;

            intent.recovery_base_id = 31;
            intent.recovery_runway_id = 32;
            intent.recovery_approach_type = RecoveryApproachType::Overhead;
            intent.takeoff_procedure_id = TakeoffProcedureType::SingleShip;
            intent.takeoff_clearance_id = TakeoffClearanceState::LineUpAndWait;
            intent.takeoff_interval_s = 33.5;
            intent.runway_slot_id = RunwaySlotPosition::Left;
            intent.formation_id = 34;
            intent.form_offset_x = 4.25;
            intent.form_offset_y = 5.5;
            intent.form_offset_z = 6.75;
            intent.warfare_role_code = 35;
            intent.officer_in_tactical_command = 36;
            intent.ground_status_phase = GroundStatusPhase::OccupyingStatic;
            intent.ground_task_mode = GroundTaskMode::OccupyStatic;
            intent.objective_area_id = 37;
            intent.objective_node_id = 38;
            intent.ground_commander_id = 39;
            intent.tactical_cadence_hz = 1.0;

            report.warfare_role_code = 41;
            report.officer_in_tactical_command = 42;
            report.ground_status_phase = GroundStatusPhase::SupportingStatic;
            report.ground_task_mode = GroundTaskMode::SupportStatic;
            report.objective_area_id = 43;
            report.objective_node_id = 44;
            report.ground_commander_id = 45;
            report.tactical_cadence_hz = 1.0;
            report.readiness_ratio = 0.75;

            const auto command_recovery = mission_command_air_recovery_directive(command);
            const auto command_takeoff = mission_command_air_takeoff_directive(command);
            const auto command_formation = mission_command_air_formation_directive(command);
            const auto command_core = mission_command_shared_core_directive(command);
            const auto command_stationing = mission_command_naval_stationing_directive(command);
            const auto command_helo = mission_command_naval_embarked_helo_directive(command);
            const auto command_ground = mission_command_ground_static_task_directive(command);

            const auto order_recovery = task_order_air_recovery_directive(order);
            const auto order_takeoff = task_order_air_takeoff_directive(order);
            const auto order_authority = task_order_naval_command_authority(order);
            const auto order_core = task_order_shared_core_directive(order);
            const auto order_ground = task_order_ground_static_task_directive(order);

            const auto intent_recovery = leader_intent_air_recovery_directive(intent);
            const auto intent_takeoff = leader_intent_air_takeoff_directive(intent);
            const auto intent_formation = leader_intent_air_formation_directive(intent);
            const auto intent_authority = leader_intent_naval_command_authority(intent);
            const auto intent_ground = leader_intent_ground_static_status_directive(intent);

            const auto report_authority = pilot_report_naval_command_authority(report);
            const auto report_ground = pilot_report_ground_static_status_directive(report);

            WorldMissionCommandAssignment mission_assignment{};
            WorldMissionCommandMaintainedAssignment maintained_mission_assignment{};
            WorldTaskOrderMaintainedAssignment maintained_task_assignment{};
            WorldLeaderIntentAssignment leader_assignment{};
            WorldLeaderIntentMaintainedAssignment maintained_leader_assignment{};
            WorldPilotReportAssignment pilot_assignment{};
            WorldPilotReportMaintainedAssignment maintained_pilot_assignment{};

            static_assert(WorldMissionCommandAssignment::kCompatibilityTransportShell);
            static_assert(WorldMissionCommandMaintainedAssignment::kMaintainedBatchTruth);
            static_assert(WorldTaskOrderMaintainedAssignment::kMaintainedBatchTruth);
            static_assert(WorldLeaderIntentAssignment::kCompatibilityTransportShell);
            static_assert(WorldLeaderIntentMaintainedAssignment::kMaintainedBatchTruth);
            static_assert(WorldPilotReportAssignment::kCompatibilityTransportShell);
            static_assert(WorldPilotReportMaintainedAssignment::kMaintainedBatchTruth);
            static_assert(MissionCommandMaintainedBatchContract::kMaintainedBatchTruth);
            static_assert(TaskOrderMaintainedBatchContract::kMaintainedBatchTruth);
            static_assert(LeaderIntentMaintainedBatchContract::kMaintainedBatchTruth);
            static_assert(PilotReportMaintainedBatchContract::kMaintainedBatchTruth);

            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(mission_assignment)),
                          MissionCommandCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_mission_command_maintained_batch_contract(maintained_mission_assignment)),
                          MissionCommandMaintainedBatchContract&>);
            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(leader_assignment)),
                          LeaderIntentCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_leader_intent_maintained_batch_contract(maintained_leader_assignment)),
                          LeaderIntentMaintainedBatchContract&>);
            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(pilot_assignment)),
                          PilotReportCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_pilot_report_maintained_batch_contract(maintained_pilot_assignment)),
                          PilotReportMaintainedBatchContract&>);
            static_assert(std::is_same_v<
                          decltype(world_task_order_maintained_batch_contract(maintained_task_assignment)),
                          TaskOrderMaintainedBatchContract&>);

            return (&world_batch_assignment_compatibility_shell(mission_assignment) ==
                        &mission_assignment.command &&
                    &world_mission_command_maintained_batch_contract(maintained_mission_assignment) ==
                        &maintained_mission_assignment.mission_command &&
                    &world_task_order_maintained_batch_contract(maintained_task_assignment) ==
                        &maintained_task_assignment.task_order &&
                    &world_batch_assignment_compatibility_shell(leader_assignment) ==
                        &leader_assignment.intent &&
                    &world_leader_intent_maintained_batch_contract(maintained_leader_assignment) ==
                        &maintained_leader_assignment.leader_intent &&
                    &world_batch_assignment_compatibility_shell(pilot_assignment) ==
                        &pilot_assignment.report &&
                    &world_pilot_report_maintained_batch_contract(maintained_pilot_assignment) ==
                        &maintained_pilot_assignment.pilot_report &&
                    command_core.cmd_heading_deg == command.cmd_heading_deg &&
                    command_core.cmd_altitude_m == command.cmd_altitude_m &&
                    command_core.cmd_speed_mps == command.cmd_speed_mps &&
                    command_core.command_code == command.command_code &&
                    command_core.route_ref_id == command.route_ref_id &&
                    command_recovery.recovery_base_id == command.recovery_base_id &&
                    command_recovery.recovery_runway_id == command.recovery_runway_id &&
                    command_takeoff.takeoff_procedure_id == command.takeoff_procedure_id &&
                    command_takeoff.takeoff_clearance_id == command.takeoff_clearance_id &&
                    command_takeoff.takeoff_interval_s == command.takeoff_interval_s &&
                    command_takeoff.runway_slot_id == command.runway_slot_id &&
                    command_formation.formation_id == command.formation_id &&
                    command_formation.form_offset_x == command.form_offset_x &&
                    command_formation.form_offset_y == command.form_offset_y &&
                    command_formation.form_offset_z == command.form_offset_z &&
                    command_stationing.reference_entity_id == command.reference_entity_id &&
                    command_stationing.station_radius_m == command.station_radius_m &&
                    command_stationing.station_bearing_deg == command.station_bearing_deg &&
                    command_helo.embarked_helo_entity_id == command.embarked_helo_entity_id &&
                    command_helo.launch_helo == command.launch_helo &&
                    command_helo.recover_helo == command.recover_helo &&
                    command_helo.relay_oth_targeting == command.relay_oth_targeting &&
                    command_ground.ground_task_mode == command.ground_task_mode &&
                    command_ground.objective_area_id == command.objective_area_id &&
                    command_ground.objective_node_id == command.objective_node_id &&
                    command_ground.ground_commander_id == command.ground_commander_id &&
                    command_ground.tactical_cadence_hz == command.tactical_cadence_hz &&
                    mission_command_maintained_batch_contract(command)
                            .ground_static_task.objective_area_id ==
                        command.objective_area_id &&
                    command_core.roe_state == command.roe_state &&
                    command_core.engagement_authority_holder_id ==
                        command.engagement_authority_holder_id &&
                    command_core.engagement_authority_grantor_id ==
                        command.engagement_authority_grantor_id &&
                    command_core.assigned_target_id == command.assigned_target_id &&
                    command_core.authorization_to_fire == command.authorization_to_fire &&
                    command_core.active == command.active &&
                    order_recovery.recovery_base_id == order.recovery_base_id &&
                    order_recovery.recovery_runway_id == order.recovery_runway_id &&
                    order_recovery.recovery_approach_type == order.recovery_approach_type &&
                    order_takeoff.takeoff_procedure_id == order.takeoff_procedure_id &&
                    order_takeoff.takeoff_clearance_id == order.takeoff_clearance_id &&
                    order_takeoff.takeoff_interval_s == order.takeoff_interval_s &&
                    order_takeoff.runway_slot_id == order.runway_slot_id &&
                    order_authority.warfare_role_code == order.warfare_role_code &&
                    order_authority.officer_in_tactical_command ==
                        order.officer_in_tactical_command &&
                    order_ground.ground_task_mode == order.ground_task_mode &&
                    order_ground.objective_area_id == order.objective_area_id &&
                    order_ground.objective_node_id == order.objective_node_id &&
                    order_ground.ground_commander_id == order.ground_commander_id &&
                    order_ground.tactical_cadence_hz == order.tactical_cadence_hz &&
                    order_core.task_id == order.task_id &&
                    order_core.service_profile == order.service_profile &&
                    order_core.task_family == order.task_family &&
                    order_core.authority_scope == order.authority_scope &&
                    order_core.active == order.active &&
                    task_order_maintained_batch_contract(order).shared_core.task_id == order.task_id &&
                    task_order_maintained_batch_contract(order).shared_core.service_profile ==
                        order.service_profile &&
                    task_order_maintained_batch_contract(order).shared_core.task_family ==
                        order.task_family &&
                    task_order_maintained_batch_contract(order).shared_core.authority_scope ==
                        order.authority_scope &&
                    task_order_maintained_batch_contract(order).shared_core.active == order.active &&
                    task_order_maintained_batch_contract(order).air_recovery.recovery_base_id ==
                        order.recovery_base_id &&
                    task_order_maintained_batch_contract(order).air_takeoff.takeoff_interval_s ==
                        order.takeoff_interval_s &&
                    task_order_maintained_batch_contract(order).naval_command_authority.warfare_role_code ==
                        order.warfare_role_code &&
                    task_order_maintained_batch_contract(order).ground_static_task.objective_area_id ==
                        order.objective_area_id &&
                    intent_recovery.recovery_base_id == intent.recovery_base_id &&
                    intent_recovery.recovery_runway_id == intent.recovery_runway_id &&
                    intent_recovery.recovery_approach_type == intent.recovery_approach_type &&
                    intent_takeoff.takeoff_procedure_id == intent.takeoff_procedure_id &&
                    intent_takeoff.takeoff_clearance_id == intent.takeoff_clearance_id &&
                    intent_takeoff.takeoff_interval_s == intent.takeoff_interval_s &&
                    intent_takeoff.runway_slot_id == intent.runway_slot_id &&
                    intent_formation.formation_id == intent.formation_id &&
                    intent_formation.form_offset_x == intent.form_offset_x &&
                    intent_formation.form_offset_y == intent.form_offset_y &&
                    intent_formation.form_offset_z == intent.form_offset_z &&
                    intent_authority.warfare_role_code == intent.warfare_role_code &&
                    intent_authority.officer_in_tactical_command ==
                        intent.officer_in_tactical_command &&
                    intent_ground.ground_status_phase == intent.ground_status_phase &&
                    intent_ground.ground_task_mode == intent.ground_task_mode &&
                    intent_ground.objective_area_id == intent.objective_area_id &&
                    intent_ground.objective_node_id == intent.objective_node_id &&
                    intent_ground.ground_commander_id == intent.ground_commander_id &&
                    intent_ground.tactical_cadence_hz == intent.tactical_cadence_hz &&
                    leader_intent_maintained_batch_contract(intent)
                            .ground_static_status.objective_area_id ==
                        intent.objective_area_id &&
                    report_authority.warfare_role_code == report.warfare_role_code &&
                    report_authority.officer_in_tactical_command ==
                        report.officer_in_tactical_command &&
                    report_ground.ground_status_phase == report.ground_status_phase &&
                    report_ground.ground_task_mode == report.ground_task_mode &&
                    report_ground.objective_area_id == report.objective_area_id &&
                    report_ground.objective_node_id == report.objective_node_id &&
                    report_ground.ground_commander_id == report.ground_commander_id &&
                    report_ground.tactical_cadence_hz == report.tactical_cadence_hz &&
                    report_ground.readiness_ratio == report.readiness_ratio &&
                    pilot_report_maintained_batch_contract(report)
                            .ground_static_status.readiness_ratio ==
                        report.readiness_ratio)
                ? 0
                : 1;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_task_order_header_marks_shared_core_as_owner_slice_directive_surface() -> None:
    text = _text(TASK_ORDER_HEADER)

    for token in (
        "using TaskOrderSharedCoreOwnerSlice = TaskOrderCore;",
        "using TaskOrderSharedCoreDirective = TaskOrderCore;",
        "inline constexpr bool kTaskOrderSharedCoreOwnedSurface = true;",
        "task_order_shared_core_directive(",
        "TaskOrder shared core must stay an explicit maintained owner surface.",
    ):
        assert token in text


def test_wp22_python_bindings_expose_owner_slice_types_and_projection_helpers() -> None:
    text = _text(BINDINGS_COMMAND_CPP)

    for token in (
        'nb::class_<TaskOrderCore>(m, "TaskOrderCore")',
        'nb::class_<TaskOrderAir::RecoveryDirective>(m, "TaskOrderAirRecoveryDirective")',
        'nb::class_<TaskOrderAir::TakeoffDirective>(m, "TaskOrderAirTakeoffDirective")',
        'nb::class_<TaskOrderAir>(m, "TaskOrderAir")',
        'nb::class_<TaskOrderNaval::CommandAuthorityDirective>(',
        '"TaskOrderNavalCommandAuthorityDirective"',
        'nb::class_<TaskOrderNaval>(m, "TaskOrderNaval")',
        'nb::class_<TaskOrderGround::StaticTaskDirective>(',
        '"TaskOrderGroundStaticTaskDirective"',
        'nb::class_<TaskOrderGround>(m, "TaskOrderGround")',
        'nb::class_<LeaderIntentCore>(m, "LeaderIntentCore")',
        'nb::class_<LeaderIntentAir>(m, "LeaderIntentAir")',
        'nb::class_<LeaderIntentNaval>(m, "LeaderIntentNaval")',
        'nb::class_<LeaderIntentGround::StaticStatusDirective>(',
        '"LeaderIntentGroundStaticStatusDirective"',
        'nb::class_<LeaderIntentGround>(m, "LeaderIntentGround")',
        'nb::class_<PilotReportCore>(m, "PilotReportCore")',
        'nb::class_<PilotReportAir>(m, "PilotReportAir")',
        'nb::class_<PilotReportNaval>(m, "PilotReportNaval")',
        'nb::class_<PilotReportGround::StaticStatusDirective>(',
        '"PilotReportGroundStaticStatusDirective"',
        'nb::class_<PilotReportGround>(m, "PilotReportGround")',
        'nb::class_<MissionCommandGround::StaticTaskDirective>(',
        '"MissionCommandGroundStaticTaskDirective"',
        'nb::class_<MissionCommandGround>(m, "MissionCommandGround")',
        '"task_order_shared_core"',
        '"task_order_shared_core_directive"',
        '"task_order_air_owner_slice"',
        '"task_order_naval_owner_slice"',
        '"task_order_ground_owner_slice"',
        '"task_order_air_recovery_directive"',
        '"task_order_air_takeoff_directive"',
        '"task_order_naval_command_authority"',
        '"task_order_ground_static_task_directive"',
        '"leader_intent_shared_core"',
        '"leader_intent_air_owner_slice"',
        '"leader_intent_naval_owner_slice"',
        '"leader_intent_ground_owner_slice"',
        '"leader_intent_ground_static_status_directive"',
        '"pilot_report_shared_core"',
        '"pilot_report_air_owner_slice"',
        '"pilot_report_naval_owner_slice"',
        '"pilot_report_ground_owner_slice"',
        '"pilot_report_ground_static_status_directive"',
        '"mission_command_ground_owner_slice"',
        '"mission_command_ground_static_task_directive"',
        "nb::inst_reference(",
    ):
        assert token in text
