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
| `A7-EVC-L Legal-State Projection Contract` | main thread | high | Select a legal-state projection mechanism that turns shadow-quality evidence into legal-open positive credit without closed-mask delta alignment. | A7 contract/status docs only | Implementation, training, weakening A3/A5 masks, HMoE redesign, M2 release | contract review; docs diff check | Contract names projection whitelist, loss split, implementation entry points, and validation gates. | After K; serial | 1 | pass; implemented by M |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | implementation worker plus diagnostics review | high | Implement the L contract: projected legal-open value/delta alignment for shadow-quality rows, while raw closed-mask rows remain value-only/opportunity-only. | `python/rl/policy_algo/first_event_projection.py`, `python/rl/policy_algo/first_event_hazard.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, focused tests, active config/diagnostics docs | Closed-mask delta alignment, runtime fire-mask weakening, broad HMoE/M2 work, 32k blind training before focused gates | projection helper tests; PPO/loss tests; active config/diagnostics tests; compileall; docs diff check | Projected positives create legal-open credit pressure, unsupported layouts are reported, A3/A5 masks remain authoritative. | After L; serial | 2 | pass; N held learned behavior |
| `A7-EVC-N Short Projection Learned Evidence` | main thread | n/a | Run a bounded learned-policy probe after M and compare projected-credit behavior against J repair evidence. | A7 evidence/status docs; no `experiments_tmp` staging | Formal long training, M2 release, HMoE redesign, missile/doctrine authority | train/probe commands; deterministic/stochastic summaries; projection metrics; docs diff check | Evidence records whether projected credit changes deterministic timing, stochastic early-fire, one-shot discipline, and projected advantage/delta signs. | After M; serial | 1 | pass; held outcome |
| `A7-EVC-O Projection Eligibility Root-Cause Audit` | main thread or diagnostics worker | high | Explain why `a7/evc_proj_active_count_mean` remains `0.0` in the learned run despite projection being enabled and focused projected-loss tests passing. | A7 docs first; optional focused diagnostics/tests after the failing handoff is isolated | More blind 32k training, coefficient tuning, weakening A3/A5 masks, HMoE redesign, M2 release | TensorBoard/probe review; rollout/loss label-source audit; focused test only for confirmed interface gap; docs diff check | Audit names candidate starvation: N train diagnostics have no accepted releases, while stochastic probe reconstruction produces shadow candidates after early release. | After N; serial | 2 | pass; spawned P contract |
| `A7-EVC-P Legal-Open Opportunity Credit Contract` | main thread | high | Define positive legal-open opportunity credit that does not depend on sampling an early accepted release. | A7 contract/status docs | Implementation, training, weakening A3/A5 masks, closed-mask delta alignment, HMoE redesign, M2 release | contract review; docs diff check | Contract selects target source, loss split, diagnostics, and rollback gates for a non-starved opportunity-credit path. | After O; serial | 1 | pass; spawned Q prototype |
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | implementation worker plus diagnostics review | high | Implement the P contract by adding direct legal-open quality-window positives before early-release sampling is required. | `python/rl/policy_algo/first_event_hazard.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, `python/rl/support/nonfinite_probe.py`, focused tests, active config/diagnostics docs | Broad reward tuning, weakening A3/A5 masks, raw shadow delta alignment, HMoE redesign, M2 release, training before focused gates | source-construction tests; PPO/loss tests; nonfinite-probe metric test; active config/diagnostics tests; compileall; docs diff check | Legal-open quality positives reach ordinary A7 value/delta credit, shadow projection remains separate, and source metrics prove the path is not candidate-starved. | After P; serial | 2 | pass; spawned R learned evidence |
| `A7-EVC-R Short Opportunity Learned Evidence` | main thread | n/a | Run a bounded learned-policy probe after Q and compare legal-open opportunity behavior against N. | A7 evidence/status docs; no `experiments_tmp` staging | Formal long training, M2 release, HMoE redesign, missile/doctrine authority | train/probe commands; deterministic/stochastic summaries; legal-open source metrics; docs diff check | Evidence records whether non-starved legal-open opportunity credit changes timing while preserving one-shot legality. | After Q; serial | 1 | pass; held outcome |
| `A7-EVC-S Explicit State Completion Probe` | main thread plus implementation worker | high | Test whether missing explicit Markov state, especially legal/window age and readiness, explains the held R outcome before M2 release. | mission observation taxonomy/builders, state-completion reset hooks, field-name-based policy/PPO consumers, focused tests, active config, A7 docs | M2 release, HMoE redesign, coefficient-only tuning, weakening A3/A5 masks, doctrine/missile authority | v2 observation tests; focused HMoE/PPO/active-entry tests; 32k train/probe summaries; diff check | Probe shows observability improves and open-window probability rises, but deterministic remains `hold` and quality-window advantage remains negative. | After R; serial | 2 | pass; held outcome |
| `A7-EVC-T Value/Policy Coupling Audit` | main thread or diagnostics worker | high | Explain why non-starved visible positives move event-fire probability but not learned advantage sign or deterministic event mode. | A7 docs plus focused diagnostic script | Blind coefficient run, formal long training, weakening A3/A5 masks, HMoE redesign, M2 release | fixed-batch offline fit probe; compileall; docs diff check | Audit verifies the breakpoint: labels/state/credit-head capacity are locally sufficient, and the residual fault is online update-path coupling. | After S; serial | 2 | pass; spawned U |
| `A7-EVC-U Online Update-Path Isolation` | main thread or diagnostics worker | high | Isolate why a credit-head-separable fixed batch does not survive online PPO/shared/event-head training. | `tools/diagnostics/a7_online_update_path_probe.py`, A7 docs | Blind coefficient run, formal long training, weakening A3/A5 masks, HMoE redesign, M2 release | gradient-norm/parameter-drift audit; compileall; TensorBoard scalar review; docs diff check | Names the blocker as shared PPO global clipping plus shared actor/feature coupling; direct PPO credit-head overwrite is excluded. | After T; serial | 2 | pass; spawned V contract |
| `A7-EVC-V Online Credit Update Contract` | main thread | high | Implement the repair contract that decouples A7 value credit from shared PPO clipping and representation drift. | `python/rl/policy_algo/policies.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, `python/rl/support/nonfinite_probe.py`, active configs, focused tests, A7 docs | Coefficient-only tuning, formal long training, weakening A3/A5 masks, HMoE redesign, M2 release | compileall; focused HMoE/PPO/config tests; 8k train/probe observation; docs diff check | Separate credit-head-only value update, protected clip budget, positive-only delta alignment, and nonfinite-probe parity are proven; learned behavior remains held. | After U; serial | 2 | pass; held outcome |
| `A7-EVC-W Active Update Window Diagnosis` | main thread or diagnostics worker | high | Explain why protected A7 credit updates become inactive or insufficient after early training even when legal-open positives exist. | A7 docs first; optional diagnostics script/tests after the failing window handoff is isolated | Blind coefficient run, formal long training, weakening A3/A5 masks, HMoE redesign, M2 release | TensorBoard/update-window review; fixed-batch vs on-policy sample audit; docs diff check | Names whether the remaining blocker is curriculum sampling, replay/fixed positive batches, adaptive label scheduling, or a broader training-loop contract. | After V; serial | 2 | planned next |

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

- `A7-EVC-W Active Update Window Diagnosis`.

Follow-on:

- Adaptive label scheduling as a guardrail only after W separates sample-window
  starvation from remaining loss-weighting issues.
- HMoE hierarchical-computation repair only if A7 learns correct credit signs
  and policy coupling still fails in a hierarchy-attributable way.

Deferred:

- M2, HMoE soft routing, missile authority, `2v2`, self-play, and doctrine.
