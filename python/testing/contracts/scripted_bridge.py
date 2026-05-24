from __future__ import annotations

import json

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

from .common import ContractSkipped, _load_spec

def run_scripted_bridge_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    try:
        import gymnasium  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ContractSkipped("gymnasium not installed") from exc

    import numpy as np

    from gym_envs.universal_env import UniversalEnv
    from python.rl.control.wrappers import get_action_wrapper_spec

    spec = _load_spec(spec_path)
    scenario_path = resolve_repo_path(str(spec["scenario"]))
    wrapper_cfg_path = resolve_repo_path(str(spec["wrapper_config"]))

    with open(wrapper_cfg_path, "r", encoding="utf-8") as f:
        wrapper_cfg = json.load(f)

    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(wrapper_cfg)
    require_wrapper = bool(spec.get("require_wrapper", True))
    if wrapper_class is None:
        if require_wrapper:
            return False, f"expected wrapper spec from {wrapper_cfg_path}"
        return True, "scripted bridge contract passed without wrapper requirement"

    wrapper_kwargs = dict(wrapper_kwargs or {})
    wrapper_kwargs.update(dict(spec.get("wrapper_overrides", {}) or {}))

    env = UniversalEnv(
        scenario_path,
        include_visual=bool(spec.get("include_visual", False)),
        include_proprio=bool(spec.get("include_proprio", True)),
        mission_obs_mode=str(spec.get("mission_obs_mode", "nav_v2")),
        action_mode=str(spec.get("action_mode", "full")),
        runtime_compatibility_enabled=True,
    )
    randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
    if randomization_overrides:
        env.set_randomization_overrides(randomization_overrides)
    env = wrapper_class(env, **wrapper_kwargs)

    seed = int(spec.get("seed", 7))
    max_steps = int(spec.get("max_steps", getattr(env.unwrapped, "max_steps", 8000)))
    expected_reason = str(spec.get("expected_termination_reason", "success_objective"))

    _obs, _info = env.reset(seed=seed)
    action = np.zeros((int(env.action_space.shape[0]),), dtype=np.float32)

    for step in range(max_steps):
        _obs, _reward, terminated, truncated, info = env.step(action)
        if bool(terminated or truncated):
            reason = str((info or {}).get("termination_reason", ""))
            if reason != expected_reason:
                return False, f"unexpected termination reason {reason!r} at step {step + 1}"
            return True, f"scripted bridge contract passed in {step + 1} steps"

    return False, f"scripted bridge contract did not terminate within {max_steps} steps"
