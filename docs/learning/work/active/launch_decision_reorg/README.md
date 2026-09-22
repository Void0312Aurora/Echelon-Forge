# Launch-Decision Architecture Reorganization

Status: 2026-09-23 implementation complete; owner verdict `Mergeable` on the
target branch `codex/launch-decision-reorg`.

Language:

- English canonical: README.md
- Chinese navigation companion: [README.zh.md](README.zh.md)

Inputs:

- [Policy execution architecture baseline](../../../standards/policy_execution_architecture.md)
- [HMoE computation-gap issue](../../issues/hmoe_hierarchical_computation_gap/README.md)
- [Launch-window label-imbalance issue](../../issues/launch_window_label_imbalance/README.md)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)
- [Bilingual documentation policy](../../../../engineering/documentation/standards/bilingual_documentation_policy.md)
- [Worktree and path policy](../../../../engineering/workspace/worktree_and_path_policy.md)
- [Subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.md)
- [WP closure-lane policy](../../../../engineering/automation/standards/wp_closure_lane_policy.md)
- [Modularization issue plan](../../../../architecture/work/issues/modularization_plan.md)
- Current source and test surfaces listed in
  [the task-cluster plan](launch_decision_reorg_task_clusters_20260922.md)

Document kind: plan
Lifecycle: active
Canonical: docs/learning/work/active/launch_decision_reorg/README.md
Owner: learning/policy-architecture
Last verified: 2026-09-23
Content status: owner-finalized and implemented through C0-C5 after the blocked
review findings were resolved in the plan. No further independent review gate is
required for this stream.

Documentation budget: three files are justified for this active package—this
canonical README, the finite task-cluster document, and a short Chinese
navigation companion permitted for an existing work README. No extra dispatch
queue, review packet, or current-status sidecar is created unless a later
implementation fact makes one necessary.

## Purpose

This active package defines a bounded reorganization of the model-side launch-decision
surface. It is intended to make executable event ownership, auxiliary evidence,
policy-visible support, runtime A5 legality, optimizer ownership, and migration
behavior inspectable from one contract.

The package authorizes the implementation sequence below. It does not
authorize changing model parameters, rollout semantics, runtime legality,
active configurations, or checkpoint contents outside the named compatibility
and migration surfaces. A learned-firing result remains valid only when its
declared mode and owner trace satisfy the acceptance gate.

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

### Prior review findings and final owner decision

The packet reviewed commit 67db9558, the previous revision of this issue.

The previous independent review returned blocked. Its findings are retained as
historical evidence, and the owner decisions below close the planning questions
without creating another review gate:

1. the proposed sole hybrid_event_head owner did not match the current
   composed event path or headless configurations;
2. the Composer/mask/distribution boundary was ambiguous;
3. the verification matrix lacked an ef_py build preflight, fixed compatibility
   fixtures, tolerances, and several direct tests;
4. C2/C3/C4 write sets and dependencies were inconsistent;
5. a global worktree audit would be blocked by unrelated existing WIP;
6. the new substantive Chinese companion did not match the Tier B work-surface
   rule.

The implementation branch followed these decisions. The owner evidence and
residuals for the completed C0-C5 stream are recorded below; this document does
not claim runtime quality, kill, damage, Pk, or effects acceptance.

### Final architecture decision

The long-term default is a governed composition owner. The owner is the typed
event-delta composition contract, not a particular neural module. The strict
direct-boundary profile remains an intentionally narrower acceptance and causal
attribution lane.

The profiles are fixed as follows:

- `legacy_composed_v0` preserves existing checkpoint/config behavior for load
  and comparison. When an old configuration enables both adapters, the legacy
  window-classifier-before-stopping precedence is preserved and recorded as
  `legacy_window_precedence` in the trace. New configurations must reject that
  conflict instead of inheriting the precedence silently.
- `direct_boundary_v1_strict` permits no executable adapter contribution. The
  base action pair is recorded for comparison, but the HMoE event slice is
  excluded from the direct learned delta and is detached in the dedicated
  direct-boundary update. Only `hybrid_event_head` parameters may receive that
  update. `action_net`, the policy trunk, and HMoE event parameters are frozen
  for the dedicated strict update. A run that trains those shared parameters
  must use a coupled profile and is not eligible for strict learned-firing
  acceptance.
- `governed_composed_v1` is the long-term default. Base action, HMoE event
  residual, and `hybrid_event_head` may contribute only when listed in the
  resolved contract. Ordinary PPO and event-policy-margin updates may write
  only the parameter roles declared by that contract and must emit the same
  owner trace.
- `auxiliary_only_v1` never changes sampled event logits.
- `adapter_coupled_v1` admits exactly one named adapter with an explicit
  coefficient, detach policy, optimizer ownership, and acceptance probe. Window
  and stopping adapters may not compete in a new configuration.

