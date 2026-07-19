from __future__ import annotations

import itertools
import math
import unittest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.angles import ( # noqa: E402
  bearing_between_deg,
  bearing_deg,
  distance_m,
  heading_error_deg,
  wrap_heading_deg,
  wrap_signed_deg,
)
from python.coercion import coerce_nonnegative_int # noqa: E402


# Reference copies of the removed inline implementations, kept here so the
# owner functions stay numerically pinned to the code they replaced.
def _removed_wrap_signed_deg(angle_deg: float) -> float:
  return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


def _removed_wrap_heading_mod_deg(angle_deg: float) -> float:
  # naval_screen/red_agent/coarse_route family; the negative branch some
  # copies carried is dead code for python float %.
  out = float(angle_deg) % 360.0
  if out < 0.0:
    out += 360.0
  return out


def _removed_bearing_plus360_deg(dx: float, dy: float) -> float:
  # spatial_runtime/contracts/benchmark family; python.angles.bearing_deg keeps
  # this exact (+360.0) % 360.0 form.
  return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)


def _removed_bearing_plain_mod_deg(dx: float, dy: float) -> float:
  # naval_screen/coarse_route family (plain % 360.0 wrap); deliberately NOT
  # merged into the owner because the two forms differ by ~1e-14 deg on
  # positive angles at the float level.
  return float(math.degrees(math.atan2(float(dx), float(dy))) % 360.0)


def _removed_naval_heading_error_deg(target_deg: float, current_deg: float) -> float:
  delta = (float(target_deg) % 360.0) - (float(current_deg) % 360.0)
  while delta > 180.0:
    delta -= 360.0
  while delta < -180.0:
    delta += 360.0
  return float(delta)


def _removed_coerce_nonnegative_int_returning_zero(raw_value) -> int:
  # air_profile/ground_profile/leader_tasking family (no default parameter).
  try:
    value = int(raw_value)
  except Exception:
    return 0
  return value if value >= 0 else 0


def _angle_gap_deg(a: float, b: float) -> float:
  return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


class WrapSignedDegParityTests(unittest.TestCase):
  def test_boundaries(self) -> None:
    self.assertEqual(wrap_signed_deg(0.0), 0.0)
    self.assertEqual(wrap_signed_deg(180.0), -180.0)
    self.assertEqual(wrap_signed_deg(-180.0), -180.0)
    self.assertEqual(wrap_signed_deg(179.5), 179.5)
    self.assertEqual(wrap_signed_deg(-181.0), 179.0)
    self.assertEqual(wrap_signed_deg(360.0), 0.0)
    self.assertEqual(wrap_signed_deg(-360.0), 0.0)
    self.assertEqual(wrap_signed_deg(540.0), -180.0)
    self.assertEqual(wrap_signed_deg(720.25), 0.25)

  def test_matches_removed_copies_bit_for_bit(self) -> None:
    samples = [k * 0.25 for k in range(-1441, 1442)]
    samples += [1234.5678, -9876.543, 0.1, -0.1, 359.999999, -359.999999]
    for x in samples:
      self.assertEqual(wrap_signed_deg(x), _removed_wrap_signed_deg(x))


class WrapHeadingDegParityTests(unittest.TestCase):
  def test_boundaries(self) -> None:
    self.assertEqual(wrap_heading_deg(0.0), 0.0)
    self.assertEqual(wrap_heading_deg(360.0), 0.0)
    self.assertEqual(wrap_heading_deg(-90.0), 270.0)
    self.assertEqual(wrap_heading_deg(450.0), 90.0)
    self.assertEqual(wrap_heading_deg(-360.0), 0.0)
    self.assertEqual(wrap_heading_deg(719.5), 359.5)

  def test_matches_removed_copies_bit_for_bit(self) -> None:
    for k in range(-1441, 1442):
      x = k * 0.25
      self.assertEqual(wrap_heading_deg(x), _removed_wrap_heading_mod_deg(x))


