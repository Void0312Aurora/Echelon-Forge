# M3-S1 Censored Optimal-Stopping Timing Contract Task Clusters

Status: `2026-06-05` finite task-cluster plan for
[M3-S1 Censored Optimal-Stopping Timing Contract](README.md); P5 validation
dispatch is active.

## Boundary Decision

M3-S1 may define and then implement a bounded censored optimal-stopping timing
contract. It must first separate the model spine and branches. Code edits are
held until data/censoring and grouped-objective contracts exist.

This plan intentionally rejects another blind A7 coefficient sweep and rejects
reward-only fire-discipline repair.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S1-P0 Boundary Map` | main thread | current main thread | Freeze trunk/branch/loss/reward ownership and first cut points. | `README*`, `m3_s1_model_architecture_boundary_map_20260605*.md`, parent/M3 indexes | training code, reward tuning, M2 release | `git diff --check -- docs/task/model`; link inspection | Boundary map names owners and forbidden couplings clearly enough for implementation workers. | serial first | 1 + 1 repair | pass |
| `M3S1-P1 Data Censoring Contract` | main thread or diagnostics worker | high reasoning | Define wait-preserving timing evidence, early-event censoring treatment, and required rollout metadata. | new `m3_s1_data_censoring_contract_*.md`; optional tests as probes only | PPO loss implementation, reward changes, policy-head changes | markdown review; optional probe script/test if needed | Contract selects a data route and names unsupported evidence assumptions. | after P0; serial | 2 | pass |
| `M3S1-P2 Grouped Objective Contract` | main thread | high reasoning | Define grouped survival/stopping objective over episode/window IDs. | new objective contract doc; possible design notes under `python/rl/policy_algo` only after P1 | per-row BCE tuning, A7 coefficient sweep | formula review; buffer grouping audit | Objective preserves grouped windows and includes early-mass/censoring terms. | after P1; serial | 2 | pass |
| `M3S1-P3 Policy Head Boundary` | main thread plus focused implementation worker | high reasoning | Decide reuse-vs-new-head and deterministic stop boundary contract. | contract doc; later `policies.py` tests only if opened | broad HMoE redesign, M2 release | focused policy-distribution tests if code opens | Stop boundary, event-time calibration, and diagnostics are specified. | after P2; serial | 2 | pass |
| `M3S1-P4 Minimal Integration` | implementation workers plus main-thread integration | high reasoning | Implement selected data/loss/head changes only. | `python/rl/policy_algo/**`, focused tests, active config docs if required | reward-only fixes, legality weakening, broad training rewrites | focused unit/PPO/loss tests; compileall | Code path is finite, grouped labels survive to loss, masks remain authoritative. | after P1-P3 accepted; P4-A/P4-B disjoint; P4-C serial | 2 | pass |
| `M3S1-P5 Diagnostics And Short Training` | diagnostics worker plus read-only evidence explorer | high reasoning | Add/report boundary crossing, cumulative prewindow mass, no-event mass, grouped-label persistence, and one-shot legality. | diagnostics docs, probe scripts/tests, active config logs | long formal training before focused gates; coefficient tuning | focused m3s1 tests; short-train command/evidence packet only after diagnostics exist | Deterministic boundary and stochastic legality are reported with caveats. | after P4 | 2 | active |
| `M3S1-P6 Closure And Archive Sync` | main thread | current main thread | Sync model/A7/M3 indexes and archive superseded local repair docs only if replacement evidence exists. | `docs/task/model/**`, selected A7 docs/archive pointers | deleting evidence, claiming success without probes | `git diff --check -- docs/task/model docs/task/air_combat/a7_event_value_advantage_credit_head` | Docs distinguish accepted slices, held learned behavior, and residuals. | after P5 | 1 | held |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- No worker may create a new Codex conversation thread.
- Do not allow concurrent edits to `ppo_adaptive_kl.py`, `first_event_hazard.py`,
  rollout buffers, or normative README/status tables.
- P1-P3 are serial because each decides the contract for the next.
- P4 passed after P1-P3 were explicitly accepted. P4-A and P4-B ran in
  parallel only while their write sets remained disjoint; P4-C stayed serial.
- P5 short training may start only after focused loss/buffer/head tests pass.
- P5 is split into `P5-A Diagnostics Surface` and `P5-B Short Training Evidence
  Path`. Only P5-A may touch `ppo_adaptive_kl.py`, and only one worker may own
  that file at a time.
- If any cluster exceeds its round cap, stop and re-scope instead of opening an
  unbounded repair wave.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Implementation worker packets must also name:

- exact write set;
- loss/reward/legality ownership boundary;
- expected diagnostics;
- rollback gate;
- whether grouped episode/window structure is preserved.

## Validation Plan

```bash
git diff --check -- docs/task/model
rg -n "M3-S1|Boundary Map|Data/Censoring|Grouped Objective|reward-only|per-row" docs/task/model
```

After code opens, validation must expand to focused unit tests for:

- first-event label grouping;
- grouped loss math;
- policy stop-boundary behavior;
- one-shot legality and mask authority;
- diagnostic metric emission.

## Acceptance Criteria

- P0-P3 contracts exist and are specific enough that implementation does not
  rely on chat history.
- Implementation, if opened, preserves C2/ROE legality and action masks.
- Grouped timing objectives do not silently collapse into independent per-row
  labels.
- Rewards, PPO base loss, and auxiliary stopping losses remain separate in docs
  and code.
- Short training evidence reports deterministic boundary behavior and
  cumulative early-event mass before any longer run is proposed.

## Residual Map

Immediate:

- `M3S1-P4A Policy Head Skeleton`, `M3S1-P4B Grouped Evidence/Loss Skeleton`,
  and `M3S1-P4C PPO Auxiliary Integration` passed.
- P5 is open only as diagnostics/short-training validation, not as another
  coefficient-tuning loop. Current P5 evidence is tracked in
  [m3_s1_p5_dispatch_plan_20260605.md](m3_s1_p5_dispatch_plan_20260605.md).

Follow-on:

- Decide whether the first implemented objective is survival-hazard likelihood,
  ordinal margin fallback, or offline direct stopping-distribution probe.

Deferred:

- M2 sequence-native causal Transformer release.
- Broad reward-surface redesign.
- Any learned-policy acceptance claim.
