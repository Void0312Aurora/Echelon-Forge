# M3-S1 Censored Optimal-Stopping Timing Contract Dispatch Queue

Status: `2026-06-05` active dispatch queue for
[M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

## Dispatch Boundary

This queue previously started M3S1-P1 evidence gathering only. P1-P4 are now
accepted as bounded slices, so the queue opens the P5 diagnostics and
short-training evidence split.

No worker may create a new Codex conversation thread. Subagents are allowed only
as bounded workers under the current thread.

## Active Dispatches

| Dispatch | Cluster | Worker type | Model / reasoning | Scope | Write set | Output | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S1-D1 Data Censoring Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | Inspect rollout/env/info paths and recommend the wait-preserving data route plus required metadata. | none; read-only | accepted into [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.md) | pass |
| `M3S1-D2 Group Preservation Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | Inspect rollout buffer/minibatch behavior and identify how grouped episode/window structure can survive to loss computation. | none; read-only | accepted into [P1](m3_s1_data_censoring_contract_20260605.md) and [P2](m3_s1_grouped_stopping_objective_contract_20260605.md) | pass |
| `M3S1-D3 Reward/Loss Boundary Evidence` | `M3S1-P1 Data Censoring Contract` | explorer | inherited / high | Inspect reward runtime, A6/A7 losses, and C2/ROE gate ownership to identify forbidden couplings and safe handoff points. | none; read-only | accepted into [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.md) | pass |
| `M3S1-P4A Policy Head Skeleton` | `M3S1-P4 Minimal Integration` | worker | inherited / high | Add an optional independent stopping/survival head to the HMoE policy surface, plus focused tests proving it is separate from executable event logits. | `python/rl/policy_algo/policies.py`; focused policy tests only | accepted into [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.md) | pass |
| `M3S1-P4B Grouped Evidence/Loss Skeleton` | `M3S1-P4 Minimal Integration` | worker | inherited / high | Add grouped evidence dataclasses and a pure grouped stopping loss helper implementing the P2 survival/event-mass contract. | new sibling module under `python/rl/policy_algo/`; dedicated grouped-loss tests only | accepted into [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.md) | pass |
| `M3S1-P4C PPO Auxiliary Integration` | `M3S1-P4 Minimal Integration` | main thread | high | Wire P4A/P4B into rollout collection and the auxiliary pass without changing base PPO minibatch flow. | `python/rl/policy_algo/ppo_adaptive_kl.py`; `tests/policy/test_auxiliary_training_updates.py` | accepted into [P4 dispatch review](m3_s1_p4_dispatch_review_20260605.md) | pass |
| `M3S1-P5A Diagnostics Surface` | `M3S1-P5 Diagnostics And Short Training` | worker | inherited / high | Add/report missing `m3s1/*` validation diagnostics for stop-boundary movement, early/prewindow mass, no-event mass, grouped-label persistence, and mask/one-shot legality. | `python/rl/policy_algo/ppo_adaptive_kl.py`; `tests/policy/test_auxiliary_training_updates.py` | integrated into [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.md) and focused test evidence | pass |
| `M3S1-P5B Short Training Evidence Path` | `M3S1-P5 Diagnostics And Short Training` | explorer | inherited / high | Identify the conservative short-training command, output artifacts, metrics, and stop criteria without running a long formal train. | none; read-only | integrated into [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.md) | pass |

## Worker Packet Template

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
key evidence:
recommended contract clauses:
behavior risks:
integration notes:
```

## Integration Rule

The main thread integrated D1/D2/D3 after local review of the cited rollout,
buffer, reward, C2/ROE, observation, and policy surfaces. P3 is complete and
P4 is explicitly opened.

P4-A, P4-B, and P4-C passed local review. P5 is active, but it must remain
separate and must not claim learned behavior until diagnostic and short-training
gates exist. No P5 worker may change reward magnitudes, weaken C2/ROE or action
masks, or treat event-logit delta as the primary stopping score.

P5-A and P5-B packets have returned. The main thread owns normative
README/status tables, final integration, and the decision to open the first
short-training config.
