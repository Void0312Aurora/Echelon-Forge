# Requirements Governance

Language:
- English canonical: `README.md`

Status: `2026-06-02` baseline for lightweight dependency governance.

This directory records dependency inputs that are narrower than a full release
or experiment lockfile.

## Files

- `constraints-smoke.txt`: lightweight constraints for CI/smoke/lint
  and coverage resolution. The file and the CI workflows that consume it are
  the authoritative package inventory; this README describes their scope
  rather than maintaining a second exhaustive list.

## How To Use

For the maintained fast smoke loop, install the direct smoke set through the
constraints file:

```bash
python -m pip install --upgrade pip -c requirements/constraints-smoke.txt
python -m pip install -c requirements/constraints-smoke.txt pytest numpy ruff gymnasium
```

This mirrors the fast smoke lane as of `2026-08-07`; the coverage lane also
installs `coverage` and `gcovr`. Always read the consuming workflow before
changing the constraints. Build the local C++/Python extension with CMake,
expose it with `tools/maintenance/cmo_env.sh` or
`tools/maintenance/cmo_env.ps1`, and run the selected suite from the repository
virtual environment.

## Scope Rules

Optional dependency groups in `pyproject.toml` are capability declarations.
They describe what a workflow may need, such as smoke tests, linting, RL
imports, training, world-model utilities, or local development convenience.
They are not reproducible environment locks. The `lint` group declares the
`ruff` gate that CI installs directly; `dev` stays the superset that also
covers it.

`constraints-smoke.txt` is the reproducible entry point for CI/smoke/lint
and coverage dependency resolution only. It should stay small and should not
hard-pin the full training or experiment stack, including `torch`,
`stable-baselines3`, or `tensorboard`. The current `gymnasium` constraint serves
the smoke and coverage interface boundary; it is not a training-environment
lock.

Training and experiment runs still need their own environment evidence. Until a
dedicated lockfile policy exists, record the resolved environment with the run
artifact, for example:

```bash
python -m pip freeze --all > run_pip_freeze.txt
```

When a future lockfile is introduced, it should be documented as a separate
release or experiment contract rather than being inferred from the smoke
constraints.

## Update Rules

- Update `constraints-smoke.txt` when CI Python support, direct
  smoke/lint/coverage installs, or `pyproject.toml` build-system requirements
  change.
- Keep environment markers only where they can still select a branch. The
  project declares `requires-python = ">=3.10"`, so a `python_version < "3.9"`
  branch is unreachable and must not be carried as pseudo-compatibility.
- Keep constraints broad enough for patch-level updates, but narrow enough to
  prevent surprising major-version changes in the smoke lane.
- Do not add optional training, RL, or world-model packages merely because they
  appear in `pyproject.toml` optional dependency groups.
- Validate changes with every consuming smoke or coverage workflow before
  treating them as release evidence.

See `docs/engineering/release/standards/release_and_dependency_policy.md` for the
release gate policy.
