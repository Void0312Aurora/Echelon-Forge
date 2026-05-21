# WP15-F Integration And Acceptance Handoff

Status: `2026-05-21` accepted / serial closure lane complete.

Language:

- English canonical: `wp15_integration_acceptance_cluster_20260521.md`
- Chinese companion:
  [wp15_integration_acceptance_cluster_20260521.zh.md](wp15_integration_acceptance_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- WP15-A through WP15-E worker handoffs
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)
- `tools/maintenance/wp_doc_closure_audit.py`

## 1. Purpose

`WP15-F` is the serial publication and acceptance lane. It ran after the
implementation streams became mergeable. It records exact validation outcomes,
residuals, acceptance status, README/route sync, bilingual closure, and any
remaining blockers without rewriting another worker's code stream.

## 2. Scope

In scope:

- collect A-E touched files, tests, blockers, residuals, and integration notes;
- run focused WP15 validation commands;
- update README and route status once implementation status is known;
- create the final acceptance review and Chinese companion when gates pass;
- keep residuals explicit.

Out of scope:

- implementing A-E code after workers hand off, except small integration fixes;
- hiding failed or blocked validation;
- claiming full snapshot/restore, broad generator runtime, maintained
  counterfactual rollout, or score-to-support promotion.

## 3. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Implementation first | A-E must be mergeable before closure marks WP15 accepted. |
| Exact commands | Acceptance records exact command strings and outcomes. |
| Residual honesty | Any unsupported restore, generator runtime, facade, or binding gaps stay visible. |
| Bilingual/index sync | English and Chinese task/review/index docs stay aligned. |

## 4. Validation Commands

Expected closure validation:

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_*.py
python -m pytest -q tests/scenario/test_wp15_*.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
python tools/maintenance/wp_doc_closure_audit.py --wp WP15
```

If public facade or binding surfaces are added, include the relevant focused
runtime/binding commands from the worker handoffs.

## 5. Handoff Contract

Return:

- final A-E status table;
- exact validation command outcomes;
- residual register;
- acceptance review paths if created;
- README/route/index files touched;
- blockers that must remain open if acceptance is not yet justified.
