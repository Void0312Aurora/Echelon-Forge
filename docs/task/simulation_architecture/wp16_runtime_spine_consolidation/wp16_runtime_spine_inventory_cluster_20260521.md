# WP16-A Runtime Spine Inventory And Bypass Map

Status: `2026-05-21` complete / inventory and bypass map accepted.

Language:

- English canonical: `wp16_runtime_spine_inventory_cluster_20260521.md`
- Chinese companion:
  [wp16_runtime_spine_inventory_cluster_20260521.zh.md](wp16_runtime_spine_inventory_cluster_20260521.zh.md)

Inputs:

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)

## 1. Purpose

`WP16-A` creates the shared map that the rest of WP16 depends on. It inventories
which paths already follow the accepted runtime spine and which paths still
bypass it through raw runtime access, direct ECS/state mutation, compatibility
wrappers, diagnostics-only helpers, legacy spawn, scenario setup, training
adapters, or experiment scaffolding.

## 2. Scope

In scope:

- inspect runtime facade, runtime window coordinator, world-batch runtime,
  Python RL adapters, scenario compiler/runtime, training helpers, experiment
  evidence surfaces, spawn/setup paths, and diagnostics exports;
- classify each path as `maintained_spine`, `compatibility_wrapper`,
  `diagnostics_only`, `deprecated_candidate`, `blocked`, or `unknown_requires_owner`;
- identify the selected spine slice for WP16-B/C implementation;
- name the exact node ids, barrier ids, facade APIs, Python adapters, and tests
  that later streams must use.

Out of scope:

- implementing clock-domain enforcement;
- migrating facade or batch consumers;
- deleting legacy APIs;
- creating acceptance review files.

## 3. Deliverables

- A code- or fixture-backed bypass inventory under the owning stream's chosen
  location.
- A maintained runtime-spine definition naming setup/admission, input injection,
  manifest nodes, clock-domain cadence, barrier/event evidence, facade export,
  and downstream consumer evidence.
- A residual list for paths that cannot yet be classified safely.
- Focused tests or audit fixtures proving the inventory covers the maintained
  files selected by this phase.

## 4. Gate Rules

| Gate item | Pass condition |
|-----------|----------------|
| Coverage | Runtime/facade/batch/scenario/training/experiment/spawn/replay/diagnostics paths touched by WP10-WP15 are explicitly classified. |
| Ownership | Each non-maintained path has an owner, next gate, or reason for retention. |
| No hidden bypass | Unknown paths are not treated as maintained by default. |
| GAP-9 handoff | Selected clock-domain slice and manifest nodes are named for WP16-B. |

## 5. Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_runtime_spine_inventory.py
```

If the worker implements an audit tool instead of a test, return the exact
command and output summary.

## 6. Handoff Contract

Return:

- touched files;
- inventory path and classification vocabulary;
- selected WP16-B/C spine slice;
- exact commands run and outcomes;
- blockers and residual paths;
- notes for streams B, C, D, and E.
