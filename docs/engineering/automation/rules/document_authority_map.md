# Agent Document Authority Map

Language:
- English canonical: `document_authority_map.md`
- Chinese companion: [document_authority_map.zh.md](document_authority_map.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/rules/document_authority_map.md`
Owner: `engineering/automation-governance`
Last verified: `2026-08-08`

Status: `2026-08-08` maintained rule index for agents reading repository
documentation.

Scope: repository documentation and project-specific operating rules. This file
does not override user requests, tool/runtime constraints, safety rules, or
platform instructions. Within the repository documentation set, use this map to
decide what to read and what can be treated as current authority.

## Fast Start

For almost every task, begin with:

1. [Root README](../../../../README.md)
2. [Docs Index](../../../README.md)
3. This authority map

Then choose the task-specific path below.

## Authority Stack

| Rank | Source | Rule |
| --- | --- | --- |
| 1 | Current user task, current worktree, and current code/tests | Do not overwrite unrelated local changes; verify implementation claims locally. |
| 2 | Maintained code, scenarios, configs, tests, and contract runners | Executable evidence wins over stale prose. Passing a narrow gate does not promote a whole domain. |
| 3 | Maintained owner-local standards under `docs/<owner>/standards/` | The relevant owner-local standard wins within its declared scope; use the alignment map for cross-owner routing. |
| 4 | Root README, `docs/README*`, local README files | Own current navigation and maturity entry points. Start there before reading dated task files. |
| 5 | Owner-local `reference/`, `work/active/`, `work/issues/`, and `reviews/` | Own verified facts, authorized work, unresolved gaps, and retained decisions within the owner boundary. |
| 6 | `docs/operations/`, `docs/reference_artifacts*`, `tests/README*` | Describe code boundaries, operator workflows, retained evidence, and test-system intent. |
| 7 | `docs/plan/**/archive/`, `docs/task/**/archive/`, `forward/`, `Archive`, `temp`, retained artifacts, dated cluster packets | Supporting or historical records only unless a maintained owner README explicitly promotes them. |

## Standardized Document Index

| Question | Read |
| --- | --- |
| Which maintained standard owns names and layers? | Start from the applicable owner README and its owner-local `standards/`; use the [Document Alignment Map](../../documentation/reference/document_alignment_map.md) for cross-owner routing. |
| What are the cross-domain conventions? | [Simulation Conventions](../../../architecture/standards/simulation_conventions.md), [Runtime Workflow and Contract Baseline](../../../architecture/standards/runtime_workflow_and_contract_baseline.md), [Scenario Configuration Guide](../../../operations/howto/scenario_configuration_guide.md) |
| What realism claims are allowed? | [Gradient Realism Principles](../../../systems/standards/gradient_realism_principles.md), [Public Data Source Admission Standard](../../../research/standards/public_data_source_admission.md) |
| How should service/domain terms be routed? | [Joint Standards Overview](../../../domains/joint/README.md), [Service Profile Overview](../../../domains/joint/service_profiles/README.md), [Air Standards](../../../domains/air/README.md), [Naval Standards](../../../domains/naval/README.md), [Ground Standards](../../../domains/ground/README.md) |
| Where is policy/model architecture defined? | [Learning owner](../../../learning/README.md), [Policy Execution Architecture](../../../learning/standards/policy_execution_architecture.md) |
| How should architecture/runtime work be routed? | [Architecture owner](../../../architecture/README.md), [Modularization issue](../../../architecture/work/issues/modularization_plan.md), [Runtime Workflow and Contract Baseline](../../../architecture/standards/runtime_workflow_and_contract_baseline.md), [Scenario Configuration Guide](../../../operations/howto/scenario_configuration_guide.md) |
| How should bilingual documentation be handled? | [Bilingual Documentation Policy](../../documentation/standards/bilingual_documentation_policy.md), [Bilingual Document Clusters](../../documentation/reference/bilingual_document_clusters.md) |
| How are document kinds, lifecycle, evidence, generated output, config indexes, links, and archives governed? | [Document Lifecycle Policy](../../documentation/standards/document_lifecycle_policy.md) |
| How are releases and dependency changes governed? | [Release and Dependency Policy](../../release/standards/release_and_dependency_policy.md) |
| Where is repository-wide consolidation sequenced and accepted? | Repository Consolidation Plan (`git show 3dc34673:docs/plan/archive/repository_consolidation_completed_20260729/README.md`) |
| How should community, license, or security text be handled? | [Contributing](../../../../CONTRIBUTING.md), [License](../../../../LICENSE), [Third Party Notices](../../../../THIRD_PARTY_NOTICES.md), [Security](../../../../SECURITY.md), [Code of Conduct](../../../../CODE_OF_CONDUCT.md) |
| How should delegated work be coordinated? | [Subagent Usage Policy](../standards/subagent_usage_policy.md), [WP Closure Lane Policy](../standards/wp_closure_lane_policy.md) |
| How should new scoped work be created? | [Subproject Creation Standard](subproject_creation_standard.md), [Subagent Usage Policy](../standards/subagent_usage_policy.md), and the affected owner's `work/active/` or `work/issues/` route |

## Capability Claim Gate

Before writing that a capability is implemented, mature, accepted, or ready,
require all three:

1. A maintained implementation owner in code or data.
2. A maintained runtime, config, scenario, test, or contract surface.
3. A current document that names the evidence level without implying a higher
   capability.

Generic negative boundaries:

- Do not turn scoped evidence into whole-domain maturity.
- Do not treat scenario-only assets as active training/runtime evidence unless
  maintained documentation and tests say so.
- Do not treat retained artifacts, signoff packets, or dated records as broader
  project authority unless a maintained entry promotes them.
- Do not let compatibility, diagnostics, or exploratory paths redefine the
  maintained path without an owner-local standard or work-entry update.

## Task Reading Recipes

| Task type | Required reading |
| --- | --- |
| Documentation refresh | Root README, docs index, this map, [Document Lifecycle Policy](../../documentation/standards/document_lifecycle_policy.md), affected local README, standards owner. |
| Repository consolidation | Repository Consolidation Plan (`git show 3dc34673:docs/plan/archive/repository_consolidation_completed_20260729/README.md`), affected owner READMEs, current callers/tests, and the required independent-review protocol. |
| Code/runtime change | Affected `src/`, `python/`, or `gym_envs` README; source layer map; relevant owner-local work entry; relevant tests. |
| Test or contract change | Tests README, local test README, reference artifacts, and the relevant owner-local architecture or domain contract. |
| Domain maturity statement | Domain owner README, domain standards, current owner-local status or acceptance record if indexed, implementation/test evidence. |
| Community/governance/license text | CONTRIBUTING, LICENSE, THIRD_PARTY_NOTICES, SECURITY, and the maintained standards routed by the relevant owner index. |
| Release or dependency change | [Release and Dependency Policy](../../release/standards/release_and_dependency_policy.md), affected manifests/lockfiles, release tooling, and focused tests. |
| Delegated-agent work | This map, subagent usage policy, assigned write set, required output packet. |
| New scoped work package | This map, subproject creation standard, owner README, relevant standards, and an owner-local `work/active/` or `work/issues/` entry. |

## Agent Output Rule

When reporting back, separate:

- confirmed implementation facts
- documentation interpretation
- residual risks
- validation commands and outcomes
- files changed

Do not leave important findings only in chat if the user asked for a durable
project assessment. Record them under the relevant maintained assessment, task,
or README surface.
