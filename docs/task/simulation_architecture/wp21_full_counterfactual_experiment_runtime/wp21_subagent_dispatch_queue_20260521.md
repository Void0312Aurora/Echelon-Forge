# WP21 Subagent Dispatch Queue

Status: `2026-05-21` planned / ready for first-wave dispatch.

Language:

- English canonical: `wp21_subagent_dispatch_queue_20260521.md`
- Chinese companion:
  [wp21_subagent_dispatch_queue_20260521.zh.md](wp21_subagent_dispatch_queue_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Queue

| Stream | Dependency | Dispatch status | Write scope |
|--------|------------|-----------------|-------------|
| `WP21-A Fact Ledger And Residual Freeze` | none | ready | Docs only: source-backed fact ledger and final residual register. |
| `WP21-B Snapshot Restore And Worldline Boundary` | A readiness | queued after A | Snapshot/restore DTO/runtime/facade tests. No experiment orchestration. |
| `WP21-D Scenario Intervention Generation Runtime` | A readiness | queued after A | Python scenario/intervention generator, artifacts, non-mutation tests. No C++ rollout. |
| `WP21-C Counterfactual Rollout And Causal Difference` | B | queued after B | Parent/branch execution and causal-difference runtime. |
| `WP21-E Experiment Facade And Evidence Collection` | C and D | queued after C/D | Experiment facade/binding/evidence collection and ancestry tests. |
| `WP21-F Final Cleanup And Acceptance Handoff` | A-E | serial closure | Integration, validation rollup, final residual closure, indexes, acceptance review. |

## First-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-A` | `gpt-5.4-mini`, xhigh | Produce the source-backed fact ledger and residual register. Edit only WP21-A docs unless a broken link blocks planning. |

## Second-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-B` | `gpt-5.4`, xhigh | Implement the bounded snapshot/restore and worldline boundary after A. Own runtime/facade/binding tests for the boundary; do not implement experiment orchestration. |
| `WP21-D` | `gpt-5.4`, high | Implement deterministic scenario/intervention generation after A. Own Python/scenario tests and loader boundary guards; do not edit C++ rollout. |

## Third-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-C` | `gpt-5.4`, xhigh | Implement parent/branch rollout and causal-difference runtime after B. Consume B's boundary and keep scenario generation untouched. |
| `WP21-E` | `gpt-5.4`, xhigh | Implement experiment facade/evidence collection after C/D. Own public surface, bindings, ancestry, and non-truth-claim tests. |

## Closure-Wave Dispatch

| Stream | Suggested model / reasoning | Dispatch packet |
|--------|-----------------------------|-----------------|
| `WP21-F` | `gpt-5.4-mini`, xhigh | Serial closure after A-E: validation rollup, residual closure, README/review sync, bilingual companions, and final acceptance review. |

## Worker Return Packet

Every worker must return:

- status: `pass`, `blocked`, or `preflight-only`;
- touched files;
- validation commands and outcomes;
- blockers and residuals;
- integration notes for the next stream;
- closure impact;
- confirmation that unrelated edits were not reverted.

## Stop Rules

- Do not promote exact GPU or resident-state support.
- Do not treat experiment outputs as truth/support claims.
- Do not mutate authoritative runtime state outside facade/request contracts.
- Do not force scenario schema migration.
- Stop at a named blocker rather than reopening earlier accepted stages.
