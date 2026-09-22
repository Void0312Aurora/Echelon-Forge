# Launch-Decision Architecture Reorganization

Status: 2026-09-22 held proposal; blocked pending an executable-owner and
compatibility-contract decision. No implementation package is authorized.

Language:

- English canonical: README.md
- Chinese navigation companion: [README.zh.md](README.zh.md)

Inputs:

- [Policy execution architecture baseline](../../../standards/policy_execution_architecture.md)
- [HMoE computation-gap issue](../hmoe_hierarchical_computation_gap/README.md)
- [Launch-window label-imbalance issue](../launch_window_label_imbalance/README.md)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)
- [Bilingual documentation policy](../../../../engineering/documentation/standards/bilingual_documentation_policy.md)
- [Worktree and path policy](../../../../engineering/workspace/worktree_and_path_policy.md)
- [Subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.md)
- [WP closure-lane policy](../../../../engineering/automation/standards/wp_closure_lane_policy.md)
- [Modularization issue plan](../../../../architecture/work/issues/modularization_plan.md)
- Current source and test surfaces listed in
  [the task-cluster plan](launch_decision_reorg_task_clusters_20260922.md)

Document kind: plan
Lifecycle: draft
Canonical: docs/learning/work/issues/launch_decision_reorg/README.md
Owner: learning/policy-architecture
Last verified: 2026-09-22
Content status: revised after blocked independent review; still held.

Documentation budget: three files are justified for this draft—this canonical
README, the required finite task-cluster document, and a short Chinese
navigation companion permitted for an existing work README. No dispatch queue,
acceptance packet, or current-status sidecar is created until an active package
is authorized.

## Purpose

This issue defines a bounded reorganization of the model-side launch-decision
surface. It is intended to make executable event ownership, auxiliary evidence,
policy-visible support, runtime A5 legality, optimizer ownership, and migration
behavior inspectable from one contract.

This is an issue/roadmap under work/issues/, not an active work package. It
does not authorize moving code, changing model parameters, changing rollout
semantics, changing runtime legality, changing active configurations, rewriting
checkpoints, or publishing a learned-firing acceptance result.

