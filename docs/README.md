# Documentation Index

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/README.md`
Owner: `project documentation`
Last verified: `2026-08-08`

`docs/` is organized by content ownership. Document kind is expressed inside
the owning area; archive is a lifecycle endpoint rather than a competing
current authority.

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

## Archive-only Legacy Containers

All maintained `standards`, `plan`, and `task` sources now route through their
content owners. Use the [Document Alignment Map](engineering/documentation/reference/document_alignment_map.md)
for the distributed authority map. The remaining `plan/` and `task/` paths all
contain an `archive` component and are historical storage, not current routes.

Do not add new maintained content under `docs/plan/`, `docs/task/`, legacy
`Archive/`, `evaluation/archive/`, or `manual/archive/`. Existing archives are
excluded from the maintained tracking surface and are changed only by a
separately authorized historical migration.

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
- [Test-system orientation](../tests/README.md)

## Authority Rules

1. Current user instructions, code, configs, scenarios, tests, and contracts
   outrank stale text.
2. A maintained owner README routes current authority; a dated packet is
   supporting evidence unless explicitly promoted.
3. Directory presence is not a capability claim.
4. A plan, task, review, reference, or standard retains its document kind after
   migration; the directory owner does not change its evidentiary boundary.
5. Existing archives remain frozen and excluded from maintained-source audits.
   The future logical `docs/archive/` endpoint is not materialized in this
   phase because it collides case-insensitively with legacy `docs/Archive/` on
   Windows; resolving that historical layout is a separate migration.

## Language And Rights

Stable entry points, standards, references, and how-to material use English
canonical pages with Chinese companions. High-churn work/evidence may remain
English-only unless promoted. Repository documentation follows Apache-2.0
unless a retained third-party source states otherwise; see
[LICENSE](../LICENSE) and [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).
