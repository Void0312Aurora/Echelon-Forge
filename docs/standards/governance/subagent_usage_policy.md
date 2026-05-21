# Subagent Usage Policy

Language:
- English canonical: `subagent_usage_policy.md`
- Chinese companion: [subagent_usage_policy.zh.md](subagent_usage_policy.zh.md)

Status: `2026-05-21` authoritative for distributed work in maintained docs and
implementation tasks.

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
- The standards tree wins for naming and layering.
- Parallelize only when subtasks are independent and useful without waiting
  for each other.
- Do not delegate the immediate blocking step.
- If two subtasks may touch the same line range or canonical terminology,
  serialize them.
- Prefer the smallest worker that can finish the bounded task.
- Reserve broader workers for cross-file, architecture-critical, or
  publication-sensitive work.

## Model And Reasoning Budget Rules

Subagent dispatch must record both model choice and reasoning budget when the
tooling exposes those controls.

Default complexity ladder:

- Light, local, or diagnostics-only tasks should use `gpt-5.4-mini` with
  `xhigh` reasoning. This includes doc audits, source fact ledgers, focused
  validation, status synchronization, and closure-lane chores that do not own
  complex code.
- Medium implementation or integration tasks should use `gpt-5.4` with at
  least `medium` reasoning. Use `high` when the task touches public APIs,
  bindings, architecture guards, compatibility behavior, or more than one
  closely related file family.
- Complex refactors, architecture-critical seams, public contracts, scheduler
  semantics, runtime materialization, capability/spawn/fidelity paths, and
  counterfactual or replay semantics should use `gpt-5.4` with `high` or
  `xhigh` reasoning. Use `xhigh` when an incorrect design choice could force a
  later rewrite or broaden the architecture boundary.
- If a task seems too hard to classify, choose the stronger model/budget or
  keep the immediate blocking work on the main thread.

Minimums:

- Do not assign non-trivial implementation, refactor, public-surface, or
  architecture work below `medium` reasoning.
- Do not use mini-model workers for complex cross-file design or risky code
  ownership, even with `xhigh` reasoning.
- Dispatch queues and worker packets should include a `Model / reasoning`
  column or equivalent field. Deviations from this policy must be called out in
  the dispatch packet.

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

## Linking Rule

- Project rules must be linked from the nearest authoritative index.
- Tier A governance rules should have a Chinese companion.
- Task-specific READMEs should link to this policy instead of restating it in
  full when they depend on it.
- If a worker result changes naming, layering, or ownership, the integration
  pass must reconcile the affected docs before the task is marked complete.
