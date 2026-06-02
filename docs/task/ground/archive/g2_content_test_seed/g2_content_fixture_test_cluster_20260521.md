# G2 Content Fixture And Test Cluster

Status: `2026-05-21` accepted by main-thread G2-C integration.

Inputs:

- [G2 README](README.md)
- [G1 profile and DTO contract cluster](../g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Create the first source-controlled ground fixtures and tests. The goal is
contract usability, not simulation realism.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `G2-A1` | Fixture placement | Choose first content roots under `examples/config/database/` without conflicting with air/naval layouts. |
| `G2-A2` | Starter unit fixture | Add a platoon-centered ground fixture that makes no runtime movement, terrain, sensing, fires, or combat claim. |
| `G2-A3` | Capability note | Document how the fixture maps toward capability-bundle construction, even if public `spawn_platform` is not available. |
| `G2-B1` | Task spec contracts | Add contract specs covering `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` profile defaults. |
| `G2-B2` | Contract tests | Tests prove contract specs normalize through the ground profile and common-core fields. |
| `G2-C1` | Integration | Synchronize G2 docs, dispatch queue, validation evidence, and G3 residuals after workers return. |

Accepted result:

- `G2-A1/G2-A2/G2-A3`: passed with
  `examples/config/database/ground/units/ground_platoon_starter.seed` and
  `examples/config/database/ground/units/CAPABILITY_NOTE.md`.
- `G2-B1/G2-B2`: passed with three runnable `unit_regression` contracts under
  `tests/contracts/unit/ground/`.
- `G2-C1`: passed after main-thread validation and status synchronization.

## Worker Dispatch

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `G2-A` | worker | `gpt-5.4`, high | Add the first ground fixture root and capability note. | `examples/config/database/ground/**` only. No tests, docs/task edits, runtime edits, or loader edits. |
| `G2-B` | worker | `gpt-5.4`, high | Add ground unit contracts and focused contract-runner coverage. | `tests/contracts/unit/ground/**` and one focused `tests/leader` or `tests/runners` test only. No fixture edits, docs/task edits, runtime edits, or loader edits. |
| `G2-C` | main-thread integration | current main thread | Accept or reject worker results and publish final synchronized status. | `docs/task/ground/g2_content_test_seed/**`, `docs/task/ground/ground_subagent_dispatch_queue_20260521.md`, validation only. |

## Write Scope

Allowed for released G2 workers:

- `G2-A`: `examples/config/database/ground/**`
- `G2-B`: `tests/contracts/unit/ground/**` and one focused test harness file
- `G2-C`: this G2 cluster document, the G2 README, and the ground dispatch queue

Do not edit:

- runtime movement/physics systems
- weapon/effects runtime
- public facade setup schema unless G1 explicitly requires it
- C++ DTO shells, bindings, or scenario-loader behavior

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/leader
```

Add focused ground contract tests once fixture paths exist.

Recommended focused commands:

```bash
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json
python -m pytest -q tests/leader/test_ground_profile_semantics.py
```

## Handoff

Return:

- fixture paths
- task specs added
- tests run
- capability-construction residuals
- blockers for G3 execution-surface design

Worker return packets must include:

```md
Stream:
Status: pass | fail | blocked | preflight-only
Model / reasoning:
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

## G2-C Integration Record

Worker returns:

- `G2-A`: `pass`, `gpt-5.4 / high`; added the first ground content root and
  capability note under `examples/config/database/ground/units/`.
- `G2-B`: `pass`, `gpt-5.4 / high`; added ground starter contracts under
  `tests/contracts/unit/ground/`.

Main-thread integration adjustment:

- Renamed the starter fixture from `ground_platoon_starter.json` to
  `ground_platoon_starter.seed`. The content remains JSON-shaped and validated
  with `python -m json.tool`, but the non-`.json` suffix prevents the current
  runtime database loader from treating the planning seed as a concrete unit
  definition and emitting unknown-type warnings.

Accepted validation:

```bash
python -m json.tool examples/config/database/ground/units/ground_platoon_starter.seed > /tmp/ground_platoon_starter.seed.pretty.json
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
python -m pytest -q tests/leader/test_ground_profile_semantics.py
```

Additional integration evidence:

```bash
python - <<'PY'
from python.testing.runtime import ensure_repo_imports
ensure_repo_imports()
import ef_py
sim = ef_py.SimulationKernel()
print(sim.load_database('examples/config/database'))
PY
```

Result: database loading succeeds without a ground unknown-type warning because
the G2 seed is not auto-loaded as a maintained runtime unit definition.

G3 residuals:

- Select exactly one G4 candidate; do not broaden into runtime movement,
  terrain, sensing, fires, weapon, damage, or combat behavior.
- Decide whether the first execution surface remains tasking-only or adds a
  minimal command/status/report shell.
- If a runtime-loadable ground unit schema becomes necessary, it must be
  introduced through accepted capability-bundle/public-platform seams, not by
  making this planning seed a private ground runtime path.
