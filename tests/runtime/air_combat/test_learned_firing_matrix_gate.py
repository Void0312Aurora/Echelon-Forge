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
    "first_release_step": 1 if evidence else None,
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


def _payload(
  seed: int,
  lane: str,
  *,
  episodes: int = LEARNED_FIRING_EPISODES_PER_SEED,
  evidence: bool = True,
) -> dict:
  return {
    "mode": "model",
    "lane": lane,
    "seed": int(seed),
    "episodes": int(episodes),
    "episode_summaries": [
      _summary(episode, evidence=evidence)
      for episode in range(int(episodes))
    ],
  }


class LearnedFiringMatrixGateTests(unittest.TestCase):
  def test_full_declared_matrix_can_pass(self) -> None:
    gate = validate_learned_firing_matrix_payloads(
      [
        _payload(seed, lane)
        for lane in ("deterministic", "stochastic")
        for seed in LEARNED_FIRING_REQUIRED_SEEDS
      ]
    )
    self.assertEqual(gate["status"], "pass")
    self.assertTrue(gate["matrix_complete"])
    self.assertEqual(gate["cell_count"], 18)
    self.assertEqual(gate["cells_per_lane"], 9)

  def test_missing_seed_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "exactly one retained probe payload"):
      validate_learned_firing_matrix_payloads([
        _payload(0, "deterministic"),
        _payload(1, "deterministic"),
      ])

  def test_single_episode_payload_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "declares 1 episodes"):
      validate_learned_firing_matrix_payloads([
        _payload(0, "deterministic", episodes=1),
        _payload(1, "deterministic"),
        _payload(2, "deterministic"),
      ])

  def test_undeclared_seed_cannot_pass(self) -> None:
    with self.assertRaisesRegex(ValueError, "undeclared seed"):
      validate_learned_firing_matrix_payloads([
        _payload(0, "deterministic"),
        _payload(1, "deterministic"),
        _payload(7, "deterministic"),
      ])

  def test_duplicate_or_wrong_episode_identity_cannot_pass(self) -> None:
    duplicate = [
      _payload(0, "deterministic"),
      _payload(1, "deterministic"),
      _payload(1, "deterministic"),
    ]
    with self.assertRaises(ValueError):
      validate_learned_firing_matrix_payloads(duplicate)

    wrong_episode = _payload(2, "deterministic")
    wrong_episode["episode_summaries"][2]["episode"] = 9
    with self.assertRaisesRegex(ValueError, "episode identity"):
      validate_learned_firing_matrix_payloads([
        _payload(0, "deterministic"),
        _payload(1, "deterministic"),
        wrong_episode,
      ])

  def test_each_cell_must_pass_independently(self) -> None:
    with self.assertRaisesRegex(ValueError, "deterministic seed 1 episode 0"):
      validate_learned_firing_matrix_payloads([
        _payload(seed, lane, evidence=not (lane == "deterministic" and seed == 1))
        for lane in ("deterministic", "stochastic")
        for seed in LEARNED_FIRING_REQUIRED_SEEDS
      ])

  def test_lane_is_required(self) -> None:
    payload = _payload(0, "deterministic")
    payload.pop("lane")
    with self.assertRaisesRegex(ValueError, "declare lane"):
      validate_learned_firing_matrix_payloads([
        payload,
        _payload(1, "deterministic"),
        _payload(2, "deterministic"),
        _payload(0, "stochastic"),
        _payload(1, "stochastic"),
        _payload(2, "stochastic"),
      ])


if __name__ == "__main__":
  unittest.main()
