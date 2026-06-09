<!-- Machine-translated draft generated on 2026-05-18 from docs/task/python_rl/python_rl_planning_support_subfolder_convergence_20260516.zh.md. Review before treating this file as authoritative. -->

# Python / RL planning and support sub‑domain convergence record

Status: `2026-05-16` First round completed  
Scope:

- `coarse_route_propagator`
- `nonfinite_probe`
- `sb3_vec_env_compat`
- `multi_agent_benchmark`

## 1. Goal

After `tasking`, `control`, `runtime`, and `policy_algo`, continue to reduce the flat pressure in the `python/rl` root directory by moving the remaining modules with clearer semantics and relatively controllable coupling into new sub‑domains.

This round does **not** touch the main bodies of `world_batch_vec_env.py` and `cooperative_world_batch_vec_env.py`; it only handles their peripheral lightweight planning and support modules.

## 2. Results of this round

New sub‑domains have been added:

- `python/rl/planning/`
- `python/rl/support/`

Modules moved:

- `python/rl/planning/coarse_route_propagator.py`
- `python/rl/support/nonfinite_probe.py`
- `python/rl/support/sb3_vec_env_compat.py`
- `python/rl/support/multi_agent_benchmark.py`

Additionally supplemented:

- `python/rl/planning/__init__.py`
- `python/rl/support/__init__.py`

## 3. Rationale for sub‑domain division

### planning

`coarse_route_propagator.py` is purely planning projection and error comparison logic, with responsibilities concentrated in:

- trajectory/heading geometry calculations
- coarse‑grain route propagation
- waypoint capture and state comparison

It does not assume training runtime, policy network, or environment compatibility duties, so it is better suited as the starting point of an independent planning sub‑domain.

### support

The modules collected into `support/` in this round are more “support layer” oriented, including:

- non‑finite numerical training probe
- SB3 `VecEnv` compatibility bridge
- multi‑agent benchmark entry

These modules serve training, diagnostics, compatibility, or performance observation, but do not belong to main control logic or task semantics ontology.

## 4. Compatibility strategy (historical)

For a short period, root‑level shims were retained:

- `python/rl/coarse_route_propagator.py`
- `python/rl/nonfinite_probe.py`
- `python/rl/sb3_vec_env_compat.py`
- `python/rl/multi_agent_benchmark.py`

After call‑site convergence was completed on `2026-05-16`, the old‑path shims were removed and the internal implementations were unified under the new sub‑domains.

Unlike `tasking` / `control`, this round did not add these modules to the pre‑registered alias list in `python/rl/__init__.py`.

Reasons:

1. The modules in `support` have noticeably heavy import chains.
2. For example, `multi_agent_benchmark` will pull in the cooperative / world‑batch runtime.
3. Adding alias registrations early in the package import phase would amplify import‑order risks and expose underlying build dependencies.

Therefore, this round adopted a “root‑level shim + sub‑domain real module” lazy resolution approach, consistent with `runtime` / `policy_algo`.

## 5. Main‑chain modules already switched to new paths

Switched in this round:

- `python/rl/world_batch_vec_env.py`
- `python/rl/cooperative_world_batch_vec_env.py`
- `tools/diagnostics/benchmarks/coarse_route_segments.py`
- `scripts/benchmark_multi_agent.py`

Before deletion, some old import paths were temporarily retained for verification; now all have been uniformly switched to the new sub‑domain paths.

## 6. Special note

`python/rl/support/__init__.py` only keeps a lightweight `__all__` declaration, without performing implementation‑level re‑exports.

The reason is that package‑level re‑exports would immediately pull in upon importing `python.rl.support`:

- `multi_agent_benchmark`
- `nonfinite_probe`
- `sb3_vec_env_compat`

This would turn modules that could otherwise be loaded on demand into hard dependencies at package import time, defeating the goal of reducing import side effects in this round.

## 7. Verification strategy

Verification in this round is split into two layers:

1. Lightweight import smoke tests
   - New‑path modules can be imported.
   - Root‑level shims correctly point back to the new implementation.

2. Focused tests
   - `tests/runtime/navigation/test_coarse_route_propagator.py`
   - `tests/runtime/multi_agent/test_multi_agent_benchmark.py`
   - `tests/hmoe/test_hmoe_policy.py`
   - `tests/world_batch/test_world_batch_vec_env.py`

## 8. Future suggestions

It is recommended to prioritise the following two lines next:

1. Remaining heavy modules in the `python/rl` root directory
   - `shared_memory_vec_env.py`
   - `world_batch_vec_env.py`
   - `cooperative_world_batch_vec_env.py`

2. High‑density directories adjacent to `python/rl`
   - Continue organising `tools/diagnostics` by sub‑domains.
   - Clarify the retention boundary between `tests/runtime` and `tests/training`.

The significance of this round is not to keep adding “horizontal shims”, but to first place low‑risk, lightweight modules inside stable semantic boundaries, preparing for subsequent handling of the heaviest world‑batch main chain.
