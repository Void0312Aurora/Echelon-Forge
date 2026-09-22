# Launch-Decision Reorganization Task Clusters

Status: 2026-09-22 finite task-cluster plan for
launch_decision_reorg/README.md. The clusters are planned only; no worker is
authorized until the parent issue is promoted to an active work package.

Parent subproject: [README.md](README.md)

## Boundary decision

The implementation target is an explicit event-delta composition contract.
The contract, not the name of one head, owns the declared executable
fire-versus-hold delta. The Composer returns an unmasked event pair and trace;
the hybrid distribution owns policy-side support masking and probability
operations; the A5 runtime adapter owns final acceptance.

The implementation must preserve a legacy compatibility mode before enabling
the direct-boundary target mode. HMoE routing, reward/physics semantics, and
runtime legality are outside the write boundary.

## Finite task cluster list

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | Main thread / architecture owner | architecture-critical / model selected at dispatch / high-equivalent | Freeze source revision, all active hybrid configs, owner vocabulary, fixtures, build preflight, and no-goals. | Parent active-package README/status only after promotion; external fixture manifest; no production code in this draft. | No renaming, forward-path edit, config rewrite, checkpoint conversion, or worktree repair. | Enumerate active configs; inspect source/test matrix; target worktree status; external build/import preflight; record missing artifacts as residuals. | Owner signs a complete baseline manifest and explicit blocked residuals. | First; no parallel implementation writes. | 1 evidence round | planned |
| C1 | Main thread or one contract worker | architecture-critical / model selected at dispatch / high-equivalent | Define owner modes, contributor/delta semantics, adapter exclusivity, serialization, and migration schema. | python/rl/policy_algo/model_contracts.py; new/extended contract tests under tests/policy/; active-package notes. | No policy forward edit, no new learned head, no A5 change. | Direct, legacy-composed, auxiliary-only, adapter-conflict, headless, and serialization construction tests. | Every current flag and headless configuration maps to one mode, with explicit conflict/error behavior. | Depends on C0; serial. | 2 implementation rounds |
| C2 | One forward-path worker | architecture-critical / model selected at dispatch / high-equivalent | Make the event-delta boundary explicit while preserving legacy outputs and state-dict behavior. | python/rl/policy_algo/policies.py; only narrowly scoped HMoE event-slice helper if required; tests/policy/test_execution_policy_event_heads.py; tests/policy/test_execution_policy_optimizer_heads.py; new Composer/trace tests. | No HMoE routing redesign, reward/runtime change, or silent mask movement. | Contributor traces; raw pair and delta comparison; unmasked output; mask handoff; deterministic mode; stochastic log-prob/entropy; old checkpoint load. | Exactly one declared owner mode is visible; Composer does not apply support mask; legacy compatibility fixture passes. | Depends on C1; serial before C3/C4 writes. | 2 implementation rounds |
| C3 | One objective/optimizer worker | cross-file architecture / model selected at dispatch / high-equivalent | Align objectives, sidecars, replay, labels, gradients, and optimizer parameter ownership with the C2 mode. | Mandatory: python/rl/policy_algo/ppo_adaptive_kl.py and the four event mixins (_first_event_mixin.py, _event_credit_mixin.py, _grouped_stopping_mixin.py, _event_window_mixin.py). Conditional only when C0/C3 proves a schema mismatch: _adaptive_kl_support.py, first_event_hazard.py, grouped_stopping.py, _window_classifier_replay.py. Tests: test_event_head_update_contracts.py, test_auxiliary_event_credit_updates.py, and related training tests. If conditional files are not admitted, they remain read-only dependencies. | No new labels, no support-preserving collection change unless separately admitted, and no forward-path edits outside the C2 interface. | Gradient and dedicated-update isolation; sidecar source/censoring metadata; replay round trip; optimizer group names/order/IDs; metric namespace compatibility. | Every objective is auxiliary-only or points to the same declared owner; no hidden action_net/HMoE update remains. | Depends on C2; serial. | 2 implementation rounds |
| C4 | One config/checkpoint migration worker | compatibility/integration / model selected at dispatch / high-equivalent | Translate flat config and checkpoint surfaces without silent precedence or state drift. | python/training/deps.py; python/training/bootstrap.py; python/experiment/air_combat_matrix.py; python/rl/policy_checkpoint.py; representative active config validation fixtures; tests/training/test_event_timing_training_config_contracts.py; tests/training/test_air_combat_training_entry_contracts.py; new migration tests. Active JSON files are read-only inputs unless a separately approved migration package names them. | No bulk active-config rewrite, destructive conversion, or runtime A5 edit. | All 14 baseline configs; headless/direct/adapter mode matrix; config round trip; state-dict key/shape comparison; optimizer/replay restore or actionable migration error. | Legacy direct-boundary and headless samples resolve deterministically; drift outside declared tolerances is rejected or named as migration. | Depends on C3; serial. | 2 implementation rounds |
| C5 | Serial integration/diagnostics worker | diagnostics/closure / model selected at dispatch / high-equivalent | Run acceptance, runtime probes, target-scoped worktree checks, and independent review; synchronize only required closure docs. | tests/runtime/air_combat/test_fire_action_release_gate.py; tests/runtime/air_combat/test_diagnostics_process_probe_summary.py; required new tests; active-package acceptance/review record. No unrelated worktree files. | No new implementation scope, global WIP repair, or changing the acceptance claim to kill/damage/Pk. | Build preflight; full focused test matrix; git diff --check; path-length ratchet; target worktree status/list; runtime counters; independent review packet. | Owner verdict Mergeable, Blocked, or Closed with residual IDs and no unresolved P1. | Depends on C4; always serial. | 1 closure round |