This makes the strict profile a safe experiment rather than the permanent
architecture, while keeping the long-term composition surface extensible and
fail-closed.

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
| legacy_composed_v0 | Load and compare existing checkpoints/configurations. | Existing base action pair + HMoE event slice + the legacy declared head/adapter. If both legacy adapters are enabled, window-classifier precedence is preserved only for compatibility and recorded in the trace. | Compatibility evidence only; never automatically a learned-firing claim. |
| direct_boundary_v1_strict | Controlled direct-boundary training and learned-firing acceptance. | Base pair is recorded; HMoE event slice and all adapters are excluded from the direct delta. Only hybrid_event_head is trainable in the dedicated direct-boundary update; shared action/trunk/HMoE parameters are detached and frozen for that update. | Learned-firing evidence is valid only when the strict owner and parameter trace are present. Shared-parameter training requires another profile. |
| governed_composed_v1 | Long-term default composition profile. | Any base, HMoE, or event-head contributor explicitly admitted by the resolved contract; every trainable role is listed in the owner trace. | Learned behavior is attributable to the resolved composition, not to an assumed module name. |
| auxiliary_only_v1 | Train evidence without changing sampled event logits. | Credit, stopping, or window evidence is side-objective only. | Signal/capacity evidence; never learned-firing acceptance. |
| adapter_coupled_v1 | Future explicitly admitted coupling. | Exactly one adapter contribution, with coefficient, detach, optimizer, and acceptance probes declared. | Requires a separate contract review; stopping and window adapters cannot silently compete. |

Headless configurations must resolve explicitly to legacy_composed_v0,
governed_composed_v1, or another named mode. They may not inherit a hidden
direct-head owner from a zero/default learning-rate flag. C1 must record the
seven headless and seven enabled baseline configurations in a manifest and
state which modes are eligible for behavioral acceptance.

The owner contract also fixes the training scopes. A strict direct-boundary
update may write only hybrid_event_head.*; an ordinary PPO update that writes
shared action/trunk/HMoE parameters must resolve governed_composed_v1 (or an
explicit future coupled profile). event-policy-margin is not allowed to
silently widen the strict write set.

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
| P0 Boundary | Freeze owner vocabulary, headless inventory, source revision, and no-goals. | The final owner decision in this README. | Baseline manifest and owner decision record are complete. | accepted |
| P1 Evidence | Establish build preflight, deterministic fixtures, contributor traces, and current test coverage. | P0 accepted. | Manifest, external artifacts, and build/import preflight are reproducible. | accepted |
| P2 Contract | Implement typed owner/mode validation and serialization tests. | P1 complete. | Conflicts reject; legacy modes round-trip without changed outputs. | accepted |
| P3 Forward path | Introduce Composer boundary and preserve compatibility mode. | P2 accepted. | Owner trace, unmasked pair, mask handoff, and state-dict behavior are tested. | accepted |
| P4 Training/config integration | Align objectives, sidecars, replay, optimizer groups, and config/checkpoint migration. | P3 accepted. | All declared write sets and migration gates pass. | accepted |
| P5 Acceptance/closure | Run focused tests, runtime probes, target-scoped worktree checks, and owner closure documentation. | P4 mergeable or explicitly blocked. | Main-thread owner verdict is Mergeable, Blocked, or Closed with residual owners. | mergeable |

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
$build = 'D:\workshop\Research\Echelon-Forge-build\ld-reorg'
cmake -S . -B $build -DCMAKE_BUILD_TYPE=Debug
cmake --build $build --target ef_core ef_py ef_test --parallel 4
$env:CMO_BUILD_DIR = $build
python -c "from python.runtime_bootstrap import ensure_repo_imports; ensure_repo_imports(); import ef_py; print(ef_py.__file__)"
~~~

The build directory must remain outside the checkout. If this preflight cannot
be completed, the test lane is Blocked, not green-by-omission.

### Compatibility fixtures and objective gates

Fixture identity is fixed rather than conceptual:

- The tracked manifest is
  `tests/fixtures/launch_decision_reorg/v1/manifest.json`.
- The deterministic generator is
  `tools/maintenance/generate_launch_decision_fixtures.py`.
- Generated artifacts live outside the checkout under
  `D:\workshop\Research\Echelon-Forge-fixtures\launch_decision_reorg\v1` by
  default. `EF_LAUNCH_DECISION_FIXTURE_ROOT` may override that root, but the
  manifest must record the resolved root-relative paths.
- The manifest is UTF-8 JSON and records the source commit, generator SHA-256,
  Python/Torch versions, profile/config IDs, seeds, episode counts, tensor
  dtypes, and a SHA-256 for every artifact. State dictionaries and optimizer
  state use `torch.save` `.pt` files; fixed observations use a separate
  `observations.pt`; replay rows use UTF-8 JSONL; no opaque unversioned binary
  is accepted.
