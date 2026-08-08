from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GROUND_TASKING_DIR = REPO_ROOT / "src" / "components" / "domains" / "ground" / "tasking"
TASK_ORDER = REPO_ROOT / "src" / "components" / "tasking" / "task_order.h"
LEADER_INTENT = REPO_ROOT / "src" / "components" / "tasking" / "leader_intent.h"
PILOT_REPORT = REPO_ROOT / "src" / "components" / "tasking" / "pilot_report.h"
COMPONENTS_README = REPO_ROOT / "src" / "components" / "README.md"
TASKING_README = REPO_ROOT / "src" / "components" / "tasking" / "README.md"
GROUND_PROGRESS = (
  REPO_ROOT
  / "docs"
  / "task"
  / "ground"
  / "archive"
  / "owner_migration_20260808"
  / "ground_current_progress_20260524.md"
)
NATIVE_STATIC_SCENARIO = REPO_ROOT / "scenarios" / "ground" / "ground_platoon_native_static_occupy_v1.json"


def _text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_ground_tasking_component_subdomain_exists_as_formal_boundary() -> None:
  expected = {
    "README.md",
    "README.zh.md",
    "ground_tasking_enums.h",
    "task_order_ground.h",
    "leader_intent_ground.h",
    "pilot_report_ground.h",
  }
  present = {path.name for path in GROUND_TASKING_DIR.iterdir() if path.is_file()}

  assert expected.issubset(present)
  assert "ground/" in _text(COMPONENTS_README)
  assert "ground/" in _text(TASKING_README)


def test_ground_tasking_headers_declare_narrow_g0_g1_owner_slices() -> None:
  enum_text = _text(GROUND_TASKING_DIR / "ground_tasking_enums.h")
  task_text = _text(GROUND_TASKING_DIR / "task_order_ground.h")
  intent_text = _text(GROUND_TASKING_DIR / "leader_intent_ground.h")
  report_text = _text(GROUND_TASKING_DIR / "pilot_report_ground.h")
  headers = [enum_text, task_text, intent_text, report_text]

  assert "enum class GroundTaskMode" in enum_text
  assert "MoveStatic = 1" in enum_text
  assert "HoldStatic" not in enum_text
  assert "OccupyStatic = 2" in enum_text
  assert "SupportStatic = 3" in enum_text
  assert "enum class GroundStatusPhase" in enum_text
  assert "Assigned = 1" in enum_text
  assert "Preparing = 2" in enum_text
  assert "HoldingStatic = 3" in enum_text
  assert "OccupyingStatic = 4" in enum_text
  assert "SupportingStatic = 5" in enum_text
  assert "Complete = 6" in enum_text

  for text, owner, directive, required_fields in (
    (
      task_text,
      "TaskOrderGround",
      "StaticTaskDirective",
      (
        "ground_task_mode",
        "objective_area_id",
        "objective_node_id",
        "ground_commander_id",
        "tactical_cadence_hz",
      ),
    ),
    (
      intent_text,
      "LeaderIntentGround",
      "StaticStatusDirective",
      (
        "ground_status_phase",
        "ground_task_mode",
        "objective_area_id",
        "objective_node_id",
        "ground_commander_id",
        "tactical_cadence_hz",
      ),
    ),
    (
      report_text,
      "PilotReportGround",
      "StaticStatusDirective",
      (
        "ground_status_phase",
        "ground_task_mode",
        "objective_area_id",
        "objective_node_id",
        "ground_commander_id",
        "tactical_cadence_hz",
        "readiness_ratio",
      ),
    ),
  ):
    assert f"struct {owner}" in text
    assert f"using {owner}OwnerSlice = {owner};" in text
    assert f"k{owner}OwnedDomainSlice = true" in text
    assert directive in text
    for field in required_fields:
      assert field in text

  for text in headers:
    for forbidden in (
      "MissionCommand",
      "PilotAction",
      "CommandPacket",
      "ObservationPacket",
      "TrackPacket",
      "components/command",
      "core/mission",
      "runtime/facade",
      "interfaces/python",
      "systems/",
    ):
      assert forbidden not in text


def test_tasking_compatibility_shells_project_ground_owner_slice() -> None:
  task_text = _text(TASK_ORDER)
  intent_text = _text(LEADER_INTENT)
  report_text = _text(PILOT_REPORT)

  assert '#include "components/domains/ground/tasking/task_order_ground.h"' in task_text
  assert "struct TaskOrder : TaskOrderCore, TaskOrderAir, TaskOrderNaval, TaskOrderGround" in task_text
  assert "kTaskOrderGroundOwnedDomainSlice" in task_text
  assert "task_order_ground_owner_slice(" in task_text
  assert "TaskOrderGround::StaticTaskDirective" in task_text
  assert "task_order_ground_static_task_directive(" in task_text

  assert '#include "components/domains/ground/tasking/leader_intent_ground.h"' in intent_text
  assert (
    "struct LeaderIntent : LeaderIntentCore, LeaderIntentAir, LeaderIntentNaval, LeaderIntentGround"
    in intent_text
  )
  assert "kLeaderIntentGroundOwnedDomainSlice" in intent_text
  assert "leader_intent_ground_owner_slice(" in intent_text
  assert "leader_intent_ground_static_status_directive(" in intent_text

  assert '#include "components/domains/ground/tasking/pilot_report_ground.h"' in report_text
  assert "struct PilotReport : PilotReportCore, PilotReportAir, PilotReportNaval, PilotReportGround" in report_text
  assert "kPilotReportGroundOwnedDomainSlice" in report_text
  assert "pilot_report_ground_owner_slice(" in report_text
  assert "pilot_report_ground_static_status_directive(" in report_text


def test_ground_tasking_boundary_docs_keep_packet_and_runtime_surfaces_held() -> None:
  readme = _text(GROUND_TASKING_DIR / "README.md")
  tasking_readme = _text(TASKING_README)
  progress = _text(GROUND_PROGRESS)
  scenario = _text(NATIVE_STATIC_SCENARIO)
  boundary_docs = "\n".join((readme, tasking_readme, progress, scenario))

  for required in (
    "maintained C++ owner-slice home",
    "G0/G1 static task and status infrastructure only",
    "without releasing G2 movement",
    "Route movement, terrain passability, sensing, fires, damage",
  ):
    assert required in readme

  for held_surface in (
    "MissionCommand",
    "PilotAction",
    "CommandPacket",
    "ObservationPacket",
    "TrackPacket",
    "route following",
    "terrain passability",
    "combat runtime",
  ):
    assert held_surface in boundary_docs

  assert "src/components/domains/ground/tasking/" in progress
  assert "task/status owner slices" in progress
