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
| `A7-EVC-E Config And Diagnostics` | implementation worker | medium | Add active config, callback/process-probe metrics, and cumulative pre-window hazard. | active configs, diagnostics/callback tests, docs | Learned evidence, doctrine claims | config parse; diagnostics tests | A7 metrics include advantage sign and cumulative early-fire probability. | After D; can parallel with F test refinement only | 2 | pass |
| `A7-EVC-F Focused Validation Sweep` | main thread | n/a | Run compile/JSON/focused tests before learned-policy probe. | evidence note only unless tests require repair | Training, broad refactor | compileall; pytest subset; `git diff --check` | Implementation is ready for short learned evidence. | After C/D/E | 1 | pass |
| `A7-EVC-G Short Learned Evidence` | main thread | n/a | Run short train/probe and compare against A6-EVT-M. | A7 evidence note; no `experiments_tmp` staging | Formal long training, M2 release | train/probe commands; deterministic/stochastic summaries | Evidence records release timing, violations, advantage sign, and cumulative hazard. | After F; serial | 1 | pass; held outcome |
| `A7-EVC-H Closure And Index Sync` | main thread | n/a | Accept, hold, or re-scope A7 and sync parent/A6/issues docs. | A7 docs, parent air-combat README, issue cross-links if needed | Hiding residuals, overclaiming stochastic-only behavior | `git diff --check -- docs/task/air_combat docs/task/issues` | Status and indexes match evidence. | After G; serial | 1 | pass; held sync |
| `A7-EVC-I Target Construction And Credit Sign Audit` | main thread or read-only diagnostics worker | high | Explain why A7 quality-window advantage stays negative, and decide whether target/loss repair is needed before more training. | A7 evidence/status docs | More 32k training, HMoE redesign, M2 release, weakening A3/A5 masks | label reconstruction; code-surface review; docs diff check | Audit names missing shadow-quality target repair after early stochastic accepted release as the failing link. | After H; serial | 2 | pass; spawned J repair |
| `A7-EVC-J Shadow Quality Target Repair` | implementation worker plus read-only diagnostics review | high | Repair target construction so early accepted release does not censor future quality-window evidence from target credit. | `python/rl/policy_algo/first_event_hazard.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, `python/training/diagnostics.py`, focused tests under `tests/hmoe/**` and `tests/training/**`, A7 docs, active config | Runtime legality changes, weakening A3/A5 masks, HMoE redesign, M2 release | focused target-construction tests; compileall; focused PPO/loss tests; docs diff check; short repair probe | Shadow quality evidence is restored after early accepted release, post-release shadow rows are not trained through event-logit delta alignment, and the repair probe records the remaining behavior. | After I; serial before K | 2 | pass; held outcome |
| `A7-EVC-K Legal-State Projection And Coupling Audit` | main thread or diagnostics worker | high | Explain why repaired shadow positives still do not make legal-open quality states learn positive event advantage. | A7 docs first; optional focused diagnostics/tests only after a bounded contract is written | Coefficient-only tuning, more 32k blind training, weakening A3/A5 masks, HMoE redesign, M2 release | label/value/coupling audit; repaired-run probe review; docs diff check | Audit distinguishes target projection, value-head learning, delta alignment, policy distillation, and HMoE-routing hypotheses before another training wave. | After J; serial | 2 | pass; spawned L contract |
| `A7-EVC-L Legal-State Projection Contract` | main thread | high | Select a legal-state projection mechanism that turns shadow-quality evidence into legal-open positive credit without closed-mask delta alignment. | A7 contract/status docs only | Implementation, training, weakening A3/A5 masks, HMoE redesign, M2 release | contract review; docs diff check | Contract names projection whitelist, loss split, implementation entry points, and validation gates. | After K; serial | 1 | pass; implementation not started |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | implementation worker plus diagnostics review | high | Implement the L contract: projected legal-open value/delta alignment for shadow-quality rows, while raw closed-mask rows remain value-only/opportunity-only. | `python/rl/policy_algo/first_event_projection.py`, `python/rl/policy_algo/first_event_hazard.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, focused tests, active config/diagnostics docs | Closed-mask delta alignment, runtime fire-mask weakening, broad HMoE/M2 work, 32k blind training before focused gates | projection helper tests; PPO/loss tests; active config/diagnostics tests; compileall; docs diff check | Projected positives create legal-open credit pressure, unsupported layouts are reported, A3/A5 masks remain authoritative. | After L; serial | 2 | planned next |

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

- `A7-EVC-M Projected Legal-Open Credit Prototype`.

Follow-on:

- Adaptive label scheduling as a guardrail only after the projection prototype
  exposes a remaining bounded weighting issue.
- HMoE hierarchical-computation repair only if A7 learns correct credit signs
  and policy coupling still fails in a hierarchy-attributable way.

Deferred:

- M2, HMoE soft routing, missile authority, `2v2`, self-play, and doctrine.
