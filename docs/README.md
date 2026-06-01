# Docs Index

`docs/` collects maintained architecture notes, planning material, task records,
standards, and reference manuals for the current repository.

Use this directory as a navigation surface, not as proof that every historical
note is still an active implementation authority.

## Start Here

- [plan/README.md](plan/README.md)
  - Architecture/program plans, frozen execution scopes, and plan-governance notes.
- [plan/documentation_bilingual_migration_plan_20260518.md](plan/documentation_bilingual_migration_plan_20260518.md)
  - English-primary bilingual rollout plan for the active docs tree.
- [task/README.md](task/README.md)
  - Focused task documents, implementation packages, and progress checkpoints.
- [standards/README.md](standards/README.md)
  - Joint/service/platform modeling baselines and specialization notes.
- [standards/bilingual_documentation_policy.md](standards/governance/bilingual_documentation_policy.md)
  - Canonical language, file-pairing, and batch translation policy.
- [manual/](manual)
  - Code layer maps, engine capability notes, physics inventory, and operator-facing manuals.
- [forward/README.md](forward/README.md)
  - Forward-looking ideas that are not yet frozen into implementation tasks.
- [reference_artifacts.md](reference_artifacts.md)
  - Retained config/scenario/artifact provenance notes for lines that still matter.

## Authority Notes

- `plan/`, `task/`, `standards/`, and `manual/` are the maintained entry
  surfaces.
- Maintained documentation is covered by the repository-level Apache-2.0
  license unless a file or retained third-party artifact states otherwise.
  Third-party assets, datasets, source excerpts, and retained input artifacts
  keep their own rights and license status; see
  [../LICENSE](../LICENSE) and
  [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
- The strict bilingual maintenance surface is intentionally narrower than the
  whole docs tree: it focuses on entry navigation, standards/governance,
  operator manuals, and stable plan authority.
- High-churn task histories, dated checkpoints, and forward-looking idea docs
  should be treated as English-canonical by default unless a narrower slice is
  explicitly promoted into the bilingual maintained surface.
- Avoid treating mixed-language pages as the target steady state.
- `Archive/` preserves historical design material and retired routes. It is
  useful for provenance, but it is not the default authority for current work.
- `temp/` is scratch space and should not be treated as a maintained source of
  truth.

## Usage Rule

- If a task needs code changes, prefer reading the relevant `plan/` or `task/`
  entry first, then verify against the current code tree.
- If a document links to historical artifacts, confirm the target still exists
  in the workspace before treating it as an actionable entrypoint.
