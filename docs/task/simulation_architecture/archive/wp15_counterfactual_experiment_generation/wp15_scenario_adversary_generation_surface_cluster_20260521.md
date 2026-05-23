# WP15-D Scenario And Adversary Generation Request Surface

Status: `2026-05-21` mergeable / first slice complete.

Language:

- English canonical: `wp15_scenario_adversary_generation_surface_cluster_20260521.md`
- Chinese companion:
  [wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md](wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)
- Current `python/scenario/compiler/*`
- Current `python/scenario/runtime/*`
- Current `tests/scenario/test_scenario_compiler.py`

## 1. Purpose

`WP15-D` creates the request surface for generated scenarios and adversaries.
The output should be deterministic, source-attributed, seed/version disciplined,
and safe to treat as experiment input evidence. It must not become a runtime
backdoor for mutating authoritative simulation state.

## 2. Scope

In scope:

- scenario/adversary generation request and validation vocabulary;
- deterministic seed, generator version, source, baseline scenario, branch
  point or replay refs, and capability/evidence refs;
- request kinds such as scenario variation, adversary placement, route/mission
  perturbation, and stressor injection as metadata;
- compiler/runtime guard tests proving generated inputs remain explicit
  requests or scenario artifacts;
- deterministic fixtures that can feed later experiment evidence.

Out of scope:

- broad generator algorithm implementation;
- direct runtime state mutation;
- changing existing scenario JSON compatibility;
- claiming generated scenarios are maintained truth or capability support.

## 3. Candidate Implementation Seams

Inspect before editing:

- `python/scenario/compiler/service.py`
- `python/scenario/compiler/clone.py`
- `python/scenario/runtime/models.py`
- `tests/scenario/test_scenario_compiler.py`
- `docs/task/simulation_architecture/wp8_learning_face/*scenario*`

Preferred approach:

- add a small Python request/validation module rather than editing the entire
  scenario compiler;
- keep generated output as data plus evidence metadata;
- include deterministic seed/version checks;
- make unsupported request kinds fail closed with stable reasons.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Seed discipline | Request must name deterministic seed and generator version. |
| Source attribution | Request must name source, baseline scenario, and evidence refs. |
| Non-mutation | Generated request artifacts do not mutate runtime state directly. |
| Compatibility | Existing scenario compiler/runtime behavior remains compatible. |

## 5. Acceptance Tests

Minimum tests:

- valid scenario/adversary request fixture validates deterministically;
- missing seed, generator version, source, baseline scenario, or evidence refs
  rejects with stable reasons;
- unsupported generation kind fails closed;
- existing scenario compiler branch/runtime isolation tests still pass.

Suggested commands:

```bash
git diff --check
python -m pytest -q tests/scenario/test_wp15_generation_request_surface.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
```

## 6. Handoff Contract

Return:

- Python files touched;
- request field names and validation helpers;
- rejection reason vocabulary;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP15-E`.
