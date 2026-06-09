# WP16-B Clock-Domain Enforcement And Merge Trace

Status: `2026-05-21` complete / strict cadence slice accepted.

Language:

- English canonical: `wp16_clock_domain_enforcement_cluster_20260521.md`
- Chinese companion:
  [wp16_clock_domain_enforcement_cluster_20260521.zh.md](wp16_clock_domain_enforcement_cluster_20260521.zh.md)

Inputs:

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)

## 1. Purpose

`WP16-B` implements the first strict `GAP-9` slice. Clock domains in the
selected runtime spine must affect execution: a node whose clock domain has not
fired in the current window must not execute silently. The scheduler/window
coordinator must record whether a node executed, skipped, deferred, or rejected,
and why.

## 2. Scope

In scope:

- add a bounded clock-domain trigger decision helper for the selected
  maintained spine slice;
- support nested trigger evidence such as base tick, declared multiple,
  declared slot, event predicate, or export cadence;
- add skip/defer/reject reason codes and execution evidence for non-triggered
  nodes;
- fail closed for independent clock domains without deterministic
  `clock_merge_policy`, source time, source snapshot, target window, and
  barrier-order metadata;
- add focused tests for triggered, skipped, deferred/rejected, and independent
  merge cases.

Out of scope:

- full global scheduler rewrite;
- hard-real-time execution;
- broad policy/control/physics multi-rate support beyond the selected slice;
- changing facade/batch consumers except for fields needed to expose evidence.

## 3. Deliverables

- Code-owned clock-domain cadence helper or coordinator extension.
- Execution evidence records for `executed`, `skipped`, `deferred`, and
  `rejected` clock-domain decisions.
- Independent-domain merge trace vocabulary or fail-closed rejection reasons.
- Focused architecture/runtime tests for `GAP-9` behavior.

## 4. Gate Rules

| Gate item | Pass condition |
|-----------|----------------|
| Triggered node | A node whose declared clock domain fires in the window executes and records the trigger source. |
| Skipped node | A node whose declared clock domain does not fire is skipped/deferred/rejected with visible evidence. |
| No silent advisory behavior | Tests prove clock-domain fields are no longer decorative for the selected slice. |
| Independent merge | Missing deterministic merge metadata rejects or diagnostics-gates the input. |
| Replay/evidence compatibility | Trigger/skip decisions carry window id, barrier id, source time or reason, and node id. |

## 5. Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_spine/test_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
```

## 6. Handoff Contract

Return:

- touched files;
- selected clock-domain slice;
- helper/API names and evidence fields;
- exact validation commands and outcomes;
- unsupported or deferred cadence cases;
- integration notes for WP16-C and WP16-F.
