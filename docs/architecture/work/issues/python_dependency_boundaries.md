# Python Dependency Boundaries

Status: active implementation of GitHub issue #60.

Owner: cross-domain architecture, with `gym_envs` and `python.rl` owners for
the retained runtime transitions.

## Purpose

The repository has several Python responsibility groups under the same
top-level `python/` package. Directory names alone cannot enforce their
direction. `tools/architecture/dependency_inventory.py` therefore builds a
repeatable source inventory from Python AST imports, the existing C++ quoted
include scanner, and project-to-project CMake link calls. It reports import
sites, unique module/file edges, target links, unresolved internal imports,
and strongly connected components.

`tools/architecture/dependency_policy.py` assigns responsibility roles and
checks the directional matrix. The architecture test fails when a new
forbidden edge appears, when a registered transition grows, or when a
transition becomes stale. This makes the current exceptions visible and
prevents the baseline from silently expanding.

## Policy states

- **allowed**: the source role may depend on the target role under the current
  directional matrix.
- **compatibility**: the target is a named compatibility bridge. It remains a
  deliberate adapter surface and is not a general-purpose dependency escape.
- **transitional**: an exact source/target edge is retained in
  `tests/architecture/fixtures/python_dependency_transitions.json` with an
  owner, reason, maximum site count, and removal condition.
- **forbidden**: any new cross-role edge without an explicit transition entry.

The policy treats `python.rl.tasking.bridge` as compatibility because existing
tests and runtime modules use it as the documented bridge to profile-specific
tasking. New environment imports of policy or runtime implementations remain
transitional and must be registered one edge at a time.

## Current structural work

`RedScriptedAgent` is now owned by `python.scenario.runtime.red_scripted_agent`.
The old `examples.agents` path remains a compatibility export for callers, but
the maintained scenario loader no longer depends on the examples layer. No
direct environment-to-policy/runtime imports remain in the transition register.
Leader execution runtime construction, wrapper-spec resolution, leader-window
runtime selection, and frozen execution policy loading now go through
`python.simulation` and no longer import their RL implementations directly.
CSG replay adapter creation also uses that provider boundary. The maintained
policy-evaluation and visualization entries now use the same factories for
single/cooperative world construction, wrapper resolution, and policy loading;
their RL provider remains lazy behind `python.simulation`.

## Verification

Run the focused gate from the repository root:

```powershell
python -m pytest -q tests/architecture/governance/test_python_dependency_boundaries.py
```

For a readable census without running pytest:

```powershell
python -m tools.architecture.dependency_inventory --format summary
```

The policy-only gate can be inspected or used as a CI command:

```powershell
python -m tools.architecture.dependency_policy --format summary
```

The current 2026-10-05 baseline from that command is 1,107 Python modules, 2,551
resolved Python import sites, 561 C/C++ source files, 1,723 quoted include
sites, and 72 CMake link sites representing 66 unique target edges. No Python,
C++ file, or CMake target multi-node cycle is present. The Python policy
classifies 2,514 edges as allowed and 37 as compatibility, with no transitional
edges remaining;
there are no unregistered forbidden edges. These counts use the maintained
scanner scope above and are not expected to equal the issue's initial census
because that census did not specify identical roots, file suffixes, or edge
deduplication rules.

This is a source census. It does not claim to resolve non-literal dynamic
imports, preprocessor expansion, CMake conditions or generator expressions, or
third-party dependencies. Those remain separate evidence limitations and are
reported as such rather than inferred from this one.