class BearingParityTests(unittest.TestCase):
  def test_cardinal_directions(self) -> None:
    self.assertEqual(bearing_deg(0.0, 1.0), 0.0)
    self.assertEqual(bearing_deg(1.0, 0.0), 90.0)
    self.assertEqual(bearing_deg(0.0, -1.0), 180.0)
    self.assertEqual(bearing_deg(-1.0, 0.0), 270.0)
    self.assertAlmostEqual(bearing_deg(1.0, 1.0), 45.0, places=12)

  def test_zero_vector_maps_to_zero(self) -> None:
    self.assertEqual(bearing_deg(0.0, 0.0), 0.0)
    self.assertEqual(bearing_deg(-0.0, 0.0), 0.0)

  def test_matches_removed_plus360_form_bit_for_bit(self) -> None:
    # The owner keeps the historical (+360.0) % 360.0 form exactly (it is NOT
    # bit-identical to plain % 360.0 on positive angles), so parity with the
    # removed copies is exact equality.
    values = [
      -1.0e9, -123.456, -3.0, -1.0, -0.25, -1.0e-9, -1.0e-300, -0.0,
      0.0, 1.0e-300, 1.0e-9, 0.25, 1.0, 3.0, 123.456, 1.0e9,
    ]
    for dx, dy in itertools.product(values, values):
      self.assertEqual(
        bearing_deg(dx, dy),
        _removed_bearing_plus360_deg(dx, dy),
        f"bearing mismatch for dx={dx}, dy={dy}",
      )

  def test_matches_removed_leader_contract_between_form_bit_for_bit(self) -> None:
    # python/testing/contracts/unit/leader.py inlined the same formula on
    # coordinate deltas.
    coords = (-123.456, -1.0, -1.0e-9, 0.0, 0.5, 2.0, 1.0e9)
    for x0, y0 in itertools.product(coords, coords):
      for x1, y1 in ((0.0, 0.0), (10.0, -2.0), (-7.25, 123.456)):
        removed = float(
          (math.degrees(math.atan2(float(x1) - float(x0), float(y1) - float(y0))) + 360.0) % 360.0
        )
        self.assertEqual(
          bearing_between_deg(x0, y0, x1, y1),
          removed,
          f"({x0!r},{y0!r})->({x1!r},{y1!r})",
        )

  def test_bearing_non_finite_inputs(self) -> None:
    self.assertTrue(math.isnan(bearing_deg(float("nan"), 1.0)))
    self.assertTrue(math.isnan(bearing_deg(1.0, float("nan"))))
    # atan2 is defined for infinite displacements; parity with the removed
    # formula is what matters.
    for dx, dy in ((float("inf"), 1.0), (1.0, float("-inf")), (float("inf"), float("inf"))):
      self.assertEqual(bearing_deg(dx, dy), _removed_bearing_plus360_deg(dx, dy), f"dx={dx!r} dy={dy!r}")

  def test_bearing_between_matches_bearing_of_delta(self) -> None:
    self.assertEqual(bearing_between_deg(3.0, 4.0, 10.0, -2.0), bearing_deg(7.0, -6.0))
    self.assertEqual(bearing_between_deg(0.0, 0.0, 0.0, 5.0), 0.0)
    self.assertEqual(bearing_between_deg(2.0, 2.0, 2.0, 2.0), 0.0)

  def test_plus360_and_plain_mod_forms_agree_as_angles(self) -> None:
    # naval_screen/coarse_route keep the plain % 360.0 wrap locally; both
    # forms must stay the same angle to well below any physical tolerance.
    values = [-123.456, -1.0, -0.25, 0.0, 0.25, 1.0, 123.456]
    for dx, dy in itertools.product(values, values):
      gap = _angle_gap_deg(bearing_deg(dx, dy), _removed_bearing_plain_mod_deg(dx, dy))
      self.assertLessEqual(gap, 1.0e-9, f"bearing family divergence for dx={dx}, dy={dy}")


class DistanceParityTests(unittest.TestCase):
  def test_planar_distance(self) -> None:
    self.assertEqual(distance_m(0.0, 0.0, 3.0, 4.0), 5.0)
    self.assertEqual(distance_m(-3.0, -4.0, 0.0, 0.0), 5.0)
    self.assertEqual(distance_m(2.0, 2.0, 2.0, 2.0), 0.0)


class NonFiniteInputTests(unittest.TestCase):
  def test_non_finite_inputs_propagate_as_nan(self) -> None:
    for x in (float("nan"), float("inf"), float("-inf")):
      self.assertTrue(math.isnan(wrap_signed_deg(x)), f"x={x!r}")
      self.assertTrue(math.isnan(wrap_heading_deg(x)), f"x={x!r}")


