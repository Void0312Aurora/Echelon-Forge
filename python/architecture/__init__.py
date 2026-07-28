"""Neutral architecture-governance facilities shared by ``gym_envs`` and ``python.rl``.

This package owns lightweight, zero-runtime-overhead governance metadata that
maintained observation/reward consumers declare against. It is the Python home
of the Unified Architecture Program's Kernel Invariant G4 declaration mechanism
(architecture design doc §3, §15). Dependency direction mirrors
``python.tasking_contracts``::

    gym_envs -> python.architecture <- python.rl

Modules here must depend only on the standard library. They must never import
``python.rl``, ``gym_envs``, or ``ef_py`` — the vocabulary they publish is pure
metadata and carries no runtime behavior.
"""

from __future__ import annotations
