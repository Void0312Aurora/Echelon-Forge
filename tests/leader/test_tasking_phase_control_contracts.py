from __future__ import annotations

from contextlib import contextmanager
import unittest
from types import SimpleNamespace
from unittest import mock

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.rl.tasking.leader_tasking import RuleBasedLeaderPhaseManager, ScriptedC2TaskManager
from python.rl.tasking import leader_tasking as _leader_tasking_module


_FAKE_COMM = SimpleNamespace(REP_WILCO=1, REP_ON_STATION=2, REP_RTB=20, WARN_BINGO=21, REP_UNABLE=22)
setattr(_FAKE_COMM, "None", 0)


class _FakeLeaderIntent:
  def __init__(self):
    self.active = False
    self.phase_id = 0
    self.command_code = 0
    self.route_ref_id = 0
    self.recovery_base_id = 0
    self.recovery_runway_id = 0
    self.recovery_approach_type = 0
    self.cmd_heading_deg = 0.0
    self.cmd_altitude_m = 0.0
    self.cmd_speed_mps = 0.0
    self.approach_armed = False
    self.commit_to_land = False
    self.abort_flag = False


class _FakePilotReport:
  def __init__(self):
    self.active = False
    self.report_type = 0
    self.sender_id = 0
    self.task_id = 0
    self.phase_id = 0
    self.timestamp_s = 0.0
    self.location_x_m = 0.0
    self.location_y_m = 0.0
    self.location_z_m = 0.0


_FAKE_EF = SimpleNamespace(
  TaskType=SimpleNamespace(Idle=0, Scramble=1, CAP=2, CAPMission=3, RTB=4, RecoverLand=5),
  StationType=SimpleNamespace(Orbit=10, Racetrack=11, RouteCAP=12),
  CommMsgType=_FAKE_COMM,
  LeaderPhase=SimpleNamespace(
    Idle=0,
    Scramble=1,
    Takeoff=2,
    Departure=3,
    TransitToStation=4,
    EstablishCAP=5,
    OnStation=6,
    Reposition=7,
    RTB=8,
    ApproachArmed=9,
    LandingFinal=10,
    Rollout=11,
    Abort=12,
  ),
  RecoveryApproachType=SimpleNamespace(ILS=2),
  LeaderIntent=_FakeLeaderIntent,
  PilotReport=_FakePilotReport,
)


@contextmanager
def _patched_tasking_ef():
  with mock.patch.object(_leader_tasking_module, "ef_py", _FAKE_EF):
    yield


def _make_base_task_order():
  return SimpleNamespace(
    active=True,
    task_id=1,
    priority=1,
    issuer_id=900,
    assignee_id=17,
    task_type=0,
    target_altitude_m=1900.0,
    target_speed_mps=210.0,
    altitude_block_min_m=1400.0,
    altitude_block_max_m=2400.0,
    speed_min_mps=170.0,
    speed_max_mps=250.0,
    anchor_x_m=25000.0,
    anchor_y_m=16000.0,
    anchor_z_m=1900.0,
    station_type=_FAKE_EF.StationType.Racetrack,
    station_radius_m=15000.0,
    station_leg_length_m=28000.0,
    station_heading_deg=40.0,
    on_station_time_s=240.0,
    issue_time_s=0.0,
  )


def _make_loader(
  *,
  scenario_task_order: dict,
  mission_cmd: dict,
  waypoints: list[dict] | None = None,
  waypoint_idx: int = 0,
  post_waypoint_transition: dict | None = None,
  pilot_report: object | None = None,
):
  return SimpleNamespace(
    agent_id=17,
    scenario_data={"task_order": dict(scenario_task_order)},
    mission_cmd=dict(mission_cmd),
    post_waypoint_transition=post_waypoint_transition,
    waypoints=list(waypoints or []),
    waypoint_idx=int(waypoint_idx),
    task_order=_make_base_task_order(),
    pilot_report=pilot_report,
  )


