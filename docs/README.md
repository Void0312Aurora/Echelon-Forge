# Documentation Index

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/README.md`
Owner: `project documentation`
Last verified: `2026-08-06`

`docs/` is organized by content ownership. Document kind is expressed inside
the owning area; archive is a lifecycle endpoint rather than a competing
current authority.

## Target Ownership Roots

| Area | Ownership | Migration status |
| --- | --- | --- |
| [project](project/README.md) | Purpose, maturity, global status, roadmap, project decisions | Active; owns the migration plan |
| [architecture](architecture/README.md) | Cross-domain architecture, runtime, contracts, backends, ADRs | Route established; legacy plan/task sources remain authoritative until migrated |
| [domains](domains/README.md) | Air, naval, ground, joint | Route established; content migration pending |
| [systems](systems/README.md) | Environment, physics, sensing, command/tasking, weapons, effects | Route established; content migration pending |
| [learning](learning/README.md) | RL, models, training, evaluation protocols, experiments | Route established; content migration pending |
| [operations](operations/README.md) | How-to, current reference, visualization and integration operations | Phase-1 manual migration complete |
| [engineering](engineering/README.md) | Contributing, build, tests, tooling, documentation governance, automation | Phase-1 automation migration complete |
| [research](research/README.md) | Questions, methods, results, publications, external sources | Phase-1 source-index migration complete |

The [documentation information architecture](project/documentation_architecture.md)
defines target boundaries, migration phases, and cutover gates.

## Current Legacy Routes

The following roots still contain maintained sources during the transition:

- [standards](standards/README.md): normative vocabulary and governance;
- [plan](plan/README.md): active/frozen direction and migration plans;
- [task](task/README.md): scoped implementation work and status;
- [forward](forward/README.md): unpromoted ideas and backlogs;
- `evaluation/`: reviews awaiting owner routing.

Do not add new top-level categories or expand these legacy roots. A document
moves only after its content owner and current authority are identified.

## Direct Operational Routes

- [Engine capabilities](operations/reference/engine_capabilities.md)
- [Source layer map](operations/reference/src_layer_map.md)
- [Physics engine inventory](operations/reference/physics_engine_inventory.md)
- [Visualization guide](operations/howto/visualization_guide.md)
- [Automation and agent guidance](engineering/automation/README.md)
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
