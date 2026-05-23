# WP16-D Legacy Path Deprecation And Compatibility Gates

Status: `2026-05-21` complete / legacy compatibility gates accepted.

Language:

- English canonical: `wp16_legacy_deprecation_compatibility_cluster_20260521.md`
- Chinese companion:
  [wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md](wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md)

Inputs:

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.md)
- [WP9 contract and infrastructure closure](../wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)

## 1. Purpose

`WP16-D` turns the inventory into compatibility policy. Legacy paths should not
remain ambiguous: each one must be preserved, wrapped, deprecated, removed, or
restricted to diagnostics-only use with tests and reasons.

## 2. Scope

In scope:

- add guard tests or allowlist updates for known bypass paths;
- classify raw runtime, direct state, legacy spawn, scenario setup, diagnostics,
  and training compatibility paths;
- add deprecation records or runtime warnings where appropriate;
- protect public compatibility APIs until WP16-C proves maintained replacements;
- prevent diagnostics-only paths from becoming maintained silently.

Out of scope:

- broad API removal without replacement evidence;
- scenario-schema migration beyond compatibility gates;
- changing capability or backend/fidelity support semantics;
- creating acceptance reviews.

## 3. Deliverables

- Legacy path status table or machine-readable fixture.
- Guard tests proving diagnostics-only and compatibility boundaries.
- Deprecation records for paths that should be migrated later.
- Removal candidates with replacement evidence and risk notes.

## 4. Gate Rules

| Gate item | Pass condition |
|-----------|----------------|
| Classification | Every legacy path from WP16-A has a bounded status and owner. |
| Replacement evidence | Deprecated or removed paths reference a maintained replacement or a documented reason. |
| Diagnostics isolation | Diagnostics-only paths cannot be called maintained by accident. |
| Compatibility preservation | Public APIs remain available unless removal is explicitly gated and tested. |

## 5. Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_legacy_path_gates.py
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
```

## 6. Handoff Contract

Return:

- touched files;
- legacy classification table or fixture;
- deprecation/removal candidates;
- exact validation commands and outcomes;
- compatibility risks;
- notes for WP16-F.