Model IDs are intentionally resolved when a future worker is dispatched. This
draft records the required risk tier and reasoning budget without copying a
historical model identifier.

## Dispatch rules

- No worker may be dispatched until the parent issue is promoted to an active
  work package and C0 is complete.
- Each worker maps to exactly one cluster and one disjoint write set.
- C0 through C5 form a serial implementation DAG. Read-only inventories may be
  prepared in parallel, but no implementation cluster may edit shared owner
  terminology concurrently.
- A cluster has at most two implementation/repair rounds. A third round is a
  planning failure signal and requires re-scoping.
- C5 remains serial until all earlier clusters return complete packets.
- The main thread owns final scope, acceptance, publication, and merge
  decisions.

## Worker packet requirements

Every delegated worker returns:

    status: pass | partial | blocked | failed
    touched files:
    commands/outcomes:
    remaining paths:
    behavior risks:
    integration notes:

The packet must state whether a file was written or only read. A transport
failure is not implementation evidence and does not change the cluster status.

## Validation plan

### Build and import preflight

From the target worktree, with output outside the checkout:

~~~powershell
$build = 'D:\workshop\Research\Echelon-Forge-build\ld-arch-plan'
cmake -S . -B $build -DCMAKE_BUILD_TYPE=Debug
cmake --build $build --target ef_core ef_py ef_test --parallel 4
$env:CMO_BUILD_DIR = $build
python -c "from python.runtime_bootstrap import ensure_repo_imports; ensure_repo_imports(); import ef_py; print(ef_py.__file__)"
~~~

If ensure_repo_imports cannot find a local ef_py artifact, policy/runtime
pytest collection is blocked. Do not fall back to an installed extension.

### Focused test matrix

The following existing tests are required after preflight:

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

Additional gates:

- owner-mode and conflict matrix tests;
- contributor/delta/mask trace tests;
- checkpoint, optimizer-state, and replay-state round trips;
- git diff --check;
- path-length budget and architecture-governance tests;
- runtime counters for requested, accepted, released, authorized release,
  rejected reasons, and repeat suppression.

### Compatibility gate

C0 freezes:

- all active air_combat_hybrid_v1 configs, with the observed headless/enabled
  split;
- representative state-dict, optimizer, and replay fixtures for every mode
  that actually exists;
- fixed observation fixtures and CPU float32;
- runtime seeds 0, 1, 2 with three declared episodes per seed.

For legacy mode, require exact shapes, state-dict keys, optimizer-group
names/order, and masked support. Compare unmasked event pairs, event deltas,
probabilities, log-probabilities, and entropies with
torch.testing.assert_close(rtol=1e-5, atol=1e-6). If a deliberate target-mode
change exceeds that tolerance, require a named migration mode and expected
fixture. Optimizer and replay restoration must be exact or fail with an
actionable migration error.

### Target-scoped worktree gate

The acceptance gate checks only the target worktree:

~~~powershell
git -C <repo>\.worktrees\ld-arch-plan status --porcelain=v1 -uall
git -C <repo> worktree list --porcelain
~~~

The target must be under the repository .worktrees directory, reachable, and
free of untracked entries. The global audit_worktrees.py command may be run for
context, but unrelated existing outside-policy or untracked findings are
inherited residuals, not this cluster's failure, and must not be repaired here.

## Acceptance criteria

The stream is Mergeable only when:

- one owner mode and one event-delta composition contract are observable;
- headless and direct-boundary configurations have explicit eligibility;
- Composer output is unmasked and distribution masking is single-owned;
- all focused tests and compatibility gates pass after build preflight;
- optimizer/replay/config/checkpoint behavior is explicit;
- target-scoped worktree checks pass;
- independent review has no unresolved P1.

Mergeable is not Closed. Closure additionally requires the owner review,
required status/index synchronization, residual ownership, and the final
bilingual-policy decision.

## Residual map

| Residual | Trigger | Owner/next step |
| --- | --- | --- |
| HMoE event-slice exclusion versus compatibility adapter | State-dict/output drift in C2 | C0/C2 owner decision and migration fixture |
| Headless acceptance eligibility | Missing direct head or ambiguous mode | C0/C4 mode manifest |
| ef_py unavailable | Build/import preflight fails | Infrastructure/build owner; keep stream Blocked |
| Optimizer/replay state drift | Round trip fails | C3/C4 migration owner |
| Unrelated worktree findings | Global audit reports inherited WIP | Record as inherited; do not edit unrelated trees |
| Independent review unavailable | Reviewer transport/upstream failure | Keep draft held and retry only after external state changes |
