"""Compatibility shell: canonical implementation moved to ``python.tasking_contracts.air.execution.takeoff``.

I24 (W2 critical period) moved this module's contents into the neutral
``python.tasking_contracts`` layer so ``gym_envs`` no longer needs to import
``python.rl`` for scripted (non-RL) controller support code.
"""

from __future__ import annotations

from python.tasking_contracts.air.execution.takeoff import ScriptedTakeoffController, scripted_takeoff_action

__all__ = ["ScriptedTakeoffController", "scripted_takeoff_action"]
