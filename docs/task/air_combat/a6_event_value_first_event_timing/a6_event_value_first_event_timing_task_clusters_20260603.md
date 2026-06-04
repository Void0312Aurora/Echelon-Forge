# A6 Event Value And First-Event Timing Task Clusters

Status: `2026-06-04` finite task-cluster plan for
[README.md](README.md), re-scoped through root-cause analysis after the
launch-window short learned evidence.

## Boundary Decision

A6 may change the policy/training objective for the masked `hold/fire_once`
event, but it may not weaken A3/A5 legality constraints, release M2, or treat
reward-only penalties as the main fix. The first accepted implementation must
directly address event-value or first-event timing.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A6-EVT-A Observation Baseline` | main thread | n/a | Create A6 and freeze retained A5 deterministic/stochastic evidence. | `docs/task/air_combat/a6_event_value_first_event_timing/**`, parent air-combat READMEs | Code changes, new training, staging `experiments_tmp` | `jq` summaries; `git diff --check -- docs/task/air_combat` | A6 docs exist and observation explains why A6 is not reward-only tuning. | First; serial | 1 | pass |
| `A6-EVT-B Mathematical Framing` | Arendt | inherited, high | Formalize masked first-event timing, delayed sparse credit, label sources, and failure modes. | A6 design note under this subproject | PPO implementation, scenario rewrites, M2 | Markdown inspection; link check | Design names objective inputs/outputs and rejects impossible labels. | After A; can run before C only | 2 | pass |
| `A6-EVT-C Objective Contract` | Arendt | inherited, high | Select the first contract: event-value head, hazard objective, curriculum-assisted labels, or staged combination. | A6 contract note only; main thread owns status/index integration after return | Broad reward penalty tuning, removing masks, sequence PPO | Contract review against A3/A5 constraints | Chosen objective has masks, diagnostics, tests, and rollback criteria. | After B; serial before D/E | 2 | pass |
| `A6-EVT-D Training Kernel Prototype` | Arendt | inherited, high | Implement the selected masked first-event hazard auxiliary loss with policy/PPO tests. | `python/rl/policy_algo/**`, focused training/policy tests | M2, self-play, missile physics, config/probe/callback integration, broad PPO rewrite beyond selected objective | Focused policy/PPO tests | Tests prove shape, loss, mask, deterministic eval, finite stats, and unchanged masked categorical semantics. | After C; serial before E until field/loss interface is stable | 2 | pass |
| `A6-EVT-E Scenario Config And Diagnostics` | Arendt + main thread | inherited, medium | Wire the maintained S1 C2/ROE training entry and diagnostics for A6 metrics. | `examples/config/training/active/air_combat/**`, `tools/diagnostics/**`, `python/training_callbacks.py`, `python/rl/runtime/world_batch_vec_env.py`, related tests | New scenario maturity claims, legality via reward penalties | Active-entry, diagnostics, non-finite probe parity, world-batch info tests | A6 metrics are visible and A3/A5 legality remains mask/state-owned. | After D exposes field/loss interface | 2 | pass |
| `A6-EVT-F Short Learned Evidence` | main thread | n/a | Run short training/probe against A5 baseline and record outcomes. | A6 evidence note; no `experiments_tmp` staging | Formal long training, M2 release | Training command plus deterministic/stochastic probes | Evidence records event probability/mode, requests, releases, violations, and blocker status. | After D/E tests pass; serial | 1 | pass; held outcome |
| `A6-EVT-G Closure And Index Sync` | main thread | n/a | Accept, hold, or re-scope A6 and sync A3/A4/A5/M1/M2/parent indexes. | A6 docs, parent air-combat READMEs, affected model docs if needed | Hiding residuals, accepting stochastic-only behavior | `git diff --check`; focused doc/link inspection | Status and indexes are consistent with evidence. | After F; serial | 1 | pass; re-scoped |
| `A6-EVT-H Deadline Bootstrap Implementation` | main thread | n/a | Add sustained deadline labels and a separate probe entry for the next A6 wave. | `python/rl/policy_algo/**`, `python/rl/support/nonfinite_probe.py`, `python/training_callbacks.py`, active config README/JSON, focused tests, A6 docs | M2 release, reward-only legality, weakening A5 masks, changing missile/damage authority | compileall; focused A6/config/diagnostics tests | Deadline source/weight/config/logging are covered; old hazard evidence config remains separate. | After G; serial before I | 1 | pass |
| `A6-EVT-I Deadline Short Learned Evidence` | main thread | n/a | Run deadline short train/probe and record deterministic/stochastic outcomes. | A6 evidence note; no `experiments_tmp` staging | Formal long training, accepting fixed-age teacher as doctrine | Training command plus deterministic/stochastic probes | Evidence records event probability/mode, requests, releases, violations, and whether deadline bootstrap is accepted or held. | After H tests pass; serial | 1 | pass; held outcome |
| `A6-EVT-J Event-Head Update-Strength Audit` | main thread | n/a | Determine why sustained positive labels only move event probability to about `0.5%`. | `tests/hmoe/test_a6_event_head_update_strength.py`, A6 evidence note | M2 release, value-head implementation before update audit, reward-only legality | focused gradient/update probe; no learned-policy acceptance from unit probe alone | Audit identifies optimizer/head scaling blocker or clears path to event-value head. | After I; serial | 1 | pass; held outcome |
| `A6-EVT-K Event-Head Optimization Lane` | main thread | n/a | Add a bounded stronger update path for `hold/fire_once` event rows and diagnostics. | `python/rl/policy_algo/**`, focused tests, A6 docs/config if needed | M2 release, weakening masks, broad reward-only legality, missile/damage authority | compileall; focused policy/PPO tests; short learned probe | Event-row LR/diagnostics are visible and learned evidence shows either deterministic crossing or a precise held residual. | After J; serial before event-value head | 2 | pass; held timing residual |
| `A6-EVT-L Launch-Window Timing Contract` | main thread | n/a | Define and implement a bounded timing-quality contract that separates legal authorization from good first-release timing. | `python/rl/policy_algo/**`, `python/rl/support/nonfinite_probe.py`, `python/training_callbacks.py`, focused tests, active config, A6 docs | M2 release, missile/damage authority, real doctrine claims, weakening A3/A5 masks | compileall; JSON parse; focused label/PPO/config/diagnostics tests | Contract names label source, window predicates, rejection handling, diagnostics, and acceptance/rollback gates; implementation is covered by focused tests. | After K; serial before learned evidence | 2 | pass |
| `A6-EVT-M Launch-Window Short Learned Evidence` | main thread | n/a | Run the L active config and compare timing/release discipline against A6-EVT-K. | A6 evidence note only; no `experiments_tmp` staging | Formal long training, M2 release, treating L range gate as doctrine | Training command plus deterministic/stochastic probes | Evidence records release step, launch-window counts, requests, accepted/rejected releases, violations, and whether L is accepted or re-scoped. | After L; serial | 1 | pass; held outcome |
| `A6-EVT-N Root-Cause Re-scope` | main thread | n/a | Pause L tuning and explain the mechanism blocker behind the held launch-window evidence. | A6 analysis/status/README/dispatch docs only | New training, L parameter search, code/config changes, M2 release, weakening A3/A5 masks | Markdown inspection; `git diff --check -- docs/task/air_combat/a6_event_value_first_event_timing` | Root-cause note identifies whether the blocker is tuning, missing labels, optimizer routing, stochastic censoring, or value credit. | After M; serial before O | 1 | pass; training paused |
| `A6-EVT-O Counterfactual Event-Time Objective` | main thread | high | Define the next objective contract that gives explicit hold-vs-fire credit and prevents early stochastic censoring from erasing quality-window targets. | A7 docs now carry the contract | L knob tuning, runtime legality changes, M2 release, missile authority, `2v2`, self-play | A7 objective-contract review | Contract selects labels/losses/diagnostics/rollback gates before implementation. | After N; transferred to A7 | 2 | moved to A7 |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not let two workers edit the same normative table, status line, scenario
  contract, or policy-loss surface concurrently.
- Keep `A6-EVT-C`, `A6-EVT-F`, and `A6-EVT-G` serial.
- Do not dispatch implementation before `A6-EVT-C Objective Contract` closes.
- Do not run `A6-EVT-M` until `A6-EVT-L` focused tests pass.
- Do not run more L training or tune L weights after `A6-EVT-N`; continue the
  counterfactual objective through
  [A7](../a7_event_value_advantage_credit_head/README.md).
- Do not dispatch A7 implementation until its objective contract names labels,
  counterfactual target source, stochastic collection handling, and cumulative
  hazard diagnostics.
- If a cluster exceeds its round cap, stop and re-scope before adding a new
  wave.
- Follow
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

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

Initial docs-only gate:

```bash
git diff --check -- docs/task/air_combat
```

Implementation gates will be defined by `A6-EVT-C`, but must include focused
policy/PPO tests, active-entry/config tests, diagnostics tests, and at least one
short learned-policy probe.

Post-N implementation gates are defined by the active objective contract. Any
new training wave must include cumulative pre-window hazard reporting in
addition to deterministic/stochastic release discipline.

## Acceptance Criteria

- The selected objective directly moves masked event timing, not raw
  `fire_weapon` thresholding.
- A3/A5 legality remains owned by mask/state transitions.
- Deterministic learned evidence improves materially over the A5 baseline or
  the residual is precisely assigned outside reward-only legality tuning.
- M2 and broader combat maturity claims remain held.

## Residual Map

Immediate:

- L tuning and additional short training are paused.
- A7 must define counterfactual event-time/value credit and cumulative
  early-fire diagnostics before implementation.

Follow-on:

- Event-value / advantage head or survival-style event-time objective if O
  selects it.

Deferred:

- M2 sequence-native PPO/HMoE.
- `2v2`, self-play, missile physics, Pk, fuze, and damage authority.
