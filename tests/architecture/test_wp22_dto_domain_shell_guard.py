from __future__ import annotations

import re
import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MISSION_COMMAND_HEADER = REPO_ROOT / "src" / "components" / "command" / "mission_command.h"
MISSION_COMMAND_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "air" / "mission_command_air.h"
)
MISSION_COMMAND_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "command" / "naval" / "mission_command_naval.h"
)
TASK_ORDER_HEADER = REPO_ROOT / "src" / "components" / "tasking" / "task_order.h"
TASK_ORDER_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "air" / "task_order_air.h"
)
TASK_ORDER_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "naval" / "task_order_naval.h"
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
PILOT_REPORT_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "pilot_report.h"
)
PILOT_REPORT_AIR_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "air" / "pilot_report_air.h"
)
PILOT_REPORT_NAVAL_HEADER = (
    REPO_ROOT / "src" / "components" / "tasking" / "naval" / "pilot_report_naval.h"
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


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = (
        Path(tempfile.gettempdir())
        / f"wp22_dto_domain_shell_guard_{uuid.uuid4().hex}"
    )
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-I",
            str(REPO_ROOT / "src"),
            "-x",
            "c++",
            "-",
            "-o",
            str(binary),
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_wp22_command_and_tasking_headers_name_compatibility_shells_and_owner_slices() -> None:
    mission_text = _text(MISSION_COMMAND_HEADER)
    task_order_text = _text(TASK_ORDER_HEADER)
    leader_text = _text(LEADER_INTENT_HEADER)
    pilot_text = _text(PILOT_REPORT_HEADER)

    for token in (
        "using MissionCommandCompatibilityTransportShell = MissionCommand;",
        "inline constexpr bool kMissionCommandCompatibilityTransportShell = true;",
        "mission_command_shared_core(",
        "mission_command_air_owner_slice(",
        "mission_command_naval_owner_slice(",
        "mission_command_air_recovery_directive(",
        "mission_command_air_takeoff_directive(",
        "mission_command_air_formation_directive(",
        "mission_command_naval_stationing_directive(",
        "mission_command_naval_embarked_helo_directive(",
    ):
        assert token in mission_text

    for token in (
        "using TaskOrderCompatibilityTransportShell = TaskOrder;",
        "inline constexpr bool kTaskOrderCompatibilityTransportShell = true;",
        "task_order_shared_core(",
        "task_order_air_owner_slice(",
        "task_order_naval_owner_slice(",
        "task_order_air_recovery_directive(",
        "task_order_air_takeoff_directive(",
        "task_order_naval_command_authority(",
    ):
        assert token in task_order_text

    for token in (
        "using LeaderIntentCompatibilityTransportShell = LeaderIntent;",
        "inline constexpr bool kLeaderIntentCompatibilityTransportShell = true;",
        "leader_intent_shared_core(",
        "leader_intent_air_owner_slice(",
        "leader_intent_naval_owner_slice(",
        "leader_intent_air_recovery_directive(",
        "leader_intent_air_takeoff_directive(",
        "leader_intent_air_formation_directive(",
        "leader_intent_naval_command_authority(",
    ):
        assert token in leader_text

    for token in (
        "using PilotReportCompatibilityTransportShell = PilotReport;",
        "inline constexpr bool kPilotReportCompatibilityTransportShell = true;",
        "pilot_report_shared_core(",
        "pilot_report_air_owner_slice(",
        "pilot_report_naval_owner_slice(",
        "pilot_report_naval_command_authority(",
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
    }

    for path, tokens in expected_tokens.items():
        text = _text(path)
        for token in tokens:
            assert token in text, f"{path.relative_to(REPO_ROOT)} is missing {token!r}"


def test_wp22_cross_domain_aggregate_shell_allowlist_stays_closed_and_marked() -> None:
    aggregate_pattern = re.compile(
        r"struct\s+(\w+)\s*:\s*(\w+Core),\s*(\w+Air),\s*(\w+Naval)\s*\{\s*\};"
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
        "using shell_type = TaskOrderCompatibilityTransportShell;",
        "using shell_type = LeaderIntentCompatibilityTransportShell;",
        "using shell_type = PilotReportCompatibilityTransportShell;",
        "static constexpr bool kCompatibilityTransportShell =",
        "world_batch_assignment_compatibility_shell(",
    ):
        assert token in text

    assert "WorldMissionCommandAssignment transports only the MissionCommand compatibility shell." in text
    assert "WorldTaskOrderAssignment transports only the TaskOrder compatibility shell." in text
    assert "WorldLeaderIntentAssignment transports only the LeaderIntent compatibility shell." in text
    assert "WorldPilotReportAssignment transports only the PilotReport compatibility shell." in text


def test_wp22_maintained_episode_consumers_use_owner_slice_directive_helpers() -> None:
    codec_text = _text(MISSION_COMMAND_CODEC_CPP)
    state_text = _text(EXECUTION_EPISODE_STATE_CPP)

    for token in (
        "mission_command_air_recovery_directive(command)",
        "mission_command_air_takeoff_directive(command)",
        "mission_command_air_formation_directive(command)",
        "mission_command_naval_stationing_directive(command)",
        "mission_command_naval_embarked_helo_directive(command)",
    ):
        assert token in codec_text

    for token in (
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
    ):
        assert token in state_text

    codec_body = re.search(
        r"void write_mission_command_fields_to_json\(const MissionCommand& command, nlohmann::json\* mission_json\) \{(?P<body>.*?)\n\}",
        codec_text,
        re.S,
    )
    assert codec_body is not None
    for forbidden in (
        "command.reference_entity_id",
        "command.station_radius_m",
        "command.station_bearing_deg",
        "command.embarked_helo_entity_id",
        "command.launch_helo",
        "command.recover_helo",
        "command.relay_oth_targeting",
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
    ):
        assert forbidden not in codec_body.group("body")

    equality_body = re.search(
        r"bool mission_commands_equal\(const MissionCommand& lhs, const MissionCommand& rhs\) \{(?P<body>.*?)\n\}",
        state_text,
        re.S,
    )
    assert equality_body is not None
    for forbidden in (
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

            static_assert(kMissionCommandAirOwnedDomainSlice);
            static_assert(kMissionCommandNavalOwnedDomainSlice);
            static_assert(kTaskOrderAirOwnedDomainSlice);
            static_assert(kTaskOrderNavalOwnedDomainSlice);
            static_assert(kLeaderIntentAirOwnedDomainSlice);
            static_assert(kLeaderIntentNavalOwnedDomainSlice);
            static_assert(kPilotReportAirOwnedDomainSlice);
            static_assert(kPilotReportNavalOwnedDomainSlice);

            static_assert(std::is_same_v<MissionCommandCompatibilityTransportShell, MissionCommand>);
            static_assert(std::is_same_v<TaskOrderCompatibilityTransportShell, TaskOrder>);
            static_assert(std::is_same_v<LeaderIntentCompatibilityTransportShell, LeaderIntent>);
            static_assert(std::is_same_v<PilotReportCompatibilityTransportShell, PilotReport>);

            MissionCommand command{};
            TaskOrder order{};
            LeaderIntent intent{};
            PilotReport report{};

            static_assert(std::is_same_v<
                          decltype(mission_command_shared_core(command)),
                          MissionCommandCore&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_air_owner_slice(command)),
                          MissionCommandAir&>);
            static_assert(std::is_same_v<
                          decltype(mission_command_naval_owner_slice(command)),
                          MissionCommandNaval&>);
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
                          decltype(task_order_shared_core(order)),
                          TaskOrderCore&>);
            static_assert(std::is_same_v<
                          decltype(task_order_air_owner_slice(order)),
                          TaskOrderAir&>);
            static_assert(std::is_same_v<
                          decltype(task_order_naval_owner_slice(order)),
                          TaskOrderNaval&>);
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
                          decltype(leader_intent_shared_core(intent)),
                          LeaderIntentCore&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_air_owner_slice(intent)),
                          LeaderIntentAir&>);
            static_assert(std::is_same_v<
                          decltype(leader_intent_naval_owner_slice(intent)),
                          LeaderIntentNaval&>);
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
                          decltype(pilot_report_shared_core(report)),
                          PilotReportCore&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_air_owner_slice(report)),
                          PilotReportAir&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_naval_owner_slice(report)),
                          PilotReportNaval&>);
            static_assert(std::is_same_v<
                          decltype(pilot_report_naval_command_authority(report)),
                          PilotReportNaval::CommandAuthorityDirective>);

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

            order.recovery_base_id = 21;
            order.recovery_runway_id = 22;
            order.recovery_approach_type = RecoveryApproachType::StraightIn;
            order.takeoff_procedure_id = TakeoffProcedureType::Wing;
            order.takeoff_clearance_id = TakeoffClearanceState::HoldShort;
            order.takeoff_interval_s = 23.5;
            order.runway_slot_id = RunwaySlotPosition::Right;
            order.warfare_role_code = 24;
            order.officer_in_tactical_command = 25;

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

            report.warfare_role_code = 41;
            report.officer_in_tactical_command = 42;

            const auto command_recovery = mission_command_air_recovery_directive(command);
            const auto command_takeoff = mission_command_air_takeoff_directive(command);
            const auto command_formation = mission_command_air_formation_directive(command);
            const auto command_stationing = mission_command_naval_stationing_directive(command);
            const auto command_helo = mission_command_naval_embarked_helo_directive(command);

            const auto order_recovery = task_order_air_recovery_directive(order);
            const auto order_takeoff = task_order_air_takeoff_directive(order);
            const auto order_authority = task_order_naval_command_authority(order);

            const auto intent_recovery = leader_intent_air_recovery_directive(intent);
            const auto intent_takeoff = leader_intent_air_takeoff_directive(intent);
            const auto intent_formation = leader_intent_air_formation_directive(intent);
            const auto intent_authority = leader_intent_naval_command_authority(intent);

            const auto report_authority = pilot_report_naval_command_authority(report);

            WorldMissionCommandAssignment mission_assignment{};
            WorldTaskOrderAssignment task_assignment{};
            WorldLeaderIntentAssignment leader_assignment{};
            WorldPilotReportAssignment pilot_assignment{};

            static_assert(WorldMissionCommandAssignment::kCompatibilityTransportShell);
            static_assert(WorldTaskOrderAssignment::kCompatibilityTransportShell);
            static_assert(WorldLeaderIntentAssignment::kCompatibilityTransportShell);
            static_assert(WorldPilotReportAssignment::kCompatibilityTransportShell);

            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(mission_assignment)),
                          MissionCommandCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(task_assignment)),
                          TaskOrderCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(leader_assignment)),
                          LeaderIntentCompatibilityTransportShell&>);
            static_assert(std::is_same_v<
                          decltype(world_batch_assignment_compatibility_shell(pilot_assignment)),
                          PilotReportCompatibilityTransportShell&>);

            return (&world_batch_assignment_compatibility_shell(mission_assignment) ==
                        &mission_assignment.command &&
                    &world_batch_assignment_compatibility_shell(task_assignment) ==
                        &task_assignment.order &&
                    &world_batch_assignment_compatibility_shell(leader_assignment) ==
                        &leader_assignment.intent &&
                    &world_batch_assignment_compatibility_shell(pilot_assignment) ==
                        &pilot_assignment.report &&
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
                    report_authority.warfare_role_code == report.warfare_role_code &&
                    report_authority.officer_in_tactical_command ==
                        report.officer_in_tactical_command)
                ? 0
                : 1;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
