"""Neutral task-dispatch contract layer shared by ``gym_envs`` and ``python.rl``.

This package owns the parts of the tasking/command-chain dispatch surface that
``gym_envs`` consumes but that do not themselves depend on service-profile
internals (air/ground/naval implementations stay under ``python.rl.profile``
and ``python.rl.tasking``). Dependency direction is::

    gym_envs -> python.tasking_contracts <- python.rl

Modules here must depend only on the standard library, ``ef_py`` (and other
compiled/native-facing packages such as ``python.scenario``), and each other.
They must never import ``python.rl`` or ``gym_envs`` — that boundary is
enforced by ``tests/architecture/tasking_contracts/test_tasking_contracts_boundary.py``.

``python.rl.control.mission_defs``, ``python.rl.tasking.bridge``, and the
scripted-controller modules under ``python.rl.control`` re-export the names
that moved here so every previously working import path keeps working.
"""

from __future__ import annotations
