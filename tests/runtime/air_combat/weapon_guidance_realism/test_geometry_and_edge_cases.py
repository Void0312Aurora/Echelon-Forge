from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.edge_cases import (
  BoundaryCaseRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.geometry_fixtures import (
  GeometryFixtureRuntimeMixin,
)


class GeometryAndEdgeCaseTests(
  GeometryFixtureRuntimeMixin,
  BoundaryCaseRuntimeMixin,
  unittest.TestCase,
):
  """Controlled geometry fixture and boundary/edge-case runtime guards."""


if __name__ == "__main__":
  unittest.main()
