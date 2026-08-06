# Documentation Information Architecture

Language:

- English canonical: `documentation_architecture.md`
- Chinese companion: [documentation_architecture.zh.md](documentation_architecture.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/project/documentation_architecture.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

## Objective

Unify maintained documentation by content ownership. The directory tree must
not mix subject domains, document kinds, audiences, and lifecycle states at the
same level.

The target maintained roots are:

1. `project/` — purpose, maturity, global status, roadmap, and project decisions.
2. `architecture/` — cross-domain architecture, runtime, contracts, backends, and ADRs.
3. `domains/` — `air`, `naval`, `ground`, and `joint` mission-domain ownership.
4. `systems/` — environment, physics, sensing, command/tasking, weapons, and effects.
5. `learning/` — RL, models, training, evaluation protocols, and experiments.
6. `operations/` — operator/maintainer how-to material, current references, visualization, and integrations.
7. `engineering/` — contributing, build, test, tooling, documentation governance, and automation.
8. `research/` — research questions, methods, results, publications, and external sources.

`archive/` is the single logical lifecycle endpoint and is excluded from the
maintained source audit. It is not materialized during Phase 1 because the
lowercase path collides with legacy `docs/Archive/` on case-insensitive Windows
filesystems. Existing archive trees remain frozen; resolving that collision is
a separate historical migration and this plan does not authorize rewrites.

## Internal Shape

Each maintained owner starts at a bilingual `README`. Optional child surfaces
are created only when they contain maintained material:

- `standards/` for normative rules;
- `reference/` for verified current facts;
- `work/active/` for authorized implementation work;
- `work/issues/` for unresolved gaps;
- `reviews/` for current review and acceptance decisions.

The [documentation structure examples](../engineering/documentation/structure_examples.md)
define the reusable skeleton for each surface and for nested owners. They are
shape guidance, not technical or normative content for an owner.

Document kind and lifecycle remain explicit metadata. Completed task facts are
promoted to a maintained standard/reference/README; the remaining package is
archived rather than kept indefinitely as an active task.

## Migration Phases

- Phase 1: create the ownership roots; migrate `manual` to `operations`, `agent`
  to `engineering/automation`, and `book` to `research/sources`.
- Phase 2 (completed 2026-08-07): retire the maintained `forward`,
  `evaluation`, and `log` surfaces by routing plans and reviews to their content
  owners. Existing `evaluation/archive/` content remains frozen and untouched.
- Phase 3: split `standards`, `plan`, and `task` by content ownership. Do not
  move those trees wholesale into new global buckets.
- Phase 4: switch all maintained entry points and disallow new writes to legacy
  roots; remove a legacy root only after it has no maintained sources.

## Gates

Every migration slice must preserve bilingual pairs, pass the maintained link
audit, update current routes, and keep archive sources excluded. The repository
must reject unregistered top-level documentation roots. Large domain moves are
separate reviewed iterations.

## Non-goals

- Reorganizing or rewriting existing archives.
- Renaming code domains to match documentation paths.
- Creating empty directory skeletons.
- Treating a directory move as evidence that a capability is accepted.
