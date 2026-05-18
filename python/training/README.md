<!-- Machine-translated draft generated on 2026-05-18 from python/training/README.md. Review before treating this file as authoritative. -->

# `python/training/` Layer Responsibilities

`python/training/` holds the bootstrap and orchestration support for the main training entry point.

Its positioning is not to replace the algorithm, policy, or vec-env logic in `python/rl/`, but rather to centralize responsibilities in the top-level script that are strongly related to "entry coordination", such as:

- CLI argument table and default values
- Training configuration and scenario path validation
- Experiment directory, resume / init-from directory conventions
- Seed and PyTorch runtime bootstrap
- Unified runtime summary print before training starts

## Current Files

- [cli.py](cli.py)
  - `argparse` definitions reused by `train.py`.
- [bootstrap.py](bootstrap.py)
  - Path validation, configuration loading, experiment directory preparation, lock file, seed / torch runtime initialization.

## Boundary

- This is the place for training entry argument parsing, experiment directory management, and runtime bootstrap.
- Do not re-import SB3 algorithm, policy structure, or vec-env details here.
- The follow-up splitting of `world_model_train.py` is not within the scope of this sub-domain at the current stage.
