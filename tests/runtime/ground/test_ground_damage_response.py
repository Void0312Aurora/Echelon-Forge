from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_GROUND_UNIT_NAME = "Ground_Platoon_MVP"

# DM-G1's reachability defect is repaired. The effects route no longer resolves
# `GroundPlatformDamageState` by name from its own translation unit: the id is
# resolved once per world in the composition path and carried on the world-scoped
# model instance, so the ground selection predicate matches and the router applies
# the ground response instead of falling through to the `GroundPlaceholder`.
#
# Tracking artifacts: docs/systems/combat/reviews/ground_damage_reachability_20260921.md
# records the defect; docs/domains/ground/work/active/ground_damage_effects_route_repair/
# records the repair, its flip set, and its residual.
#
# One node below used to carry a `strict=True` marker for a second expectation it
# bundled with reachability. That expectation was withdrawn on 2026-09-28 rather
# than satisfied with a coefficient: the node is split so reachability and the
# mobility contract are asserted separately.

# A ground hit does not degrade mobility on the synthesized bootstrap surface (the
# default Ground fixture spawned below, which declares no `damage_model`), and the cause
# is a scope gate, not a warhead property. `apply_default_effects_ground_chassis_consequence_blocks`
# degrades `mobility_integrity` and `track_integrity` only when the ground spatial scales carry a
# blast or a mobility term. Those terms come from sampled warhead mechanism load, and the
# effects model estimates mechanism load only for structured *air* targets: the
# direct-hit and spatial-projection paths are gated on `structured_air_target`, and a
# ground target receives the default `WarheadEffectProfile{}`. The blast and mobility
# scales are therefore always zero on the ground route, whatever the warhead family,
# which makes those chassis branches implemented but unreachable, the same class as
# DM-G1. Mission and survivability still degrade through `command_integrity` and
# `structural_integrity`.
#
# This scope gate is specific to the synthesized bootstrap surface. An authored Ground
# `damage_model` whose hitbox declares an `engine`, `engineering`, or `fuel` system takes a
# different, already-reachable path: the generic non-air branch in
# `apply_default_effects_system_effect`
# (src/models/weapons/detail/default_effects_system_effect_detail.h, the `!context.structured_air_target`
# case) matches the system name and subtracts directly from `platform_damage->mobility_capability`.
# That is a pre-existing naval/generic system-name coefficient, not a Ground mechanism, and
# is not exercised by the fixture this suite spawns.
#
# The expectation that a hit degrades mobility was withdrawn on 2026-09-28 rather than
# satisfied: admitting ground mechanism-load estimation without a Ground vulnerability
# profile would put uncalibrated air warhead physics into Ground consequences. The
# follow-up and its entry conditions are in
# docs/domains/ground/work/active/ground_damage_effects_route_repair/README.md; this
# suite pins the current contract so that work has to change it deliberately.

# `get_unit_damage_state` order: [mission, mobility, sensor, survivability].
_MISSION = 0
_MOBILITY = 1
_SENSOR = 2
_SURVIVABILITY = 3

# The ground bootstrap synthesizes one provisional whole-body hitbox spanning
# +/-1.0 m. These body-frame coordinates place the detonation inside it, which is
# what a real structural hit looks like. `debug_apply_proximity_hit` cannot be
# used here: it places the impact at local (0, 0, 2.0) for any non-air target, so
# there is no direct structure hit and the ground consequence block is skipped by
# design.
_HIT_LOCAL_FORWARD_M = 0.2
_HIT_LOCAL_RIGHT_M = 0.1
_HIT_LOCAL_UP_M = 0.0


