from __future__ import annotations

import unittest

from tools.diagnostics.launch_decision_learned_firing_matrix import (
  LEARNED_FIRING_EPISODES_PER_SEED,
  LEARNED_FIRING_REQUIRED_SEEDS,
  validate_learned_firing_matrix_payloads,
)


def _summary(episode: int, *, evidence: bool = False) -> dict:
  return {
    "episode": int(episode),
    "fire_once_requested_count": int(evidence),
    "fire_once_accepted_count": int(evidence),
    "release_executed_count": int(evidence),
    "authorized_release_count": int(evidence),
    "valid_authorized_release_count": int(evidence),
    "fire_once_rejected_count": 0,
    "repeat_release_before_assessment_count": 0,
    "pending_assessment_release_count": 0,
    "unauthorized_release_count": 0,
    "violation_release_count": 0,
    "fire_under_hold_count": 0,
    "shot_budget_violation_count": 0,
  }


def _payload(seed: int, *, episodes: int = LEARNED_FIRING_EPISODES_PER_SEED) -> dict:
  return {
    "mode": "model",
    "seed": int(seed),
    "episodes": int(episodes),
    "episode_summaries": [
      _summary(episode, evidence=(seed == 0 and episode == 0))
      for episode in range(int(episodes))
    ],
  }


class LearnedFiringMatrixGateTests(unittest.TestCase):
  def test_full_declared_matrix_can_pass(self) -> None:
    gate = validate_learned_firing_matrix_payloads(
      [_payload(seed) for seed in LEARNED_FIRING_REQUIRED_SEEDS]
    )
    self.assertEqual(gate["status"], "pass")
    self.assertTrue(gate["matrix_complete"])
    self.assertEqual(gate["cell_count"], 9)

  def test_missing_seed_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "exactly one retained probe payload"):
      validate_learned_firing_matrix_payloads([_payload(0), _payload(1)])

  def test_single_episode_payload_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "declares 1 episodes"):
      validate_learned_firing_matrix_payloads([
        _payload(0, episodes=1),
        _payload(1),
        _payload(2),
      ])

  def test_undeclared_seed_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "undeclared seed"):
      validate_learned_firing_matrix_payloads([_payload(0), _payload(1), _payload(7)])

  def test_duplicate_or_wrong_episode_identity_cannot_pass(self) -> None:
    duplicate = [_payload(0), _payload(1), _payload(1)]
    with self.assertRaises(ValueError):
      validate_learned_firing_matrix_payloads(duplicate)

    wrong_episode = _payload(2)
    wrong_episode["episode_summaries"][2]["episode"] = 9
    with self.assertRaisesRegex(ValueError, "episode identity"):
      validate_learned_firing_matrix_payloads([
        _payload(0),
        _payload(1),
        wrong_episode,
      ])


if __name__ == "__main__":
  unittest.main()
