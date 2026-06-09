# WP23 Legacy Retirement Recovery And Reset

Status: closed as `blocked` on `2026-05-24`. WP23 supersedes WP22 and was
allowed to end as `blocked` because deletion or migration was not safely
achievable in its bounded implementation window. `WP23-A` through `WP23-D`
provide the source-backed recovery baseline; `WP23-E` is skipped because no
deletion-ready implementation surface was identified; `WP23-F` records the
blocked close-out. No implementation dispatch started.

Documentation budget:

- Canonical WP23 planning surface is this file plus its Chinese companion only.
- No sidecar task-cluster, salvage-ledger, or acceptance-rule files are allowed
  during WP23 unless the owner explicitly approves them.
- If WP23 needs more planning surface than this file can hold, that is a scope
  failure signal and the work must stop for re-baseline instead of creating more
  documents.

Inputs:

- [WP22 legacy compatibility retirement](../wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.md)
- [WP22 remaining task clusters](../wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.md)
- [WP22 dispatch queue](../wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.md)
- [Architecture refactoring audit](../../../review/architecture_refactoring_audit_20260522.md)
- [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)
- [WP Closure Lane Policy](../../../../standards/governance/wp_closure_lane_policy.md)

## 1. Stop Order

WP23 starts with a hard stop, not another WP22 wave.

- WP22 implementation dispatches are terminated or frozen.
- WP22 queues are historical provenance only and are not dispatchable.
- Kepler's interrupted TaskOrder wiring is unvalidated partial work.
- Hubble's TaskOrder maintained-batch contract is partial evidence and carries
  dual-representation risk until audited.
- Galileo/Locke preflights are historical source facts, not implementation
  evidence.
- Poincare shutdown provides no closure evidence.

No `partial`, `preflight-only`, `timeout`, `shutdown`, quarantine label, or old
queue row may unlock WP23 implementation or closure.

## 2. Recovery Principles

WP22 failed as a control process: R2 expanded into more than twenty waves,
partial evidence became next-step fuel, and quarantine started functioning like
completion. WP23 exists to prevent that pattern from repeating.

Rules:

- One maintained truth per business concept.
- Delete or migrate when safe; otherwise stop as `blocked`.
- `blocked` is an acceptable WP23 outcome, not a failure to hide.
- `blocked` is not a pass state and cannot sit unreviewed.
- Do not preserve sunk-cost work merely because it exists in the worktree.
- Do not create a new DTO, bridge, helper, or compatibility layer unless it
  removes, migrates, or explicitly blocks the old maintained truth in the same
  decision.

## 3. Current Work Buckets

The worktree is intentionally not reset here. WP23-A must classify current dirty
work into these buckets before implementation starts.

