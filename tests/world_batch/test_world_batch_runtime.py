from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.rl.leader_tasking import infer_route_ref_id  # noqa: E402
from python.scenario_compiler import ScenarioCompiler  # noqa: E402
from python.scenario_compiler import _clone_runtime_mission_command  # noqa: E402
from python.scenario_runtime import (  # noqa: E402
    BatchWorldApplyBuffer,
    build_compiled_world_layout,
    load_compiled_scenario_batch,
    prepare_scenario_world_layout,
)


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _inline_batch_scenario() -> dict:
    return {
        "scenario_name": "phase4_batch_runtime_inline",
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {
                "speed_mps": 6.0,
                "dir_from_deg": 210.0,
                "shear_mps_per_km": 0.5,
            },
            "randomization": {
                "world_yaw_range": [-20.0, 20.0],
                "world_yaw_origin": [0.0, 0.0],
            },
            "zones": [
                {
                    "name": "Runway_A",
                    "x": 0.0,
                    "y": 0.0,
                    "width": 60.0,
                    "length": 2500.0,
                    "heading": 90.0,
                    "surface": "Concrete",
                }
            ],
        },
        "mission_command": {
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        "entities": [
            {
                "name": "Lead",
                "type": "Aircraft",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
                "randomization": {
                    "along_body_m_range": [-100.0, 100.0],
                    "cross_body_m_range": [-50.0, 50.0],
                    "heading_offset_deg_range": [-5.0, 5.0],
                },
            },
            {
                "name": "Wing",
                "type": "Aircraft",
                "side": "Blue",
                "is_agent": False,
                "pos": [-1550.0, -120.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            },
        ],
    }


def _inline_route_scenario() -> dict:
    scenario = _inline_batch_scenario()
    scenario["mission_command"] = {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
        "waypoint_mode": "flyby",
        "waypoints": [
            {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0},
            {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0},
        ],
    }
    return scenario


def _inline_route_template_scenario() -> dict:
    scenario = _inline_batch_scenario()
    scenario["environment"]["randomization"] = {
        "world_yaw_range": [20.0, 20.0],
        "world_yaw_origin": [0.0, 0.0],
        "rotate_mission_heading_with_world": True,
    }
    scenario["mission_command"] = {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
        "waypoint_mode": "flyby",
        "randomization": {
            "waypoint_templates": [
                [
                    {"x": 500.0, "y": 0.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 700.0},
                    {"x": 2000.0, "y": 1000.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 700.0},
                ]
            ]
        },
    }
    return scenario


def _inline_route_generator_scenario() -> dict:
    scenario = _inline_batch_scenario()
    scenario["mission_command"] = {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
        "waypoint_mode": "flyby",
        "randomization": {
            "route_generator": {
                "enabled": True,
                "waypoint_count_range": [3, 3],
                "first_leg_length_m_range": [4000.0, 4000.0],
                "subsequent_leg_length_m_range": [5000.0, 5000.0],
                "waypoint_radius_m_range": [700.0, 700.0],
                "speed_mps_range": [180.0, 180.0],
                "altitude_m_range": [1200.0, 1200.0],
                "turn_angle_deg_range": [20.0, 20.0],
                "min_turn_abs_deg": 5.0,
                "max_turn_abs_deg": 30.0,
            }
        },
    }
    return scenario


class WorldBatchRuntimeTests(unittest.TestCase):
    def test_world_batch_runtime_worker_thread_controls(self) -> None:
        batch = ef_py.WorldBatchRuntime(3)
        self.assertEqual(int(batch.worker_threads()), 1)
        self.assertGreaterEqual(int(batch.effective_worker_threads()), 1)
        self.assertLessEqual(int(batch.effective_worker_threads()), 3)

        batch.set_worker_threads(1)
        self.assertEqual(int(batch.worker_threads()), 1)
        self.assertEqual(int(batch.effective_worker_threads()), 1)

        batch.set_worker_threads(8)
        self.assertEqual(int(batch.worker_threads()), 8)
        self.assertEqual(int(batch.effective_worker_threads()), 3)

    def test_world_batch_runtime_steps_and_reads_observations(self) -> None:
        batch = ef_py.WorldBatchRuntime(2)
        self.assertEqual(int(batch.world_count()), 2)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
        batch.set_time_step(0.05)
        batch.reset_batch([7, 11])

        eid0 = batch.world(0).spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            -1400.0,
            0.0,
            2.1,
            90.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
        eid1 = batch.world(1).spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            -2400.0,
            100.0,
            2.1,
            90.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )

        batch.step_batch()
        refs = [_entity_ref(0, eid0), _entity_ref(1, eid1)]
        obs = batch.get_agent_observations_batch(refs)
        inst = batch.get_instrument_states_batch(refs)

        self.assertEqual(len(obs), 2)
        self.assertEqual(len(inst), 2)
        self.assertEqual(int(obs[0].id), int(eid0))
        self.assertEqual(int(obs[1].id), int(eid1))
        self.assertGreaterEqual(float(obs[0].sim_time), 0.05)
        self.assertGreaterEqual(float(obs[1].sim_time), 0.05)
        self.assertNotEqual(float(obs[0].x), float(obs[1].x))

    def test_world_batch_runtime_applies_world_setup_batch(self) -> None:
        batch = ef_py.WorldBatchRuntime(2)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

        terrain0 = ef_py.WorldTerrainAssignment()
        terrain0.world_index = 0
        terrain0.terrain_type = "flat"
        terrain1 = ef_py.WorldTerrainAssignment()
        terrain1.world_index = 1
        terrain1.terrain_type = "legacy"

        wind0 = ef_py.WorldWindAssignment()
        wind0.world_index = 0
        wind0.speed_mps = 5.0
        wind0.dir_from_deg = 180.0
        wind0.shear_mps_per_km = 0.0
        wind1 = ef_py.WorldWindAssignment()
        wind1.world_index = 1
        wind1.speed_mps = 7.0
        wind1.dir_from_deg = 220.0
        wind1.shear_mps_per_km = 1.0

        zone0 = ef_py.WorldZoneDefinition()
        zone0.world_index = 0
        zone0.name = "Runway_A"
        zone0.x = 0.0
        zone0.y = 0.0
        zone0.width = 60.0
        zone0.length = 2000.0
        zone0.heading = 90.0
        zone0.surface_type = 0
        zone1 = ef_py.WorldZoneDefinition()
        zone1.world_index = 1
        zone1.name = "Runway_B"
        zone1.x = 100.0
        zone1.y = 50.0
        zone1.width = 70.0
        zone1.length = 2100.0
        zone1.heading = 45.0
        zone1.surface_type = 1

        spawn0 = ef_py.WorldSpawnRequest()
        spawn0.world_index = 0
        spawn0.side = ef_py.Side.Blue
        spawn0.type_name = "Aircraft"
        spawn0.entity_name = "Lead0"
        spawn0.is_agent = True
        spawn0.x = -1400.0
        spawn0.y = 0.0
        spawn0.z = 2.1
        spawn0.heading = 90.0
        spawn1 = ef_py.WorldSpawnRequest()
        spawn1.world_index = 1
        spawn1.side = ef_py.Side.Blue
        spawn1.type_name = "Aircraft"
        spawn1.entity_name = "Lead1"
        spawn1.is_agent = True
        spawn1.x = -2400.0
        spawn1.y = 100.0
        spawn1.z = 2.1
        spawn1.heading = 45.0

        entity_ids = batch.apply_world_setup_batch(
            [7, 11],
            [terrain0, terrain1],
            [wind0, wind1],
            [zone0, zone1],
            [spawn0, spawn1],
            [0.05, 0.08],
        )

        self.assertEqual(len(entity_ids), 2)
        refs = [_entity_ref(0, int(entity_ids[0])), _entity_ref(1, int(entity_ids[1]))]
        obs = batch.get_agent_observations_batch(refs)
        self.assertEqual(int(obs[0].id), int(entity_ids[0]))
        self.assertEqual(int(obs[1].id), int(entity_ids[1]))
        self.assertAlmostEqual(float(batch.world(0).get_time_step()), 0.05, places=6)
        self.assertAlmostEqual(float(batch.world(1).get_time_step()), 0.08, places=6)
        self.assertNotEqual(float(obs[0].x), float(obs[1].x))

    def test_world_batch_runtime_command_chain_roundtrip(self) -> None:
        batch = ef_py.WorldBatchRuntime(2)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
        batch.reset_batch([3, 5])

        eid0 = batch.world(0).spawn_unit(ef_py.Side.Blue, "Aircraft", -1400.0, 0.0, 2.1, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        eid1 = batch.world(1).spawn_unit(ef_py.Side.Blue, "Aircraft", -1400.0, 0.0, 2.1, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        batch.world(0).set_command_link(eid0, 0.0, 0.0)
        batch.world(1).set_command_link(eid1, 0.0, 0.0)
        refs = [_entity_ref(0, eid0), _entity_ref(1, eid1)]

        cmd0 = ef_py.MissionCommand()
        cmd0.command_code = 2
        cmd0.cmd_heading_deg = 45.0
        cmd0.cmd_altitude_m = 1200.0
        cmd0.cmd_speed_mps = 180.0
        cmd0.active = True

        cmd1 = ef_py.MissionCommand()
        cmd1.command_code = 4
        cmd1.cmd_heading_deg = 90.0
        cmd1.cmd_altitude_m = 600.0
        cmd1.cmd_speed_mps = 95.0
        cmd1.active = True

        cmd_assign0 = ef_py.WorldMissionCommandAssignment()
        cmd_assign0.world_index = 0
        cmd_assign0.entity_id = int(eid0)
        cmd_assign0.command = cmd0
        cmd_assign1 = ef_py.WorldMissionCommandAssignment()
        cmd_assign1.world_index = 1
        cmd_assign1.entity_id = int(eid1)
        cmd_assign1.command = cmd1
        batch.set_mission_commands_batch([cmd_assign0, cmd_assign1])

        intent0 = ef_py.LeaderIntent()
        intent0.phase_id = ef_py.LeaderPhase.Departure
        intent0.element_phase_id = 11
        intent0.service_profile = ef_py.ServiceProfile.AirForce
        intent0.task_family = ef_py.TaskFamily.Patrol
        intent0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        intent0.tactical_unit_id = 7001
        intent0.task_group_id = 8001
        intent0.role_code = 21
        intent0.coordination_mode = ef_py.CoordinationMode.Follow
        intent0.relative_slot_code = 11
        intent0.recovery_site_id = 91
        intent0.command_code = 2
        intent0.cmd_heading_deg = 45.0
        intent0.formation_mode_id = ef_py.FormationMode.Joining
        intent0.join_required_flag = True
        intent0.wingman_command_mode = ef_py.WingmanCommandMode.HoldSlot
        intent0.active = True
        intent1 = ef_py.LeaderIntent()
        intent1.phase_id = ef_py.LeaderPhase.ApproachArmed
        intent1.element_phase_id = 23
        intent1.service_profile = ef_py.ServiceProfile.AirForce
        intent1.task_family = ef_py.TaskFamily.Recover
        intent1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        intent1.tactical_unit_id = 7001
        intent1.task_group_id = 8001
        intent1.role_code = 22
        intent1.coordination_mode = ef_py.CoordinationMode.Recover
        intent1.relative_slot_code = 12
        intent1.recovery_site_id = 91
        intent1.command_code = 4
        intent1.cmd_heading_deg = 90.0
        intent1.formation_mode_id = ef_py.FormationMode.Recover
        intent1.rejoin_required_flag = True
        intent1.wingman_command_mode = ef_py.WingmanCommandMode.Rejoin
        intent1.active = True
        intent_assign0 = ef_py.WorldLeaderIntentAssignment()
        intent_assign0.world_index = 0
        intent_assign0.entity_id = int(eid0)
        intent_assign0.intent = intent0
        intent_assign1 = ef_py.WorldLeaderIntentAssignment()
        intent_assign1.world_index = 1
        intent_assign1.entity_id = int(eid1)
        intent_assign1.intent = intent1
        batch.set_leader_intents_batch([intent_assign0, intent_assign1])

        order0 = ef_py.TaskOrder()
        order0.task_type = ef_py.TaskType.CAP
        order0.task_id = 101
        order0.service_profile = ef_py.ServiceProfile.AirForce
        order0.task_family = ef_py.TaskFamily.Patrol
        order0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        order0.command_relationship = ef_py.CommandRelationship.TACON
        order0.authority_scope = ef_py.AuthorityScope.Tactical
        order0.parent_node_id = 5001
        order0.task_group_id = 8001
        order0.supported_node_id = 9001
        order0.supporting_node_id = 9002
        order0.role_code = 21
        order0.coordination_mode = ef_py.CoordinationMode.Attached
        order0.relative_slot_code = 11
        order0.assignee_kind = ef_py.AssigneeKind.Element
        order0.recovery_site_id = 91
        order0.element_id = 7001
        order0.lead_aircraft_id = int(eid0)
        order0.formation_template_id = 91
        order0.formation_role_id = ef_py.FormationRole.ElementLead
        order0.active = True
        order1 = ef_py.TaskOrder()
        order1.task_type = ef_py.TaskType.RTB
        order1.task_id = 202
        order1.service_profile = ef_py.ServiceProfile.AirForce
        order1.task_family = ef_py.TaskFamily.Recover
        order1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        order1.command_relationship = ef_py.CommandRelationship.TACON
        order1.authority_scope = ef_py.AuthorityScope.Tactical
        order1.parent_node_id = 5001
        order1.task_group_id = 8001
        order1.role_code = 22
        order1.coordination_mode = ef_py.CoordinationMode.Follow
        order1.relative_slot_code = 12
        order1.assignee_kind = ef_py.AssigneeKind.Element
        order1.recovery_site_id = 91
        order1.element_id = 7001
        order1.lead_aircraft_id = int(eid0)
        order1.formation_template_id = 91
        order1.formation_role_id = ef_py.FormationRole.Wingman
        order1.wingman_slot_id = ef_py.WingmanSlot.Right
        order1.active = True
        order_assign0 = ef_py.WorldTaskOrderAssignment()
        order_assign0.world_index = 0
        order_assign0.entity_id = int(eid0)
        order_assign0.order = order0
        order_assign1 = ef_py.WorldTaskOrderAssignment()
        order_assign1.world_index = 1
        order_assign1.entity_id = int(eid1)
        order_assign1.order = order1
        batch.set_task_orders_batch([order_assign0, order_assign1])

        report0 = ef_py.PilotReport()
        report0.report_type = ef_py.CommMsgType.REP_WILCO
        report0.service_profile = ef_py.ServiceProfile.AirForce
        report0.task_family = ef_py.TaskFamily.Patrol
        report0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        report0.tactical_unit_id = 7001
        report0.task_group_id = 8001
        report0.role_code = 21
        report0.coordination_mode = ef_py.CoordinationMode.Attached
        report0.element_id = 7001
        report0.phase_id = int(ef_py.LeaderPhase.Departure)
        report0.formation_role_id = int(ef_py.FormationRole.ElementLead)
        report0.separation_m = 126.0
        report0.active = True
        report1 = ef_py.PilotReport()
        report1.report_type = ef_py.CommMsgType.REP_JOINED
        report1.service_profile = ef_py.ServiceProfile.AirForce
        report1.task_family = ef_py.TaskFamily.Recover
        report1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
        report1.tactical_unit_id = 7001
        report1.task_group_id = 8001
        report1.role_code = 22
        report1.coordination_mode = ef_py.CoordinationMode.Recover
        report1.element_id = 7001
        report1.phase_id = int(ef_py.LeaderPhase.ApproachArmed)
        report1.formation_role_id = int(ef_py.FormationRole.Wingman)
        report1.formation_error_m = 18.0
        report1.active = True
        report_assign0 = ef_py.WorldPilotReportAssignment()
        report_assign0.world_index = 0
        report_assign0.entity_id = int(eid0)
        report_assign0.report = report0
        report_assign1 = ef_py.WorldPilotReportAssignment()
        report_assign1.world_index = 1
        report_assign1.entity_id = int(eid1)
        report_assign1.report = report1
        batch.set_pilot_reports_batch([report_assign0, report_assign1])

        got_cmds = batch.get_mission_commands_batch(refs)
        got_orders = batch.get_task_orders_batch(refs)
        got_intents = batch.get_leader_intents_batch(refs)
        got_reports = batch.get_pilot_reports_batch(refs)

        self.assertEqual(int(got_cmds[0].command_code), 2)
        self.assertEqual(int(got_cmds[1].command_code), 4)
        self.assertAlmostEqual(float(got_cmds[0].cmd_heading_deg), 45.0, places=6)
        self.assertAlmostEqual(float(got_cmds[1].cmd_speed_mps), 95.0, places=6)
        self.assertEqual(got_orders[0].task_type, ef_py.TaskType.CAP)
        self.assertEqual(got_orders[1].task_type, ef_py.TaskType.RTB)
        self.assertEqual(int(got_orders[0].task_id), 101)
        self.assertEqual(int(got_orders[1].task_id), 202)
        self.assertEqual(got_orders[0].service_profile, ef_py.ServiceProfile.AirForce)
        self.assertEqual(got_orders[0].task_family, ef_py.TaskFamily.Patrol)
        self.assertEqual(got_orders[0].tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(got_orders[0].command_relationship, ef_py.CommandRelationship.TACON)
        self.assertEqual(got_orders[0].authority_scope, ef_py.AuthorityScope.Tactical)
        self.assertEqual(int(got_orders[0].task_group_id), 8001)
        self.assertEqual(int(got_orders[0].role_code), 21)
        self.assertEqual(got_orders[0].coordination_mode, ef_py.CoordinationMode.Attached)
        self.assertEqual(int(got_orders[0].relative_slot_code), 11)
        self.assertEqual(int(got_orders[0].recovery_site_id), 91)
        self.assertEqual(got_orders[0].assignee_kind, ef_py.AssigneeKind.Element)
        self.assertEqual(int(got_orders[0].element_id), 7001)
        self.assertEqual(got_orders[0].formation_role_id, ef_py.FormationRole.ElementLead)
        self.assertEqual(got_orders[1].formation_role_id, ef_py.FormationRole.Wingman)
        self.assertEqual(got_orders[1].wingman_slot_id, ef_py.WingmanSlot.Right)
        self.assertEqual(got_intents[0].phase_id, ef_py.LeaderPhase.Departure)
        self.assertEqual(got_intents[1].phase_id, ef_py.LeaderPhase.ApproachArmed)
        self.assertEqual(got_intents[0].service_profile, ef_py.ServiceProfile.AirForce)
        self.assertEqual(got_intents[0].task_family, ef_py.TaskFamily.Patrol)
        self.assertEqual(got_intents[0].tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(int(got_intents[0].tactical_unit_id), 7001)
        self.assertEqual(int(got_intents[0].task_group_id), 8001)
        self.assertEqual(int(got_intents[0].role_code), 21)
        self.assertEqual(got_intents[0].coordination_mode, ef_py.CoordinationMode.Follow)
        self.assertEqual(int(got_intents[0].relative_slot_code), 11)
        self.assertEqual(int(got_intents[0].recovery_site_id), 91)
        self.assertEqual(int(got_intents[0].element_phase_id), 11)
        self.assertEqual(got_intents[0].formation_mode_id, ef_py.FormationMode.Joining)
        self.assertTrue(bool(got_intents[0].join_required_flag))
        self.assertEqual(got_intents[1].formation_mode_id, ef_py.FormationMode.Recover)
        self.assertTrue(bool(got_intents[1].rejoin_required_flag))
        self.assertEqual(got_reports[0].report_type, ef_py.CommMsgType.REP_WILCO)
        self.assertEqual(got_reports[1].report_type, ef_py.CommMsgType.REP_JOINED)
        self.assertEqual(got_reports[0].service_profile, ef_py.ServiceProfile.AirForce)
        self.assertEqual(got_reports[0].task_family, ef_py.TaskFamily.Patrol)
        self.assertEqual(got_reports[0].tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(int(got_reports[0].tactical_unit_id), 7001)
        self.assertEqual(int(got_reports[0].task_group_id), 8001)
        self.assertEqual(int(got_reports[0].role_code), 21)
        self.assertEqual(got_reports[0].coordination_mode, ef_py.CoordinationMode.Attached)
        self.assertEqual(int(got_reports[0].element_id), 7001)
        self.assertEqual(int(got_reports[1].formation_role_id), int(ef_py.FormationRole.Wingman))
        self.assertAlmostEqual(float(got_reports[1].formation_error_m), 18.0, places=6)


class BatchScenarioRuntimeTests(unittest.TestCase):
    def test_load_compiled_scenario_batch_reuses_apply_buffer(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())
        batch = ef_py.WorldBatchRuntime(2)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
        apply_buffer = BatchWorldApplyBuffer(2)

        worlds_a = load_compiled_scenario_batch(batch, compiled, seeds=[11, 17], apply_buffer=apply_buffer)
        worlds_b = load_compiled_scenario_batch(batch, compiled, seeds=[21, 27], apply_buffer=apply_buffer)

        self.assertEqual(len(worlds_a), 2)
        self.assertEqual(len(worlds_b), 2)
        self.assertEqual(len(apply_buffer.terrain_assignments), 2)
        self.assertEqual(len(apply_buffer.wind_assignments), 2)
        self.assertEqual(len(apply_buffer.zone_defs), 2)
        self.assertEqual(len(apply_buffer.spawn_requests), 4)
        self.assertNotEqual(float(worlds_a[0].layout.world_yaw_deg), float(worlds_b[0].layout.world_yaw_deg))
        self.assertIsNotNone(worlds_b[0].agent_id)
        obs = batch.world(0).get_agent_observation(int(worlds_b[0].agent_id))
        self.assertEqual(int(obs.id), int(worlds_b[0].agent_id))

    def test_load_compiled_scenario_batch_spawns_worlds(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())
        batch = ef_py.WorldBatchRuntime(2)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

        worlds = load_compiled_scenario_batch(batch, compiled, seeds=[11, 17])
        self.assertEqual(len(worlds), 2)
        self.assertIsNotNone(worlds[0].agent_id)
        self.assertIsNotNone(worlds[1].agent_id)
        self.assertIn("Lead", worlds[0].entities)
        self.assertIn("Wing", worlds[1].entities)
        self.assertNotEqual(float(worlds[0].layout.world_yaw_deg), float(worlds[1].layout.world_yaw_deg))

        refs = []
        for world_index, applied in enumerate(worlds):
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(world_index)
            ref.entity_id = int(applied.agent_id)
            refs.append(ref)

        observations = batch.get_agent_observations_batch(refs)
        self.assertEqual(len(observations), 2)
        self.assertNotEqual(float(observations[0].x), float(observations[1].x))

    def test_scenario_loader_and_batch_runtime_share_setup_semantics(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        loader_agent_id = loader.load_compiled_scenario(compiled, seed=23)
        loader_obs = sim.get_agent_observation(int(loader_agent_id))

        batch = ef_py.WorldBatchRuntime(1)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
        worlds = load_compiled_scenario_batch(batch, compiled, seeds=[23])
        self.assertEqual(len(worlds), 1)
        batch_obs = batch.world(0).get_agent_observation(int(worlds[0].agent_id))

        self.assertAlmostEqual(float(loader.world_yaw_deg), float(worlds[0].layout.world_yaw_deg), places=6)
        self.assertAlmostEqual(float(loader_obs.x), float(batch_obs.x), places=6)
        self.assertAlmostEqual(float(loader_obs.y), float(batch_obs.y), places=6)
        self.assertAlmostEqual(float(loader_obs.z), float(batch_obs.z), places=6)
        self.assertEqual(set(loader.entities.keys()), set(worlds[0].entities.keys()))

    def test_route_ref_id_is_cached_after_waypoint_parse(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_route_scenario())

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_compiled_scenario(compiled, seed=31)

        self.assertIsNotNone(agent_id)
        cached_before = loader._cached_route_ref_id
        route_ref_id_1 = infer_route_ref_id(loader)
        route_ref_id_2 = infer_route_ref_id(loader)

        self.assertGreater(int(route_ref_id_1), 0)
        self.assertEqual(int(route_ref_id_1), int(route_ref_id_2))
        if cached_before is not None:
            self.assertEqual(int(cached_before), int(route_ref_id_1))
        self.assertEqual(int(loader._cached_route_ref_id), int(route_ref_id_1))

    def test_compiled_route_metadata_materializes_runtime_waypoint_cache(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_route_scenario())

        self.assertEqual(len(compiled.runtime_metadata.normalized_route_waypoints), 2)
        self.assertGreater(int(compiled.runtime_metadata.mission_command_template.get("route_ref_id", 0)), 0)

        layout = build_compiled_world_layout(compiled, seed=41)
        mission_cmd = layout.scenario_data.get("mission_command", {})
        self.assertIsInstance(mission_cmd.get("_normalized_waypoints"), list)
        self.assertEqual(len(mission_cmd.get("_normalized_waypoints", [])), 2)
        self.assertEqual(
            int(mission_cmd.get("route_ref_id", 0)),
            int(compiled.runtime_metadata.mission_command_template.get("route_ref_id", 0)),
        )

    def test_compiled_layout_template_matches_legacy_layout_build(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())

        layout_compiled = build_compiled_world_layout(compiled, seed=41, use_compiled_template=True)
        legacy_data = compiled.instantiate_runtime()
        legacy_data["mission_command"] = _clone_runtime_mission_command(compiled.runtime_metadata.mission_command_template)
        legacy_layout = prepare_scenario_world_layout(
            legacy_data,
            seed=41,
            rng=np.random.RandomState(41),
            compiled_template=None,
        )

        self.assertAlmostEqual(float(layout_compiled.world_yaw_deg), float(legacy_layout.world_yaw_deg), places=6)
        self.assertEqual(len(layout_compiled.zones), len(legacy_layout.zones))
        self.assertEqual(len(layout_compiled.spawns), len(legacy_layout.spawns))
        self.assertAlmostEqual(float(layout_compiled.wind_speed_mps), float(legacy_layout.wind_speed_mps), places=6)
        self.assertAlmostEqual(float(layout_compiled.wind_dir_from_deg), float(legacy_layout.wind_dir_from_deg), places=6)
        self.assertAlmostEqual(float(layout_compiled.spawns[0].x), float(legacy_layout.spawns[0].x), places=6)
        self.assertAlmostEqual(float(layout_compiled.spawns[0].y), float(legacy_layout.spawns[0].y), places=6)
        self.assertAlmostEqual(float(layout_compiled.spawns[0].heading), float(legacy_layout.spawns[0].heading), places=6)

    def test_batch_loaded_route_template_preserves_rotated_waypoint_cache(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_route_template_scenario())
        batch = ef_py.WorldBatchRuntime(1)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

        worlds = load_compiled_scenario_batch(batch, compiled, seeds=[41])
        loader = ScenarioLoader(batch.world(0))
        loader._compiled_scenario = compiled
        loader._compiled_runtime_metadata = compiled.runtime_metadata
        loader.load_prepared_world(worlds[0], seed=41, sync_to_kernel=False)

        cached = loader.mission_cmd.get("_normalized_waypoints", None)
        self.assertTrue(bool(loader.mission_cmd.get("_runtime_waypoint_cache_valid", False)))
        self.assertIsInstance(cached, list)
        self.assertEqual(len(cached), 2)
        self.assertGreater(int(loader.mission_cmd.get("route_ref_id", 0)), 0)
        self.assertEqual(
            int(loader.mission_cmd.get("route_ref_id", 0)),
            int(compiled.runtime_metadata.waypoint_template_route_ref_ids[0]),
        )
        self.assertAlmostEqual(float(cached[0]["x"]), float(loader.mission_cmd["waypoints"][0]["x"]), places=6)
        self.assertAlmostEqual(float(cached[0]["y"]), float(loader.mission_cmd["waypoints"][0]["y"]), places=6)

    def test_batch_loaded_route_generator_uses_runtime_agent_spawn_context(self) -> None:
        compiled = ScenarioCompiler.compile_data(_inline_route_generator_scenario())
        batch = ef_py.WorldBatchRuntime(1)
        self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

        worlds = load_compiled_scenario_batch(batch, compiled, seeds=[53])
        loader = ScenarioLoader(batch.world(0))
        loader._compiled_scenario = compiled
        loader._compiled_runtime_metadata = compiled.runtime_metadata
        loader.load_prepared_world(worlds[0], seed=53, sync_to_kernel=False)

        self.assertEqual(len(loader.waypoints), 3)
        self.assertTrue(bool(loader.mission_cmd.get("_route_generator_used", False)))
        self.assertGreater(int(loader.mission_cmd.get("route_ref_id", 0)), 0)
        self.assertNotIn("entities", worlds[0].layout.scenario_data)
        self.assertIn("_runtime_agent_spawn", worlds[0].layout.scenario_data)


if __name__ == "__main__":
    unittest.main()
