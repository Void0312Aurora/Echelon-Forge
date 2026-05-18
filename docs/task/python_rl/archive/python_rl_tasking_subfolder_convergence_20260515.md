<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_tasking_subfolder_convergence_20260515.zh.md. Review before treating this file as authoritative. -->

# python/rl tasking Subdomain Convergence Record

Status: `2026-05-16` – Finished migration into subfolder and root-level shim cleanup  
Scope: `tasking`-related implementation files and their compat entries under `python/rl`

## 1. Background

Previously, the `python/rl` root directory showed a pronounced flat tendency:

- `common_core_profile.py`
- `leader_tasking.py`
- `tasking_air_adapter.py`
- `tasking_bridge.py`

These files all belong to the same `tasking` semantic chain but were long scattered in the root directory, causing two issues:

1. High semantic density in the root directory, making it hard to identify subdomains from the directory structure.
2. New files tend to keep piling up in the root directory, blurring the boundaries between “bridge layer / adapter layer / concrete implementation”.

## 2. Freeze Goals for This Round

This round addresses only structural issues without large-scale behavioral rewrites:

1. Move `tasking`-related implementations into a real subdirectory.
2. Let internal project use the sub-package path first.
3. Delete old-path shims after completing the main-chain and test switchover.

## 3. Result

Now placed at:

- `python/rl/tasking/common_core_profile.py`
- `python/rl/tasking/leader_tasking.py`
- `python/rl/tasking/air_adapter.py`
- `python/rl/tasking/bridge.py`
- `python/rl/tasking/__init__.py`

The corresponding implementation files in the root directory have been removed and no longer reside as real implementations in the `python/rl/` root layer.

## 4. Compatibility Strategy (Historical)

To avoid modifying all old call sites at once, root-level shims were temporarily kept in the first phase:

- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `python/rl/tasking_air_adapter.py`
- `python/rl/tasking_bridge.py`

These shims were “module-object-level” compat, not just ordinary symbol re-exports. Therefore they continued to support:

- Old-style `from python.rl.leader_tasking import ...`
- Old-style `import python.rl.tasking_bridge as ...`
- `mock.patch("python.rl.leader_tasking.ef_py", ...)` in tests.

After completing main-chain, test, and tool-chain switchover on `2026-05-16`, the above shims have been removed.

## 5. Internal Calls Already Synchronized to New Path

This round migrated the following internal uses to the sub-package path:

- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `game/backend/app.py`
- `python/testing/scenario_contract_runner.py`

Note:

- The project main-chain now uniformly references `python.rl.tasking.*`.
- No root-level `python/rl/*.py` tasking compat entry is retained.

## 6. Current Boundaries

This round did **not** handle further:

1. Splitting responsibilities inside `leader_tasking.py`.
2. Further sinking of `common_core_profile.py` semantics with `profile/`.
3. Full replacement of old paths on the `ScenarioLoader` / runtime side.
4. Overall consolidation of non-`tasking` subdomains.

## 7. Suggestions for Next Steps

The next phase can continue with two actions:

1. Further split inside the `tasking` sub-package:
   - `phase_manager`
   - `scripted_c2_manager`
   - `mission_command_builder`
   - `common_core_facade`

2. Keep `python.rl.tasking.*` as the only stable import surface, avoiding re-introduction of root-level compatibility layers.

This prevents a second-layer build-up problem: “files have moved into a subfolder but individual files are still too fat.”
