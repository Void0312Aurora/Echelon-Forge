# Launch-Decision Architecture Reorganization

Language:
- English canonical: README.md
- Chinese companion: README.zh.md

Document kind: plan
Lifecycle: draft
Canonical: docs/learning/work/issues/launch_decision_reorg/README.md
Owner: learning/policy-architecture
Last verified: 2026-09-19
Content status: held proposal; implementation is not authorized.

## Authorization boundary

This is a bounded architecture plan, not an implementation work package. It
does not authorize moving code, changing model parameters, changing rollout
semantics, changing runtime legality, changing active configurations, or
publishing a new acceptance result.

An implementation may start only after the owner accepts this plan and creates
a separately scoped package under the appropriate active-work surface. That
package must name the exact files, compatibility behavior, focused tests,
acceptance evidence, and residual owners. A plan revision is not permission to
edit the current dirty governance worktree or any unrelated worktree.

The plan has a documentation budget of two files: this English canonical and
the required Chinese companion. It intentionally does not create a dispatch
queue, ledger, or acceptance report.

## Authority and evidence order

The proposal is subordinate to the following maintained sources, in this
order:

1. [Policy execution architecture baseline](../../../standards/policy_execution_architecture.md)
   for model roles, executable-versus-auxiliary classification, one-shot
   timing semantics, and the A5 acceptance boundary.
2. Current source and executable tests for implemented behavior.
3. The [HMoE computation-gap issue](../hmoe_hierarchical_computation_gap/README.md)
   and [launch-window imbalance issue](../launch_window_label_imbalance/README.md)
   for known gaps and open evidence.
4. [Modularization issue policy](../../../../architecture/work/issues/modularization_plan.md)
   for the draft/authorization boundary.
5. [Worktree and path policy](../../../../engineering/workspace/worktree_and_path_policy.md),
   [subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.md),
   and [WP closure-lane policy](../../../../engineering/automation/standards/wp_closure_lane_policy.md)
   for execution discipline.

The plan was prepared from revision cfb9924e (the branch's origin/main
baseline). The reference worktree
.worktrees/long-horizon-governance-architecture was inspected read-only for
discipline and remains independently dirty. Its uncommitted files are not
part of this plan.

## Problem statement

The maintained model baseline already separates observation, actor latent,
action distribution, policy-visible support, runtime A5 legality, auxiliary
heads, and diagnostics. The current implementation nevertheless leaves the
launch decision spread across several seams:

- HierarchicalMoEExecutionPolicy applies a shared action net and an HMoE
  residual to the full hybrid action parameter vector. The event slice can
  therefore receive a tactical residual before the dedicated event head.
- _apply_hybrid_event_head then applies the dedicated hybrid_event_head and
  can replace its hold/fire logits with a stopping-head or
  window-classifier adapter. If both adapter flags are enabled, precedence is
  implicit in the forward method rather than rejected by a typed contract.
- The PPO algorithm surface is a large flat constructor composed from
  _first_event_mixin.py, _event_credit_mixin.py, _grouped_stopping_mixin.py,
  and _event_window_mixin.py. Label collection, objective selection,
  optimizer ownership, and forward-path coupling are consequently difficult
  to inspect as one launch-decision contract.
- model_contracts.py has detailed contracts for the window-classifier adapter
  and direct fire-boundary objective, but does not provide one complete
  contract covering all possible event owners, auxiliary evidence branches,
  configuration exclusivity, and migration behavior.
- The active direct-boundary probe deliberately has both stopping and
  window-classifier adapters disabled. That is a useful canonical baseline,
  but the code still permits incompatible combinations and can silently
  change the executable owner.
- A5 remains the final runtime authority. A learned head, a policy-visible
  support mask, a requested pulse, and an accepted fire_once release are
  different observations and must not be collapsed into one metric.

These are architecture and ownership findings, not evidence that the current
policy has failed to emit an accepted release. The existing learned-firing
gate remains the narrower claim defined by the maintained baseline.

## Goal

Create one inspectable launch-decision boundary that makes the following
questions answerable from source, configuration, and tests:

1. Which branch owns the executable hold/fire logits for this policy instance?
2. Which branches are opportunity, stopping, credit, or window evidence only?
3. How are evidence branches combined, detached, masked, and optimized?
4. Which support constraints are policy-visible and which remain A5 runtime
   truth?
5. Can an old checkpoint and active configuration be loaded without silently
   changing the event owner?

The first migration should preserve the existing hybrid_event_head parameter
name and direct-boundary behavior where possible. A new learned event owner is
not justified merely to make the module names cleaner.

