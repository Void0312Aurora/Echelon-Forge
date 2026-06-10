# WP20-F Integration And Handoff

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp20_integration_handoff_cluster_20260521.md`
- Chinese companion:
  [wp20_integration_handoff_cluster_20260521.zh.md](wp20_integration_handoff_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- A-E task returns

## Purpose

Integrate WP20 worker results, run validation, record residuals, sync indexes,
and prepare acceptance only after implementation evidence exists.

## Scope

In scope:

- merge and validate A-E changes;
- resolve conflicts between B/C/D contract, runtime, and binding surfaces;
- record compatibility boundaries and residuals for WP21;
- update README/review indexes and bilingual closure docs;
- create acceptance review only after gates pass.

Out of scope:

- first-wave implementation ownership;
- public acceptance from planned docs alone.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `F1` | Merge review | A-E changes are checked for scope, compatibility, and guard consistency. |
| `F2` | Validation rollup | Exact commands and outcomes are recorded. |
| `F3` | Residual routing | Scenario migration, arbitrary bundle materialization, and WP21 dependencies are routed honestly. |
| `F4` | Acceptance prep | README/index sync and acceptance review are prepared only after gates pass. |

## Closure Validation Rollup

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp14_*.py tests/architecture/runtime_facade
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py tests/architecture/platform_spawn/test_runtime_setup_consume_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "typed_platform_setup or world_setup or capability or spawn"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary
```

Observed outcomes:

- `git diff --check`: passed.
- Architecture batch: `34 passed in 3.05s`.
- Runtime binding DTO surface batch: `26 passed in 0.06s`.
- Runtime facade slice: `4 passed, 16 deselected in 0.27s`.
- `cmake --build build-workshop --target ef_py -j2`: passed; `ef_py` built.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary`:
  passed; the WP20 acceptance review and required Chinese companions are
  present.

## Handoff

Acceptance decision: WP20 is accepted as a bounded public capability-platform
composition increment.

Residuals intentionally carried forward:

- no `spawn_platform` surface;
- no forced scenario migration;
- no arbitrary capability-bundle materialization;
- WP21/full counterfactual remains separate;
- type-name compatibility remains maintained.

Return the validation rollup, residual register, and next-route notes; no
blockers remain for WP20 closure.
