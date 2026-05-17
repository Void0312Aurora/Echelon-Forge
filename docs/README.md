# Docs Index

`docs/` collects maintained architecture notes, planning material, task records,
standards, and reference manuals for the current repository.

Use this directory as a navigation surface, not as proof that every historical
note is still an active implementation authority.

## Start Here

- [plan/README.md](plan/README.md)
  - Architecture/program plans, frozen execution scopes, and plan-governance notes.
- [task/README.md](task/README.md)
  - Focused task documents, implementation packages, and progress checkpoints.
- [standards/README.md](standards/README.md)
  - Joint/service/platform modeling baselines and specialization notes.
- [manual/](manual)
  - Code layer maps, engine capability notes, physics inventory, and operator-facing manuals.
- [forward/README.md](forward/README.md)
  - Forward-looking ideas that are not yet frozen into implementation tasks.
- [reference_artifacts.md](reference_artifacts.md)
  - Retained config/scenario/artifact provenance notes for lines that still matter.

## Authority Notes

- `plan/`, `task/`, `standards/`, and `manual/` are the maintained entry
  surfaces.
- `Archive/` preserves historical design material and retired routes. It is
  useful for provenance, but it is not the default authority for current work.
- `temp/` is scratch space and should not be treated as a maintained source of
  truth.

## Usage Rule

- If a task needs code changes, prefer reading the relevant `plan/` or `task/`
  entry first, then verify against the current code tree.
- If a document links to historical artifacts, confirm the target still exists
  in the workspace before treating it as an actionable entrypoint.