def _make_recovery_loader(
  *,
  ils_obs: list[float],
  runway_frame: tuple[bool, float, float, float, float],
  runway_heading_deg: float | None,
  c2_logic: dict | None = None,
):
  return SimpleNamespace(
    agent_id=17,
    scenario_data={"c2_logic": dict(c2_logic or {})},
    get_ils_observation=lambda x_m, y_m, alt_m: list(ils_obs),
    get_runway_local_frame=lambda x_m, y_m: tuple(runway_frame),
    _nearest_ils_beacon=(
      (lambda x_m, y_m: None)
      if runway_heading_deg is None
      else (lambda x_m, y_m: {"heading": float(runway_heading_deg)})
    ),
  )


def _make_phase_loader(
  *,
  c2_task_name: str,
  ils_obs: list[float],
  runway_frame: tuple[bool, float, float, float, float],
  runway_heading_deg: float,
):
  return SimpleNamespace(
    agent_id=17,
    sim=SimpleNamespace(
      get_agent_observation=lambda agent_id: SimpleNamespace(x=-9200.0, y=50.0, heading=104.0),
      get_instrument_state=lambda agent_id: SimpleNamespace(
        alt_radar=900.0,
        alt_baro=900.0,
        ground_speed=84.0,
        heading=104.0,
      ),
    ),
    mission_cmd={
      "command_code": 3,
      "target_heading": 90.0,
      "target_altitude": 420.0,
      "target_speed": 84.0,
    },
    post_waypoint_transition={
      "phase_name": "landing_ils",
      "command_code": 4,
      "target_heading": 90.0,
      "target_altitude": 0.0,
      "target_speed": 82.0,
    },
    waypoints=[
      {"x": -12000.0, "y": 0.0},
      {"x": -8200.0, "y": 0.0},
    ],
    waypoint_idx=0,
    task_order=_make_base_task_order(),
    c2_task_name=str(c2_task_name),
    get_ils_observation=lambda x_m, y_m, alt_m: list(ils_obs),
    get_runway_local_frame=lambda x_m, y_m: tuple(runway_frame),
    _nearest_ils_beacon=lambda x_m, y_m: {"heading": float(runway_heading_deg)},
  )


