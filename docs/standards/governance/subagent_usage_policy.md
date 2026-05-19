# Subagent Usage Policy

Language:
- English canonical: `subagent_usage_policy.md`
- Chinese companion: [subagent_usage_policy.zh.md](subagent_usage_policy.zh.md)

Status: `2026-05-20` authoritative for distributed work in maintained docs and
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

## Handoff And Integration

- Every delegated task must return the touched files and a short conclusion.
- The main thread owns final scope decisions, acceptance, and any publish or
  merge action.
- A final integration worker owns cross-file conflict resolution and task
  status updates.
- Status docs and README indexes must be synchronized with the final
  authoritative location.

## Linking Rule

- Project rules must be linked from the nearest authoritative index.
- Tier A governance rules should have a Chinese companion.
- Task-specific READMEs should link to this policy instead of restating it in
  full when they depend on it.
- If a worker result changes naming, layering, or ownership, the integration
  pass must reconcile the affected docs before the task is marked complete.
