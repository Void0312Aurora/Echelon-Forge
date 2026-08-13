# Documentation Index

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/README.md`
Owner: `project documentation`
Last verified: `2026-08-12`

`docs/` is organized by content ownership. Document kind is expressed inside
the owning area; retirement is a lifecycle endpoint recorded in a ledger rather
than a competing current authority stored in the tree.

## Target Ownership Roots

| Area | Ownership | Migration status |
| --- | --- | --- |
| [project](project/README.md) | Purpose, maturity, global status, roadmap, project decisions | Active; owns the migration plan |
| [architecture](architecture/README.md) | Cross-domain architecture, runtime, contracts, backends, ADRs | Standards, references, reviews, and open architecture work are owner-local |
| [domains](domains/README.md) | Air, naval, ground, joint | Joint/service-profile, Air, Ground, and Naval standards routed to owners |
| [systems](systems/README.md) | Environment, physics, sensing, command/tasking, weapons, effects | Environment, command/tasking, effects, weapons, and realism routes are owner-local |
| [learning](learning/README.md) | RL, models, training, evaluation protocols, experiments | Standards, active work, issues, and retained reviews are owner-local |
| [operations](operations/README.md) | How-to, current reference, visualization and integration operations | Scenario, manual, and visualization routes migrated |
| [engineering](engineering/README.md) | Contributing, build, tests, tooling, documentation governance, automation, release | Documentation, automation, release, and testing routes are owner-local |
| [research](research/README.md) | Questions, methods, results, publications, external sources | Source index and public-data admission standard migrated |

The [documentation information architecture](project/documentation_architecture.md)
defines target boundaries, migration phases, and cutover gates.

## Retired Legacy Containers

All maintained `standards`, `plan`, and `task` sources route through their
content owners. Use the [Document Alignment Map](engineering/documentation/reference/document_alignment_map.md)
for the distributed authority map.

The `Archive/`, `evaluation/`, `manual/`, `plan/`, and `task/` containers held
historical storage only and were retired on 2026-08-13. Git history is the
archive: every retired file is listed in the
[Retired Documentation Ledger](archive_ledger.md) with the
`git show <commit>:<path>` address that still retrieves it, and the
machine-readable form is `engineering/documentation/reference/retired_documents.json`.
Owner-local archives retired at the same time are listed in the
[Retired Systems Archive Ledger](systems/archive_ledger.md).

Do not reintroduce an `archive/`, `Archive/`, or `temp/` path component under
`docs/`; `tests/architecture/governance/test_archive_retirement.py` fails the
build if one reappears. Retire a document by deleting it and adding a ledger
row, and route content that is still current to its owner instead.

## Direct Operational Routes

- [Engine capabilities](operations/reference/engine_capabilities.md)
- [Source layer map](operations/reference/src_layer_map.md)
- [Physics engine inventory](operations/reference/physics_engine_inventory.md)
- [Visualization guide](operations/howto/visualization_guide.md)
- [Automation and agent guidance](engineering/automation/README.md)
- [Documentation engineering and examples](engineering/documentation/README.md)
- [Release and dependency governance](engineering/release/README.md)
- [Testing engineering](engineering/testing/README.md)
- [Retained artifact provenance](reference_artifacts.md)
- [Retired documentation ledger](archive_ledger.md)
- [Test-system orientation](../tests/README.md)

## Authority Rules

1. Current user instructions, code, configs, scenarios, tests, and contracts
   outrank stale text.
2. A maintained owner README routes current authority; a dated packet is
   supporting evidence unless explicitly promoted.
3. Directory presence is not a capability claim.
4. A plan, task, review, reference, or standard retains its document kind after
   migration; the directory owner does not change its evidentiary boundary.
5. Retention is retirement: a superseded document is deleted and recorded in an
   archive ledger rather than kept under an `archive/` path. There is no
   maintained archive directory to audit, and the legacy `docs/Archive/`
   case-collision that once blocked a `docs/archive/` endpoint is gone with it.

## Language And Rights

Stable entry points, navigation READMEs, standards, references, and how-to
material use English canonical pages with Chinese companions. Work and
evidence surfaces (`docs/**/work/**`) are maintained in English only; a Chinese
companion is added only when a document is explicitly promoted into the strict
bilingual surface. Chinese navigation pages may therefore link directly to
English work documents. Existing archives keep the language layout they were
frozen with. Repository documentation follows Apache-2.0 unless a retained
third-party source states otherwise; see
[LICENSE](../LICENSE) and [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).
