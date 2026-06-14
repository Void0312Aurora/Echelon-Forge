from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.aircraft_damage import (
  AircraftDamageRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.component_damage import (
  ComponentDamageRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.default_effects_modularization import (
  DefaultEffectsModularizationRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.warhead_effects import (
  WarheadEffectsRuntimeMixin,
)


class WarheadAndComponentDamageTests(
  WarheadEffectsRuntimeMixin,
  AircraftDamageRuntimeMixin,
  ComponentDamageRuntimeMixin,
  DefaultEffectsModularizationRuntimeMixin,
  unittest.TestCase,
):
  """Warhead-effects, aircraft/component damage, and default-effects modularization runtime guards."""


if __name__ == "__main__":
  unittest.main()
