from __future__ import annotations

from typing import Any


VALID_ACTION_MODES = {"full", "takeoff2", "takeoff4"}
VALID_MISSION_OBS_MODES = {"basic", "nav_v1", "nav_v2"}


def infer_include_visual_from_train_config(train_config: dict[str, Any] | None) -> bool:
    if not isinstance(train_config, dict):
        return False
    hyper = train_config.get("hyperparameters", {})
    if not isinstance(hyper, dict):
        return False
    policy_kwargs = hyper.get("policy_kwargs", {})
    if not isinstance(policy_kwargs, dict):
        return False
    return str(policy_kwargs.get("features_extractor_class", "")).strip() == "TransformerVisualExtractor"


def resolve_env_settings(train_config: dict[str, Any] | None, args: Any) -> dict[str, Any]:
    env_cfg = train_config.get("env", {}) if isinstance(train_config, dict) else {}
    if not isinstance(env_cfg, dict):
        env_cfg = {}

    include_visual = getattr(args, "include_visual", None)
    if include_visual is None:
        if "include_visual" in env_cfg:
            include_visual = bool(env_cfg.get("include_visual"))
        else:
            include_visual = infer_include_visual_from_train_config(train_config)
    else:
        include_visual = bool(include_visual)

    include_proprio = getattr(args, "include_proprio", None)
    if include_proprio is None:
        include_proprio = bool(env_cfg.get("include_proprio", False))
    else:
        include_proprio = bool(include_proprio)

    action_mode = getattr(args, "action_mode", None)
    if action_mode is None:
        action_mode = str(env_cfg.get("action_mode", "full"))
    else:
        action_mode = str(action_mode)

    mission_obs_mode = getattr(args, "mission_obs_mode", None)
    if mission_obs_mode is None:
        mission_obs_mode = str(env_cfg.get("mission_obs_mode", "basic"))
    else:
        mission_obs_mode = str(mission_obs_mode)

    visual_downsample = getattr(args, "visual_downsample", None)
    if visual_downsample is None:
        visual_downsample = int(env_cfg.get("visual_downsample", 1))
    else:
        visual_downsample = int(visual_downsample)

    visual_update_interval = getattr(args, "visual_update_interval", None)
    if visual_update_interval is None:
        visual_update_interval = int(env_cfg.get("visual_update_interval", 1))
    else:
        visual_update_interval = int(visual_update_interval)

    action_mode = action_mode.strip()
    mission_obs_mode = mission_obs_mode.strip().lower()
    visual_downsample = max(1, int(visual_downsample))
    visual_update_interval = max(1, int(visual_update_interval))

    if action_mode not in VALID_ACTION_MODES:
        raise ValueError(f"Unknown action_mode in merged env config: {action_mode!r}")
    if mission_obs_mode not in VALID_MISSION_OBS_MODES:
        raise ValueError(f"Unknown mission_obs_mode in merged env config: {mission_obs_mode!r}")

    return {
        "include_visual": bool(include_visual),
        "include_proprio": bool(include_proprio),
        "action_mode": action_mode,
        "mission_obs_mode": mission_obs_mode,
        "visual_downsample": visual_downsample,
        "visual_update_interval": visual_update_interval,
    }
