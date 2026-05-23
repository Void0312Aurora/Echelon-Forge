# WP17 First-Wave Preflight Recovery

Status: `2026-05-21` historical preflight record; later implementation waves
converted B/C/D/E/F into selected-slice runtime evidence.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP17 dispatch queue](wp17_subagent_dispatch_queue_20260521.md)

## 1. Verdict

The WP17 task family and first-wave task clusters are valid against current code
facts. The first-wave subagents were dispatched and recovered.

The important distinction at preflight time was:

- `WP17-A` and `WP17-B` are implementation-ready after preflight.
- `WP17-C`, `WP17-D`, and `WP17-E` are correctly scoped but not currently
  satisfied by the codebase; they are real implementation streams, not closure
  work.
- `WP17-F` was held for prerequisite evidence from `WP17-C` and `WP17-D`.

Follow-up on `2026-05-21`: subsequent implementation waves satisfied the B/C/D/E
selected-slice gates and released a narrowed F runtime slice. The original
preflight verdict below is retained as historical context, not current task
status.

## 2. Recovered Results

| Stream | Result | Meaning |
|--------|--------|---------|
| `WP17-A Fact Ledger And Boundary Freeze` | `pass` | The six current code facts in the WP17 main plan are accurate. Current `RuntimeFacade::capabilities()` is not empty, but it is still static metadata rather than provider negotiation. |
| `WP17-B Facade Business Migration And Compatibility Cleanup` | `pass` | Maintained business code already uses adapter/facade-shaped paths; remaining direct `vec_env.batch_runtime` ready/state reads are mainly in tests and should be migrated or guarded. |
| `WP17-C Multi-Rate Runtime Example` | historical preflight gap | The §8 10Hz/20Hz/60Hz example needed selected-slice cadence DTOs/traces, runtime-window planning, `hold_last`, expiry evidence, and a helper that does not flip global `kWp10ClockDomainAdvisoryOnly`. |
| `WP17-D Fidelity Provider Runtime` | historical preflight gap | Contract-level fidelity request/admission helpers existed, but `RuntimeFacade` still needed a facade-owned request/admission/provider-selection method. |
| `WP17-E Capability Spawn Runtime Promotion` | historical preflight gap | `CapabilityBundle`, `ResolvedPlatformSpawnPlan`, bindings, and internal factory resolution existed, but `DefaultUnitFactory::spawn()` still needed to consume the resolved plan before materialization. |

## 3. Next Implementation Order

Recommended order after this planning pass:

1. Implement `WP17-B` first. It is the smallest business cleanup and narrows
   compatibility-only `batch_runtime` use before larger runtime streams start.
2. Start `WP17-C` and `WP17-D` as separate implementation streams after B or in
   parallel if write scopes remain disjoint. Do not claim runnable multi-rate or
   provider-selection support until their selected-slice tests pass.
3. Start `WP17-E` independently after confirming whether spawn evidence should
   be stored on the factory, entity metadata, or a diagnostic query surface.
4. Hold `WP17-F` until C has deterministic cadence/barrier evidence and D names
   the profile/provider scope used by snapshot support.

Current follow-up: that release condition has been satisfied for the narrow
explicit-setup selected-entity branch/compare API. Broad counterfactual
orchestration remains out of scope.

## 4. Guardrails From Preflight

- Do not flip `kWp10ClockDomainAdvisoryOnly` globally to pass WP17-C.
- Do not treat module-level fidelity helper bindings as facade-owned runtime
  admission.
- Do not introduce public `spawn_platform` or route `TypedPlatformSpawnRequest`
  into the maintained mainline before the additive boundary changes.
- Do not delete `WorldBatchRuntime`, `RuntimeFacade.runtime()`, or
  `batch_runtime` during the first cleanup slice.
- Do not claim counterfactual restore or rollout while
  `snapshot_restore_supported` remains fail-closed.

## 5. Validation Already Reported By Workers

Reported passing checks included:

```bash
python -m pytest -q tests/runtime/facade/test_runtime_facade.py tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp14_boundary_guards.py tests/architecture/test_wp16_legacy_path_gates.py
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
python -m pytest -q tests/architecture/test_wp16_legacy_path_gates.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "compatibility_view or execution_episode_controller_mainline or shadow_compare"
python -m pytest -q tests/architecture/test_wp16_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capabilities or fidelity"
python -m pytest -q tests/test_gpu_runtime_bindings.py -k "capabilities or fidelity"
```

One reported blocker was environmental rather than semantic:

```text
tests/architecture/test_wp14_*.py compile-style checks: missing spdlog/spdlog.h
from hard-coded build-local-win include paths in the current environment.
```