class CoarseRouteHelperParityTests(unittest.TestCase):
  """The route propagator helpers were rewired onto the owner; they must stay
  bit-for-bit identical to the removed module-local formulas."""

  def test_angle_diff_deg_matches_removed_formula_bit_for_bit(self) -> None:
    from python.rl.planning.coarse_route_propagator import angle_diff_deg

    targets = [k * 0.25 for k in range(-1441, 1442, 7)] + [359.999999, 720.25]
    sources = (0.0, -0.5, 90.0, -180.0, 359.999999, 720.25)
    for target in targets:
      for source in sources:
        removed = ((float(target) - float(source) + 180.0) % 360.0) - 180.0
        self.assertEqual(angle_diff_deg(target, source), removed, f"t={target!r} s={source!r}")

  def test_route_bearing_and_distance_match_removed_formulas_bit_for_bit(self) -> None:
    from python.rl.planning.coarse_route_propagator import (
      bearing_deg as route_bearing_deg,
      distance_m as route_distance_m,
    )

    coords = (0.0, -0.0, 1.0e-9, -1.0e-9, 0.5, -1.0, 123.456, -123.456, 1.0e9)
    for x1 in coords:
      for y1 in coords:
        removed_bearing = float(
          math.degrees(math.atan2(float(x1) - 2.0, float(y1) - 3.0)) % 360.0
        )
        self.assertEqual(route_bearing_deg(2.0, 3.0, x1, y1), removed_bearing, f"x1={x1!r} y1={y1!r}")
        self.assertEqual(
          route_distance_m(2.0, 3.0, x1, y1),
          math.hypot(float(x1) - 2.0, float(y1) - 3.0),
          f"x1={x1!r} y1={y1!r}",
        )


class HeadingErrorParityTests(unittest.TestCase):
  def test_keeps_positive_half_turn_unlike_wrap_signed(self) -> None:
    # Key semantic split: the naval-screen error keeps +180.0, while the
    # signed wrap folds +180.0 to -180.0. Both are pinned so the two owner
    # functions can never be silently merged.
    self.assertEqual(heading_error_deg(270.0, 90.0), 180.0)
    self.assertEqual(wrap_signed_deg(270.0 - 90.0), -180.0)

  def test_shortest_signed_delta(self) -> None:
    self.assertEqual(heading_error_deg(10.0, 350.0), 20.0)
    self.assertEqual(heading_error_deg(350.0, 10.0), -20.0)
    self.assertEqual(heading_error_deg(0.0, 0.0), 0.0)
    self.assertEqual(heading_error_deg(90.0, 270.0), -180.0)

  def test_matches_removed_naval_screen_copy_bit_for_bit(self) -> None:
    for target in range(-720, 721, 7):
      for current in range(-720, 721, 11):
        t = float(target) + 0.5
        c = float(current) + 0.25
        self.assertEqual(heading_error_deg(t, c), _removed_naval_heading_error_deg(t, c))


class CoerceNonnegativeIntParityTests(unittest.TestCase):
  def test_basic_coercion_and_default(self) -> None:
    self.assertEqual(coerce_nonnegative_int(5), 5)
    self.assertEqual(coerce_nonnegative_int("7"), 7)
    self.assertEqual(coerce_nonnegative_int(3.9), 3)
    self.assertEqual(coerce_nonnegative_int(True), 1)
    self.assertEqual(coerce_nonnegative_int(-1), 0)
    self.assertEqual(coerce_nonnegative_int(None), 0)
    self.assertEqual(coerce_nonnegative_int("garbage"), 0)
    self.assertEqual(coerce_nonnegative_int(float("nan")), 0)
    self.assertEqual(coerce_nonnegative_int(-1, default=9), 9)
    self.assertEqual(coerce_nonnegative_int("garbage", default=4), 4)
    self.assertEqual(coerce_nonnegative_int(11, default=4), 11)

  def test_matches_removed_zero_returning_variant(self) -> None:
    samples = (5, "7", 3.9, -1, -7.5, None, "garbage", float("nan"), float("inf"), 0, True, False, [], {})
    for raw in samples:
      self.assertEqual(
        coerce_nonnegative_int(raw),
        _removed_coerce_nonnegative_int_returning_zero(raw),
        f"mismatch for {raw!r}",
      )