The plan is based on revision cfb9924e (the branch's origin/main baseline).
The governance reference worktree
.worktrees/long-horizon-governance-architecture was inspected read-only for
discipline; it is a separate worktree and its changes are not part of this
plan.

## Current state

### Verified implementation facts

| Surface | Current fact | Boundary |
| --- | --- | --- |
| Shared action path | action_net produces the hybrid action parameter vector; HMoE residuals are added to that vector in _get_action_dist_from_latent. | The current path has multiple event-logit contributors; hybrid_event_head is not the sole current contributor. |
| Direct event head | hybrid_event_head adds a two-value event residual in _apply_hybrid_event_head. | It is a contributor to the event delta, not proof of exclusive ownership. |
| Adapter paths | Window-classifier logic is evaluated before stopping logic; the current elif order gives it precedence when both flags are enabled. | Precedence is implementation order, not a typed conflict contract. |
| Policy margin update | The event-policy-margin lane selects action_net, hybrid_event_head, and policy-trunk parameters. | The optimizer lane currently spans more than one event module. |
| Headless configurations | The active air_combat_hybrid_v1 inventory at the baseline contains 14 configurations: 7 without hybrid_event_head_lr_scale and 7 with it. | A headless configuration must not silently be reported as a direct-head learned-firing result. The inventory must be regenerated at implementation time. |
| Support mask | _HybridActionDistribution applies the fire-event support mask internally before sampling, mode, log-prob, and entropy. | Policy-visible support is not A5 runtime acceptance. |
| Runtime gate | The A5 air-combat adapter owns final fire_once acceptance, FiredAssess, authority, readiness, ammunition, and repeat suppression. | A requested pulse, accepted pulse, and release are separate facts. |
| Auxiliary storage/objectives | Sidecar and replay data are distributed across _adaptive_kl_support.py, first_event_hazard.py, grouped_stopping.py, and _window_classifier_replay.py. | These helpers are part of the dependency surface even when a cluster does not write them. |

The active direct-boundary example remains:

examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1.json

It enables the direct fire-boundary update and explicitly disables both
hybrid_event_use_stopping_head and hybrid_event_use_window_classifier_head.
This is a compatibility baseline, not evidence that other configurations have
the same owner.

### Blocked review decision

The packet reviewed commit 67db9558, the previous revision of this issue.

The independent review of the previous revision returned blocked. The blocking
findings were:

1. the proposed sole hybrid_event_head owner did not match the current
   composed event path or headless configurations;
2. the Composer/mask/distribution boundary was ambiguous;
3. the verification matrix lacked an ef_py build preflight, fixed compatibility
   fixtures, tolerances, and several direct tests;
4. C2/C3/C4 write sets and dependencies were inconsistent;
5. a global worktree audit would be blocked by unrelated existing WIP;
6. the new substantive Chinese companion did not match the Tier B work-surface
   rule.

This revision addresses those findings at the plan level only. It does not
claim that the proposed contract has been implemented.

## Scope

### In scope

- A typed launch-decision composition contract in model_contracts.py.
- An explicit forward-path boundary in policies.py with provenance for every
  event-delta contributor.
- Translation and conflict validation for the current flat PPO and
  policy_kwargs surfaces.
- Alignment of event-window, fire-boundary, stopping, credit, first-event,
  sidecar, replay, and optimizer ownership.
- Checkpoint, optimizer-state, replay-state, and active-configuration migration
  rules.
- Focused policy, training, runtime, serialization, and architecture tests.

### Out of scope

- Re-designing HMoE family/subexpert routing or resolving the separate HMoE
  hierarchy issue.
- Changing reward shaping, mission observations, weapon physics, damage,
  kill/Pk semantics, or A5 runtime legality.
- Adding a new launch head only to make a probe green.
- Claiming timing optimality, quality-window closure, effects realism, or target
  kill acceptance.
- Bulk rewriting active configurations or destructive checkpoint conversion
  before the compatibility gate passes.
- Renaming historical M3-S1/M3-S2 metric namespaces.

## Proposed owner contract

The previous wording that made hybrid_event_head the sole owner is replaced by
a more precise definition:

> The sole learned executable owner is the event-delta composition contract:
> the declared mode that produces the unmasked fire-versus-hold delta consumed
> by the hybrid distribution. It is not necessarily one parameter module.

The contract must distinguish:

- Contributors: the base action_net event pair, HMoE event-slice residual,
  hybrid_event_head residual, and any explicitly admitted adapter residual.
- Owner mode: the named composition rule, contribution set, detach policy,
  trainable parameter set, optimizer lane, and compatibility behavior.
- Observable target: the event delta fire_logit - hold_logit, because a common
  shift of both logits does not change the categorical event probability. Raw
  hold/fire pairs remain in the trace for debugging and distribution
  reconstruction.

The contract must provide at least these modes:

| Mode | Purpose | Event contributors | Acceptance meaning |
| --- | --- | --- | --- |
| legacy_composed_v0 | Load and compare existing checkpoints/configurations. | Existing base action pair + HMoE event slice + whichever declared head/adapter is enabled. | Compatibility evidence only; not automatically a learned-firing claim. |
| direct_boundary_v1 | Target direct-boundary behavior. | Base contribution is recorded; HMoE event slice is either excluded/frozen by contract, or explicitly retained as a named compatibility adapter; trainable direct event delta is hybrid_event_head. | Learned-firing evidence is valid only when the contract and optimizer trace show the declared owner. |
| auxiliary_only_v1 | Train evidence without changing sampled event logits. | Credit, stopping, or window evidence is side-objective only. | Signal/capacity evidence; never learned-firing acceptance. |
| adapter_coupled_v1 | Future explicitly admitted coupling. | Exactly one adapter contribution, with coefficient, detach, optimizer, and acceptance probes declared. | Requires a separate contract review; stopping and window adapters cannot silently compete. |

Headless configurations must resolve explicitly to legacy_composed_v0 or to
another named mode. They may not inherit a hidden direct-head owner from a
zero/default learning-rate flag. C1 must record the seven headless and seven
enabled baseline configurations in a manifest and state which modes are
eligible for behavioral acceptance.

## Composer, mask, and distribution boundary

The target graph is deliberately fixed as:

    observation -> feature extractor -> actor latent
                                  -> action/HMoE contributors
                                  -> LaunchDecisionComposer
                                       -> unmasked hold/fire pair + owner trace
                                       -> _HybridActionDistribution
                                            -> support mask
                                            -> sample/mode/log-prob/entropy
                                       -> fire_once pulse
                                       -> A5 runtime adapter

LaunchDecisionComposer is a proposed extraction boundary, not an immediate
module addition. Its interface:

- accepts the typed owner mode, latent features, base event pair, and declared
  contributor outputs;
- returns an unmasked hold/fire pair, the composed event delta, and a
  provenance trace;
- does not accept, derive, or apply the support mask;
- does not calculate labels, rewards, runtime acceptance, or A5 state.

_HybridActionDistribution remains the sole policy-side owner of support
masking, sampling, deterministic mode, log-probability, and entropy. The trace
must record mask source and final support as downstream facts, but the Composer
must not report them as its applied output. A5 remains the final runtime
authority.

The trace must include:

- owner mode and compatibility mode;
- raw base hold/fire pair;
- each contributor's delta, detach status, and parameter IDs;
- composed unmasked pair and fire-minus-hold delta;
- distribution mask source and applied support;
- optimizer/dedicated-update parameter IDs;
- requested, accepted, released, rejected, and repeat-suppressed counters when
  a runtime probe is attached.

## Phase plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| P0 Boundary | Freeze owner vocabulary, headless inventory, source revision, and no-goals. | This held issue exists. | Baseline manifest and owner decision record are complete. | held |
| P1 Evidence | Establish build preflight, fixtures, contributor traces, and current test coverage. | P0 complete. | All required artifacts or explicit blocked residuals are recorded. | blocked |
| P2 Contract | Implement only typed owner/mode validation and serialization tests. | P1 accepted by owner. | Conflicts reject; legacy modes round-trip without changed outputs. | not authorized |
| P3 Forward path | Introduce Composer boundary and preserve compatibility mode. | P2 accepted. | Owner trace, unmasked pair, mask handoff, and state-dict behavior are tested. | not authorized |
| P4 Training/config integration | Align objectives, sidecars, replay, optimizer groups, and config/checkpoint migration. | P3 accepted. | All declared write sets and migration gates pass. | not authorized |
| P5 Acceptance/closure | Run focused tests, runtime probes, target-scoped worktree checks, independent review, and closure documentation. | P4 mergeable or explicitly blocked. | Owner verdict is Mergeable, Blocked, or Closed with residual owners. | not authorized |

## Task clusters

The finite cluster plan is maintained separately as required by the repository
subproject standard:

[launch_decision_reorg_task_clusters_20260922.md](launch_decision_reorg_task_clusters_20260922.md)

The implementation DAG is intentionally serial at shared architecture seams:

    C0 -> C1 -> C2 -> C3 -> C4 -> C5

Only read-only inventories may be prepared in parallel. No two implementation
clusters may edit the owner contract, forward boundary, or compatibility
terminology concurrently. Each cluster has a maximum of two implementation
rounds; exceeding that cap requires re-scoping.

## Outputs and evidence

### Build preflight

Policy/runtime pytest collection requires a local ef_py artifact;
python/runtime_bootstrap.py::ensure_repo_imports fails closed when it is absent.
Before running policy or runtime tests, a Windows implementation lane must run
from the worktree root:

~~~powershell
$build = 'D:\workshop\Research\Echelon-Forge-build\ld-arch-plan'
cmake -S . -B $build -DCMAKE_BUILD_TYPE=Debug
cmake --build $build --target ef_core ef_py ef_test --parallel 4
$env:CMO_BUILD_DIR = $build
python -c "from python.runtime_bootstrap import ensure_repo_imports; ensure_repo_imports(); import ef_py; print(ef_py.__file__)"
~~~

The build directory must remain outside the checkout. If this preflight cannot
be completed, the test lane is Blocked, not green-by-omission.

### Compatibility fixtures and objective gates

C0 must freeze a manifest containing:

- all active air_combat_hybrid_v1 configurations, including the baseline seven
  headless and seven event-head-enabled entries;
- one representative checkpoint/state-dict for each available owner mode;
- optimizer state and parameter-group metadata for each representative mode;
- window-classifier replay state, including storage type, capacity, keys, and
  positive/negative rows where available;
- a fixed observation fixture set and CPU float32 execution environment.

The compatibility probe uses seeds 0, 1, 2 and three declared episodes per
seed for runtime behavior. For fixed observation fixtures, the legacy mode must
preserve tensor shapes, state-dict keys, optimizer-group names/order, and
masked support exactly. CPU float32 unmasked event pairs, event deltas,
probabilities, log-probabilities, and entropies use
torch.testing.assert_close(rtol=1e-5, atol=1e-6). Any intentional drift
outside that tolerance requires a named migration mode and an updated expected
fixture; it cannot be hidden under a rename.

Checkpoint loading must either restore the optimizer and replay state exactly
or fail with an actionable migration error. A successful policy-only load is
not evidence of optimizer/replay compatibility.

### Required tests

The implementation package must run the existing focused lanes after the build
preflight:

~~~text
python -m pytest tests/policy/test_execution_policy_event_heads.py
python -m pytest tests/policy/test_event_head_update_contracts.py
python -m pytest tests/policy/test_execution_policy_optimizer_heads.py
python -m pytest tests/policy/test_auxiliary_event_credit_updates.py
python -m pytest tests/policy/test_execution_policy_transformer_surface.py
python -m pytest tests/training/test_event_timing_training_config_contracts.py
python -m pytest tests/training/test_air_combat_training_entry_contracts.py
python -m pytest tests/runtime/air_combat/test_fire_action_release_gate.py
python -m pytest tests/runtime/air_combat/test_diagnostics_process_probe_summary.py
~~~

New tests must cover owner-mode construction, conflict rejection, contributor
traces, HMoE event-slice isolation/compatibility, mask handoff, gradients,
optimizer ownership, legacy config translation, checkpoint/optimizer/replay
round trips, and deterministic/stochastic distribution invariants.

The closure lane also runs git diff --check, the path-length ratchet, and the
architecture governance tests. Worktree acceptance is target-scoped:

~~~powershell
git -C <repo>\.worktrees\ld-arch-plan status --porcelain=v1 -uall
git -C <repo> worktree list --porcelain
~~~

The target must have zero untracked entries, be under <repo>\.worktrees, and
remain reachable. The global audit_worktrees.py report may be recorded as
informational context, but findings from unrelated pre-existing worktrees are
not acceptance failures for this plan and must not be repaired by this work
package.

## Acceptance gate

This issue may be promoted to an implementation package only when an owner
review accepts all of the following:

- the event-delta composition contract, not a convenient module name, is the
  declared unique learned executable owner;
- headless and direct-boundary configurations have explicit modes and
  acceptance eligibility;
- Composer returns unmasked event outputs and the distribution alone owns the
  policy support mask;
- the build preflight and all required fixtures are reproducible;
- numerical tolerances, seed/episode counts, checkpoint/optimizer/replay
  migration rules, and test commands are fixed;
- C0-C5 write sets and the serial dependency DAG are internally consistent;
- target-scoped worktree checks pass without touching unrelated WIP;
- Tier B documentation remains English-canonical with only a navigation
  companion, unless the owner explicitly promotes and registers a bilingual
  pair;
- an independent reviewer returns pass or an explicitly accepted partial with
  no unresolved P1.

Acceptance still reports requested, accepted, released, authorized-release,
rejection, and repeat-suppression counters separately. Kill, damage, Pk, and
effects results are not substitutes.

## Residuals and next steps

The following residuals remain intentionally open:

| Residual | Owner/gate | Replacement condition |
| --- | --- | --- |
| Whether direct-boundary mode excludes or freezes HMoE event dimensions without state-dict drift | C0/C2 | A measured fixture comparison and explicit migration decision |
| Which active configurations qualify for learned-firing acceptance | C0/C4 | Mode manifest and owner-approved eligibility table |
| Whether old optimizer/replay states can be restored | C4 | Exact round-trip or named migration error |
| Local ef_py artifact availability | P1 | Build preflight succeeds with external CMO_BUILD_DIR |
| Independent review availability | C5 | Read-only reviewer returns a packet against the revised commit |

Until these are resolved, the issue remains held and no implementation package
should be opened.

## Archive

This issue is not closed or archived. After an implementation stream is
accepted, lasting owner decisions should move to the maintained policy
baseline; the accepted review and residual record should remain under the
owner's review/closure surface. If the proposal is abandoned, retain this
draft as a superseded issue and record the replacement decision rather than
deleting the evidence boundary.