## Target ownership model

The following table is the proposed normative target for a future
implementation package. It is a design decision for review, not a claim about
the current code.

| Surface | Target role | Allowed effect on sampled event |
| --- | --- | --- |
| Observation and feature extractor | Input contract and representation | None by itself |
| HMoE tactical branch | Continuous/action-family residual | Must not silently own the event slice |
| Opportunity/window branch | Evidence prior w_t | May contribute only through an explicit, typed adapter mode |
| Stopping/trigger branch | Conditional evidence h_t | May contribute only through the same explicit adapter mode |
| Credit branch | Auxiliary value/diagnostic | No event effect by default |
| hybrid_event_head | Sole default learned executable owner lambda_t | Direct hold/fire logit residual |
| LaunchDecisionComposer (proposed extraction) | Resolve one owner, evidence policy, and ordering | One deterministic composition, no hidden precedence |
| Policy-visible support mask | legal_t before sampling | Removes unavailable support; does not prove A5 acceptance |
| _HybridActionDistribution | Transport, sample, mode, log-prob, entropy | No label or runtime truth |
| A5 event-action state machine | Final runtime legality and one-shot consumption | Accepts or rejects the requested pulse |

The default target is therefore one learned executable owner plus explicit
auxiliary evidence. Adapter-coupled modes may be admitted later, but only
when the contract names the owner, coefficient/combination rule, detach
behavior, optimizer lane, and acceptance probes. The stopping and
window-classifier adapters must never silently compete.

## Normative invariants for implementation

An implementation package must preserve these invariants:

1. Exactly one executable learned owner is selected for the hold/fire event
   slice in every policy instance. A configuration with two incompatible
   adapters fails validation before training.
2. HMoE residuals either exclude the event slice or enter through an explicit
   contract that records their event authority. Adding a full-vector residual
   must not remain an undocumented side effect.
3. The composition order is visible: evidence, executable owner, policy
   support mask, distribution, pulse normalization, and A5 acceptance are
   separate stages.
4. Auxiliary-only heads cannot be used as learned-firing acceptance evidence.
   Adapter-coupled heads require gradient, detach, and deterministic/stochastic
   behavior tests.
5. Optimizer groups and dedicated updates identify the same owner selected by
   the forward contract. No update may train a branch that is not connected to
   the claimed objective.
6. Legacy flags and checkpoint keys either map to the new typed contract with
   an explicit compatibility note or fail with an actionable error. Silent
   precedence is not compatibility.
7. A5 masks, authority checks, weapon readiness, ammunition, FiredAssess, and
   repeat suppression remain stronger than learned behavior. No refactor may
   weaken them to make a model metric green.
8. Historical M3-S1/M3-S2 labels remain usable in metrics and mechanism IDs
   where needed, but are not introduced as current module, head, config, or
   active-file prefixes.
9. Every behavior claim reports the distinction between requested, accepted,
   and released events, plus rejection and repeat-suppression counters.

## Proposed graph and extraction boundary

The candidate graph is:

    observation -> feature extractor -> actor latent
                                  -> tactical/action branch
                                  -> auxiliary evidence branches
                                  -> LaunchDecisionComposer
                                       -> executable event logits
                                       -> policy-visible support mask
                                       -> hybrid distribution
                                       -> fire_once pulse
                                       -> A5 runtime adapter

LaunchDecisionComposer is a proposed name for an extracted composition
boundary, not a request to add a module immediately. Its minimum interface
should accept a typed launch-decision specification, latent features, the
base event slice, auxiliary evidence tensors, and policy-visible support. It
should return event logits plus a structured trace identifying:

- selected executable owner;
- evidence branches used and their detach/combination modes;
- support-mask source and applied support;
- event-owner parameter IDs used by the update;
- compatibility mode, if a legacy configuration was translated.

The first implementation phase should keep the current
hybrid_event_head weights and state-dict key shape. Whether HMoE's event
dimensions can be excluded without a checkpoint migration is a required
compatibility experiment, not an assumption. If exclusion is impossible,
the package must explicitly preserve the old event residual as a named
compatibility adapter and schedule its removal separately.

## Scope and non-goals

### In scope

- A typed launch-decision specification and a complete mechanism/ownership
  matrix in model_contracts.py.
- A forward-path extraction or equivalent local boundary in policies.py that
  makes event-owner selection and ordering explicit.
- A configuration translation/validation layer for the current flat PPO and
  policy kwargs surface.
