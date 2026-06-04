# A7 Event-Value / Advantage Credit Head Task Clusters

Status: `2026-06-04` finite task-cluster plan for
[README.md](README.md).

## Boundary Decision

A7 may add an event-value / advantage-credit head and auxiliary objective for
the masked `hold/fire_once` event action. It must not weaken A3/A5 legal masks,
turn L label-weight scheduling into the main fix, redesign HMoE, release M2, or
claim missile/real-doctrine authority.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-A Evidence And Architecture Intake` | main thread or read-only diagnostics worker | high | Reconcile A6-N, A6 label-density issue, HMoE gap, and current policy/PPO code entry points. | A7 docs only; optional issue cross-links | Code changes, training, HMoE redesign | Markdown review; code-surface references | Intake names what A7 must solve and what HMoE gap can only influence. | First; serial before B | 1 | pass |
| `A7-EVC-B Objective Contract` | main thread | high | Define value/advantage targets, target source, losses, diagnostics, and rollback gates. | A7 contract/status docs | L-only tuning, M2 release, runtime legality changes | Contract review against A3/A5/A6-N | Contract is specific enough for implementation and rejects unsupported labels. | After A; serial before C/D | 2 | pass |
| `A7-EVC-C Policy Head Prototype` | main thread plus read-only subagent review | high | Add a bounded event-value or advantage head and expose its outputs. | `python/rl/policy_algo/policies.py`, focused policy tests | HMoE family/subexpert redesign, soft routing, M2 | focused policy tests; serialization/load smoke | Head is zero-safe, shape-stable, optimizer-visible, and can be coupled to event logits. | Completed before D; API stable for PPO coupling. | 2 | pass |
| `A7-EVC-D PPO Auxiliary Credit` | main thread plus read-only subagent scan | high | Train A7 head and connect advantage credit to event-logit delta. | `python/rl/policy_algo/**`, rollout/loss tests | Reward-only legality, weakening masks | focused PPO/loss tests; finite stats | Loss handles masks, early censoring, and counterfactual targets. | Completed before E; no learned-policy run yet. | 2 | pass |
| `A7-EVC-E Config And Diagnostics` | future implementation worker | medium | Add active config, callback/process-probe metrics, and cumulative pre-window hazard. | active configs, diagnostics/callback tests, docs | Learned evidence, doctrine claims | config parse; diagnostics tests | A7 metrics include advantage sign and cumulative early-fire probability. | After D; can parallel with F test refinement only | 2 | planned next |
| `A7-EVC-F Focused Validation Sweep` | main thread | n/a | Run compile/JSON/focused tests before learned-policy probe. | evidence note only unless tests require repair | Training, broad refactor | compileall; pytest subset; `git diff --check` | Implementation is ready for short learned evidence. | After C/D/E | 1 | planned |
| `A7-EVC-G Short Learned Evidence` | main thread | n/a | Run short train/probe and compare against A6-EVT-M. | A7 evidence note; no `experiments_tmp` staging | Formal long training, M2 release | train/probe commands; deterministic/stochastic summaries | Evidence records release timing, violations, advantage sign, and cumulative hazard. | After F; serial | 1 | planned |
| `A7-EVC-H Closure And Index Sync` | main thread | n/a | Accept, hold, or re-scope A7 and sync parent/A6/issues docs. | A7 docs, parent air-combat README, issue cross-links if needed | Hiding residuals, overclaiming stochastic-only behavior | `git diff --check -- docs/task/air_combat docs/task/issues` | Status and indexes match evidence. | After G; serial | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Dispatch implementation only from `A7-EVC-C` or later; `A7-EVC-B` is closed by
  the objective contract.
- Do not allow concurrent edits to the same policy-loss surface or status table.
- HMoE gap work is read-only in A7 unless a separate issue-board implementation
  task is created.
- `experiments_tmp` is never staged.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  wave.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Docs-only gate:

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

Implementation gates must include focused policy/PPO tests, active-entry/config
tests, diagnostics tests, JSON parsing, compileall for touched Python files, and
a learned-policy probe before acceptance.

## Acceptance Criteria

- A7 objective directly gives counterfactual hold/fire credit under A5 masks.
- Deterministic learned evidence fires once inside the configured quality
  window.
- Stochastic early-fire cumulative probability is bounded and reported.
- A3/A5 legality and one-shot discipline remain intact.
- HMoE gap is considered without turning A7 into an HMoE redesign.

## Residual Map

Immediate:

- Active config and diagnostics for the focused A7 credit loss.

Follow-on:

- Adaptive label scheduling as a guardrail if value credit works but training is
  unstable.
- HMoE hierarchical-computation repair only if A7 evidence makes it an active
  blocker.

Deferred:

- M2, HMoE soft routing, missile authority, `2v2`, self-play, and doctrine.
