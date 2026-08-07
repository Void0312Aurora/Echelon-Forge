# Legacy Standards Migration Index

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/standards/README.md`
Owner: `legacy/standards-migration-index`
Last verified: `2026-08-08`

Status: migration-time index for the standards that have not yet moved to a
content owner.

`docs/standards/` is not a target ownership root. Existing documents listed
below retain their current authority until their separate migration slices
land, but no new document may be created under this legacy root. Stable rules
must be written under the applicable owner's `standards/` surface.

## Migrated Owner Routes

| Content | Current owner route | Status |
| --- | --- | --- |
| Joint common core | [Joint owner](../domains/joint/README.md) | migrated |
| Service profiles | [Service-profile owner](../domains/joint/service_profiles/README.md) | migrated |
| Air specialization | [Air owner](../domains/air/README.md) | migrated |
| Ground specialization | [Ground owner](../domains/ground/README.md) | migrated |
| Documentation governance | [Documentation engineering](../engineering/documentation/README.md) | migrated |
| Automation governance | [Automation engineering](../engineering/automation/README.md) | migrated |
| Release and dependency governance | [Release engineering](../engineering/release/README.md) | migrated |

These owner-local documents, not this legacy directory, define the current
route for migrated content.

## Remaining Legacy Sources

| Legacy subtree | Maintained purpose | Target disposition |
| --- | --- | --- |
| [`naval/`](naval/README.md) | Naval specialization standards and reference data | `docs/domains/naval/` |
| [`model/`](model/README.md) | Policy/model execution architecture | `docs/learning/` |
| [`foundation/`](foundation/conventions.md) | Mixed architecture, system-realism, and research-source rules | split among `docs/architecture/`, `docs/systems/`, and `docs/research/` |
| [`bridge/`](bridge/runtime_workflow_and_contract_baseline.md) | Runtime/workflow contracts and scenario guidance | split between `docs/architecture/` and `docs/operations/` |
| [`overview/`](overview/document_alignment_map.md) | Documentation alignment reference | `docs/engineering/documentation/reference/` |
| [`planning/`](planning/modularization_plan.md) | Draft modularization issue with current `src/*/domains` layout notes | `docs/architecture/work/issues/` after factual refresh |

The target column is a migration decision, not evidence that the target file
already exists. `foundation/` and `bridge/` contain mixed owners and must be
split; moving either directory wholesale would recreate the current taxonomy
problem.

## Routing Rules

1. Determine the content owner before moving or substantially rewriting a
   legacy source.
2. Preserve document kind and lifecycle. A draft planning supplement does not
   become a standard merely because it moves below an owner.
3. Update every non-archive consumer in the same slice. Existing archive files
   remain frozen and outside the default verdict surface.
4. Do not add documents or subdirectories under `docs/standards/`.
5. Remove this index only after no maintained source remains below the legacy
   root and every current entry point routes directly to an owner.

## Relationship To Work Documents

Legacy [plans](../plan/README.md) and [tasks](../task/README.md) may record
implementation state, evidence, or unresolved work. They must cite the relevant
owner standard and cannot redefine its stable vocabulary. When a stable
contract emerges from a task, promote it to the owner's `standards/` surface;
do not copy it back into this directory.

## Governance

- [Standards Maintenance Policy](../engineering/documentation/standards/standards_maintenance_policy.md)
- [Document Lifecycle Policy](../engineering/documentation/standards/document_lifecycle_policy.md)
- [Bilingual Documentation Policy](../engineering/documentation/standards/bilingual_documentation_policy.md)
- [Documentation Information Architecture](../project/documentation_architecture.md)
- [Document Alignment Map](overview/document_alignment_map.md)
