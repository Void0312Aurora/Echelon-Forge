# WP20 Public Capability-Platform Composition Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical:
  `wp20_public_capability_platform_composition_acceptance_review_20260521.md`
- Chinese companion:
  [wp20_public_capability_platform_composition_acceptance_review_20260521.zh.md](wp20_public_capability_platform_composition_acceptance_review_20260521.zh.md)

Inputs:

- [WP20 Public Capability-Platform Composition](../simulation_architecture/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.md)
- [WP20-A Public Capability Fact Ledger](../simulation_architecture/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md)
- [WP20-B Public Typed Platform Spawn Contract](../simulation_architecture/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.md)
- [WP20-C Runtime Setup Consume Bridge](../simulation_architecture/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.md)
- [WP20-D Facade And Binding Public Surface](../simulation_architecture/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.md)
- [WP20-E Compatibility And Schema Guard](../simulation_architecture/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.md)
- [WP20-F Integration And Handoff](../simulation_architecture/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.md)
- [WP20 dispatch queue](../simulation_architecture/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.md)

## 1. Verdict

WP20 is accepted as a bounded public capability-platform composition
increment. It publicizes the typed setup path through validation-first
admission/result evidence, keeps `spawn_unit(type_name)` and
`WorldSpawnRequest.type_name` intact, preserves scenario-schema stability, and
keeps backend `RuntimeCapabilities` separate from platform composition
semantics.

No blocking findings were identified. The remaining items are deliberate
residuals, not acceptance blockers.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP20-A Public Capability Fact Ledger` | pass | The fact ledger freezes the source/test inventory for capability contracts, typed setup DTOs, internal resolved plans, and public gaps, and keeps the WP20 seam narrow. |
| `WP20-B Public Typed Platform Spawn Contract` | pass | The public admission/result contract and focused architecture tests define typed platform spawn request evidence without making typed requests mandatory. |
| `WP20-C Runtime Setup Consume Bridge` | pass | Runtime setup consumes validated typed requests through the compatibility-preserving resolved-plan bridge and returns stable result evidence. |
| `WP20-D Facade And Binding Public Surface` | pass | Facade and Python bindings expose `TypedPlatformSpawnResult` and `BatchWorldSetupResult.typed_platform_spawn_results` without changing runtime materialization semantics. |
| `WP20-E Compatibility And Schema Guard` | pass | Architecture/schema/compatibility guards keep scenario schema, backend naming, and type-name compatibility stable while rejecting unsupported drift. |
| `WP20-F Integration And Handoff` | pass | The closure lane integrates A-E evidence, records validation and residuals, syncs indexes, and prepares acceptance only after implementation evidence exists. |

## 3. Validation Rollup

Recorded closure-pass validation:

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_boundary_guards.py tests/architecture/runtime_facade tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py tests/architecture/platform_spawn/test_runtime_setup_consume_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_typed_platform_spawn_bindings.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "typed_platform_setup or world_setup or capability or spawn"
cmake --build build-workshop --target ef_py -j2
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary
```

Observed outcomes:

- `git diff --check`: passed.
- Architecture batch:
  `34 passed in 3.05s`.
- Runtime binding DTO surface batch:
  `26 passed in 0.06s`.
- Runtime facade slice:
  `4 passed, 16 deselected in 0.27s`.
- `cmake --build build-workshop --target ef_py -j2`: passed; `ef_py` built.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP20 --summary`:
  passed, with the WP20 acceptance review recorded and required Chinese
  companions present.

## 4. Residuals

The accepted scope intentionally leaves these items outside WP20:

- `spawn_platform` was not introduced.
- No scenario JSON, example, or Python caller migration was forced.
- Arbitrary capability-bundle materialization remains out of scope.
- Backend `RuntimeCapabilities` remains separate from platform composition
  semantics.
- Type-name compatibility remains maintained.
- WP21 and full counterfactual / experiment runtime remain separate.

## 5. Next Route

If future work needs broader platform publicization, it should start from a
new evidence gate and preserve the compatibility bridge rather than reopening
WP20. Full counterfactual / experiment runtime remains routed to WP21.