- Alignment of mixin objectives, rollout sidecars, optimizer groups, and
  diagnostics with the same ownership contract.
- Focused unit, contract, serialization, and A5 integration tests.
- Documentation of migration, deprecation, and residual ownership.

### Out of scope

- Re-designing HMoE routing, family/subexpert hierarchy, or the separate
  hmoe_hierarchical_computation_gap issue.
- Changing reward shaping, mission observations, weapon physics, damage,
  kill/Pk semantics, or the A5 runtime legality contract.
- Adding a new launch head solely for an experiment or probe.
- Claiming timing optimality, quality-window closure, effects realism, or
  target-kill acceptance from this reorganization.
- Rewriting old checkpoints or active configurations in place before the
  compatibility gate passes.
- Broad renaming of historical metric namespaces.

## Finite task-cluster plan

No implementation worker is authorized by this document. If an owner later
opens an implementation package, every worker must map to one of these finite
clusters. Each cluster has a maximum of two implementation rounds; exceeding
that cap requires re-scoping instead of an ad-hoc follow-up. C0 and C1 are
serial authority work. C2, C3, and C4 may be parallel only after C1 is
accepted and their file scopes remain disjoint. C5 is always serial after the
other clusters return complete packets.

### C0 — Baseline and authority freeze

- Goal: freeze the current graph, active direct-boundary configuration,
  checkpoint/state-dict facts, and acceptance vocabulary.
- Write scope: one owner-local evidence section or the implementation
  package's canonical notes; no production code.
- Non-goals: no renaming, behavior change, or HMoE redesign.
- Validation: source/test/config census; git diff --check; worktree status;
  confirm no untracked artifacts.
- Closure gate: owner signs off on the evidence ledger and the exact
  non-goals. Dependency: none. Parallel-safe: no.

### C1 — Typed contract and ownership matrix

- Goal: define the launch-decision specification, one-owner invariant,
  adapter exclusivity, evidence/gradient semantics, and compatibility modes.
- Write scope: model_contracts.py plus the canonical implementation notes
  named by the package.
- Non-goals: no forward-path edits or new learned head.
- Validation: contract construction tests for direct, auxiliary-only, and
  rejected-conflict configurations; serialization of the typed spec.
- Closure gate: every current flag has an owner, default, migration rule,
  and rejection behavior. Dependency: C0. Parallel-safe: no.

### C2 — Forward-path ownership boundary

- Goal: extract or make explicit the event composition boundary while
  preserving current direct-boundary behavior.
- Write scope: policies.py and, only if required by the chosen boundary,
  the HMoE event-slice helper.
- Non-goals: no changes to A5, reward, or HMoE routing semantics.
- Validation: logits-before/after traces, event-slice isolation, deterministic
  mode, stochastic log-prob/entropy, and old-checkpoint load tests.
- Closure gate: source and tests prove exactly one executable owner and no
  implicit stopping/window precedence. Dependency: C1. Parallel-safe with
  C3/C4 only after C1.

### C3 — Objective, rollout, and optimizer alignment

- Goal: align event-window, fire-boundary, stopping, credit, first-event
  sidecars, and optimizer groups with the typed owner.
- Write scope: ppo_adaptive_kl.py and the four event-related mixins; no
  policy forward code.
- Non-goals: no new labels and no support-preserving collect changes unless
  separately admitted as an action-changing intervention.
- Validation: gradient ownership, dedicated-update isolation, sidecar
  censoring/source metadata, and metric namespace compatibility tests.
- Closure gate: every objective points to the same declared owner or is
  explicitly auxiliary-only. Dependency: C1. Parallel-safe with C2/C4 after
  C1.

### C4 — Configuration, checkpoint, and migration compatibility

- Goal: translate the current flat constructor/config surface into the
  typed specification without silent precedence or state-dict drift.
- Write scope: config adapters, active-example validation, serialization
  helpers, and migration notes; no changes to runtime A5.
- Non-goals: no bulk rewrite of active configs and no destructive checkpoint
  conversion.
- Validation: representative active config load, legacy flag matrix,
  round-trip serialization, checkpoint key/shape comparison, and explicit
  conflict failures.
- Closure gate: old canonical direct-boundary config either round-trips
  unchanged or has a documented, tested migration. Dependency: C1; C2/C3
  interface decisions may be required before final closure.

### C5 — Acceptance and closure review

- Goal: prove the refactor preserves the architecture boundary and learned
  firing evidence without conflating policy and runtime truth.
- Write scope: focused tests, review packet, and required bilingual/index
  synchronization in a serial closure pass.
