# Agent Document Authority Map

Language:
- English canonical: `document_authority_map.md`
- Chinese companion: [document_authority_map.zh.md](document_authority_map.zh.md)

Status: `2026-06-01` maintained rule index for agents reading repository
documentation.

Scope: repository documentation and project-specific operating rules. This file
does not override user requests, tool/runtime constraints, safety rules, or
platform instructions. Within the repository documentation set, use this map to
decide what to read and what can be treated as current authority.

## Fast Start

For almost every task, begin with:

1. [Root README](../../../README.md)
2. [Docs Index](../../README.md)
3. This authority map

Then choose the task-specific path below.

## Authority Stack

| Rank | Source | Rule |
| --- | --- | --- |
| 1 | Current user task, current worktree, and current code/tests | Do not overwrite unrelated local changes; verify implementation claims locally. |
| 2 | Maintained code, scenarios, configs, tests, and contract runners | Executable evidence wins over stale prose. Passing a narrow gate does not promote a whole domain. |
| 3 | `docs/standards/` | Owns naming, layering, service/domain ownership, public-source admission, document lifecycle, bilingual policy, and governance rules. |
| 4 | Root README, `docs/README*`, local README files | Own current navigation and maturity entry points. Start there before reading dated task files. |
| 5 | `docs/plan/` and active `docs/task/` entries | Own architecture direction, scoped implementation plans, progress records, and residuals. |
| 6 | `docs/manual/`, `docs/reference_artifacts*`, `tests/README*` | Describe code boundaries, operator workflows, retained evidence, and test-system intent. |
| 7 | `forward/`, `archive`, `Archive`, `temp`, retained artifacts, dated cluster packets | Supporting or historical records only unless a maintained README explicitly promotes them. |

## Standardized Document Index

| Question | Read |
| --- | --- |
| Which document owns names and layers? | [Standards Overview](../../standards/README.md), [Document Alignment Map](../../standards/overview/document_alignment_map.md) |
| What are the cross-domain conventions? | [Simulation Conventions](../../standards/foundation/conventions.md), [Runtime Workflow and Contract Baseline](../../standards/bridge/runtime_workflow_and_contract_baseline.md), [Scenario Configuration Guide](../../standards/bridge/scenario_guide.md) |
| What realism claims are allowed? | [Gradient Realism Principles](../../standards/foundation/gradient_realism_principles.md), [Public Data Source Admission Standard](../../standards/foundation/public_data_source_admission.md) |
| How should service/domain terms be routed? | [Joint Standards Overview](../../standards/joint/README.md), [Service Profile Overview](../../standards/services/README.md), [Air Standards](../../standards/air/README.md), [Naval Standards](../../standards/naval/README.md), [Ground Standards](../../standards/ground/README.md) |
| How should architecture/runtime work be routed? | [Runtime Workflow and Contract Baseline](../../standards/bridge/runtime_workflow_and_contract_baseline.md), [Scenario Configuration Guide](../../standards/bridge/scenario_guide.md), [Standards Overview](../../standards/README.md) |
| How should bilingual documentation be handled? | [Bilingual Documentation Policy](../../standards/governance/bilingual_documentation_policy.md), [Bilingual Document Clusters](../../standards/governance/bilingual_document_clusters.md) |
| How are document kinds, lifecycle, evidence, generated output, config indexes, links, and archives governed? | [Document Lifecycle Policy](../../standards/governance/document_lifecycle_policy.md) |
| Where is repository-wide consolidation sequenced and accepted? | [Repository Consolidation Plan](../../plan/repository_consolidation/README.md) |
| How should community, license, or security text be handled? | [Contributing](../../../CONTRIBUTING.md), [License](../../../LICENSE), [Third Party Notices](../../../THIRD_PARTY_NOTICES.md), [Security](../../../SECURITY.md), [Code of Conduct](../../../CODE_OF_CONDUCT.md) |
| How should delegated work be coordinated? | [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md), [WP Closure Lane Policy](../../standards/governance/wp_closure_lane_policy.md) |
| How should a new task subproject be created? | [Subproject Creation Standard](subproject_creation_standard.md), [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md), [Task Index](../../task/README.md) |

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
  maintained path without a standards or task update.

## Task Reading Recipes

| Task type | Required reading |
| --- | --- |
| Documentation refresh | Root README, docs index, this map, [Document Lifecycle Policy](../../standards/governance/document_lifecycle_policy.md), affected local README, standards owner. |
| Repository consolidation | [Repository Consolidation Plan](../../plan/repository_consolidation/README.md), affected owner READMEs, current callers/tests, and the required independent-review protocol. |
| Code/runtime change | Affected `src/`, `python/`, or `gym_envs` README; source layer map; relevant plan/task entry; relevant tests. |
| Test or contract change | Tests README, local test README, reference artifacts, relevant standards/bridge contract. |
| Domain maturity statement | Domain task README, domain standards README, current local status or acceptance doc if indexed, implementation/test evidence. |
| Community/governance/license text | CONTRIBUTING, LICENSE, THIRD_PARTY_NOTICES, SECURITY, standards/governance. |
| Delegated-agent work | This map, subagent usage policy, assigned write set, required output packet. |
| New `docs/task/**` subproject | This map, subproject creation standard, parent domain README, relevant standards owner, task-cluster plan. |

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
