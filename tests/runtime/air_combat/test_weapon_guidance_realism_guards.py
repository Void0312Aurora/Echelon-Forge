from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.aircraft_damage import AircraftDamageRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.a8_aero_consumer import (
    A8AeroConsumerRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_mq9_aim120 import (
    A8Mq9Aim120ValidationRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_sensor_datalink_consumer import (
    A8SensorDataLinkConsumerRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_fire_consequence import (
    A8FireConsequenceRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.component_damage import ComponentDamageRuntimeMixin
from tests.runtime.air_combat.weapon_guidance_realism.default_effects_modularization import (
    DefaultEffectsModularizationRuntimeMixin,
)
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
    A8Mq9Aim120ValidationRuntimeMixin,
    A8AeroConsumerRuntimeMixin,
    A8SensorDataLinkConsumerRuntimeMixin,
    A8FireConsequenceRuntimeMixin,
    AircraftDamageRuntimeMixin,
    ComponentDamageRuntimeMixin,
    DefaultEffectsModularizationRuntimeMixin,
    VulnerabilityAuthorityRuntimeMixin,
    VulnerabilityScaffoldRuntimeMixin,
    MissileDynamicsRuntimeMixin,
    BoundaryCaseRuntimeMixin,
    unittest.TestCase,
):
    """Compatibility collector for split weapon-guidance realism subdomains."""


if __name__ == "__main__":
    unittest.main()