- Non-goals: no new implementation scope discovered during closure.
- Validation: all commands in the verification matrix below, plus worktree
  and path audits.
- Closure gate: complete worker packets, named residuals, independent review,
  and owner verdict of Mergeable, Blocked, or Closed. Dependency: C2, C3,
  and C4. Parallel-safe: no.

## Suggested implementation sequence after approval

1. Freeze C0 and record the current active direct-boundary configuration as
   the compatibility baseline.
2. Land C1 as contract-only behavior: typed ownership, conflict rejection,
   and serialization tests with no changed logits.
3. Land C2 behind the compatibility path. Compare old and new event logits,
   event masks, log-probs, and state-dict loading before enabling the new
   composer by default.
4. Land C3 and C4 together only after C2's owner trace is stable. Keep
   legacy flat kwargs accepted through an explicit translation layer.
5. Run C5. Deprecate redundant flags only after active examples and old
   checkpoints pass the declared migration gate. Any unresolved incompatibility
   becomes a blocked residual with an owner and replacement condition.

This sequence is intentionally conservative: reorganizing ownership must not
be used as an excuse to change the learned-firing experiment or weaken A5.

## Verification matrix

The eventual implementation package should add or extend tests for:

- one executable owner and rejection of stopping-plus-window conflicts;
- HMoE event-slice isolation or explicit compatibility-adapter tracing;
- direct-boundary, auxiliary-only, and adapter-coupled contract construction;
- gradient and optimizer ownership for event, stopping, window, and credit
  branches;
- legacy config translation and checkpoint/state-dict round trips;
- event support-mask, deterministic-mode, stochastic log-prob, and entropy
  invariants;
- A5 accepted/rejected fire_once, FiredAssess, authority, ammunition,
  readiness, repeat suppression, reset, and reattack behavior.

The named existing evidence lanes remain required:

    python -m pytest tests/policy/test_execution_policy_event_heads.py
    python -m pytest tests/policy/test_event_head_update_contracts.py
    python -m pytest tests/training/test_event_timing_training_config_contracts.py
    python -m pytest tests/runtime/air_combat/test_fire_action_release_gate.py

The new contract tests should run before any long training or probe. A
complete implementation pass also runs git diff --check, the architecture
governance tests, the path-length budget, and
tools/maintenance/audit_worktrees.py from an ordinary shell. Build output
must remain outside the checkout through CMO_BUILD_DIR.

Acceptance must report separately:

- requested event count;
- accepted event count;
- release count and authorized release count;
- rejection reasons and repeat-release count;
- executable-owner trace and event probability/logit diagnostics;
- any stochastic instability across the declared seed/episode set.

No kill, damage, Pk, or effects result is an acceptance substitute.

## Risks and residuals to carry forward

| Residual | Why it matters | Required owner or gate |
| --- | --- | --- |
| Full-vector HMoE residual may be present in old checkpoints | Removing its event slice can alter outputs or state-dict shape | C0/C2 compatibility experiment |
| Legacy stopping/window flags can be combined | Existing precedence is implicit and order-dependent | C1 conflict rejection |
| Flat PPO constructor and mixins encode duplicate ownership | Partial extraction can leave a second hidden optimizer path | C3 graph/gradient audit |
| Event-window and first-event labels have censoring/source semantics | A cleaner module name must not change target meaning | C0/C3 sidecar contract |
| Support-preserving collection changes rollout support | It is an action-changing intervention, not a diagnostic | C3 explicit admission |
| Policy-visible support differs from A5 acceptance | A green policy metric can still be rejected at runtime | C5 paired policy/runtime probes |
| Historical M3-S1/M3-S2 names are widely referenced | Bulk renaming creates unnecessary compatibility risk | C4 alias and namespace policy |
| Active configurations are experimental and unevenly validated | A default change can invalidate prior evidence | C0/C4 active-config matrix |

If any residual cannot be resolved within the cluster's two-round budget, mark
the stream Blocked rather than widening the plan.

## Review and status gate

The next action is a read-only independent review of this exact plan revision.
The reviewer must inspect the plan, the maintained policy baseline, the
governance reference documents, and the cited source/test surfaces. The
reviewer must not edit the worktree.

The review packet must contain:

    status: pass | partial | blocked | failed
    touched files: none (diagnostics-only)
    commands/outcomes:
    remaining paths:
    behavior risks:
    integration notes:

The owner will decide whether to revise the draft, open an implementation
package, or leave it held. Until that decision, this issue remains Lifecycle:
draft and no implementation is authorized.
