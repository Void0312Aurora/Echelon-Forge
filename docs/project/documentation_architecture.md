# Documentation Information Architecture

Language:

- English canonical: `documentation_architecture.md`
- Chinese companion: [documentation_architecture.zh.md](documentation_architecture.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/project/documentation_architecture.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

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
7. `engineering/` — contributing, build, test, tooling, documentation governance, automation, dependency, and release.
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
- Phase 3 (completed 2026-08-08): split `standards`, `plan`, and `task` by content
  ownership. The first slice moves documentation, automation, dependency, and
  release governance into `engineering/`; the second slice moves the Joint
  common-core README and standards into `domains/joint/`; the third parallel
  wave moves service profiles, Air standards, and Ground standards to their
  owner-local surfaces; the fourth parallel wave moves Naval standards and
  references, the policy-architecture standard, and the modularization issue to
  their owners. The fifth wave moves runtime conventions and workflow into
  `architecture/`, gradient-realism gates into `systems/`, scenario authoring
  into `operations/`, source admission into `research/`, and the alignment map
  into documentation engineering; it then removes the empty legacy standards
  root. The final parallel owner slices route retained plan/task standards,
  references, active work, issues, and reviews into their owners and place
  completed packages in new archive containers. No maintained plan/task source
  remains under the legacy roots.
- Phase 4 (completed 2026-08-08): switch all maintained entry points, disallow
  new maintained writes to legacy roots, and retain `plan/` and `task/` only as
  archive containers because existing archives are outside migration scope.

## Gates

Every migration slice must preserve bilingual pairs, pass the maintained link
audit, update current routes, and keep archive sources excluded. The repository
must reject unregistered top-level documentation roots and any tracked
non-archive source under the retired `standards`, `plan`, or `task` surfaces.

## Non-goals

- Reorganizing or rewriting existing archives.
- Renaming code domains to match documentation paths.
- Creating empty directory skeletons.
- Treating a directory move as evidence that a capability is accepted.
