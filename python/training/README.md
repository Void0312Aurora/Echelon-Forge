# `python/training/` Layer Responsibilities

`python/training/` holds the bootstrap and orchestration support for the main training entry point.

Its positioning is not to replace the algorithm, policy, or vec-env logic in `python/rl/`, but rather to centralize responsibilities in the top-level script that are strongly related to "entry coordination", such as:

- CLI argument table and default values
- Training configuration and scenario path validation
- Experiment directory, resume / init-from directory conventions
- Seed and PyTorch runtime bootstrap
- Unified runtime summary print before training starts

## Implemented Training Surfaces

- `agent_layer="execution"` is the single-policy air/execution path. The maintained production setup uses `runtime.world_batch_vec_env=true` and `python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv`; the raw `UniversalEnv` / SB3 vec-env route is a quarantined compatibility path and requires `env.runtime_compatibility_enabled=true`.
- `agent_layer="cooperative_execution"` is the cooperative/common integration line. It builds `python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv`, supports the maintained multi-timescale wrapper, and is the active cooperative training surface.
- `agent_layer="leader"` builds `gym_envs.leader_env.LeaderTrainingEnv` for leader-layer policy work. The single-process batched leader inference path is still opt-in experimental; normal multi-process vectorization is the default.
- Naval N4 train configs may declare `naval_entry`; bootstrap validates the declared scenario/contract paths and requires `action_mode="naval_station3"` plus `mission_obs_mode="naval_screen_station_v1"`. This is a scoped pre-fire/tasking/contact gate, not a learned naval weapon-outcome acceptance.
- Ground currently has tasking/profile/schema bootstrap only. There is no maintained full ground runtime or active ground RL training entry here.

## Current Files

- [cli.py](cli.py)
  - `argparse` definitions reused by `train.py`.
- [bootstrap.py](bootstrap.py)
  - Path validation, configuration loading, experiment directory preparation, lock file, seed / torch runtime initialization.

## Boundary

- This is the place for training entry argument parsing, experiment directory management, and runtime bootstrap.
- Do not re-import SB3 algorithm, policy structure, or vec-env details here.
- The follow-up splitting of `world_model_train.py` is not within the scope of this sub-domain at the current stage.