| Bucket | Meaning | Initial examples |
|--------|---------|------------------|
| `keep-after-audit` | Evidence-backed changes that narrow maintained paths and do not create a second truth. | Typed command/control narrowing, terrain/setup default normalization, command-link pending transport narrowing, guard hardening. |
| `audit-before-keep` | Useful-looking changes with dual-representation, incomplete wiring, or unvalidated shutdown risk. | `TaskOrderMaintainedBatchContract`, `WorldTaskOrderMaintainedAssignment`, maintained TaskOrder runtime/facade/binding APIs, Python `hasattr` fallbacks. |
| `delete-or-migrate-target` | Compatibility or flat-shell surfaces that still behave like maintained defaults. | Whole-shell assignment truth, default-factory behavior-bearing `MovementCommand` / `LaggedCommand` projection, non-opt-in runtime escape-hatch consumers. |
| `blocked-target` | Cannot be deleted now without breaking public API or consumers that lack replacement ownership. | `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, `vec_env.batch_runtime`, public `World*Assignment` batch methods, diagnostics bindings. |
| `rollback-candidate` | Interrupted or speculative edits that fail audit or validation. | Any Kepler-era wiring that cannot be validated or that preserves dual truth. |
| `historical-only` | Prior packets and queues that explain provenance but authorize nothing. | WP22 waves, read-only preflights, shutdown records, closure notes saying `WP22-F not eligible`. |

## 4. Blocked-State Contract

`blocked` must not become the new `quarantine`. Every blocked item must include:

- exact surface and current caller;
- why deletion/migration is unsafe now;
- owner responsible for the replacement or public API decision;
- required replacement or deletion condition;
- validation command or missing guard;
- forced review trigger.

Forced review triggers:

- the replacement API lands;
- a public consumer is removed;
- a guard starts failing;
- one implementation batch finishes;
- the blocked item is older than the next WP23 review point.

WP23 may close as `blocked` only if all blocked items are explicit and no item
is mislabeled as retired, migrated, or accepted.

## 5. Task Clusters

WP23 has six finite clusters. No worker may be dispatched unless the task maps
to one row here.

| Cluster | Round cap | Purpose | Exit |
|---------|-----------|---------|------|
| `WP23-A Freeze And Salvage Audit` | 1 diagnostics/docs round | Classify all dirty WP22-era changes into the buckets above. | No unnamed "next step" bucket remains. |
| `WP23-B Delete-Or-Block Table` | 1 diagnostics/docs round | For every live legacy surface, decide `delete now`, `migrate then delete`, `blocked`, or `rollback`. | Every row has owner, validation, and forced review trigger. |
| `WP23-C Tasking Single Representation` | 1 implementation/design round | Resolve TaskOrder first: keep, rollback, or block maintained-batch work. Only after that decide LeaderIntent/PilotReport. | One maintained tasking truth, or explicit blocked close-out. |
| `WP23-D Public API Exit` | 1 implementation/design round | Decide raw runtime/world/batch escape hatches and diagnostics/public whole-shell APIs. | Deleted, migrated, or blocked with public API reason. |
| `WP23-E Minimal Implementation Batch` | 1 implementation round | Apply only B-D decisions already proven ready. | Patch set lands or WP23 stops as blocked. No follow-up wave is created. |
| `WP23-F Close-Out` | 1 serial closure round | Publish accept/reject/blocked result and archive WP22 queue status. | Fails on partial evidence, dual truth, or unowned legacy paths. |

If any implementation cluster cannot finish inside its single round, WP23 stops
as `blocked` or re-baselines only with owner approval. It must not create a
"second wave" by default.

## 5.1 WP23-A Salvage Audit Baseline

Audit date: `2026-05-24`.

Worktree state:

- Branch is `main`, ahead of `origin/main` by two commits.
- WP22 queues are frozen and historical only.
- WP23 planning surface is still within budget: this file plus Chinese
  companion only.
- Current dirty work includes WP22-era code, tests, governance edits, WP22
  freeze notes, and WP23 reset docs. No code is accepted or rejected wholesale
  by this audit.

Salvage classification:

| Surface | Source anchors | Classification | Decision |
|---------|----------------|----------------|----------|
| WP22 freeze/governance docs | `docs/task/simulation_architecture/README.md`, `docs/standards/governance/subagent_usage_policy.md`, `docs/standards/governance/wp_closure_lane_policy.md` | `keep-after-audit` | Keep as process correction. They reduce WP22 re-entry risk and add document-budget / blocked-state governance. |
| Scenario terrain/setup normalization | `python/scenario/compiler/common.py:114-132`, `python/scenario/runtime/world_setup_compat.py:17-54`, `tests/runtime/core/test_world_setup_compat.py:147-161` | `keep-after-audit` | Keep if validation passes. Missing terrain now defaults to `flat` / `default_mainline`; explicit legacy terrain is labeled compatibility. |
| Command/control typed-state narrowing | `src/components/command/default_factory_legacy_spawn_compat.h:9-18`, `src/systems/core/operation_system.h:46-111`, `src/systems/systems/command_link_system.h:29-120` | `keep-after-audit` with residual blockers | Keep guarded narrowing, but do not call it retirement while `MovementCommand`, `LaggedCommand`, `ActionCommand`, and pending shells remain behavior-bearing compatibility surfaces. |
| TaskOrder maintained-batch contract and wiring | `src/runtime/contracts/world_batch_contracts.h:563-720`, `src/core/engine/world_batch_runtime.h:109-116`, `src/core/engine/world_batch_runtime.cpp:738-857`, `src/runtime/facade/runtime_facade.h:97-129`, `src/runtime/facade/runtime_facade.cpp:2649-2768`, `src/interfaces/python/bindings_runtime.cpp:1165-1173`, `src/interfaces/python/bindings_runtime.cpp:1444-1457`, `src/interfaces/python/bindings_runtime.cpp:1535-1582`, `src/interfaces/python/bindings_runtime.cpp:1692-1735`, `python/rl/runtime/world_batch/adapter.py:118-141`, `python/rl/runtime/world_batch/adapter.py:773-887`, `python/rl/runtime/world_batch_vec_env.py:1261-1315` | `audit-before-keep` | Do not accept as pass yet. It introduces a maintained-looking TaskOrder path while whole-shell write/read, observation packet, bindings, and Python fallback paths remain live. |
| TaskOrder / LeaderIntent / PilotReport whole-shell assignments | `src/runtime/contracts/world_batch_contracts.h:596-655`, `src/core/engine/world_batch_runtime.cpp:766-797`, `src/runtime/facade/runtime_facade.cpp:2655-2665`, `src/interfaces/python/bindings_runtime.cpp:1444-1469` | `delete-or-migrate-target` for maintained truth; `blocked-target` for public API | Must not be accepted as maintained truth. Delete/migrate only after public replacements are proven; otherwise mark blocked. |
| Observation task-order whole-shell read | `src/runtime/facade/runtime_facade.cpp:2779-2788`, `src/runtime/facade/runtime_facade.cpp:3008-3031`, `src/interfaces/python/bindings_runtime.cpp:1105-1117`, `tests/architecture/runtime_facade/test_layering.py:1000-1004` | `blocked-target` | Remains whole-shell read surface. Cannot be called retired while `ObservationBatchPacket.task_orders` is public. |
| Runtime/world/batch escape hatches | `src/runtime/facade/runtime_facade.cpp:2498-2503`, `src/core/engine/world_batch_runtime.h:65-68`, `python/rl/runtime/world_batch_vec_env.py:302-306`, `tests/architecture/runtime_facade/test_layering.py:499-608` | `blocked-target` | Keep guarded as explicit compatibility/diagnostics only. Deletion is blocked by public consumers and diagnostics paths. |
| Default-factory legacy command projection | `src/components/command/default_factory_legacy_spawn_compat.h:36-54`, `src/components/command/default_factory_legacy_spawn_compat.h:101-121` | `delete-or-migrate-target` with blocker | Must migrate to typed control-state-only spawn before deletion. Current state still projects `MovementCommand` and `LaggedCommand`. |
| Python maintained path fallbacks | `python/rl/runtime/world_batch/adapter.py:118-141`, `python/rl/runtime/world_batch/adapter.py:773-887`, `python/rl/runtime/world_batch_vec_env.py:1261-1315` | `rollback-candidate` if fallback hides truth | Keep only if C proves explicit representation selection. Silent `hasattr` fallback can otherwise preserve dual truth. |

WP23-A exit: complete for planning. No unnamed "next step" bucket remains:
every audited surface is keep-after-audit, audit-before-keep,
delete-or-migrate-target, blocked-target, rollback-candidate, or historical-only.

## 5.2 WP23-B Delete-Or-Block Table

This table is the only active decision table for WP23. It replaces WP22 queue
continuations.

| Surface | Decision | Owner | Replacement / exit condition | Validation / missing guard | Forced review trigger |
|---------|----------|-------|------------------------------|----------------------------|-----------------------|
| WP22 queue entries | `blocked as historical-only` | WP23-F | Archive or keep frozen references only. | `rg` must show no README or WP23 text pointing to deleted sidecars or active WP22 queue dispatch. | Any future dispatch request that cites WP22 queue directly. |
| TaskOrder maintained-batch path | `audit-before-keep`; may become `rollback` or `blocked` | WP23-C | Keep only if it becomes the sole maintained TaskOrder write/read path, or old whole-shell surfaces become explicit compatibility/blocked public API. | Need build plus focused runtime/facade/binding/DTO tests; must prove `ObservationBatchPacket.task_orders` and Python fallback do not reintroduce maintained whole-shell truth. | Completion of WP23-C audit/design round. |
| `WorldTaskOrderAssignment.order` and `get/set_task_orders_batch` | `migrate then delete` where private; `blocked public API` where exposed | WP23-C | Maintained callers use `TaskOrderMaintainedBatchContract`; public old API remains only explicit compatibility or is removed. | Missing guard: old whole-shell getter/setter still bound in runtime/facade/Python. | Maintained contract accepted, or public consumer list changes. |
| `WorldLeaderIntentAssignment.intent` | `blocked` | WP23-C after TaskOrder | Wait for TaskOrder decision before designing analogous path. | Missing maintained public write/read replacement. | TaskOrder reaches keep/rollback/blocked decision. |
| `WorldPilotReportAssignment.report` | `blocked` | WP23-C after TaskOrder | Wait for TaskOrder decision before designing analogous path. | Missing maintained public write/read replacement. | TaskOrder reaches keep/rollback/blocked decision. |
| `ObservationBatchPacket.task_orders` | `blocked public API` | WP23-C / WP23-D | Replace with maintained contract read or explicitly mark as compatibility retained. | Current packet still exposes `std::vector<TaskOrder> task_orders`. | TaskOrder maintained read path accepted or packet API changes. |
| `RuntimeFacade::runtime()` | `blocked public API` | WP23-D | Remove only after all public consumers have facade-owned replacements. | Guard currently localizes consumers but does not delete API. | New raw-runtime consumer appears, or replacement API covers all consumers. |
| `WorldBatchRuntime::world()` | `blocked public API` | WP23-D | Remove only after raw-world adapter/diagnostics consumers migrate. | Guard localizes `.world()` consumers to explicit allowlist. | Adapter no longer needs raw-world compatibility handle. |
| `vec_env.batch_runtime` | `blocked compatibility view` | WP23-D | Keep explicit opt-in or delete after public users migrate. | Runtime compatibility flag guard exists; public view still exists. | Public Python consumers are removed or replacement facade APIs land. |
| Default-factory `MovementCommand` / `LaggedCommand` projection | `migrate then delete`; currently `blocked` | WP23-E only after C/D readiness | Spawn defaults must seed typed control-state without behavior-bearing legacy mirrors. | Existing helper still sets projected `MovementCommand` / `LaggedCommand`. | Typed control-state replacement covers remaining command/link/factory consumers. |
| Diagnostics legacy bindings and GPU/visual compatibility helpers | `blocked compatibility retained` | WP23-D / WP23-F | Keep only as diagnostics/compatibility with guard labels, not retirement evidence. | Must remain outside maintained path allowlists. | Diagnostics path becomes maintained dependency or guard fails. |

WP23-B exit: complete for planning. Implementation is now allowed only for
bounded `WP23-C` / `WP23-D` work chosen from this table. If either cannot finish
inside its single round, WP23 must stop as `blocked` instead of creating a new
wave.

## 5.3 WP23-C TaskOrder Decision

Audit date: `2026-05-24`.

Decision: `blocked`, not `keep` and not immediate rollback.

Rationale:

- The maintained-batch path exists and has guard value:
  `TaskOrderMaintainedBatchContract` and
  `WorldTaskOrderMaintainedAssignment` are defined in
  `src/runtime/contracts/world_batch_contracts.h:563-628`; runtime and facade
  APIs expose maintained set/get functions at
  `src/core/engine/world_batch_runtime.cpp:738-849` and
  `src/runtime/facade/runtime_facade.cpp:2649-2765`.
- The maintained path still writes back into the compatibility shell: runtime
  code builds a `TaskOrder compatibility_shell` and calls
  `world.set_task_order(...)` in
  `src/core/engine/world_batch_runtime.cpp:746-761`.
- The old whole-shell path remains public and live:
  `WorldTaskOrderAssignment.order` remains in
  `src/runtime/contracts/world_batch_contracts.h:596-614`, while
  `set_task_orders_batch` / `get_task_orders_batch` remain exposed through
  runtime, facade, and Python bindings at
  `src/core/engine/world_batch_runtime.cpp:766-857`,
  `src/runtime/facade/runtime_facade.cpp:2655-2768`, and
  `src/interfaces/python/bindings_runtime.cpp:1444-1457`.
- `ObservationBatchPacket` still exports whole-shell
  `std::vector<TaskOrder> task_orders` in
  `src/runtime/facade/runtime_facade_types.h:295-310`, and
  `RuntimeFacade::build_observation_packet` fills it through
  `runtime_->get_task_orders_batch(...)` in
  `src/runtime/facade/runtime_facade.cpp:3029-3030`.
- Python still contains fallback/feature-detection branches that can route
  through either maintained assignments or whole-shell assignments:
  `python/rl/runtime/world_batch/adapter.py:773-887` and
  `python/rl/runtime/world_batch_vec_env.py:1261-1315`.
- Existing tests document coexistence rather than retirement:
  `tests/world_batch/test_world_batch_runtime.py:921-964` validates maintained
  write followed by legacy read, and
  `tests/architecture/runtime_facade/test_layering.py:976-1008` explicitly
  checks that maintained APIs and legacy shells remain together.

WP23-C outcome:

- Do not accept TaskOrder maintained-batch work as the single maintained
  representation.
- Do not roll it back immediately, because the typed contract is useful
  evidence and may become the replacement shape once public whole-shell exits
  are decided.
- Mark TaskOrder as `blocked` until public old read/write surfaces are either
  removed, compatibility-labeled with guards, or replaced by a maintained packet
  shape.
- Keep LeaderIntent and PilotReport blocked; no analogous maintained-path work
  starts until the TaskOrder public API decision is resolved.

Blocked-state contract for TaskOrder:

| Surface | Owner | Unsafe deletion reason | Replacement / deletion condition | Validation / missing guard | Forced review trigger |
|---------|-------|------------------------|----------------------------------|----------------------------|-----------------------|
| `TaskOrderMaintainedBatchContract` / `WorldTaskOrderMaintainedAssignment` | WP23-C / WP23-D | Useful replacement candidate, but not yet sole truth because it projects through compatibility storage. | Keep only if old whole-shell APIs are removed or compatibility-labeled and guarded. | Missing guard proving callers cannot treat both maintained and whole-shell shapes as maintained truth. | WP23-D public API exit decision or any TaskOrder implementation patch. |
| `WorldTaskOrderAssignment.order` and `set/get_task_orders_batch` | WP23-D | Public runtime/facade/Python API still has consumers and tests. | Delete where private; otherwise label as explicit compatibility API outside maintained path. | Missing public API deprecation/removal guard and consumer inventory. | Public API inventory changes or maintained contract packet replacement lands. |
| `ObservationBatchPacket.task_orders` | WP23-D | Public packet shape exports whole-shell `TaskOrder`. | Replace with maintained contract packet field or label retained compatibility export. | Missing guard preventing observation packet from being cited as maintained TaskOrder truth. | Observation packet API changes or facade-owned replacement lands. |
| Python `hasattr` maintained/legacy fallbacks | WP23-D / WP23-E | Fall back silently to whole-shell assignment and can hide representation drift. | Use explicit representation choice or remove fallback after bindings baseline is fixed. | Missing test that fails when fallback preserves dual truth unexpectedly. | Binding baseline changes or vector-env tasking path changes. |

WP23-C exit: complete as `blocked`. This consumes the single WP23-C
design/audit round. Any further TaskOrder code work belongs only to `WP23-D`
public API exit classification or a user-approved re-baseline, not to another
WP23-C repair wave.

## 5.4 WP23-D Public API Exit Decision

Audit date: `2026-05-24`.

Decision: `blocked public API`, with no deletion-ready implementation surface
identified in this round.

Rationale:

- `RuntimeFacade::runtime()` is still a public compatibility escape hatch:
  it is declared in `src/runtime/facade/runtime_facade.h:53-56`, implemented in
  `src/runtime/facade/runtime_facade.cpp:2498-2503`, and bound to Python in
  `src/interfaces/python/bindings_runtime.cpp:1645`.
- `WorldBatchRuntime::world()` is still public on the raw batch runtime:
  `src/core/engine/world_batch_runtime.h:65-68` documents it as a
  compatibility/diagnostics escape hatch. Existing low-level tests and
  diagnostics still use raw worlds, for example
  `tests/world_batch/test_world_batch_runtime.py:355-408` and engagement
  diagnostics tests through `facade.runtime().world(0)`.
- `vec_env.batch_runtime` is not deleted; it is gated by explicit
  `runtime_compatibility_enabled` opt-in in
  `python/rl/runtime/world_batch_vec_env.py:302-306`, backed by
  `RuntimeCompatibilityView` in
  `python/rl/runtime/world_batch/compat.py:29-43`, and tested as an explicit
  compatibility view in
  `tests/world_batch/test_world_batch_vec_env.py:669-704`.
- Current architecture guards localize, but do not remove, escape-hatch
  consumers: `tests/architecture/runtime_facade/test_layering.py:499-607`
  checks that `.batch_runtime` and `RuntimeFacade.runtime()` consumers stay in
  explicit allowlists; `tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py:43-86`
  preserves public compatibility surfaces until replacement gates exist.
- TaskOrder whole-shell public APIs remain live across C++ and Python bindings:
  `set_task_orders_batch` / `get_task_orders_batch` remain bound for both
  `WorldBatchRuntime` and `RuntimeFacade` in
  `src/interfaces/python/bindings_runtime.cpp:1539-1582` and
  `src/interfaces/python/bindings_runtime.cpp:1696-1735`.
- GPU/visual compatibility overloads still accept raw `WorldBatchRuntime&`
  arguments at `src/interfaces/python/bindings_gpu.cpp:790-880`, while facade
  overloads also exist. The raw overloads therefore remain compatibility
  retained until public users move to the facade overloads.

WP23-D classification:

| Surface | Decision | Reason | Exit condition | Guard / validation |
|---------|----------|--------|----------------|--------------------|
| `RuntimeFacade::runtime()` | `blocked compatibility escape hatch` | Public Python binding and diagnostics consumers still exist. | Delete only after diagnostics and legacy adapters have facade-owned replacements. | Keep architecture guard that forbids maintained-path consumers outside allowlists. |
| `WorldBatchRuntime::world()` | `blocked diagnostics/raw-world escape hatch` | Low-level runtime tests, scenario-loader seams, and diagnostics still require raw world access. | Delete only after spawn/setup/diagnostics helper APIs cover those consumers. | Keep `.world()` allowlist guard; add deletion guard only when replacement is ready. |
| `vec_env.batch_runtime` / `RuntimeCompatibilityView` | `blocked compatibility view` | Explicit opt-in compatibility contract exists and is tested. | Delete only after public callers migrate from `batch_runtime` to facade/runtime adapter APIs. | Existing `runtime_compatibility_enabled` gate must remain; failures are not retirement evidence. |
| TaskOrder whole-shell batch APIs | `blocked public tasking API` | WP23-C proved whole-shell read/write and observation export still coexist with maintained contract. | Delete or compatibility-label after public API inventory and replacement packet decision. | Missing guard that prevents whole-shell APIs from being counted as maintained truth. |
| `ObservationBatchPacket.task_orders` | `blocked public packet shape` | Public packet still exports whole-shell `TaskOrder`. | Replace with maintained contract field or explicitly mark as compatibility export. | Missing DTO guard separating maintained tasking truth from compatibility export. |
| Raw GPU/visual `WorldBatchRuntime&` overloads | `blocked diagnostics/compat overloads` | Raw overloads coexist with facade overloads for existing callers. | Delete only after callers use facade overloads and diagnostics coverage is preserved. | Missing binding guard that rejects new maintained consumers of raw overloads. |
| Diagnostics traces and diagnostics-only bindings | `compatibility retained` | Diagnostics are intentionally not maintained truth. | Keep with explicit `diagnostics_only` labels unless they become maintained dependencies. | Existing diagnostics-only policy tests remain relevant. |

WP23-D exit: complete as `blocked`. It does not unlock broad deletion. The only
WP23-E candidates are guard/label hardening tasks that make the above blocked
state enforceable; any business migration or API deletion requires owner
approval or a re-baselined work package.

## 5.5 WP23-E Minimal Implementation Decision

Decision: `skipped`.

Reason:

- `WP23-C` blocked TaskOrder as a dual-representation public API problem.
- `WP23-D` blocked the public runtime/world/batch/diagnostics exits and found no
  deletion-ready implementation surface.
- Existing guards already localize the most important escape hatches:
  `tests/architecture/runtime_facade/test_layering.py:499-607` covers
  `.batch_runtime` and `RuntimeFacade.runtime()` allowlists, while
  `tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py:43-86` keeps public
  compatibility surfaces tied to replacement gates.
- Adding a small guard-only patch now would not delete or migrate any business
  surface, and would risk converting `blocked` into another permanent
  intermediate state.

WP23-E exit: no implementation batch is run. This is intentional close-out
control, not missing work. Any future code work must be opened as a new,
replacement-backed package with explicit API ownership and deletion criteria.

## 5.6 WP23-F Close-Out

Result: `blocked`, accepted as the correct WP23 recovery outcome.

Close-out evidence:

- WP22 is frozen and historical only; its queues are not dispatchable.
- WP23 stayed within its document budget: this file plus the Chinese companion.
- Current dirty WP22-era work was classified rather than accepted wholesale.
- TaskOrder maintained-batch work is not accepted as single maintained truth.
- Runtime/world/batch public escape hatches are explicitly blocked instead of
  being mislabeled retired.
- No subagent or implementation wave was started after C/D revealed blocked
  public API conditions.

Blocked follow-up conditions:

| Follow-up surface | Required opening condition |
|-------------------|----------------------------|
| TaskOrder single representation | Owner approves a public API migration that either removes whole-shell tasking APIs or labels them compatibility-only with failing guards. |
| Observation packet tasking field | Owner approves a maintained packet replacement or explicit compatibility export policy. |
| Runtime/world escape hatches | Facade-owned replacement APIs cover diagnostics, scenario-loader seams, and low-level tests. |
| `vec_env.batch_runtime` | Public callers migrate to facade/runtime-adapter APIs or accept a documented compatibility deprecation plan. |
| Raw GPU/visual runtime overloads | Maintained callers use facade overloads and diagnostics parity remains covered. |

WP23-F exit: complete. WP23 is not a pass for legacy retirement; it is a
controlled `blocked` recovery closure that prevents WP22's partial/quarantine
evidence from being reused as acceptance.

## 6. TaskOrder Sunk-Cost Guard

TaskOrder is the highest-risk WP23-C item because current work already contains
both Hubble's partial contract and Kepler's interrupted wiring.

Decision order:

1. Validate whether the maintained-batch path actually replaces maintained
   whole-shell truth.
2. If yes, keep only with guards proving the old whole-shell path is
   compatibility-only or blocked.
3. If no, roll back or mark blocked instead of repairing indefinitely.
4. Do not start LeaderIntent/PilotReport implementation until TaskOrder has a
   keep/rollback/blocked decision.

The one WP23-C round may be spent on audit/design rather than code. Ending
WP23-C as `blocked` is preferable to recreating WP22 R2.

## 7. Dispatch Rules

- Light diagnostics/docs tasks: `gpt-5.4-mini`, `xhigh`.
- Runtime/facade/bindings/DTO/public API tasks: `gpt-5.4`, `high` or `xhigh`.
- `WP23-C` and `WP23-E`: `gpt-5.4`, `xhigh`.
- Do not dispatch implementation before `WP23-A` and `WP23-B` complete.
- Do not close normally running workers after dispatch just to end the main
  thread turn.
- Close early only for explicit user stop, request/transport failure,
  duplicate/mis-scoped dispatch, or unsafe scope conflict.

Required worker packet:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 8. Validation Baseline

Choose exact commands by changed files, but WP23 implementation or close-out
should normally include relevant subsets of:

```bash
git diff --check
cmake --build build-workshop --target ef_py -j4
python -m pytest -q tests/architecture/runtime_facade/test_layering.py
python -m pytest -q tests/architecture/test_wp22_dto_domain_shell_guard.py
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py
python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py
python -m pytest -q tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py
```

## 9. Next Action

WP23 is closed as `blocked`.

Next executable action:

1. Decide whether to open a new replacement-backed package for TaskOrder/public
   API migration, or stop legacy-retirement work here and return to product or
   architecture work outside WP22/WP23.
2. Do not dispatch further WP23 workers. Any new work needs a fresh scope,
   owner, deletion criteria, and validation gates.
