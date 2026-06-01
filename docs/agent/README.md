# Agent Documentation Index

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-06-01` maintained entry point for repository-facing AI/agent
orientation.

This directory turns the maintained documentation tree into a compact operating
surface for AI agents. It does not replace the root README, standards, code, or
tests. Its job is to tell an agent which documents to load first, which
documents are normative, and which claims require implementation evidence before
they can be repeated.

## Entry Points

| File | Use |
| --- | --- |
| [rules/document_authority_map.md](rules/document_authority_map.md) | Rule index for repository documentation authority, standard references, task-specific reading paths, and capability-claim gates. |
| [rules/subproject_creation_standard.md](rules/subproject_creation_standard.md) | Standard for creating task subprojects with README, phase plan, task clusters, current status, acceptance, residuals, and archive boundaries. |
| [prompts/project_orientation_prompt.md](prompts/project_orientation_prompt.md) | Copyable task-start prompt for agents working on this repository. |
| [../standards/governance/subagent_usage_policy.md](../standards/governance/subagent_usage_policy.md) | Repository policy for delegated subagent or worker activity when the execution environment allows it. |

## How Agents Should Use This

1. Read the root [README.md](../../README.md), [docs/README.md](../README.md),
   and [rules/document_authority_map.md](rules/document_authority_map.md).
2. Select the task lane: documentation, code/runtime, tests/contracts, domain
   maturity, contribution/governance, or release/maintenance.
3. Read the lane-specific documents named by the authority map.
4. Verify claims against current code, tests, scenarios, configs, or retained
   artifacts before updating status text.
5. Use [prompts/project_orientation_prompt.md](prompts/project_orientation_prompt.md)
   when preparing a reusable agent prompt for a new task.
6. If the task creates or revives a `docs/task/**` subproject, follow
   [rules/subproject_creation_standard.md](rules/subproject_creation_standard.md).

## Repository Boundary

The ignored `.agent/` directory may exist as a local runtime or personal agent
workspace. It is not the tracked project documentation system. Tracked
agent-facing guidance lives under `docs/agent/`.

## Maintenance Rules

- Keep this directory small and operational.
- Link to existing standards instead of copying their full text.
- Add Chinese companions for maintained entry/rule/prompt documents.
- Do not promote archived, temporary, retained-artifact, or dated task records
  into current authority unless a maintained README does so explicitly.
- Whenever a new standardized document changes project-wide rules, add it to the
  authority map instead of relying on chat memory.
