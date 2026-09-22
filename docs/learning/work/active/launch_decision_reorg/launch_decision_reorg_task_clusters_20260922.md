# Launch-Decision Reorganization Task Clusters

Status: 2026-09-23 finite task-cluster plan completed through C0-C5; owner
verdict `Mergeable` on `codex/launch-decision-reorg`. No independent review
dispatch is required.

Parent subproject: [README.md](README.md)

## Boundary decision

The implementation target is an explicit event-delta composition contract.
The long-term default is governed_composed_v1: the contract, not the name of
one head, owns the declared executable fire-versus-hold delta. The Composer
returns an unmasked event pair and trace; the hybrid distribution owns
policy-side support masking and probability operations; the A5 runtime adapter
owns final acceptance. direct_boundary_v1_strict is a separate controlled
profile: no adapters or HMoE event contribution enter its direct delta, and
only hybrid_event_head.* may be written by its dedicated update.

Legacy loading preserves the old window-before-stopping precedence only under
legacy_composed_v0, records legacy_window_precedence, and rejects the same
conflict in new configurations.

The implementation must preserve a legacy compatibility mode before enabling
the direct-boundary target mode. HMoE routing, reward/physics semantics, and
runtime legality are outside the write boundary.

## Finite task cluster list

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | Main thread / architecture owner | architecture-critical / n/a / high | Freeze source revision, all active hybrid configs, owner vocabulary, fixture identity, build preflight, and no-goals. | `docs/learning/work/active/launch_decision_reorg/README.md`; `docs/learning/work/active/launch_decision_reorg/launch_decision_reorg_task_clusters_20260922.md`; `tests/fixtures/launch_decision_reorg/v1/manifest.json`; `tools/maintenance/generate_launch_decision_fixtures.py`. | No policy forward edit, config rewrite, checkpoint conversion, or unrelated worktree repair. | Active-config census; deterministic generator; external fixture hashes; local ef_py import; target worktree status. | Manifest records all 14 configs, exact fixture root/format/hash rules, and explicit infrastructure residuals. | First; serial. | 1 evidence round | accepted |
| C1 | Main thread / contract owner | architecture-critical / n/a / high | Define owner modes, contributor/delta semantics, adapter exclusivity, serialization, and migration schema. | `python/rl/policy_algo/model_contracts.py`; `tests/policy/test_launch_decision_model_contracts.py`. | No policy forward edit, new learned head, or A5 change. | `python -m pytest tests/policy/test_launch_decision_model_contracts.py -q`; `python -m pytest tests/training/test_air_combat_training_entry_contracts.py -q`. | Every current flag and headless configuration maps to one mode; new adapter conflicts reject; both named test lanes pass. | Depends on C0; serial. | 2 implementation rounds | accepted |
| C2 | Main thread / forward-path owner | architecture-critical / n/a / high | Make the event-delta boundary explicit while preserving legacy outputs and state-dict behavior. | `python/rl/policy_algo/policies.py`; `tests/policy/test_launch_decision_composer.py`; `tests/policy/test_execution_policy_event_heads.py`; `tests/policy/test_execution_policy_optimizer_heads.py`. | No HMoE routing redesign, reward/runtime change, or support-mask movement. | Contributor traces; raw pair/delta comparison; strict HMoE isolation; unmasked output; mask handoff; deterministic mode; stochastic log-prob/entropy; old checkpoint load. | Exactly one declared owner mode is visible; Composer does not apply support mask; legacy fixture passes. | Depends on C1; serial before C3/C4 writes. | 2 implementation rounds | accepted |
| C3 | Main thread / objective owner | cross-file architecture / n/a / high | Align objectives, sidecars, replay, labels, gradients, and optimizer parameter ownership with the C2 mode. | `python/rl/policy_algo/ppo_adaptive_kl.py`; `python/rl/policy_algo/_first_event_mixin.py`; `python/rl/policy_algo/_event_credit_mixin.py`; `python/rl/policy_algo/_grouped_stopping_mixin.py`; `python/rl/policy_algo/_event_window_mixin.py`; `tests/policy/test_launch_decision_optimizer_ownership.py`; `tests/policy/test_event_head_update_contracts.py`; `tests/policy/test_auxiliary_event_credit_updates.py`. Read-only dependencies: `python/rl/policy_algo/_adaptive_kl_support.py`; `python/rl/policy_algo/first_event_hazard.py`; `python/rl/policy_algo/grouped_stopping.py`; `python/rl/policy_algo/_window_classifier_replay.py`. | No new labels, collection-support change, or forward-path edit outside the C2 interface. | Gradient/dedicated-update isolation; sidecar metadata; replay round trip; optimizer names/order/IDs; metric namespace compatibility. | Every objective is auxiliary-only or points to the declared owner; no hidden action_net/HMoE update remains in strict mode. | Depends on C2; serial. | 2 implementation rounds | accepted |
| C4 | Main thread / migration owner | compatibility/integration / n/a / high | Translate flat config and checkpoint surfaces without silent precedence or state drift. | `python/training/deps.py`; `python/training/bootstrap.py`; `python/experiment/air_combat_matrix.py`; `python/rl/policy_checkpoint.py`; `tests/training/test_launch_decision_migration.py`; `tests/training/test_event_timing_training_config_contracts.py`; `tests/training/test_air_combat_training_entry_contracts.py`; `tests/fixtures/launch_decision_reorg/v1/manifest.json`. Active JSON files are read-only inputs. | No bulk active-config rewrite, destructive conversion, or A5 edit. | All 14 baseline configs; headless/direct/adapter matrix; config round trip; state-dict key/shape comparison; optimizer/replay restore or actionable migration error. | Legacy precedence is explicit; strict and governed samples resolve deterministically; drift is rejected or named as migration. | Depends on C3; serial. | 2 implementation rounds | accepted |
| C5 | Main thread / closure owner | diagnostics/closure / n/a / high | Run acceptance, runtime probes, target-scoped worktree checks, and owner closure documentation. | `tests/runtime/air_combat/test_fire_action_release_gate.py`; `tests/runtime/air_combat/test_diagnostics_process_probe_summary.py`; `docs/learning/work/active/launch_decision_reorg/README.md`; `docs/learning/work/active/launch_decision_reorg/launch_decision_reorg_task_clusters_20260922.md`. No unrelated files. | No new implementation scope, global WIP repair, independent review dispatch, or claim about kill/damage/Pk. | Build preflight; focused matrix; `git diff --check`; path-length ratchet; target-scoped worktree status/list; runtime counters. | Main-thread verdict Mergeable, Blocked, or Closed with residual IDs and no unresolved declared P1. | Depends on C4; always serial. | 1 closure round | mergeable |

