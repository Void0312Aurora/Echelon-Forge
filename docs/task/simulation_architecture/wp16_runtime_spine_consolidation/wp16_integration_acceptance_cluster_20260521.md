# WP16-F Integration And Acceptance Handoff

Status: `2026-05-21` complete / accepted integration and acceptance handoff.

Language:

- English canonical: `wp16_integration_acceptance_cluster_20260521.md`
- Chinese companion:
  [wp16_integration_acceptance_cluster_20260521.zh.md](wp16_integration_acceptance_cluster_20260521.zh.md)

Inputs:

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.md)
- WP16-A through WP16-E worker handoffs
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)
- `tools/maintenance/wp_doc_closure_audit.py`

## 1. Purpose

`WP16-F` is the serial publication and acceptance lane. It should run after the
implementation streams become mergeable. Its job is to validate the runtime
spine consolidation, record residuals honestly, sync README/route/review index
documents, and create the acceptance review only when gates pass.

## 2. Scope

In scope:

- collect A-E touched files, tests, blockers, residuals, and integration notes;
- run focused WP16 validation commands;
- confirm `GAP-9` clock-domain enforcement status and residual boundary;
- update README and route status once implementation status is known;
- create final acceptance review and Chinese companion when gates pass;
- keep generated documentation hints separate from acceptance authority.

Out of scope:

- implementing A-E code after workers hand off, except small integration fixes;
- hiding failed or blocked validation;
- claiming global scheduler rewrite, full multi-rate support, or broad legacy
  deletion without evidence.

## 3. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Implementation first | A-E must be mergeable before closure marks WP16 accepted. |
| Exact commands | Acceptance records exact command strings and outcomes. |
| GAP-9 honesty | Clock-domain enforcement claims must name the selected slice and residuals. |
| Generated-doc boundary | Generated summaries may assist closure but cannot accept the WP. |
| Bilingual/index sync | English and Chinese task/review/index docs stay aligned. |

## 4. Validation Commands

Expected closure validation:

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_*.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_execution_episode_batch_prepare.py -k "facade or window or evidence or batch"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16
```

If public facade or binding surfaces are added, include the relevant focused
runtime/binding commands from worker handoffs.

## 5. Handoff Contract

Return:

- final A-E status table;
- exact validation command outcomes;
- `GAP-9` enforcement status and residuals;
- legacy path classification summary;
- generated documentation automation status;
- acceptance review paths if created;
- README/route/index files touched;
- blockers that must remain open if acceptance is not justified.
