from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.a8_aero_consumer import (
  A8AeroConsumerRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_fire_consequence import (
  A8FireConsequenceRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_mq9_aim120 import (
  A8Mq9Aim120ValidationRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.a8_sensor_datalink_consumer import (
  A8SensorDataLinkConsumerRuntimeMixin,
)


class A8ConsumerValidationTests(
  A8Mq9Aim120ValidationRuntimeMixin,
  A8AeroConsumerRuntimeMixin,
  A8SensorDataLinkConsumerRuntimeMixin,
  A8FireConsequenceRuntimeMixin,
  unittest.TestCase,
):
  """A8 MQ-9/AIM-120 end-to-end validation and downstream consumer guards."""


if __name__ == "__main__":
  unittest.main()