No delegated worker is required for this stream. `n/a` records that the main
thread owns the implementation and the declared risk tier is retained for
scope control.

## Dispatch rules

- The main thread executes C0 through C5 serially; no independent review or
  worker dispatch is required.
- If a future worker is explicitly added, it must map to exactly one cluster
  and one disjoint write set.
- C0 through C5 form a serial implementation DAG. Read-only inventories may be
  prepared in parallel, but no implementation cluster may edit shared owner
  terminology concurrently.
- A cluster has at most two implementation/repair rounds. A third round is a
  planning failure signal and requires re-scoping.
- C5 remains serial until all earlier clusters are complete.
- The main thread owns final scope, acceptance, publication, and merge
  decisions.

## Worker packet requirements

If a delegated worker is later introduced, it returns:

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
$build = 'D:\workshop\Research\Echelon-Forge-build\ld-reorg'
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
git -C <repo>\.worktrees\ld-reorg status --porcelain=v1 -uall
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
- the main-thread owner has recorded no unresolved declared P1.

Mergeable is not Closed. Closure additionally requires the owner review,
required status/index synchronization, residual ownership, and the final
bilingual-policy decision.

## C5 closure record

Owner verdict: `Mergeable`. Build/import, deterministic fixture regeneration,
focused policy/training/runtime matrices, `git diff --check`, path-length, and
target-scoped worktree gates passed on 2026-09-23. The exact counts and the one
inherited documentation-governance residual are recorded in the parent README.
The inherited residual is outside this write set and does not reopen C0-C5.

## Residual map

| Residual | Trigger | Owner/next step |
| --- | --- | --- |
| HMoE event-slice exclusion versus compatibility adapter | resolved in C2/C3 | Preserve the Composer trace and strict write-set tests |
| Headless acceptance eligibility | resolved in C0/C4 | Use the tracked mode manifest and explicit eligibility |
| ef_py unavailable | resolved in C5 for this target | Re-run the external build preflight after native/runtime changes |
| Optimizer/replay state drift | resolved in C4 | Require the envelope manifest or named migration error |
| Unrelated worktree findings | inherited outside this target | Record as inherited; do not edit unrelated trees |
