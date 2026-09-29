# Launch-Decision Reorganization Task Clusters

Status: 2026-09-24 finite active task-cluster plan for
launch_decision_reorg/README.md. The plan is finalized and the main thread is
authorized to execute the clusters serially; no independent review dispatch is
required.

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/learning/work/active/launch_decision_reorg/launch_decision_reorg_task_clusters_20260922.md`
Owner: `learning/policy-architecture`
Last verified: `2026-09-24`

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
conflict in new configurations. An unmarked input qualifies for that legacy
fallback only when it exactly matches one immutable C0 provenance entry by
source commit, repository-relative path, and exact-byte SHA-256; omission of a
marker is not itself proof of legacy provenance.

The implementation must preserve a legacy compatibility mode before enabling
the direct-boundary target mode. HMoE routing, reward/physics semantics, and
runtime legality are outside the write boundary.

## Finite task cluster list

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | Main thread / architecture owner | architecture-critical / n/a / high | Freeze source revision, all active hybrid configs, owner vocabulary, fixture identity, legacy provenance allowlist, strict learned-firing acceptance identity, build preflight, and no-goals. | `docs/learning/work/active/launch_decision_reorg/README.md`; `docs/learning/work/active/launch_decision_reorg/launch_decision_reorg_task_clusters_20260922.md`; `tests/fixtures/launch_decision_reorg/v1/manifest.json`; `tools/maintenance/generate_launch_decision_fixtures.py`. | No policy forward edit, config rewrite, checkpoint conversion, or unrelated worktree repair. | Active-config census; source/test matrix; deterministic fixture manifest; exact config-byte hashes; target worktree status; external build/import preflight. | The immutable v1 manifest records all 14 configs, each unmarked-legacy-eligible config's source commit/path/SHA-256, exact fixture root/format/hash rules, the full deterministic+stochastic 3-seed x 3-episode acceptance matrix, exact process-probe counter keys, zero-rejection bound, and explicit infrastructure residuals. Downstream clusters may reference its hash but may not rewrite it. | First; serial. | 1 evidence round | planned |
| C1 | Main thread / contract owner | architecture-critical / n/a / high | Define owner modes, contributor/delta semantics, provenance-qualified legacy fallback, adapter exclusivity, serialization, and migration schema. | `python/rl/policy_algo/model_contracts.py`; `tests/policy/test_launch_decision_model_contracts.py`. | No policy forward edit, new learned head, or A5 change. | Direct strict, governed composed, legacy precedence, auxiliary-only, adapter-conflict, headless, serialization, and provenance x marker matrix tests. | Every provenance x marker x headless x adapter-flag combination maps to exactly one mode or explicit rejection; only exact C0 provenance may use unmarked legacy fallback, and new unmarked conflicts reject. | Depends on C0; serial. | 2 implementation rounds | planned |
| C2 | Main thread / forward-path owner | architecture-critical / n/a / high | Make the event-delta boundary explicit while preserving legacy outputs and state-dict behavior. | `python/rl/policy_algo/policies.py`; `tests/policy/test_launch_decision_composer.py`; `tests/policy/test_execution_policy_event_heads.py`; `tests/policy/test_execution_policy_optimizer_heads.py`. | No HMoE routing redesign, reward/runtime change, or support-mask movement. | Contributor traces; raw pair/delta comparison; strict HMoE isolation; unmasked output; mask handoff; deterministic mode; stochastic log-prob/entropy; old checkpoint load. | Exactly one declared owner mode is visible; Composer does not apply support mask; legacy fixture passes. | Depends on C1; serial before C3/C4 writes. | 2 implementation rounds | planned |
| C3 | Main thread / objective owner | cross-file architecture / n/a / high | Align objectives, sidecars, replay, labels, gradients, and optimizer parameter ownership with the C2 mode. | `python/rl/policy_algo/ppo_adaptive_kl.py`; `python/rl/policy_algo/_first_event_mixin.py`; `python/rl/policy_algo/_event_credit_mixin.py`; `python/rl/policy_algo/_grouped_stopping_mixin.py`; `python/rl/policy_algo/_event_window_mixin.py`; `tests/policy/test_launch_decision_optimizer_ownership.py`; `tests/policy/test_event_head_update_contracts.py`; `tests/policy/test_auxiliary_event_credit_updates.py`. Read-only dependencies: `python/rl/policy_algo/_adaptive_kl_support.py`; `python/rl/policy_algo/first_event_hazard.py`; `python/rl/policy_algo/grouped_stopping.py`; `python/rl/policy_algo/_window_classifier_replay.py`. | No new labels, collection-support change, or forward-path edit outside the C2 interface. | Gradient/dedicated-update isolation; sidecar metadata; replay round trip; optimizer names/order/IDs; metric namespace compatibility. | Every objective is auxiliary-only or points to the declared owner; no hidden action_net/HMoE update remains in strict mode. | Depends on C2; serial. | 2 implementation rounds | planned |
| C4 | Main thread / migration owner | compatibility/integration / n/a / high | Translate flat config and checkpoint surfaces without silent precedence, provenance ambiguity, or state drift. | `python/training/deps.py`; `python/training/bootstrap.py`; `python/experiment/air_combat_matrix.py`; `python/rl/policy_checkpoint.py`; `tests/training/test_launch_decision_migration.py`; `tests/training/test_event_timing_training_config_contracts.py`; `tests/training/test_air_combat_training_entry_contracts.py`. Read-only dependency: `tests/fixtures/launch_decision_reorg/v1/manifest.json` (immutable C0 identity). Active JSON files are read-only inputs. | No bulk active-config rewrite, destructive conversion, or A5 edit. | All 14 baseline configs; exact C0 provenance matches; copied/renamed/edited unmarked rejection; headless/direct/adapter matrix; config round trip; state-dict key/shape comparison; optimizer/replay restore or actionable migration error. | Legacy precedence is available only to exact C0 provenance; strict and governed samples resolve deterministically; unlisted unmarked inputs fail closed; drift is rejected or named as migration; any C4 manifest references retain the C0 SHA-256. | Depends on C3; serial. | 2 implementation rounds | planned |
| C5 | Main thread / closure owner | diagnostics/closure / n/a / high | Run acceptance, runtime probes, target-scoped worktree checks, and owner closure documentation. | `tests/runtime/air_combat/test_fire_action_release_gate.py`; `tests/runtime/air_combat/test_diagnostics_process_probe_summary.py`; `docs/learning/work/active/launch_decision_reorg/README.md`; `docs/learning/work/active/launch_decision_reorg/launch_decision_reorg_task_clusters_20260922.md`. No unrelated files. | No new implementation scope, global WIP repair, independent review dispatch, or claim about kill/damage/Pk. | Build preflight; focused matrix; `git diff --check`; path-length ratchet; target worktree status/list; immutable-C0 acceptance validation. Run both deterministic and stochastic learned-model lanes across every pinned 3-seed x 3-episode cell, with no forced/manual fire injection. Each cell must independently satisfy requested/accepted/released/authorized >= 1; `violation_release_count == 0`; `repeat_release_before_assessment_count == 0`; `fire_once_rejected_count == 0`; and a reported `first_release_step`. | Main-thread verdict Mergeable, Blocked, or Closed with residual IDs and no unresolved declared P1. Missing cells, missing counter keys, non-model/forced probe mode, aggregate-only success, or any threshold violation is Blocked. | Depends on C4; always serial. | 1 closure round | planned |

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

- owner-mode and conflict matrix tests, including exact legacy provenance;
- contributor/delta/mask trace tests;
- checkpoint, optimizer-state, and replay-state round trips;
- git diff --check;
- path-length budget and architecture-governance tests;
- runtime process-probe counters using the exact keys pinned below.

### Compatibility and acceptance identity gate

C0 freezes:

- all active air_combat_hybrid_v1 configs, with the observed headless/enabled
  split;
- for every baseline config allowed to use an unmarked legacy fallback, the
  source commit, repository-relative path, and SHA-256 of the exact UTF-8 bytes;
- representative state-dict, optimizer, and replay fixtures for every mode
  that actually exists;
- fixed observation fixtures and CPU float32;
- runtime seeds 0, 1, 2 with three declared episodes per seed;
- two learned-model acceptance lanes, `deterministic` and `stochastic`, each
  covering all nine seed/episode cells with forced/manual fire injection false;
- the exact process-probe episode-summary keys
  `fire_once_requested_count`, `fire_once_accepted_count`,
  `fire_once_rejected_count`, `release_count`, `authorized_release_count`,
  `violation_release_count`, `repeat_release_before_assessment_count`, and
  `first_release_step`;
- per-cell minima of 1 for requested, accepted, released, and authorized
  release; exact zero for violation, repeat-before-assessment, and rejected
  requests. The v1 stochastic reject bound is therefore numerically fixed at
  zero per cell and zero over the full stochastic matrix; deterministic uses
  the same zero-rejection bound.

An unmarked input may resolve to legacy_composed_v0 only when its complete
provenance tuple matches a C0 entry. Path match without byte hash, hash match at
another path, source-commit mismatch, or an unlisted/copy/edited config must
fail closed. Complete owner-v1 version/mode markers are required for new
configurations; partial or conflicting markers reject.

For legacy mode, require exact shapes, state-dict keys, optimizer-group
names/order, and masked support. Compare unmasked event pairs, event deltas,
probabilities, log-probabilities, and entropies with
torch.testing.assert_close(rtol=1e-5, atol=1e-6). If a deliberate target-mode
change exceeds that tolerance, require a named migration mode and expected
fixture. Optimizer and replay restoration must be exact or fail with an
actionable migration error.

C5 consumes this immutable acceptance identity without weakening it. Every
cell in both lanes must independently pass; aggregate counts cannot compensate
for an empty or failing cell. Changing coverage, counter names, or numeric
limits requires a new versioned acceptance identity rather than modifying v1
after probe results are known.

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
- unmarked legacy fallback is restricted to exact immutable C0 provenance;
- Composer output is unmasked and distribution masking is single-owned;
- all focused tests and compatibility gates pass after build preflight;
- both deterministic and stochastic strict learned-model matrices pass every
  pinned cell and threshold from the immutable C0 acceptance identity;
- optimizer/replay/config/checkpoint behavior is explicit;
- target-scoped worktree checks pass;
- the main-thread owner has recorded no unresolved declared P1.

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
