from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics.m3s2_real_update_path_probe import _build_groups_from_rows  # noqa: E402


class M3S2RealUpdatePathProbeTests(unittest.TestCase):
    def test_build_groups_marks_quality_after_launch_and_min_age(self) -> None:
        groups = _build_groups_from_rows(
            fire_mask=[False, True, True, True, True],
            fire_once_accepted=[False, False, False, False, False],
            episode_id=[0, 0, 0, 0, 0],
            launch_window_open=[False, False, True, True, True],
            launch_min_age=3,
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].legal_mask, (False, True, True, True, True))
        self.assertEqual(groups[0].quality_mask, (False, False, False, True, True))
        self.assertEqual(groups[0].censoring_kind, "timeout")

    def test_build_groups_early_accepted_before_quality_is_prefix_censored(self) -> None:
        groups = _build_groups_from_rows(
            fire_mask=[True, True, True, True],
            fire_once_accepted=[False, True, False, False],
            episode_id=[0, 0, 0, 0],
            launch_window_open=[False, False, True, True],
            launch_min_age=3,
        )

        self.assertEqual(groups[0].row_indices, (0, 1))
        self.assertEqual(groups[0].accepted_event, (False, True))
        self.assertEqual(groups[0].censoring_kind, "early_event_prefix")


if __name__ == "__main__":
    unittest.main()