- If a representative checkpoint or replay artifact does not exist, the
  generator creates it from the fixed tiny policy/config specification and
  seeds in the manifest. It must refuse to overwrite a different manifest and
  must emit the same bytes for the same source/generator identity.

C0 must freeze a manifest containing:

- all active air_combat_hybrid_v1 configurations, including the baseline seven
  headless and seven event-head-enabled entries;
- one representative checkpoint/state-dict for each owner mode that actually
  exists;
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

The named new tests are:

- `tests/policy/test_launch_decision_model_contracts.py` for owner-mode
  construction, conflict rejection, headless resolution, and serialization;
- `tests/policy/test_launch_decision_composer.py` for contributor traces, HMoE
  strict isolation, unmasked output, mask handoff, and distribution invariants;
- `tests/policy/test_launch_decision_optimizer_ownership.py` for gradient and
  dedicated-update write-set checks;
- `tests/training/test_launch_decision_migration.py` for legacy config,
  checkpoint, optimizer, and replay round trips.

Existing focused tests remain required. No open-ended “related tests” write set
is permitted.

The closure lane also runs git diff --check, the path-length ratchet, and the
architecture governance tests. Worktree acceptance is target-scoped:

~~~powershell
git -C <repo>\.worktrees\ld-arch-plan status --porcelain=v1 -uall
git -C <repo> worktree list --porcelain
~~~

The target is `.worktrees\ld-reorg`; it must have zero untracked entries, be
under <repo>\.worktrees, and
remain reachable. The global audit_worktrees.py report may be recorded as
informational context, but findings from unrelated pre-existing worktrees are
not acceptance failures for this plan and must not be repaired by this work
package.

## Acceptance gate

This active package is accepted incrementally by the main-thread owner when
all of the following are true:

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
- every residual has an owner, replacement condition, and next step. No
  independent reviewer is required for this stream; focused tests, fixture
  hashes, and the owner trace are the acceptance evidence.

Acceptance still reports requested, accepted, released, authorized-release,
rejection, and repeat-suppression counters separately. Kill, damage, Pk, and
effects results are not substitutes.

## C5 owner verdict and evidence

Verdict: `Mergeable` for the target worktree and branch. The implementation
stream completed C0-C5 in serial batches; it is not published or merged by this
record.

Evidence recorded on 2026-09-23:

- External Debug preflight succeeded for `ef_core`, `ef_py`, and `ef_test`, and
  `ensure_repo_imports()` resolved the local `ef_py` artifact from
  `D:\workshop\Research\Echelon-Forge-build\ld-reorg`.
- The deterministic fixture generator passed twice with the tracked manifest,
  current ownership roles, fixed CPU float32 observations, seeds `0/1/2`, and
  three episodes per seed.
- Policy/ownership focused matrix: `79 passed, 24 subtests passed`; the
  migration/config matrix: `33 passed, 42 subtests passed`; runtime release and
  diagnostics gates: `26 passed`.
- The target worktree is clean, reachable under `.worktrees\ld-reorg`, and has
  no untracked entries. `git diff --check` and the path-length budget pass.
- The owner trace shows an unmasked Composer result, distribution-owned mask,
  explicit mode, contributor roles, and dedicated update parameter IDs.

One broad governance invocation retained an inherited, out-of-scope failure:
`docs/systems/effects/reviews/continuous_rod_component_load_admission_20260914/README.md`
lacks the repository-wide metadata fields. It belongs to another subproject and
was not edited; the targeted worktree and all launch-decision gates pass. This
is a residual for the documentation-governance owner, not a launch-decision P1.

The stream makes no claim about kill, damage, Pk, timing optimality, or effects
quality. Those remain outside this package's acceptance boundary.

## Residuals and next steps

The following register records resolved implementation residuals and the one
inherited documentation residual that remains outside this stream:

| Residual | Owner/gate | Replacement condition |
| --- | --- | --- |
| Strict direct-boundary freeze and write set | resolved in C2/C3 | Keep the strict trace and dedicated-head write-set tests with future changes |
| Which active configurations qualify for learned-firing acceptance | resolved in C0/C4 | Use the tracked mode manifest; do not infer eligibility from a head name |
| Whether old optimizer/replay states can be restored | resolved in C4 | Require the envelope manifest or emit the named migration error |
| Local ef_py artifact availability | resolved in C5 for this target | Re-run external build preflight after native/runtime changes |
| Inherited effects-review metadata gap | documentation-governance owner | Add required metadata in that separate worktree; do not alter this stream |

These are implementation residuals, not reasons to reopen the plan or request
another review. A phase may be marked blocked when its declared infrastructure
or migration condition is unavailable; the next phase must not silently bypass
that block.

## Archive

This issue is not closed or archived. After an implementation stream is
accepted, lasting owner decisions should move to the maintained policy
baseline; the accepted review and residual record should remain under the
owner's review/closure surface. If the proposal is abandoned, retain this
draft as a superseded issue and record the replacement decision rather than
deleting the evidence boundary.
