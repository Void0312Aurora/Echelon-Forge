from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.fuze import FuzeRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.launch_guidance import (
  LaunchGuidanceRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.missile_dynamics import (
  MissileDynamicsRuntimeMixin,
)


class LaunchGuidanceAndDynamicsTests(
  LaunchGuidanceRuntimeMixin,
  MissileDynamicsRuntimeMixin,
  FuzeRuntimeMixin,
  unittest.TestCase,
):
  """Launch-guidance, missile-dynamics, and fuze runtime realism guards."""


if __name__ == "__main__":
  unittest.main()