class GroundDamageResponseTests(unittest.TestCase):
  """DM-G1 ground-owned damage mechanism reachability and progression."""

  def _spawn_ground_pair(self) -> tuple[ef_py.SimulationKernel, int, int]:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    target_id = int(
      sim.spawn_unit(
        ef_py.Side.Blue,
        _GROUND_UNIT_NAME,
        100.0,
        250.0,
        0.0,
        37.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
      )
    )
    attacker_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        _GROUND_UNIT_NAME,
        400.0,
        250.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
      )
    )
    self.assertGreater(target_id, 0)
    self.assertGreater(attacker_id, 0)
    return sim, target_id, attacker_id

  def _apply_structural_hit(
    self, sim: ef_py.SimulationKernel, attacker_id: int, target_id: int, damage: float
  ) -> bool:
    return bool(
      sim.debug_apply_local_proximity_hit(
        attacker_id,
        target_id,
        _HIT_LOCAL_FORWARD_M,
        _HIT_LOCAL_RIGHT_M,
        _HIT_LOCAL_UP_M,
        damage,
        80.0,
      )
    )

  def _is_alive(self, sim: ef_py.SimulationKernel, entity_id: int) -> bool:
    return any(float(component) != 0.0 for component in sim.get_unit_position(entity_id))

  def _readings(self, sim: ef_py.SimulationKernel, entity_id: int) -> list[float]:
    return [float(value) for value in sim.get_unit_damage_state(entity_id)]

  def test_structured_ground_hit_applies_ground_response_instead_of_legacy_kill(self) -> None:
    """The structured ground route must win over the placeholder fallback.

    The all-zero capability vector and the destruction of the element come from
    the `GroundPlaceholder` fallback's shared finalize, not from the legacy
    one-shot HP path: with the ground route accepted, a single 120-damage hit
    leaves the element alive with an untouched capability vector. Reaching the
    ground route at all requires the ground-owned damage state to be present at
    effects-routing time, so this test is also the reachability pin for the
    spawn-side bootstrap that attaches `GroundPlatformDamageState`.
    """
    sim, target_id, attacker_id = self._spawn_ground_pair()

    initial = self._readings(sim, target_id)
    self.assertEqual(initial, [1.0, 1.0, 1.0, 1.0])

    self.assertTrue(
      self._apply_structural_hit(sim, attacker_id, target_id, 120.0),
      "the local debug hit must report a resolved engagement",
    )

    after_hit = self._readings(sim, target_id)
    self.assertNotEqual(
      after_hit,
      [0.0, 0.0, 0.0, 0.0],
      "an all-zero vector means the legacy HP path destroyed the ground element "
      "instead of the ground-owned damage mechanism running",
    )
    self.assertTrue(
      self._is_alive(sim, target_id),
      "a single 120-damage structural hit must not remove the ground element",
    )
    self.assertLess(
      after_hit[_MISSION],
      initial[_MISSION],
      "ground consequence application must degrade mission capability",
    )
    self.assertLess(
      after_hit[_SURVIVABILITY],
      initial[_SURVIVABILITY],
      "ground consequence application must degrade the survivability margin",
    )

  def test_ground_route_does_not_degrade_mobility_for_any_warhead_family(self) -> None:
    """Pins the current mobility contract on the synthesized bootstrap surface.

    This pins the default Ground fixture spawned by `_spawn_ground_pair`, which declares
    no `damage_model` and so gets the factory's synthesized whole-body hitbox and
    `SystemHealth` (see `default_unit_factory.h`). The ground route never estimates
    warhead mechanism load for that surface (that estimation is gated on structured air
    targets), so the blast/mobility spatial scales stay zero and the chassis mobility
    branches cannot fire for any warhead family. Mission and survivability degrade;
    mobility stays at 1.0. This is a recorded scope gap of the uncalibrated bootstrap
    route, not a claim that ground movement is immune to damage: an authored Ground
    `damage_model` declaring an `engine`/`fuel` system reaches mobility instead, through
    the generic non-air system-name path in `apply_default_effects_system_effect`
    (src/models/weapons/detail/default_effects_system_effect_detail.h) — not pinned here,
    since pinning that uncalibrated coefficient would entrench it. The registered
    follow-up must change this node deliberately.
    """
    for family in ("blast", "blast_fragmentation", "fragmentation", "continuous_rod"):
      with self.subTest(family=family):
        sim, target_id, attacker_id = self._spawn_ground_pair()
        profile = ef_py.WarheadProfile()
        profile.family = family
        profile.mass_kg = 12.0
        profile.lethal_radius_m = 80.0
        profile.damage_scalar = 120.0
        profile.synthetic = False
        profile.damage_scalar_synthetic = False
        profile.provenance = f"test_ground_{family}_profile"
        self.assertTrue(
          bool(
            sim.debug_apply_profiled_local_proximity_hit(
              attacker_id,
              target_id,
              _HIT_LOCAL_FORWARD_M,
              _HIT_LOCAL_RIGHT_M,
              _HIT_LOCAL_UP_M,
              profile,
            )
          )
        )
        after_hit = self._readings(sim, target_id)
        self.assertLess(after_hit[_MISSION], 1.0)
        self.assertLess(after_hit[_SURVIVABILITY], 1.0)
        self.assertEqual(
          after_hit[_MOBILITY],
          1.0,
          "ground mechanism-load estimation is not admitted, so no warhead family "
          "reaches the chassis mobility branches; changing this requires the "
          "registered Ground mobility follow-up",
        )

  def test_ground_damage_state_advances_across_ticks(self) -> None:
    """Ground capability keeps degrading per tick after the warhead consequence."""
    sim, target_id, attacker_id = self._spawn_ground_pair()
    self.assertTrue(self._apply_structural_hit(sim, attacker_id, target_id, 120.0))

    after_hit = self._readings(sim, target_id)
    sim.step()
    after_one_tick = self._readings(sim, target_id)
    for _ in range(59):
      sim.step()
    after_sixty_ticks = self._readings(sim, target_id)

    self.assertLess(
      after_one_tick[_MISSION],
      after_hit[_MISSION],
      "the ground damage system must advance the projection on the first tick",
    )
    self.assertLess(
      after_sixty_ticks[_MISSION],
      after_one_tick[_MISSION],
      "the ground damage system must keep advancing the projection over time",
    )
    self.assertLess(
      after_sixty_ticks[_SURVIVABILITY],
      after_hit[_SURVIVABILITY],
      "progressive ground damage must keep eroding the survivability margin",
    )
    self.assertTrue(self._is_alive(sim, target_id))

  def test_ground_damage_projection_stays_monotonic_and_bounded(self) -> None:
    """Repeated ticks must not compound or unstably grow the same damage load."""
    sim, target_id, attacker_id = self._spawn_ground_pair()
    self.assertTrue(self._apply_structural_hit(sim, attacker_id, target_id, 120.0))

    readings = [self._readings(sim, target_id)]
    for _ in range(120):
      sim.step()
      readings.append(self._readings(sim, target_id))

    for previous, current in zip(readings, readings[1:]):
      for index in (_MISSION, _MOBILITY, _SENSOR, _SURVIVABILITY):
        self.assertLessEqual(
          current[index],
          previous[index] + 1.0e-9,
          "ground capability projection must be monotonically non-increasing",
        )
        self.assertGreaterEqual(current[index], 0.0)
        self.assertLessEqual(current[index], 1.0)

  def test_ground_element_survives_a_single_hit_and_stays_combat_capable(self) -> None:
    """One structural hit degrades the element without crossing a kill threshold.

    The shared loss projection declares a mobility kill at `mobility_capability
    <= 0.25` and a lost platform only once survivability reaches zero. A single
    warhead consequence must leave the element on the capable side of both, which
    is what makes sustained damage (rather than one hit) the thing that decides
    the outcome.
    """
    sim, target_id, attacker_id = self._spawn_ground_pair()
    self.assertTrue(self._apply_structural_hit(sim, attacker_id, target_id, 120.0))

    for _ in range(120):
      sim.step()

    self.assertTrue(
      self._is_alive(sim, target_id),
      "one structural hit plus damage-control progression must not destroy the element",
    )
    readings = self._readings(sim, target_id)
    self.assertGreater(
      readings[_MOBILITY],
      0.25,
      "one structural hit must not reach the shared mobility-kill threshold",
    )
    self.assertGreater(
      readings[_SURVIVABILITY],
      0.0,
      "one structural hit must not reach the shared lost-state threshold",
    )

  def test_sustained_ground_damage_reaches_lost_state_through_shared_projection(self) -> None:
    """Sustained pressure, not one hit, is what reaches the lost state."""
    sim, target_id, attacker_id = self._spawn_ground_pair()

    self.assertTrue(
      self._apply_structural_hit(sim, attacker_id, target_id, 240.0),
      "the first structural hit must resolve",
    )
    self.assertTrue(
      self._is_alive(sim, target_id),
      "the first hit must leave the element combat capable",
    )

    for _ in range(10):
      self._apply_structural_hit(sim, attacker_id, target_id, 240.0)
      for _ in range(40):
        sim.step()
      if not self._is_alive(sim, target_id):
        break

    self.assertFalse(
      self._is_alive(sim, target_id),
      "sustained ground damage must reach the lost state through the shared "
      "loss projection",
    )

  def test_repaired_route_holds_in_a_world_created_after_earlier_worlds(self) -> None:
    """The resolution is per world, not per process.

    `flecs::_::type_impl<T>::s_id` is cached process-globally per type, and this
    repository runs many worlds in one process, so "the route works" measured in
    one world does not by itself say anything about the next. The repair resolves
    the component id in each world's own composition path -- once per world, after
    that world's component registration -- and this node is the measurement that
    keeps that true rather than assumed.

    Every world below is created after the previous ones have resolved the id, and
    the last one is created after the earlier kernels are gone. Each must show the
    ground consequence: an all-zero vector means the legacy one-shot kill ran
    behind the placeholder, and an untouched vector means the hit never reached
    the ground route.
    """
    worlds = [self._spawn_ground_pair() for _ in range(3)]
    expected: list[float] | None = None

    for index, (world_sim, world_target, world_attacker) in enumerate(worlds):
      self.assertEqual(
        self._readings(world_sim, world_target),
        [1.0, 1.0, 1.0, 1.0],
        f"world {index}: the spawn path must attach the ground damage state",
      )
      self.assertTrue(
        self._apply_structural_hit(world_sim, world_attacker, world_target, 120.0),
        f"world {index}: the local debug hit must report a resolved engagement",
      )
      after = self._readings(world_sim, world_target)
      self.assertNotEqual(
        after,
        [0.0, 0.0, 0.0, 0.0],
        f"world {index}: an all-zero vector means the legacy HP path ran instead "
        "of the ground-owned damage mechanism",
      )
      self.assertLess(
        after[_MISSION],
        1.0,
        f"world {index}: the ground consequence must land on the mission channel",
      )
      self.assertLess(
        after[_SURVIVABILITY],
        1.0,
        f"world {index}: the ground consequence must land on the survivability channel",
      )
      if expected is None:
        expected = after
      else:
        self.assertEqual(
          after,
          expected,
          f"world {index}: the same hit in a later world must produce the same "
          "consequence, or the resolution is not per world",
        )

    del worlds

    survivor_sim, survivor_target, survivor_attacker = self._spawn_ground_pair()
    self.assertEqual(self._readings(survivor_sim, survivor_target), [1.0, 1.0, 1.0, 1.0])
    self.assertTrue(self._apply_structural_hit(survivor_sim, survivor_attacker, survivor_target, 120.0))
    self.assertEqual(
      self._readings(survivor_sim, survivor_target),
      expected,
      "a world created after the earlier worlds are gone must still resolve the "
      "component id in its own composition path",
    )

  def test_worlds_do_not_leak_ground_damage_into_each_other(self) -> None:
    """Two live worlds, one of them hit twice: the other must not move."""
    first_sim, first_target, first_attacker = self._spawn_ground_pair()
    second_sim, second_target, second_attacker = self._spawn_ground_pair()

    self._apply_structural_hit(first_sim, first_attacker, first_target, 120.0)
    self._apply_structural_hit(second_sim, second_attacker, second_target, 120.0)
    second_after_one = self._readings(second_sim, second_target)

    self._apply_structural_hit(first_sim, first_attacker, first_target, 120.0)
    first_after_two = self._readings(first_sim, first_target)

    self.assertLess(
      first_after_two[_MISSION],
      second_after_one[_MISSION],
      "the second hit must land in the world that received it",
    )
    self.assertEqual(
      self._readings(second_sim, second_target),
      second_after_one,
      "hitting one world must not move another world's ground damage state",
    )


if __name__ == "__main__":
  unittest.main()
