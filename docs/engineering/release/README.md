# Release Engineering

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/release/README.md`
Owner: `engineering/release`
Last verified: `2026-08-07`

This area owns repository-wide dependency and release governance: dependency
declarations, project-version consistency, release gates, and third-party or
asset redistribution checks. It does not own the version semantics, change
claims, or acceptance evidence produced by individual content owners. Those
owners supply scoped facts and artifacts; release engineering defines and
applies the cross-repository gate.

## Current Standard

- [Release and dependency policy](standards/release_and_dependency_policy.md):
  minimum dependency, version, release-note, checklist, license, and provenance
  requirements for a release candidate.

## Current Boundaries

- `CMakeLists.txt` and `pyproject.toml` both declared version `0.2.0` when last
  verified. A release gate must check them again for each candidate.
- The repository has no canonical CHANGELOG or dedicated release-checklist
  document. An equivalent release-note and checklist packet is required before
  tagging until those maintained artifacts exist.
- Smoke constraints and tool-local lock artifacts have narrower scopes than a
  resolved repository or training environment. They must not be cited as proof
  of full-environment reproducibility.
- This index and its policy define governance requirements; they do not assert
  that the current repository state is release-ready.
