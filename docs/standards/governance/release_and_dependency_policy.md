# Release And Dependency Policy

Language:
- English canonical: `release_and_dependency_policy.md`

Status: `2026-06-02` baseline for dependency and release governance.

This policy defines the minimum release governance surface for Echelon Forge.
It is intentionally lightweight because the repository does not currently carry
a full lockfile.

## Scope

This policy applies to:

- dependency declarations and smoke constraints;
- release candidate preparation;
- source, wheel, binary, documentation, scenario, model, and retained-artifact
  bundles prepared for external consumption;
- third-party source, package, and asset license checks.

It does not make optional dependency groups into reproducible environment locks,
and it does not authorize hard-pinning the full training stack in the smoke
constraints file.

## Dependency Governance

`pyproject.toml` optional dependency groups are capability declarations. They
state which packages are needed for a workflow capability, such as test, RL,
training, world-model, or dev convenience. They do not prove an exact resolved
environment.

`requirements/constraints-smoke.txt` is the CI/smoke reproducibility entry
point. It may constrain:

- direct packages installed by the current CI smoke lane, currently `pytest`
  and `numpy`;
- Python build frontend/backend packages relevant when package build/install
  smoke is deliberately exercised, currently `pip`, `scikit-build-core`, and
  `nanobind`.

It must not grow into a hidden training lockfile. Do not add hard pins for
`torch`, `stable-baselines3`, `gymnasium`, `tensorboard`, or similar optional
training/experiment packages unless a separate training lock policy is approved.

Training and experiment reproducibility must record the resolved environment
with the run artifact until a dedicated lockfile exists. At minimum, record:

- Python version and platform;
- `python -m pip freeze --all` output;
- CUDA, accelerator, driver, or compiler details when relevant;
- scenario/config identifiers and run artifact checksums.

## Version Governance

Release candidates must review both project version surfaces:

- CMake: `project(EchelonForge VERSION ...)` in `CMakeLists.txt`;
- Python distribution: `[project].version` in `pyproject.toml`.

For a release tag, the CMake project version and Python distribution version
must either match or carry an explicit release-note exception explaining why the
native and Python artifacts are intentionally versioned differently.

As of this policy baseline, the repository has a known version-sync gap:
`CMakeLists.txt` declares `0.1.0`, while `pyproject.toml` declares `0.2.0`.
A release checklist must close or explicitly waive that mismatch before a
release tag is cut.

## Release Gate

A release candidate must not be published until the release owner records:

- version synchronization or an approved version mismatch exception;
- smoke validation using the maintained smoke dependency entry point;
- CHANGELOG or release-note coverage for user-visible changes, dependency
  policy changes, compatibility breaks, and known residuals;
- a release checklist result that names the exact commit, artifact set,
  validation commands, and unresolved risks;
- third-party package, source, model, media, scenario, and retained-artifact
  license review;
- asset provenance review for redistributed files, including generated,
  downloaded, converted, or extracted assets.

The repository currently lacks a canonical CHANGELOG and a dedicated release
checklist document. That is a release-governance gap, not a reason to publish
without release notes. Until those files exist, the release owner must create an
equivalent release-note and checklist packet before tagging.

## Third-Party And Asset Gate

Before release, check the license and redistribution status for:

- repository license and `THIRD_PARTY_NOTICES.md`;
- CMake `FetchContent` dependencies and any vendored source;
- Python dependencies used by the released artifact or smoke/install path;
- model, media, scenario, data, calibration, and retained evidence artifacts;
- generated or converted assets whose original source license may still apply.

Release artifacts must not include assets with unknown provenance, incompatible
redistribution terms, missing attribution, or unclear generated/converted
ownership. If an asset is needed for local research but not release-safe, keep
it out of the release bundle and document the exclusion.

## Maintenance Rules

- Keep smoke constraints small and scoped to the smoke lane.
- Treat new lockfiles as separate governance artifacts with explicit ownership.
- Update this policy when CI dependency installation, release packaging, or
  third-party asset handling changes.
- Do not treat a passing local training run as release dependency evidence
  unless its resolved environment and artifact provenance were recorded.
