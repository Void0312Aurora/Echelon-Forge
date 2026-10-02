# Simulation Experiment Platform

Status: `2026-09-27` active architecture foundation; contract and reference implementation work is not yet admitted into the maintained runtime.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is an English-first architecture work surface.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/simulation_experiment_platform/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-27`

Inputs:

- [Simulation system architecture standard](../../../standards/simulation_system_architecture_design.md)
- [Runtime workflow and contract baseline](../../../standards/runtime_workflow_and_contract_baseline.md)
- [Simulation conventions](../../../standards/simulation_conventions.md)
- [Runtime facade contract issue](../../issues/runtime_facade_contract_plan.md)
- [Policy execution architecture](../../../../learning/standards/policy_execution_architecture.md)
- [Adaptive counterfactual search preparation](../../../../learning/work/issues/adaptive_counterfactual_search/README.md)
- [Current RuntimeFacade](../../../../../src/runtime/facade/runtime_facade.h)
- [Current WorldBatchVecEnv](../../../../../python/rl/runtime/world_batch/vec_env.py)

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
| Runtime stepping | accepted | `RuntimeFacade` and `WorldBatchVecEnv` expose maintained setup, step, observation, and batch paths | No generic snapshot, restore, or fork contract exists. |
| Observation provenance | active | `python/rl/runtime/agent_shim.py` distinguishes maintained observation, decision belief, raw truth, and diagnostics | The experiment platform must preserve these labels; it must not widen policy visibility. |
| Replay evidence | partial | `src/runtime/contracts/cuda_resident_replay_contract.h` and existing replay tests define backend-specific trace concepts | This contract is not a generic counterfactual state contract. |
| Experiment canary | active | `python/experiment/counterfactual_toy.py` and its focused tests | Synthetic/toy evidence only; no runtime claim. |
| Training storage | partial | `python/world_model/replay.py` stores basic episodes | Branch ancestry, snapshot identity, and experiment manifest are missing. |

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
| `P1 Contract` | Define versioned session, state, branch, trace, and manifest contracts. | P0 accepted. | Schemas/DTOs have owners, provenance fields, and rejection rules. | `planned` |
| `P2 Reference` | Build a small reference session and timeline graph. | P1 contracts exist. | Determinism, restore, fork isolation, and serialization tests pass. | `planned` |
| `P3 Runtime` | Adapt the maintained CPU runtime behind the session contract. | P2 reference gates pass. | Runtime adapter passes the same contract suite without policy leakage. | `planned` |
| `P4 Learning` | Project traces into PPO, BC, world-model, and evaluation inputs. | P3 trace evidence exists. | Training projections preserve ancestry and fixed comparison protocols. | `planned` |
| `P5 Scale` | Add batch, GPU-resident, and remote scheduler implementations. | P3/P4 semantics stable. | Each backend passes selected-slice parity and cost evidence. | `planned` |
| `P6 Closure` | Publish accepted boundaries, residuals, and owner/index links. | P0-P5 evidence reviewed. | Acceptance record and residual owners are synchronized. | `planned` |

## Task Clusters

- [Finite task-cluster plan](simulation_experiment_platform_task_clusters_20260927.md)
- [Current status](simulation_experiment_platform_current_status_20260927.md)

## Outputs And Evidence

- Versioned C++/Python contracts under `src/runtime/contracts/` and
  `python/experiment/`.
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

- `R1`: no maintained full-state snapshot/restore surface; owner is
  `architecture/runtime-facade`, exit is P1 contract plus P3 implementation.
- `R2`: current episode storage lacks branch ancestry and manifest identity;
  owner is `learning/training`, exit is P4 projection contract.
- `R3`: GPU-resident replay contracts are backend-specific and quarantined;
  owner is `architecture/runtime-backend`, exit is P5 selected-slice parity.
- `R4`: the adaptive toy canary has synthetic evidence only; owner is
  `learning/training`, exit is a maintained-runtime experiment with fixed
  comparison protocol.

## Archive

This active package is the current architecture work surface. Accepted facts
will move to architecture standards or references; completed task narratives
will move to an owner-local acceptance/review or archive package.
