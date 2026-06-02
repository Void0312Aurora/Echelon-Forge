from __future__ import annotations

from typing import Any

from python.mission_obs_taxonomy import VALID_MISSION_OBS_MODES


VALID_ACTION_MODES = {"full", "takeoff2", "takeoff4", "naval_station3", "air_combat_hybrid_v1"}
VALID_EXECUTION_STEP_RUNTIME_MODES = {"compiled", "legacy"}
VALID_STEP_INFO_MODES = {"full", "terminal", "off"}
VALID_FLIGHT_SHAPING_BACKENDS = {"auto", "legacy", "compiled", "gpu_host"}

_RUNTIME_COMPAT_TRUE = {"1", "true", "on", "yes", "compat", "compatibility", "diagnostics", "debug"}
_RUNTIME_COMPAT_FALSE = {"", "0", "false", "off", "no", "none", "mainline", "compiled"}


def _normalize_runtime_compatibility_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return bool(value)
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in _RUNTIME_COMPAT_TRUE:
        return True
    if normalized in _RUNTIME_COMPAT_FALSE:
        return False
    return bool(value)


def _merge_config_value(
    args: Any,
    attr_name: str,
    env_cfg: dict[str, Any],
    *,
    default: Any,
    coerce: Any,
) -> Any:
    value = getattr(args, attr_name, None)
    if value is None:
        value = env_cfg.get(attr_name, default)
    return coerce(value)


def _merge_optional_config_value(
    args: Any,
    attr_name: str,
    env_cfg: dict[str, Any],
    *,
    coerce: Any,
) -> Any:
    value = getattr(args, attr_name, None)
    if value is None:
        value = env_cfg.get(attr_name)
    if value is None:
        return None
    value = coerce(value)
    return value if value != "" else None


def _merge_optional_config_value_with_alias(
    args: Any,
    attr_name: str,
    alias_attr_name: str,
    env_cfg: dict[str, Any],
    *,
    coerce: Any,
) -> Any:
    value = getattr(args, attr_name, None)
    if value is None:
        value = getattr(args, alias_attr_name, None)
    if value is None:
        value = env_cfg.get(attr_name)
    if value is None:
        value = env_cfg.get(alias_attr_name)
    if value is None:
        return None
    value = coerce(value)
    return value if value != "" else None


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

    include_proprio = _merge_config_value(args, "include_proprio", env_cfg, default=False, coerce=bool)
    action_mode = _merge_config_value(args, "action_mode", env_cfg, default="full", coerce=str)
    mission_obs_mode = _merge_config_value(args, "mission_obs_mode", env_cfg, default="basic", coerce=str)
    visual_downsample = _merge_config_value(args, "visual_downsample", env_cfg, default=1, coerce=int)
    visual_update_interval = _merge_config_value(args, "visual_update_interval", env_cfg, default=1, coerce=int)
    temporal_history_len = _merge_config_value(args, "temporal_history_len", env_cfg, default=1, coerce=int)
    execution_step_runtime_mode = _merge_optional_config_value(
        args,
        "execution_step_runtime_mode",
        env_cfg,
        coerce=lambda value: str(value).strip().lower(),
    )
    step_info_mode = _merge_config_value(args, "step_info_mode", env_cfg, default="full", coerce=str)
    flight_shaping_backend = _merge_optional_config_value_with_alias(
        args,
        "flight_shaping_backend",
        "shaping_backend",
        env_cfg,
        coerce=lambda value: str(value).strip().lower(),
    )
    runtime_compatibility_enabled = _merge_config_value(
        args,
        "runtime_compatibility_enabled",
        env_cfg,
        default=False,
        coerce=_normalize_runtime_compatibility_enabled,
    )

    action_mode = action_mode.strip()
    mission_obs_mode = mission_obs_mode.strip().lower()
    step_info_mode = step_info_mode.strip().lower()
    visual_downsample = max(1, int(visual_downsample))
    visual_update_interval = max(1, int(visual_update_interval))
    temporal_history_len = max(1, int(temporal_history_len))

    if action_mode not in VALID_ACTION_MODES:
        raise ValueError(f"Unknown action_mode in merged env config: {action_mode!r}")
    if mission_obs_mode not in VALID_MISSION_OBS_MODES:
        raise ValueError(f"Unknown mission_obs_mode in merged env config: {mission_obs_mode!r}")
    if execution_step_runtime_mode is not None and execution_step_runtime_mode not in VALID_EXECUTION_STEP_RUNTIME_MODES:
        raise ValueError(
            f"Unknown execution_step_runtime_mode in merged env config: {execution_step_runtime_mode!r}"
        )
    if step_info_mode not in VALID_STEP_INFO_MODES:
        raise ValueError(f"Unknown step_info_mode in merged env config: {step_info_mode!r}")
    if flight_shaping_backend is not None and flight_shaping_backend not in VALID_FLIGHT_SHAPING_BACKENDS:
        raise ValueError(f"Unknown flight_shaping_backend in merged env config: {flight_shaping_backend!r}")
    if execution_step_runtime_mode == "legacy" and not bool(runtime_compatibility_enabled):
        raise ValueError(
            "execution_step_runtime_mode='legacy' is quarantined; "
            "set runtime_compatibility_enabled=True to opt in explicitly."
        )

    return {
        "include_visual": bool(include_visual),
        "include_proprio": bool(include_proprio),
        "action_mode": action_mode,
        "mission_obs_mode": mission_obs_mode,
        "visual_downsample": visual_downsample,
        "visual_update_interval": visual_update_interval,
        "temporal_history_len": temporal_history_len,
        "execution_step_runtime_mode": execution_step_runtime_mode,
        "step_info_mode": step_info_mode,
        "flight_shaping_backend": flight_shaping_backend,
        "runtime_compatibility_enabled": bool(runtime_compatibility_enabled),
    }
