# Subagent Usage Policy

Language:
- English canonical: `subagent_usage_policy.md`
- Chinese companion: [subagent_usage_policy.zh.md](subagent_usage_policy.zh.md)

Status: `2026-05-23` authoritative for distributed work in maintained docs and
implementation tasks.

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/standards/subagent_usage_policy.md`
Owner: `engineering/automation`
Last verified: `2026-08-07`

Use these rules when distributing implementation workers.

## Purpose And Scope

This policy applies whenever a task is split across subagents, workers, or
integration helpers in docs, plans, code, or tests.

It does not override safety rules, ownership rules, or architecture closure
rules that already exist elsewhere in the repository.

Project principle:

- Policy computation and test/orchestration should be modeled as explicit
  producers and consumers of facade contracts, not as hidden owners of
  simulation state.

## Terms

- `subagent`: any delegated agent used to advance a bounded subtask.
- `worker`: a subagent assigned a concrete write or analysis scope.
- `main thread`: the primary owner of intent, scope, and final acceptance.
- `integration worker`: the worker that resolves cross-file conflicts and
  publishes the final synchronized state.
- `diagnostics worker`: a worker restricted to read-only validation, review,
  or evidence gathering.

## Rules

- Each worker gets one bounded scope, preferably a disjoint file set or a
  disjoint section set.
- Workers MUST NOT split the same normative table across multiple concurrent
  authors.
- A single file should have one writer at a time unless the edits are
  explicitly non-overlapping and trivial.
- Workers must not revert, reword, or reformat another worker's completed
  edits unless they own the integration pass.
- The maintained standards accepted by the relevant owner under
  `docs/<owner>/standards/` win for naming and layering within that owner's
  scope.
- Parallelize only when subtasks are independent and useful without waiting
  for each other.
- Do not delegate the immediate blocking step.
- If two subtasks may touch the same line range or canonical terminology,
  serialize them.
- Prefer the smallest worker that can finish the bounded task.
- Reserve broader workers for cross-file, architecture-critical, or
  publication-sensitive work.

## Cluster Planning Discipline

Distributed work must start from a finite task-cluster plan rather than from an
open-ended sequence of ad-hoc waves.

Before dispatching implementation workers, the main thread must record or name:

- the finite cluster list for the current WP, phase, or remediation slice;
- each cluster's goal, write scope, non-goals, validation commands, and closure
  gate;
- which clusters are parallel-safe and which are dependency-gated;
- the maximum expected implementation rounds per cluster before re-scoping is
  required.

Hard rules:

- Do not dispatch a worker whose task cannot be mapped to a named cluster.
- Do not let a cluster grow by repeatedly adding "one more follow-up" without
  re-baselining the cluster boundary.
- If a cluster exceeds its planned round cap, stop and re-scope it instead of
  issuing another ad-hoc wave.
- Closure or acceptance clusters must stay serial until implementation clusters
  have returned complete packets.

Recommended defaults:

- Small stabilization or repair clusters should allow at most one repair round.
- Implementation clusters should allow at most two rounds before re-scoping.
- Exceeding three rounds for one cluster is a planning failure signal and must
  be called out explicitly before further dispatch.

## Documentation Budget Discipline

Planning documents are work products with cost. A recovery, remediation, or
cleanup WP must set an explicit documentation budget before it creates sidecar
plans, bilingual companions, dispatch queues, ledgers, or acceptance files.

Hard rules:

- Do not create extra task-cluster, salvage-ledger, dispatch, or acceptance
  documents merely to restate the same plan in a new structure.
- If a recovery WP claims to reduce process drag, its document count must shrink
  or be explicitly justified.
- If the plan cannot fit in the declared planning surface, stop for
  re-baseline instead of adding more documents.
- Closure lanes may add required acceptance/index artifacts only after the
  implementation stream is mergeable or explicitly blocked.

## Model And Reasoning Budget Rules

Subagent dispatch must record the capability/risk tier and reasoning budget when
the tooling exposes those controls. Record an exact model ID only when the
current execution environment explicitly lists that ID as available. Do not
copy a model ID from historical task packets or repository prose.

Default complexity ladder:

- Low-risk, local, or diagnostics-only tasks should use the least costly
  available general-purpose tier that can reliably inspect the assigned
  evidence. This includes doc audits, source fact ledgers, focused validation,
  status synchronization, and closure-lane chores that do not own complex code.
- Moderate-risk implementation or integration tasks should use an
  implementation-capable tier with at least medium-equivalent reasoning. Use a
  higher reasoning budget when the task touches public APIs, bindings,
  architecture guards, compatibility behavior, or more than one closely
  related file family.
- High-risk refactors, architecture-critical seams, public contracts, scheduler
  semantics, runtime materialization, capability/spawn/fidelity paths, and
  counterfactual or replay semantics should use the strongest suitable
  coding/reasoning tier currently available, with high-equivalent or stronger
  reasoning. Use the highest justified budget when an incorrect design choice
  could force a later rewrite or broaden the architecture boundary.
- If a task is hard to classify, move it to the higher risk tier or keep the
  immediate blocking work on the main thread.

Minimums:

- Do not assign non-trivial implementation, refactor, public-surface, or
  architecture work below medium-equivalent reasoning when reasoning controls
  are available.
- Do not use a reduced-capability or speed-optimized tier for complex cross-file
  design or risky code ownership merely because it permits a larger reasoning
  budget.
- Dispatch queues and worker packets should include a `Capability tier / model
  ID / reasoning` column or equivalent field. Use `model ID: n/a` when the
  current environment does not expose exact selectable IDs. Deviations from
  this policy must be called out in the dispatch packet.

## Dispatch Lifecycle And Background Execution

The main thread should treat subagents as durable background workers, not as
interactive scratchpads.

- The main thread should not take over the primary implementation assigned to a
  worker unless the task is clearly blocked, mis-scoped, or returned incomplete.
- After dispatch succeeds, the main thread may end the current turn and let
  workers continue in the background.
- Do not close, cancel, or replace a worker merely because the main thread is
  done waiting, the user asked for a status handoff, or the next foreground turn
  should end.
- Only close a worker early for explicit transport or request failures,
  duplicate/mis-scoped dispatch, unsafe scope conflict, or a user request to
  stop that worker.
- A closed, timed-out, rate-limited, or interrupted worker is a transport event
  only. It is not implementation evidence unless the worker returned a complete
  packet before closure.
- If dispatch fails because of a request/platform error, such as a thread limit
  or rate limit, the main thread may close already-completed workers and
  re-dispatch the failed task. This is exception recovery, not a new task wave.
- Do not re-dispatch a task that is already running normally.

## Handoff And Integration

- Every delegated task must return the touched files and a short conclusion.
- The main thread owns final scope decisions, acceptance, and any publish or
  merge action.
- A final integration worker owns cross-file conflict resolution and task
  status updates.
- Status docs and README indexes must be synchronized with the final
  authoritative location.
- WP implementation streams may stop at `Mergeable`; the dedicated closure lane
  owns acceptance review, README/index, archive, and required bilingual sync
  before a WP is marked `Closed`.
- Use [WP Closure Lane Policy](wp_closure_lane_policy.md) when a delegated task
  includes simulation-architecture WP publication or acceptance cleanup.

Required worker packet:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Acceptance rules:

- `pass` is scoped to the assigned cluster slice only.
- `partial` records evidence but never unlocks downstream closure.
- `blocked` must name the blocker, owner, replacement path, failing or missing
  guard, and forced review trigger. It is not a pass state, but it is an
  acceptable honest stop state when continuing would create churn.
- The main thread must locally verify important worker claims before accepting
  them as integration evidence.
- A WP or phase cannot be marked complete while named compatibility, legacy,
  diagnostics, or public escape-hatch residuals remain unowned.

## Linking Rule

- Project rules must be linked from the nearest authoritative index.
- Tier A governance rules should have a Chinese companion.
- Task-specific READMEs should link to this policy instead of restating it in
  full when they depend on it.
- If a worker result changes naming, layering, or ownership, the integration
  pass must reconcile the affected docs before the task is marked complete.
