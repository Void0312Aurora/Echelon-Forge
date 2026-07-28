# `python/training/` Layer Responsibilities

`python/training/` holds the bootstrap and orchestration support for the main training entry point.

Its positioning is not to replace the algorithm, policy, or vec-env logic in `python/rl/`, but rather to centralize responsibilities in the top-level script that are strongly related to "entry coordination", such as:

- CLI argument table and default values
- Training configuration and scenario path validation
- Experiment directory, resume / init-from directory conventions
- Seed and PyTorch runtime bootstrap
- Unified runtime summary print before training starts

## Implemented Training Surfaces

- `agent_layer="execution"` is the single-policy air/execution path. The maintained production setup uses `runtime.world_batch_vec_env=true` and `python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv`; raw `UniversalEnv` / SB3 vec-env compatibility is no longer accepted through maintained training config.
- `agent_layer="cooperative_execution"` is the cooperative/common integration line. It builds `python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv`, supports the maintained multi-timescale wrapper, and is the active cooperative training surface.
- `agent_layer="leader"` builds `gym_envs.leader_env.LeaderTrainingEnv` for leader-layer policy work. The single-process batched leader inference path is still opt-in experimental; normal multi-process vectorization is the default.
- Naval N4 train configs may declare `naval_entry`; bootstrap validates the declared scenario/contract paths and requires `action_mode="naval_station3"` plus `mission_obs_mode="naval_screen_station_v1"`. This is a scoped pre-fire/tasking/contact gate, not a learned naval weapon-outcome acceptance.
- Ground currently has tasking/profile/schema bootstrap only. There is no maintained full ground runtime or active ground RL training entry here.

## Current Files

- [cli.py](cli.py)
  - `argparse` definitions reused by `train.py`.
- [bootstrap.py](bootstrap.py)
  - Path validation, configuration loading, experiment directory preparation, lock file, seed / torch runtime initialization.
- [deps.py](deps.py)
  - Lazy loader for the heavyweight SB3/torch/policy/vec-env imports used by the training entry, plus `get_policy_kwargs`.
- [action_bias.py](action_bias.py)
  - Safe action-head bias initialization (`apply_safe_action_bias`, `apply_leader_action_bias`, `infer_full_action_safe_defaults`) and HMoE shared-head bootstrap (`maybe_initialize_hmoe_from_shared`). `train.py` re-exports these names for historical `from train import ...` callers.
- [vec_env_factory.py](vec_env_factory.py)
  - Vec-env backend selection (`resolve_vec_env_spec`) and per-agent-layer vec-env construction/runtime-summary printing for `train.py`.

## Boundary

- This is the place for training entry argument parsing, experiment directory management, runtime bootstrap, and entry-side orchestration (dependency loading, action-bias initialization, vec-env construction wiring).
- Algorithm, policy, and vec-env *implementations* stay in `python/rl/`; this package only selects, constructs, and summarizes them for the entry. Do not duplicate those implementations here.
- The maintained-execution `runtime.world_batch_vec_env=true` guard message stays in `train.py` (architecture tests scan the entry source for it).
- The follow-up splitting of `world_model_train.py` is not within the scope of this sub-domain at the current stage.
