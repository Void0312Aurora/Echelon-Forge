from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.aircraft_damage import AircraftDamageRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.component_damage import ComponentDamageRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.edge_cases import BoundaryCaseRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.fuze import FuzeRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.launch_guidance import LaunchGuidanceRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.missile_dynamics import MissileDynamicsRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.vulnerability_authority import VulnerabilityAuthorityRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.vulnerability_scaffold import (
    VulnerabilityScaffoldRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.warhead_effects import WarheadEffectsRuntimeMixin


class WeaponGuidanceRealismGuardTests(
    LaunchGuidanceRuntimeMixin,
    FuzeRuntimeMixin,
    WarheadEffectsRuntimeMixin,
    AircraftDamageRuntimeMixin,
    ComponentDamageRuntimeMixin,
    VulnerabilityAuthorityRuntimeMixin,
    VulnerabilityScaffoldRuntimeMixin,
    MissileDynamicsRuntimeMixin,
    BoundaryCaseRuntimeMixin,
    unittest.TestCase,
):
    """Compatibility collector for split weapon-guidance realism subdomains."""


if __name__ == "__main__":
    unittest.main()