class TaskingPhaseControlTests(unittest.TestCase):
  def test_task_only_scramble_preserves_randomized_task_center(self):
    loader = _make_loader(
      scenario_task_order={
        "task_id": 7713,
        "task_type": "CAP",
        "anchor_x_m": 26521.3,
        "anchor_y_m": -22253.3,
        "anchor_z_m": 2430.2,
        "station_type": "Racetrack",
        "station_radius_m": 12879.1,
        "station_leg_length_m": 26997.9,
        "station_heading_deg": 243.8,
        "target_altitude_m": 2430.2,
        "altitude_block_min_m": 1945.3,
        "altitude_block_max_m": 2915.1,
        "target_speed_mps": 211.9,
        "speed_min_mps": 180.5,
        "speed_max_mps": 243.3,
        "on_station_time_s": 324.7,
      },
      mission_cmd={
        "command_code": 2,
        "target_heading": 58.0,
        "target_altitude": 1900.0,
        "target_speed": 210.0,
      },
    )

    manager = ScriptedC2TaskManager()
    with _patched_tasking_ef():
      manager._retask_order(loader, task_name=manager.TASK_SCRAMBLE, sim_time_s=0.0)

    task = loader.task_order
    self.assertAlmostEqual(float(task.target_altitude_m), 2430.2, places=3)
    self.assertAlmostEqual(float(task.target_speed_mps), 211.9, places=3)
    self.assertAlmostEqual(float(task.altitude_block_min_m), 1945.3, places=3)
    self.assertAlmostEqual(float(task.altitude_block_max_m), 2915.1, places=3)
    self.assertAlmostEqual(float(task.speed_min_mps), 180.5, places=3)
    self.assertAlmostEqual(float(task.speed_max_mps), 243.3, places=3)

  def test_route_driven_cap_recenters_block_on_active_waypoint(self):
    loader = _make_loader(
      scenario_task_order={
        "task_id": 7101,
        "task_type": "CAP",
        "anchor_x_m": 28000.0,
        "anchor_y_m": 14000.0,
        "anchor_z_m": 2100.0,
        "station_type": "Racetrack",
        "station_radius_m": 14500.0,
        "station_leg_length_m": 32000.0,
        "station_heading_deg": 35.0,
        "target_altitude_m": 2100.0,
        "altitude_block_min_m": 1650.0,
        "altitude_block_max_m": 2650.0,
        "target_speed_mps": 228.0,
        "speed_min_mps": 190.0,
        "speed_max_mps": 245.0,
        "on_station_time_s": 900.0,
      },
      mission_cmd={
        "command_code": 3,
        "target_heading": 72.0,
        "target_altitude": 2150.0,
        "target_speed": 235.0,
      },
      waypoints=[
        {"x": 20000.0, "y": 4000.0, "altitude_m": 1650.0, "speed_mps": 188.0, "radius_m": 1500.0, "waypoint_mode": "flyby"},
        {"x": 33000.0, "y": 15000.0, "altitude_m": 2550.0, "speed_mps": 225.0, "radius_m": 1750.0, "waypoint_mode": "flyby"},
      ],
      waypoint_idx=0,
    )

    manager = ScriptedC2TaskManager()
    with _patched_tasking_ef():
      manager._retask_order(loader, task_name=manager.TASK_CAP, sim_time_s=0.0)

    task = loader.task_order
    self.assertAlmostEqual(float(task.target_altitude_m), 1650.0, places=3)
    self.assertAlmostEqual(float(task.altitude_block_min_m), 1200.0, places=3)
    self.assertAlmostEqual(float(task.altitude_block_max_m), 2200.0, places=3)
    self.assertAlmostEqual(float(task.target_speed_mps), 188.0, places=3)
    self.assertAlmostEqual(float(task.speed_min_mps), 150.0, places=3)
    self.assertAlmostEqual(float(task.speed_max_mps), 205.0, places=3)

  def test_recovery_ready_rejects_preterminal_runway_geometry(self):
    loader = _make_recovery_loader(
      ils_obs=[1.0, 0.18, 0.22, 9500.0],
      runway_frame=(True, -1500.0, 250.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    truth = SimpleNamespace(x=-9800.0, y=100.0)
    inst = SimpleNamespace(alt_radar=900.0, heading=90.0)

    manager = ScriptedC2TaskManager()
    self.assertFalse(manager._recovery_ready(loader, truth=truth, inst=inst))

  def test_recovery_ready_accepts_terminal_feasible_geometry(self):
    loader = _make_recovery_loader(
      ils_obs=[1.0, 0.18, 0.22, 9500.0],
      runway_frame=(True, -600.0, 900.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    truth = SimpleNamespace(x=-9200.0, y=50.0)
    inst = SimpleNamespace(alt_radar=900.0, heading=104.0)

    manager = ScriptedC2TaskManager()
    self.assertTrue(manager._recovery_ready(loader, truth=truth, inst=inst))

  def test_rtb_route_exhaustion_transitions_to_recover_land(self):
    loader = _make_loader(
      scenario_task_order={
        "task_id": 7102,
        "task_type": "RTB",
        "target_altitude_m": 420.0,
        "altitude_block_min_m": 0.0,
        "altitude_block_max_m": 770.0,
        "target_speed_mps": 84.0,
        "speed_min_mps": 64.0,
        "speed_max_mps": 104.0,
      },
      mission_cmd={
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 420.0,
        "target_speed": 84.0,
      },
      waypoints=[{"x": -8200.0, "y": 0.0, "altitude_m": 420.0, "speed_mps": 84.0}],
      waypoint_idx=1,
      post_waypoint_transition={
        "phase_name": "landing_ils",
        "command_code": 4,
        "target_heading": 90.0,
        "target_altitude": 0.0,
        "target_speed": 82.0,
      },
      pilot_report=SimpleNamespace(active=True, report_type=_FAKE_EF.CommMsgType.REP_RTB),
    )
    truth = SimpleNamespace(x=-8200.0, y=0.0)
    inst = SimpleNamespace(alt_radar=450.0, ground_speed=84.0, heading=90.0)

    manager = ScriptedC2TaskManager()
    manager.current_task_name = manager.TASK_RTB
    with _patched_tasking_ef():
      state = manager.update(loader, sim_time_s=42.0, truth=truth, inst=inst)

    self.assertEqual(manager.TASK_RECOVER_LAND, manager.current_task_name)
    self.assertTrue(bool(state["transitioned"]))
    self.assertEqual("route_exhausted_recovery_final", state["transition_reason"])

  def test_phase_manager_blocks_landing_until_recover_land_and_terminal_geometry(self):
    manager = RuleBasedLeaderPhaseManager(terminal_waypoint_count=2)

    loader_rtb = _make_phase_loader(
      c2_task_name=ScriptedC2TaskManager.TASK_RTB,
      ils_obs=[1.0, 0.18, 0.22, 9500.0],
      runway_frame=(True, -600.0, 900.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    truth = loader_rtb.sim.get_agent_observation(loader_rtb.agent_id)
    inst = loader_rtb.sim.get_instrument_state(loader_rtb.agent_id)
    self.assertFalse(
      manager._should_arm_approach(
        loader=loader_rtb,
        truth=truth,
        alt_agl_m=float(inst.alt_radar),
        heading_deg=float(inst.heading),
        ils_valid=True,
        loc_abs=0.18,
        gs_abs=0.22,
        dme_m=9500.0,
        remaining_waypoints=2,
      )
    )

    loader_recover_preterminal = _make_phase_loader(
      c2_task_name=ScriptedC2TaskManager.TASK_RECOVER_LAND,
      ils_obs=[1.0, 0.18, 0.22, 9500.0],
      runway_frame=(True, -1500.0, 250.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    self.assertFalse(
      manager._should_arm_approach(
        loader=loader_recover_preterminal,
        truth=truth,
        alt_agl_m=float(inst.alt_radar),
        heading_deg=float(inst.heading),
        ils_valid=True,
        loc_abs=0.18,
        gs_abs=0.22,
        dme_m=9500.0,
        remaining_waypoints=2,
      )
    )

    loader_recover_terminal = _make_phase_loader(
      c2_task_name=ScriptedC2TaskManager.TASK_RECOVER_LAND,
      ils_obs=[1.0, 0.18, 0.22, 9500.0],
      runway_frame=(True, -600.0, 900.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    self.assertTrue(
      manager._should_arm_approach(
        loader=loader_recover_terminal,
        truth=truth,
        alt_agl_m=float(inst.alt_radar),
        heading_deg=float(inst.heading),
        ils_valid=True,
        loc_abs=0.18,
        gs_abs=0.22,
        dme_m=9500.0,
        remaining_waypoints=2,
      )
    )

    self.assertTrue(
      manager._should_arm_approach(
        loader=loader_recover_preterminal,
        truth=truth,
        alt_agl_m=float(inst.alt_radar),
        heading_deg=float(inst.heading),
        ils_valid=True,
        loc_abs=0.18,
        gs_abs=0.22,
        dme_m=9500.0,
        remaining_waypoints=0,
      )
    )

  def test_phase_manager_preserves_route_command_but_clears_route_ref_after_exhaustion(self):
    manager = RuleBasedLeaderPhaseManager(terminal_waypoint_count=2)
    loader = _make_phase_loader(
      c2_task_name=ScriptedC2TaskManager.TASK_RECOVER_LAND,
      ils_obs=[1.0, 0.18, 0.22, 6544.0],
      runway_frame=(True, -8039.0, -109.0, 3000.0, 45.0),
      runway_heading_deg=90.0,
    )
    loader.waypoint_idx = len(loader.waypoints)
    loader.mission_cmd["target_heading"] = 225.0
    truth = loader.sim.get_agent_observation(loader.agent_id)
    inst = loader.sim.get_instrument_state(loader.agent_id)

    with _patched_tasking_ef():
      manager.update(loader, sim_time_s=42.0, truth=truth, inst=inst, sync_to_kernel=False)

    self.assertEqual(3, int(loader.leader_intent.command_code))
    self.assertEqual(0, int(loader.leader_intent.route_ref_id))
    self.assertAlmostEqual(225.0, float(loader.leader_intent.cmd_heading_deg), places=3)
    self.assertEqual("rtb", str(loader.mission_phase_name))


if __name__ == "__main__":
  unittest.main()
