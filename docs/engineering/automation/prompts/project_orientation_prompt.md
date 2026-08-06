# Project Orientation Prompt For Agents

Language:
- English canonical: `project_orientation_prompt.md`
- Chinese companion: [project_orientation_prompt.zh.md](project_orientation_prompt.zh.md)

Status: `2026-06-01` copyable prompt template for agents working on this
repository.

Use this when starting a new agent or worker on Echelon Forge. Fill the task
block before dispatching or pasting.

```md
You are working in the Echelon Forge repository.

Task:
<describe the concrete task>

Write scope:
<list files/directories the agent may modify, or say read-only>

Non-goals:
<list files/directories or claims that are out of scope>

Validation expected:
<list commands, link checks, tests, or inspection checks expected>

Before acting, read:

1. README.md
2. docs/README.md
3. docs/engineering/automation/rules/document_authority_map.md
4. The local README and standard/task documents named by the authority map for
   this task.
5. If creating or reviving a task subproject:
   docs/engineering/automation/rules/subproject_creation_standard.md.

Repository rules:

- Do not treat archive, Archive, temp, retained artifacts, or dated cluster
  packets as current authority unless a maintained README explicitly promotes
  them.
- Do not upgrade a capability claim unless there is a maintained implementation
  owner, a maintained runtime/config/test surface, and current documentation
  naming the evidence level.
- Read project identity, domain maturity, and current status from maintained
  entry documents and verify them against code/tests before repeating them.
- Treat retained artifacts as scoped evidence only; do not let one retained
  packet or dated record define broader project maturity.
- Preserve unrelated dirty worktree changes.
- If subagents or workers are allowed by the current execution environment and
  user request, follow docs/standards/governance/subagent_usage_policy.md.
- If creating a `docs/task/**` subproject, include a README, finite task-cluster
  document, phase/status/acceptance/residual sections, parent index links, and
  archive/current boundaries as required by the subproject creation standard.

Output requirements:

- Report changed files.
- Separate confirmed implementation facts from documentation interpretation.
- Name residual risks.
- List validation commands and outcomes.
- If the task produces a durable project assessment, write it into the relevant
  maintained assessment, task, or README surface instead of leaving it only in
  chat.
```
