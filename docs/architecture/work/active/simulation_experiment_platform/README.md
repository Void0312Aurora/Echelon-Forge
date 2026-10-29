# Simulation Experiment Platform

Status: `2026-10-18` active. P0/P1/P2 are complete. The selected native CPU
slice supports session checkpoints, restore, historical/nested branches, and
verified replay. Typed flight actions, an explicit speed-change evaluator, and
a fixed native branch comparison now pass. The P4-A trace projection contract
preserves lineage and fixed seed splits for downstream consumers. A
RuntimeFacade Agent-packet bridge, a fail-closed maintained-facade session
boundary, an explicit Python action/ref branch-owner injection, and optional
persisted PPO `EpisodeStore` export are available for selected native branches;
broader mission and durable recovery coverage remain incomplete.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; English-only `work/active` task slice.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-10-18`

Inputs:

- [Simulation system architecture standard](../../../standards/simulation_system_architecture_design.md)
- [Runtime workflow and contract baseline](../../../standards/runtime_workflow_and_contract_baseline.md)
- [Simulation conventions](../../../standards/simulation_conventions.md)
- [Runtime facade contract issue](../../issues/runtime_facade_contract_plan.md)
- [Policy execution architecture](../../../../learning/standards/policy_execution_architecture.md)
- [Adaptive counterfactual search preparation](../../../../learning/work/issues/adaptive_counterfactual_search/README.md)
- [Current RuntimeFacade](../../../../../src/runtime/facade/runtime_facade.h)
- [Current WorldBatchVecEnv](../../../../../python/rl/runtime/world_batch/vec_env.py)
- [Long-horizon architecture governance](../long_horizon_architecture_governance/README.md)
  and its [plan/RunReceipt authority decision](../long_horizon_architecture_governance/decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md):
  owner of `ExperimentRequest`, `ResolvedCompositionPlan`, `RunReceipt`, the
  native `StateCheckpoint`, and the `echelon_forge.canonical_json.v2` wire.

## Purpose

This subproject builds the long-lived experiment surface for deterministic
simulation sessions, state identity, replay, branching timelines, evaluation,
and training projections. It provides one architecture for controlled tests,
counterfactual search, multi-agent decision experiments, and later distributed
or GPU execution.

The platform is an experiment layer over the maintained simulation runtime. It
does not replace `SimulationKernel`, `WorldBatchRuntime`, `RuntimeFacade`, or
the learning algorithms. It gives them versioned contracts and a durable
evidence path.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Runtime stepping | accepted | `RuntimeFacade` and `WorldBatchVecEnv` expose maintained setup, step, observation, and batch paths | Generic branch publication requires an explicit caller-supplied Agent action/ref owner. |
| Observation provenance | active | `python/tasking_contracts/common/agent_contracts.py` distinguishes maintained observation, decision belief, raw truth, and diagnostics | The experiment platform must preserve these labels; it must not widen policy visibility. |
| Replay evidence | partial | `src/runtime/contracts/cuda_resident_replay_contract.h` and existing replay tests define backend-specific trace concepts | This contract is not a generic counterfactual state contract. |
| Experiment canary | active | `python/experiment/counterfactual_toy.py` and its focused tests | Synthetic/toy evidence only; no runtime claim. |
| Runtime candidate seam | pass (selected slice) | `runtime_candidate.py` consumes the native CPU candidate, records branch traces, supports saved checkpoint restore and verified replay, and `runtime_facade_backend.py` binds maintained setup/step/packet access behind native identity plus an optional explicit branch action/ref owner | Typed flight controls and explicit diagnostic scoring pass; callers without an action/ref owner remain fail-closed. |
| Experiment contracts | pass | `python/experiment/contracts.py`, `python/experiment/trace.py`, and their tests | Value contracts only; digests use the float-free canonical JSON v2 subset. |
| Reference session | pass | `python/experiment/reference_session.py` and `tests/experiment/test_reference_session.py` | In-memory reference backend; evidence is `toy` or `synthetic`. |
| Training storage | partial | `python/world_model/replay.py` stores basic episodes; `python/experiment/trace_projection.py`, `numeric_observation_adapter.py`, and `runtime_facade_observation.py` provide audited projection, RuntimeFacade packet bridging, and `EpisodeStore` export contracts | The fixed native pilot captures branch-bound Agent packets at export barriers and can persist selected PPO branches with a sidecar. This remains `runtime_candidate` evidence until admitted production mission surfaces are wired; broader mission and learner coverage remain open. |
| Native state checkpoint | selected CPU lifecycle implemented | Native branch barrier/executor, opaque checkpoint clones, and separate `ef_runtime_candidate_py` extension | Reuses the state-transfer owner authority; in-process, dark/shadow, and single-world only. |

## Scope

In scope:

- Versioned contracts for `SimulationSession`, `SnapshotRef`, `BranchRef`,
  `DecisionWindow`, `Transition`, and experiment manifests.
- A backend-neutral timeline/branch model with explicit parentage and state
  identity.
- Determinism, snapshot/restore, branch isolation, provenance, and replay
  acceptance tests.
- Reference and maintained-runtime adapters.
- Evaluation and training projections that consume audited traces.
- Local execution first, with backend and scheduler extension points for batch,
  GPU-resident, and remote execution.

Out of scope:

- Reviving the retired counterfactual facade or compiled episode-controller
  surface.
- Changing physics, mission semantics, reward semantics, or policy architecture
  as an incidental part of this project.
- Treating a toy model, replay parity, or a single runtime seed as evidence of
  causal validity or training improvement.
- Making GPU or distributed execution a prerequisite for the first contract.

## Architecture Boundary

The stable center is a versioned `SimulationSession` and immutable timeline
graph. Prefix replay, full state cloning, copy-on-write checkpoints, and
GPU-resident forks are interchangeable `BranchExecutor` implementations.

The authoritative runtime state remains in the simulation backend. Python
adapters may hold mirrors and training buffers, but they cannot become episode
truth owners. Every observation, action, event, reward, and termination record
must carry its source and destination state identity.

Ownership split with the long-horizon governance program:

- that program owns durable execution authority: `ExperimentRequest`,
  `ResolvedCompositionPlan`, `RunReceipt`, `StateCheckpoint`, and the
  canonical wire/digest envelope;
- this package owns the experiment-layer branch vocabulary only: sessions,
  snapshot references, branch timelines, decision windows, transitions, and the
  trace manifest that binds them;
- experiment-layer snapshot identity is a reference to backend state, never a
  second checkpoint format. A runtime adapter (P3) must obtain identities from
  the native checkpoint authority once it admits a branch consumer, and it must
  not mint or persist its own checkpoint payloads;
- digests in this package reuse the canonical JSON profile; they do not define
  a parallel canonicalization.

The initial state model is hybrid:

```text
authoritative mutable state
+ deterministic event journal
+ canonical checkpoint/snapshot
```

This preserves runtime performance while making replay, branch isolation, and
recovery auditable.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze ownership, scope, terms, and non-goals. | Current architecture and toy preparation inspected. | This README and task-cluster plan are internally consistent. | `accepted` |
| `P1 Contract` | Define versioned session, state, branch, trace, and manifest contracts. | P0 accepted. | Schemas/DTOs have owners, provenance fields, and rejection rules. | `pass` |
| `P2 Reference` | Build a small reference session and timeline graph. | P1 contracts exist. | Determinism, restore, fork isolation, and serialization tests pass. | `pass` |
| `P3 Runtime` | Adapt the maintained CPU runtime behind the session contract and admit native branch execution. | P2 reference gates pass and the native checkpoint owner admits a branch consumer. | Selected CPU adapter/branch contracts pass without policy leakage; the maintained C++ owner and caller-injected Python action/ref owner pass isolation and session lifecycle tests. | `pass (selected CPU slice)` |
| `P4 Learning` | Project traces into PPO, BC, world-model, and evaluation inputs. | P3 trace evidence exists. | Training projections preserve ancestry and fixed comparison protocols. | `partial` |
| `P5 Scale` | Add batch, GPU-resident, and remote scheduler implementations. | P3/P4 semantics stable. | Each backend passes selected-slice parity and cost evidence. | `planned` |
| `P6 Closure` | Publish accepted boundaries, residuals, and owner/index links. | P0-P5 evidence reviewed. | Acceptance record and residual owners are synchronized. | `planned` |

## Task Clusters

- [Finite task-cluster plan](simulation_experiment_platform_task_clusters_20260927.md)
- [Current status](simulation_experiment_platform_current_status_20260927.md)
- [P3 runtime owner-decision preflight](p3_runtime_owner_decision_preflight_20261014.md)
- [Current-main integration record](current_main_integration_20261014.md)
- [P3-B native branch consumer design](p3b_native_branch_consumer_design_20261014.md)
- [Native flight-control comparison](native_pilot_action_comparison_20261015.md)
- [P3 runtime adapter boundary](p3_runtime_adapter_boundary_20261017.md)
- [Trace projection contract](../../../../../python/experiment/trace_projection.py)
- [Numeric observation adapter](../../../../../python/experiment/numeric_observation_adapter.py)
- [RuntimeFacade Agent observation bridge](../../../../../python/experiment/runtime_facade_observation.py)
- [Native session checkpoint and replay](native_session_checkpoint_replay_20261015.md)

## Outputs And Evidence

- Versioned Python contracts under `python/experiment/` (P1). C++ contract
  headers under `src/runtime/contracts/` are deferred to P3: no C++ consumer
  exists before a runtime adapter, and the native checkpoint authority is owned
  by the long-horizon governance program.
- Reference timeline and branch tests under `tests/experiment/`.
- Runtime adapter and integration tests under `python/rl/runtime/` and
  `tests/runtime/`.
- Immutable run manifests, event traces, checkpoint identities, and evaluation
  reports under the experiment output layout.
- A maintained acceptance record only after exact scope and evidence gates pass.

## Acceptance Gate

This subproject can be accepted only when:

- identical session inputs and action traces reproduce the same declared state,
  event, observation, reward, and termination outputs;
- restoring a full snapshot produces an equivalent continuation over the
  declared horizon;
- parent and sibling branches are isolated and retain ancestry;
- maintained policy inputs are limited to admitted observation/belief
  provenance;
- runtime, replay, and training projections retain schema/config/seed/policy
  identity;
- CPU and later backend implementations pass the same selected-slice contract
  tests;
- residuals and forbidden claims remain explicit in the acceptance record.

## Residuals And Next Steps

The residual register lives in the
[current status](simulation_experiment_platform_current_status_20260927.md#residual-register);
this README does not keep a second copy.

## Archive

This active package is the current architecture work surface. Accepted facts
will move to architecture standards or references; completed task narratives
will move to an owner-local acceptance/review or archive package.
