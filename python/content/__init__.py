"""Content-face owner package (unified architecture program, track T11).

Owner for content-defined capability-bundle documents: the pilot direction
where content declares platform capability composition directly (the
``typed_platform_request`` path from the T11 census G-C), instead of the
runtime deriving a projection bundle from the monolithic ``UnitDefinition``
struct at spawn time.

Standard library only: importing this package must never pull runtime, gym,
or training dependencies. Nothing in the maintained default path
(``spawn_unit`` / ``WorldSpawnRequest`` / the scenario compiler chain) may
import this package; that isolation is the rollback shell and is pinned by
``tests/content/capability_bundles/test_rollback_shell_guard.py`` (this
iteration).
"""
