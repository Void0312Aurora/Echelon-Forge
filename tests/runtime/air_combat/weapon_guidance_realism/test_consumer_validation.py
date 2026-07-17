from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.aero_consumer import (
  AeroConsumerRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.fire_consequence import (
  FireConsequenceRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.mq9_aim120 import (
  Mq9Aim120ValidationRuntimeMixin,
)
from tests.runtime.air_combat.weapon_guidance_realism.sensor_datalink_consumer import (
  SensorDataLinkConsumerRuntimeMixin,
)


class ConsumerValidationTests(
  Mq9Aim120ValidationRuntimeMixin,
  AeroConsumerRuntimeMixin,
  SensorDataLinkConsumerRuntimeMixin,
  FireConsequenceRuntimeMixin,
  unittest.TestCase,
):
  """A8 MQ-9/AIM-120 end-to-end validation and downstream consumer guards."""


if __name__ == "__main__":
  unittest.main()
