from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import build_universal_observation  # noqa: E402
from python.mission_obs_taxonomy import (  # noqa: E402
    mission_observation_dim,
    mission_observation_field_index,
)


_DB_PATH = resolve_repo_path("examples", "config", "database")
_STAGE1_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
)


def _wait_for_assigned_target_track(
    sim: ef_py.SimulationKernel,
    shooter_id: int,
    target_id: int,
    *,
    max_steps: int = 160,
) -> object:
    for _ in range(max_steps):
        sim.step()
        truth = sim.get_agent_observation(shooter_id)
        for track in getattr(truth, "contacts", []) or []:
            if int(getattr(track, "id", 0) or 0) == int(target_id):
                return truth
    raise AssertionError("expected assigned target track before A3 observation check")


class AirCombatC2RoeMissionObservationTests(unittest.TestCase):
    def test_air_combat_c2_roe_v1_exposes_command_and_release_discipline_fields(self) -> None:
        mode = "air_combat_c2_roe_v1"
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260603))
        target_id = int(loader.primary_target_id or 0)
        self.assertGreater(target_id, 0)

        loader.mission_cmd.update(
            {
                "roe_state": 2,
                "wcs_state": 2,
                "engagement_authority_holder_id": agent_id,
                "engagement_authority_grantor_id": 9001,
                "assigned_target_track_id": target_id,
                "assigned_target_source_id": 9002,
                "assigned_target_snapshot_time_s": 12.5,
                "target_identity_state": 3,
                "engage_order_state": 2,
                "shot_policy_state": 1,
                "shot_budget_remaining": 1,
                "pending_assessment": True,
                "own_missiles_in_flight_count": 0,
            }
        )
        truth = _wait_for_assigned_target_track(sim, agent_id, target_id)
        inst = sim.get_instrument_state(agent_id)

        obs = build_universal_observation(
            loader,
            inst,
            truth,
            mission_obs_mode=mode,
            max_contacts=10,
            max_rwr=4,
            include_proprio=False,
            last_action=None,
            action_space=None,
            steps=1,
            max_steps=loader.get_max_steps(),
        )
        mission = np.asarray(obs["mission"], dtype=np.float32)

        self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
        self.assertEqual(float(mission[mission_observation_field_index(mode, "roe_state")]), 2.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "wcs_state")]), 2.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "authorization_to_fire")]), 1.0)
        self.assertEqual(
            float(mission[mission_observation_field_index(mode, "engagement_authority_holder_id")]),
            float(agent_id),
        )
        self.assertEqual(float(mission[mission_observation_field_index(mode, "assigned_target_id")]), float(target_id))
        self.assertEqual(
            float(mission[mission_observation_field_index(mode, "assigned_target_track_id")]),
            float(target_id),
        )
        self.assertEqual(float(mission[mission_observation_field_index(mode, "target_identity_state")]), 3.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "engage_order_state")]), 2.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 1.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 1.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 1.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "target_contact_present")]), 1.0)

    def test_air_combat_c2_roe_v1_defaults_to_fail_closed_shot_policy(self) -> None:
        mode = "air_combat_c2_roe_v1"
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260604))
        loader.mission_cmd["roe_state"] = 3
        truth = sim.get_agent_observation(agent_id)
        inst = sim.get_instrument_state(agent_id)

        mission = loader.get_mission_observation(mode, truth=truth, inst=inst)

        self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
        self.assertEqual(float(mission[mission_observation_field_index(mode, "roe_state")]), 3.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "wcs_state")]), 1.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 0.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 0.0)
        self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 0.0)


if __name__ == "__main__":
    unittest.main()
