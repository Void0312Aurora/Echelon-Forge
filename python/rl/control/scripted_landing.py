"""Compatibility shell: canonical implementation moved to ``python.tasking_contracts.scripted_landing``.

I24 (W2 critical period) moved this module's contents into the neutral
``python.tasking_contracts`` layer so ``gym_envs`` no longer needs to import
``python.rl`` for scripted (non-RL) controller support code.
"""

from __future__ import annotations

from python.tasking_contracts.scripted_landing import ScriptedLandingController, scripted_landing_action

__all__ = ["ScriptedLandingController", "scripted_landing_action"]