class OwnerReexportSurfaceTests(unittest.TestCase):
  """Migrated call sites must resolve to the exact owner objects."""

  def test_angle_reexports_are_owner_objects(self) -> None:
    from gym_envs.leader_env_parts import common as leader_common
    from gym_envs.scenario_loader.behavior_runtime import naval_screen
    from gym_envs.scenario_loader.spatial_runtime import utils as spatial_utils
    from gym_envs.universal_env_parts import naval_actions
    from python.rl.planning import coarse_route_propagator
    from python.rl.runtime import leader_window_runtime
    from python.rl.tasking import leader_tasking
    from python.testing.contracts import common as contracts_common

    self.assertIs(spatial_utils.bearing_to_deg, bearing_deg)
    self.assertIs(spatial_utils.wrap_angle_deg, wrap_signed_deg)
    self.assertIs(leader_common.wrap_deg, wrap_signed_deg)
    self.assertIs(naval_actions._wrap_heading_deg, wrap_heading_deg)
    self.assertIs(naval_screen._wrap_heading_deg, wrap_heading_deg)
    self.assertIs(naval_screen._heading_error_deg, heading_error_deg)
    self.assertIs(coarse_route_propagator._wrap_deg, wrap_heading_deg)
    # coarse_route_propagator.bearing_deg stays a deliberate local variant
    # (plain % 360.0 wrap); its parity is pinned in CoarseRouteHelperParityTests.
    self.assertIs(coarse_route_propagator.distance_m, distance_m)
    self.assertIs(leader_window_runtime._wrap_deg, wrap_signed_deg)
    self.assertIs(leader_tasking._wrap_deg, wrap_signed_deg)
    self.assertIs(contracts_common._wrap_deg, wrap_signed_deg)

  def test_naval_screen_bearing_keeps_fallback_for_degenerate_geometry(self) -> None:
    from gym_envs.scenario_loader.behavior_runtime import naval_screen

    self.assertEqual(naval_screen._bearing_deg(0.0, 0.0, 405.0), 45.0)
    self.assertEqual(naval_screen._bearing_deg(1.0e-12, -1.0e-12, 45.0), 45.0)
    self.assertEqual(naval_screen._bearing_deg(1.0, 0.0, 45.0), 90.0)

  def test_coercion_reexports_are_owner_objects(self) -> None:
    from gym_envs.scenario_loader import coerce_nonnegative_int as loader_coerce
    from python.rl.profile import air_profile, ground_profile
    from python.rl.tasking import leader_tasking
    from python.scenario.compiler import _coerce_nonnegative_int as compiler_coerce

    self.assertIs(loader_coerce, coerce_nonnegative_int)
    self.assertIs(compiler_coerce, coerce_nonnegative_int)
    self.assertIs(air_profile._coerce_nonnegative_int, coerce_nonnegative_int)
    self.assertIs(ground_profile._coerce_nonnegative_int, coerce_nonnegative_int)
    self.assertIs(leader_tasking._coerce_nonnegative_int, coerce_nonnegative_int)

  def test_leader_tasking_positive_int_still_builds_on_owner(self) -> None:
    from python.rl.tasking.leader_tasking import _coerce_positive_int

    self.assertEqual(_coerce_positive_int(3), 3)
    self.assertEqual(_coerce_positive_int(0), 0)
    self.assertEqual(_coerce_positive_int(-2), 0)
    self.assertEqual(_coerce_positive_int("garbage"), 0)

  def test_zero_snap_wrap_variants_preserved(self) -> None:
    from python.rl.control.base_scripted_controller import wrap_deg as scripted_wrap_deg
    from tools.eval.eval_utils import wrap_deg as eval_wrap_deg

    for variant in (scripted_wrap_deg, eval_wrap_deg):
      self.assertEqual(variant(1.0e-10), 0.0)
      self.assertEqual(variant(360.0 - 1.0e-12), 0.0)
      self.assertEqual(variant(30.0), 30.0)
      self.assertEqual(variant(-190.0), 170.0)


if __name__ == "__main__":
  unittest.main()
