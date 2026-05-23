# WP21-D Scenario Intervention Generation Runtime

Status: `2026-05-21` planned; may run after WP21-A in parallel with B.

Language:

- English canonical: `wp21_scenario_intervention_generation_cluster_20260521.md`
- Chinese companion:
  [wp21_scenario_intervention_generation_cluster_20260521.zh.md](wp21_scenario_intervention_generation_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP15 scenario and adversary request surface](../wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.md)
- [WP18 ScenarioLoader adapter split](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.md)

## Purpose

Turn the WP15 generation request surface into a deterministic runtime-adjacent
generator that produces admitted artifacts for counterfactual experiments
without directly mutating authoritative simulation state.

## Scope

In scope:

- first maintained generator for parameter variation such as starting distance,
  altitude, speed, selected platform setup, or intervention metadata;
- versioned artifact output with seed, lineage, evidence refs, and baseline
  scenario/setup refs;
- non-mutation guard proving generated artifacts enter runtime only through
  setup/admission paths;
- `ScenarioLoader` mirror pre-gate or adapter boundary if generator integration
  would otherwise rely on loader-owned runtime state.

Out of scope:

- adversarial search, curriculum optimization, or learned scenario generation;
- changing public scenario schemas by default;
- direct runtime state writes.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `D1` | Deterministic generator | Same request, version, and seed produce the same artifact. |
| `D2` | Artifact lineage | Artifact records baseline scenario/setup, replay envelope, branch point, generator version, and evidence refs. |
| `D3` | Runtime admission seam | Generated artifact can feed setup/admission without bypassing facade authority. |
| `D4` | Loader boundary guard | Scenario/content adaptation remains distinct from maintained runtime state ownership. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario/test_wp15_generation_request_surface.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario -k "generation or scenario_loader"
```

## Handoff

Return generator API, artifact schema, non-mutation evidence, loader boundary
notes, touched files, commands run, and E-facing experiment input notes.
