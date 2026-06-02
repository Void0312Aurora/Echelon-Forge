# Requirements Governance

Language:
- English canonical: `README.md`

Status: `2026-06-02` baseline for lightweight dependency governance.

This directory records dependency inputs that are narrower than a full release
or experiment lockfile.

## Files

- `constraints-smoke.txt`: lightweight constraints for CI/smoke resolution.
  It covers the direct smoke installs, `pytest` and `numpy`, plus Python
  package build tools that are reasonable to constrain when explicitly testing
  package build/install behavior.

## How To Use

For the maintained fast smoke loop, install the direct smoke set through the
constraints file:

```bash
python -m pip install --upgrade pip -c requirements/constraints-smoke.txt
python -m pip install -c requirements/constraints-smoke.txt pytest numpy
```

This mirrors the repository smoke boundary: build the local C++/Python
extension with CMake, expose it with `tools/maintenance/cmo_env.sh` or
`tools/maintenance/cmo_env.ps1`, and run the smoke suites from the repository
virtual environment.

## Scope Rules

Optional dependency groups in `pyproject.toml` are capability declarations.
They describe what a workflow may need, such as smoke tests, RL imports,
training, world-model utilities, or local development convenience. They are not
reproducible environment locks.

`constraints-smoke.txt` is the reproducible entry point for CI/smoke dependency
resolution only. It should stay small and should not hard-pin the training or
experiment stack, including `torch`, `stable-baselines3`, `gymnasium`, or
`tensorboard`.

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

- Update `constraints-smoke.txt` when CI Python support, direct smoke installs,
  or `pyproject.toml` build-system requirements change.
- Keep constraints broad enough for patch-level updates, but narrow enough to
  prevent surprising major-version changes in the smoke lane.
- Do not add optional training, RL, or world-model packages merely because they
  appear in `pyproject.toml` optional dependency groups.
- Validate changes with the smoke workflow before treating them as release
  evidence.

See `docs/standards/governance/release_and_dependency_policy.md` for the
release gate policy.
