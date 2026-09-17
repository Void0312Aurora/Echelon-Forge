# Equipment Work Set (Reduced Scope)

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/README.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`
Content status: reduced write set for the equipment work while the branch lags `origin/main`. This file is a work-scope declaration, not a data contract and not a maturity claim.

## Responsibility

Declares the reduced write set for the equipment work on `codex/database-scaffold`, so that further
collection and repair stay conflict-free while the branch is 218 commits behind `origin/main`.

## Not Responsible For

It does not approve a source, grant runtime authority, define the final equipment-data schema, or
promote any equipment record above its current backlog status. It does not replace
[backlog/README.md](../research/equipment/backlog/README.md) as the state model or
[coverage/README.md](../research/equipment/coverage/README.md) as the batch plan.

## Why This Scope Is Reduced

The branch was cut at `d1ebb5d3` and carries exactly one own commit, `3fc57c7e`. `origin/main` has
advanced 218 commits since that base. The divergence is real but the conflict surface is empty:
`origin/main` contains zero files under `database/`, so the whole tree this work touches is
branch-exclusive. Anything written outside `database/` would land in the 218-commit moving surface
instead.

## Write Set

Allowed:

- `database/**` — catalog leaves, backlog queues, coverage queue, raw source packages, ledger, templates.

Forbidden:

- `docs/**` — route new work packages through the existing `docs/research/` owners instead of adding a parallel subproject surface here.
- `src/**`, `python/**`, `gym_envs/**`, `scenarios/**`, `examples/**`, `tests/**`, `tools/**`, `CMakeLists.txt`, `pyproject.toml`.
- Any change to already-landed catalog leaves other than a cited repair (dangling reference, missing `Equipment ID`, missing `Last verified`).
- Any new runtime JSON or any claim that this tree is consumed by the runtime loader.

## Conflict Rule

`database/**` is the only directory where this branch and `origin/main` cannot collide. Within
`database/`, the scope is limited to `database/research/equipment/**` and `database/_templates/**`.
`database/{platforms,modules,weapons,sources}/` are superseded by the equipment research tree and are
held read-only unless a decision changes that.

## Normative Tables

These files are single-writer at any time. Do not split any of them across concurrent authors:

| Table | Path |
| --- | --- |
| Coverage queue | `database/research/equipment/coverage/coverage.csv` |
| Air backlog | `database/research/equipment/backlog/air.csv` |
| Ground backlog | `database/research/equipment/backlog/ground.csv` |
| Naval backlog | `database/research/equipment/backlog/naval.csv` |
| Weapon backlog | `database/research/equipment/backlog/weapon.csv` |
| Module backlog | `database/research/equipment/backlog/module.csv` |

## Closure Gate

A collection or repair cluster is done only when all five hold:

1. Every `p5-*` source id named in a catalog leaf resolves to a `Source ID:` line in a `raw/sources/**/manifest.md`.
2. Every backlog `catalog_path` exists, and the leaf carries an `Equipment ID` equal to the CSV `equipment_id`.
3. Backlog `status` and `coverage.csv` `status` agree for every shared candidate.
4. No `D`-tier source and no source package without a retention note is present.
5. `git status --porcelain -- database` shows only files inside the write set.

## Current State

See [equipment_work_current_status_20260917.md](equipment_work_current_status_20260917.md) for the
measured state and [equipment_work_task_clusters_20260917.md](equipment_work_task_clusters_20260917.md)
for the finite cluster list.

## Maintenance Trigger

Update this file when the branch catches up with `origin/main`, when the write set changes, or when
the equipment tree becomes runtime-consumed.
