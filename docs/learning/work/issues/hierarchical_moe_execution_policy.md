# Hierarchical MoE Execution Policy

Language: English canonical; [Chinese companion](hierarchical_moe_execution_policy.zh.md).

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/learning/work/issues/hierarchical_moe_execution_policy.md`
Owner: `learning/policy-architecture`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

## Purpose

This note formalizes a forward direction for the execution-layer policy:
keep the current unified pipeline, but replace the single dense decision head
with a hierarchical, semantically routed specialization structure.

The goal is not to fragment the system into unrelated models. The goal is to
preserve the shared execution stack while reducing negative transfer across:

- takeoff and runway-roll behavior
- departure and initial climb
- route / cruise navigation
- cooperative formation execution
- recovery / landing execution

This document is intentionally scoped to the execution-layer policy and its
training line. It does not redefine the larger C2 / leader / mission stack.

## Motivation

The current execution policy is a single shared model. This is operationally
clean, but it pushes heterogeneous control regimes through the same dense
decision head.

That creates a likely source of interference:

- different phases prefer different action priors
- different roles prefer different coordination behaviors
- some lower-level skills are shared, but some decisions are phase-specific

The key observation is that our system already has a semantic hierarchy:

- `TaskOrder`
- `LeaderIntent`
- `MissionCommand`
- execution-layer control

So the project does not need a fully free-form learned router as the first
step. It already has a natural routing substrate.

## Core Design Judgment

### 1. Shared parameters remain the default

Many flight skills are generic and should stay shared:

- observation encoding
- attitude stabilization representations
- energy management representations
- basic turning / climb / descent control priors
- route geometry and navigation abstractions

Therefore the execution policy should not become a collection of isolated
end-to-end experts.

### 2. Specialization should sit near the decision head

The first HMoE version should keep:

1. shared observation encoder
2. shared latent trunk
3. hierarchical actor specialization
4. conservative critic sharing

This makes the design a hierarchy of decision experts, not a full sparse-MoE
replacement of the entire network.

### 3. Routing should be semantic and explicit first

The first router should come from already justified operational fields, not
from training-only synthetic hints and not from a fully learned black-box
gating network.

That keeps the design realistic, easier to debug, and better aligned with the
existing command stack.

## Architectural Shape

Recommended near-term structure:

1. shared encoder
2. shared flight trunk
3. level-1 semantic family routing
4. level-2 role / procedure specialization
5. actor head output

The critic should remain mostly shared in the first iteration, with at most a
coarse conditional head if needed later.

## Proposed Hierarchy

### Level 0: Shared Flight Backbone

Always shared:

- existing observation contract
- transformer-based feature extractor
- generic flight / navigation latent
- continuous-control priors used across all regimes

This layer learns "how the aircraft flies" rather than "which mission regime is
currently active".

### Level 1: Family Experts

Level-1 routing should choose a coarse behavior family.

Initial family split:

- `takeoff_ground_family`
- `departure_nav_family`
- `formation_cooperative_family`
- `recovery_landing_family`

This is a small and intentionally coarse partition. It should not be expanded
too early.

### Level 2: Role / Procedure Sub-Experts

Inside each family, a second routing step may choose a smaller specialization.

Examples:

- takeoff family:
  - single-ship
  - interval takeoff
  - wing takeoff
- formation family:
  - lead
  - wingman-left
  - wingman-right
  - trail / support slot
- recovery family:
  - straight-in
  - visual
  - overhead
  - ILS / procedure-guided

This level should remain lightweight. The first implementation should prefer
small residual or head-level experts over large independent trunks.

## Natural Routers Already Present in the System

### Primary execution router: `MissionCommand`

`MissionCommand` is the best first routing object for the execution layer
because it is already the command-level interface intended for downstream
execution.

Priority fields:

- `command_code`
- `takeoff_procedure_id`
- `takeoff_clearance_id`
- `runway_slot_id`
- `recovery_approach_type`
- `formation_id`

These fields are operationally meaningful and already part of the maintained
stack.

### Secondary auxiliary router: `TaskOrder`

`TaskOrder` can provide coarse structural context, especially when cooperative
or role-specific behavior matters.

Useful candidates:

- `task_family`
- `coordination_mode`
- `formation_role_id`
- `wingman_slot_id`
- `role_code`

However, execution should only consume fields that are appropriate to expose at
the execution layer. Purely internal C2 semantics should not be leaked into the
policy just because they are available.

### Upstream semantic source: `LeaderIntent`

`LeaderIntent` contains valuable upstream semantic structure, but the first
execution HMoE should not depend on direct coupling to leader-internal state.

Preferred rule:

- `LeaderIntent` may inform upstream translation
- execution HMoE should primarily route from `MissionCommand`
- `TaskOrder` may be used as bounded auxiliary context where appropriate

## Routing Rules for the First Prototype

The first HMoE prototype should use explicit routing rules.

### Level-1 family routing

Suggested initial rules:

- `command_code == takeoff` -> `takeoff_ground_family`
- `command_code == landing` -> `recovery_landing_family`
- `command_code in {vector, route}` and cooperative formation is active ->
  `formation_cooperative_family`
- otherwise `command_code in {vector, route}` ->
  `departure_nav_family`

### Level-2 sub-routing

Suggested initial rules:

- takeoff family:
  route by `takeoff_procedure_id`
- formation family:
  route by `formation_role_id`, `wingman_slot_id`, `role_code`
- recovery family:
  route by `recovery_approach_type`

These rules are intentionally transparent and hand-auditable.

## Parameter Sharing Boundary

### Shared

- observation encoder
- shared latent trunk
- generic flight stabilization features
- generic navigation features
- basic action continuity and low-level control priors

### Specialized

- phase-specific action priors
- role-specific cooperative control biases
- procedure-specific edge behavior
- regime-specific residual experts layered over the shared action head

### First principle

Shared layers should carry common flight skill.
Experts should add selective specialization, not relearn the full aircraft.

## Why Not Full Sparse MoE First

Full sparse-MoE remains a possible later direction, but it is not the right
starting point for the current line.

Reasons:

- PPO router instability
- expert collapse risk
- fragmented batches
- harder debugging while the training line is still stabilizing
- unnecessary duplication of low-level flight skill

So the project should begin with a shared action-head baseline plus
hierarchical residual experts, not full sparse expert routing inside the full
trunk.

## Suggested Implementation Boundary

The HMoE line should stay separate from the current baseline execution model.

### Baseline remains

- existing shared execution model remains the maintained reference
- existing configs remain the baseline training line

### HMoE experiment line adds

- separate policy class
- separate policy configuration path
- separate training configs
- separate experiment naming
- stability controls that keep the routed residual path conservative at startup:
  - zero-initialized expert heads
  - lower optimizer rate for expert parameters
  - residual warmup during early training progress

Suggested implementation split:

- keep current baseline policy untouched
- add dedicated HMoE policy module beside the current policy path
- keep routing logic explicit and inspectable

## Suggested Code Separation

Illustrative split:

- baseline shared policy:
  - current `SquashedMultiInputPolicy` path
- HMoE policy path:
  - dedicated policy class beside the baseline path
  - shared actor head remains the initial policy mean
  - routed family/subexpert heads contribute residual corrections
- semantic routing helpers:
  - standalone helper module
- HMoE configs:
  - dedicated config names that clearly differ from baseline configs

This reduces the risk of hidden behavior drift in the main training line.

## Research Value

This direction may become more than an engineering refactor.

Potential novelty for this project:

- semantic hierarchical routing from realistic command/task structures
- conditional execution policy without training-only route hints
- unified execution backbone with phase- and role-specific specialization
- direct comparison against the dense shared execution baseline

The most promising question is not merely "does MoE help RL?" but:

"Can a realistic command-driven hierarchical expert policy reduce interference
in a unified continuous-control execution stack?"

## Recommended Experimental Order

1. baseline dense shared execution policy
2. shared backbone + level-1 family heads
3. shared backbone + level-1 family heads + level-2 role/procedure heads
4. optional soft router inside a family
5. only then consider deeper sparse MoE variants

## Engineering Placement

The HMoE implementation line should stay distinguishable from the baseline in
configuration and experiment naming, while living in the same mainline codebase.

Suggested engineering intent:

- keep the baseline model recognizable and runnable
- isolate HMoE behavior through dedicated policy/config paths
- allow direct baseline vs HMoE comparison without ambiguity

## Status

This document establishes the design freeze for the first HMoE direction.

It does not imply that full sparse MoE is the default target.
The intended first implementation is:

- shared backbone
- explicit semantic level-1 routing
- shared action-head baseline
- lightweight residual level-2 specialization
- baseline-compatible training and evaluation comparison
