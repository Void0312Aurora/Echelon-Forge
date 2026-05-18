from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import mission_observation_dim as env_mission_observation_dim  # noqa: E402
from python.mission_obs_taxonomy import (  # noqa: E402
    BASE_MISSION_OBS_MODES,
    COOPERATIVE_MISSION_OBS_MODES,
    mission_observation_field_index,
    mission_obs_mode_code,
    mission_observation_dim,
    mission_observation_field_names,
)


class MissionObservationTaxonomyTests(unittest.TestCase):
    def test_shared_taxonomy_matches_runtime_entrypoints(self) -> None:
        modes = list(BASE_MISSION_OBS_MODES) + list(COOPERATIVE_MISSION_OBS_MODES)
        self.assertEqual(
            modes,
            [
                "basic",
                "nav_v1",
                "nav_v2",
                "nav_v2_formation_v1",
                "nav_v2_formation_role_v1",
                "nav_v2_cooperative_takeoff_v1",
            ],
        )

        for expected_code, mode in enumerate(modes):
            fields = mission_observation_field_names(mode)
            self.assertEqual(mission_obs_mode_code(mode), expected_code)
            self.assertEqual(mission_observation_dim(mode), len(fields))
            self.assertEqual(env_mission_observation_dim(mode), len(fields))
            self.assertEqual(ScenarioLoader._mission_observation_mode_code(mode), expected_code)

        self.assertEqual(ScenarioLoader._mission_observation_mode_code(""), mission_obs_mode_code("basic"))

    def test_shared_taxonomy_keeps_expected_field_layouts(self) -> None:
        self.assertEqual(
            mission_observation_field_names("basic"),
            [
                "command_code",
                "target_heading_deg",
                "target_altitude_m",
                "target_speed_mps",
            ],
        )
        self.assertEqual(
            mission_observation_field_names("nav_v2")[4:],
            [
                "selected_steerpoint",
                "steerpoint_mode_code",
                "dist_m",
                "bearing_rel_deg",
                "altitude_delta_m",
                "cdi_norm",
                "track_angle_error_deg",
                "leg_distance_remaining_m",
                "next_turn_deg",
                "distance_to_turn_m",
            ],
        )
        self.assertEqual(
            mission_observation_field_names("nav_v2_formation_v1")[-3:],
            ["form_offset_x_m", "form_offset_y_m", "form_offset_z_m"],
        )
        self.assertEqual(
            mission_observation_field_names("nav_v2_formation_role_v1")[-4:],
            [
                "self_role_code",
                "self_formation_role_code",
                "relative_slot_code",
                "reference_relative_slot_code",
            ],
        )
        self.assertEqual(
            mission_observation_field_names("nav_v2_cooperative_takeoff_v1")[14:],
            [
                "takeoff_procedure_code",
                "takeoff_clearance_code",
                "takeoff_interval_s",
                "runway_slot_code",
                "form_offset_x_m",
                "form_offset_y_m",
                "form_offset_z_m",
                "self_role_code",
                "self_formation_role_code",
                "relative_slot_code",
                "reference_relative_slot_code",
            ],
        )
        self.assertEqual(mission_observation_field_index("basic", "command_code"), 0)
        self.assertEqual(mission_observation_field_index("nav_v2", "selected_steerpoint"), 4)
        self.assertEqual(mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m"), 14)
        self.assertEqual(mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code"), 17)
        self.assertEqual(
            mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code"),
            14,
        )
        self.assertEqual(
            mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "reference_relative_slot_code"),
            24,
        )


if __name__ == "__main__":
    unittest.main()
