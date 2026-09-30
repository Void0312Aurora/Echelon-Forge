"""Acceptance-gate invariance test for the stable-entity-identity package (SI-P3).

Before this package, every stochastic draw site mixed raw Flecs ids into its seed. Ids move
with the component census: an unrelated unit spawned first, or firing on episode 1 instead of
episode 0 after `reset`, changes the ids the E-3 scenario's attacker and target receive without
changing anything about the scenario itself. `docs/architecture/work/active/stable_entity_identity
/README.md`'s P1 finding (E6) measured this on main `9ee4558e`: the E-3 target survives 80 steps
at the baseline ids but is removed at step 1 (or step 12, for the 2-pre-spawn variation) once
unrelated pre-spawns or a later episode shift the ids -- with nothing else about the scenario
changed. Every draw now derives its seed from each participant's `StableEntitySerial`
(`core/interfaces/stochastic_draw.h`) and the reset seed.

What that guarantees, precisely (P5 review N2): the outcome is invariant to the component
census and to raw-id movement, i.e. allocations and recycled generations. It is *not*
invariant to creation order within an episode. Serials count creation order by design, so a
unit spawned after `reset` but before the scenario's pair shifts the pair's serials and
legitimately changes the draw. The review measured this: 4 MQ-9 pre-spawns after `reset`
changed the outcome. The pre-spawn node therefore spawns the unrelated units in the
*previous* episode, before `reset`. That moves every raw id the scenario later receives,
which is what flipped outcomes on main (E6), while leaving within-episode creation order
unchanged.

This reuses `test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth`'s scenario
(`tests/runtime/air_combat/weapon_guidance_realism/aircraft_damage.py`): an E-3 Sentry AWACS
target takes three profiled blast-fragmentation hits, then steps 80 times.
"""

from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _aircraft_damage_overlay,
  _make_warhead_profile,
  ef_py,
)


# The three local-frame hit points the P1/P2 measurement used: two wing hits, then a fuselage
# hit (mirrors test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth's damaged case).
_HIT_LOCAL_POINTS = ((-7.0, -10.2, -0.2), (-7.0, 10.2, -0.2), (-2.0, 0.0, 0.0))
_STEP_COUNT = 80


def _spawn_e3_pair(sim: "ef_py.SimulationKernel") -> tuple[int, int]:
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      5000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "E-3_Sentry_AWACS",
      0.0,
      1000.0,
      5000.0,
      180.0,
      0.0,
      0.0,
      0.0,
      -200.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _spawn_unrelated_unit(sim: "ef_py.SimulationKernel") -> int:
  # An MQ-9, matching the P1/P2 measurement's unrelated pre-spawn (README E6 table): its only
  # role is to advance the census and the ids before the scenario's own pair spawns.
  return int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "MQ-9_Reaper",
      -20000.0,
      -20000.0,
      6000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      120.0,
      0.0,
    )
  )


def _run_e3_scenario(sim: "ef_py.SimulationKernel") -> dict[str, object]:
  """Runs the E-3 scenario on an already reset+loaded kernel and returns the final outcome.

  A removed target (README E6: "removed, step 1") has no `AircraftDamageState` left to read --
  `debug_get_aircraft_damage_state` returns no values once the entity is no longer alive -- so
  the overlay is only meaningful, and only fetched, while the target is still alive. "Removed"
  is itself part of the comparable outcome: the invariance is that every variation removes the
  target at the same step, or none do, not that a dead target's non-existent overlay matches.
  """
  attacker_id, target_id = _spawn_e3_pair(sim)
  for local_x, local_y, local_z in _HIT_LOCAL_POINTS:
    applied = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id,
      target_id,
      float(local_x),
      float(local_y),
      float(local_z),
      _make_warhead_profile("blast_fragmentation", damage=180.0, radius=35.0),
    )
    assert applied, "the scenario's profiled hit must land for the invariance check to be meaningful"
  removed_at_step: int | None = None
  for step in range(_STEP_COUNT):
    sim.step()
    if removed_at_step is None and not sim.is_unit_active(target_id):
      removed_at_step = step
  alive = removed_at_step is None
  return {
    "alive": alive,
    "removed_at_step": removed_at_step,
    "overlay": _aircraft_damage_overlay(sim, target_id) if alive else None,
  }


class StableEntityIdentityDrawInvarianceTest(unittest.TestCase):
  """Acceptance Gate / Invariance: the E-3 scenario's final overlay is exactly equal when raw
  ids move (unrelated units spawned in an earlier episode, and later episodes of the same
  reset seed)."""

  def test_units_spawned_in_an_earlier_episode_do_not_change_the_outcome(self) -> None:
    def run_with_pre_spawns(pre_spawn_count: int) -> dict[str, object]:
      sim = ef_py.SimulationKernel()
      self.assertTrue(sim.load_database(_DB_PATH))
      for _ in range(pre_spawn_count):
        _spawn_unrelated_unit(sim)
      # The fence: reset deletes the pre-spawned units and restarts serials. The scenario's
      # raw ids still differ from the baseline's (allocations and recycled generations).
      sim.reset(20260529)
      self.assertTrue(sim.load_database(_DB_PATH))
      return _run_e3_scenario(sim)

    baseline = run_with_pre_spawns(0)

    for count in (1, 2, 3, 4):
      result = run_with_pre_spawns(count)
      self.assertEqual(
        result["alive"], baseline["alive"], f"{count} unrelated pre-spawn(s) changed liveness"
      )
      self.assertEqual(
        result["removed_at_step"],
        baseline["removed_at_step"],
        f"{count} unrelated pre-spawn(s) changed the removal step",
      )
      self.assertEqual(
        result["overlay"],
        baseline["overlay"],
        f"{count} unrelated pre-spawn(s) changed the final damage overlay",
      )

  def test_episodes_after_reset_do_not_change_the_outcome(self) -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(20260529)
    self.assertTrue(sim.load_database(_DB_PATH))

    episode_0 = _run_e3_scenario(sim)

    for episode in (1, 2, 3):
      sim.reset(20260529)
      self.assertTrue(sim.load_database(_DB_PATH))
      result = _run_e3_scenario(sim)
      self.assertEqual(
        result["alive"], episode_0["alive"], f"episode {episode} changed liveness vs. episode 0"
      )
      self.assertEqual(
        result["removed_at_step"],
        episode_0["removed_at_step"],
        f"episode {episode} changed the removal step vs. episode 0",
      )
      self.assertEqual(
        result["overlay"],
        episode_0["overlay"],
        f"episode {episode} changed the final damage overlay vs. episode 0",
      )


if __name__ == "__main__":
  unittest.main()
