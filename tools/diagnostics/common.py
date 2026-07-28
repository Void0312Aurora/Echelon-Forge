from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# Canonical dest names for shared probe CLI groups (always underscore).
PROBE_RUN_ARG_NAMES: tuple[str, ...] = ("scenario", "episodes", "seed", "max_steps")
MODEL_LOAD_ARG_NAMES: tuple[str, ...] = ("train_config", "model", "algo", "device")
_DUAL_OPTION_DESTS: frozenset[str] = frozenset({"max_steps", "train_config", "json_out"})


def _option_strings(dest: str, *, primary: str = "underscore") -> tuple[str, str]:
    """Return (visible_primary, suppressed_alias) option strings for *dest*."""

    underscore = f"--{dest}"
    hyphen = f"--{dest.replace('_', '-')}"
    if primary == "hyphen":
        return hyphen, underscore
    if primary != "underscore":
        raise ValueError(f"primary must be 'underscore' or 'hyphen', got {primary!r}")
    return underscore, hyphen


def add_dual_option(
    parser: argparse.ArgumentParser,
    dest: str,
    *,
    primary: str = "underscore",
    **kwargs: Any,
) -> None:
    """Register one CLI option with underscore/hyphen aliases and a fixed dest.

    The *primary* option string is the one shown in ``--help``; the alternate
    form is registered with ``help=argparse.SUPPRESS`` so help text stays
    byte-identical to historical single-form scripts while both spellings parse
    to the same underscore ``dest``.

    ``required=True`` needs special handling: argparse tracks "was this
    argument seen" per *action*, not per *dest*, so two independently
    ``required=True`` actions sharing one dest would force a caller to spell
    out both the primary and the alias. Registering the pair as a required
    mutually exclusive group instead requires exactly one of the two
    spellings, which is the actual "either form satisfies the requirement"
    contract implied by "dual option". This changes the error text argparse
    prints when *neither* form is supplied (``one of the arguments ... is
    required`` instead of ``the following arguments are required: ...``);
    ``--help`` output is unaffected either way (verified empirically: a
    suppressed group member renders in neither the usage line nor the
    detailed listing, same as a suppressed plain alias). One further semantic
    shift under ``required=True``: supplying *both* spellings in one
    invocation now raises argparse's mutually-exclusive error, where the old
    (unusable) registration would have silently let the later value win --
    no historical call site ever reached the old behavior, so this only
    constrains new required-dual adopters.
    """

    kwargs = dict(kwargs)
    kwargs["dest"] = dest
    if dest in _DUAL_OPTION_DESTS or "_" in dest:
        primary_opt, alias_opt = _option_strings(dest, primary=primary)
        alias_kwargs = dict(kwargs)
        alias_kwargs["help"] = argparse.SUPPRESS
        if kwargs.pop("required", False):
            alias_kwargs.pop("required", None)
            group = parser.add_mutually_exclusive_group(required=True)
            group.add_argument(primary_opt, **kwargs)
            group.add_argument(alias_opt, **alias_kwargs)
            return
        parser.add_argument(primary_opt, **kwargs)
        parser.add_argument(alias_opt, **alias_kwargs)
        return
    # Single-token names have identical underscore/hyphen spellings.
    parser.add_argument(f"--{dest}", **kwargs)


def _resolve_include(
    all_names: Sequence[str],
    *,
    include: Sequence[str] | None,
    exclude: Sequence[str] | None,
) -> tuple[str, ...]:
    names = tuple(all_names if include is None else include)
    unknown = [name for name in names if name not in all_names]
    if unknown:
        raise ValueError(f"unknown argument name(s): {unknown!r}; expected subset of {list(all_names)}")
    excluded = set(exclude or ())
    unknown_excl = excluded - set(all_names)
    if unknown_excl:
        raise ValueError(f"unknown exclude name(s): {sorted(unknown_excl)!r}")
    return tuple(name for name in names if name not in excluded)


def add_probe_run_args(
    parser: argparse.ArgumentParser,
    *,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
    defaults: Mapping[str, Any] | None = None,
    helps: Mapping[str, str | None] | None = None,
    required: Mapping[str, bool] | None = None,
    types: Mapping[str, Any] | None = None,
    option_primary: Mapping[str, str] | None = None,
) -> None:
    """Add shared probe-run options: scenario / episodes / seed / max_steps."""

    defaults = dict(defaults or {})
    helps = dict(helps or {})
    required = dict(required or {})
    types = dict(types or {})
    option_primary = dict(option_primary or {})
    default_types: dict[str, Any] = {
        "episodes": int,
        "seed": int,
        "max_steps": int,
    }
    for name in _resolve_include(PROBE_RUN_ARG_NAMES, include=include, exclude=exclude):
        kwargs: dict[str, Any] = {}
        type_ = types[name] if name in types else default_types.get(name)
        if type_ is not None:
            kwargs["type"] = type_
        if name in defaults:
            kwargs["default"] = defaults[name]
        if name in helps:
            kwargs["help"] = helps[name]
        if name in required:
            kwargs["required"] = bool(required[name])
        add_dual_option(
            parser,
            name,
            primary=option_primary.get(name, "underscore"),
            **kwargs,
        )


def add_model_load_args(
    parser: argparse.ArgumentParser,
    *,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
    defaults: Mapping[str, Any] | None = None,
    helps: Mapping[str, str | None] | None = None,
    required: Mapping[str, bool] | None = None,
    types: Mapping[str, Any] | None = None,
    option_primary: Mapping[str, str] | None = None,
) -> None:
    """Add shared model-load options: train_config / model / algo / device."""

    defaults = dict(defaults or {})
    helps = dict(helps or {})
    required = dict(required or {})
    types = dict(types or {})
    option_primary = dict(option_primary or {})
    for name in _resolve_include(MODEL_LOAD_ARG_NAMES, include=include, exclude=exclude):
        kwargs: dict[str, Any] = {}
        if name in types:
            kwargs["type"] = types[name]
        if name in defaults:
            kwargs["default"] = defaults[name]
        if name in helps:
            kwargs["help"] = helps[name]
        if name in required:
            kwargs["required"] = bool(required[name])
        add_dual_option(
            parser,
            name,
            primary=option_primary.get(name, "underscore"),
            **kwargs,
        )


def add_json_out_arg(
    parser: argparse.ArgumentParser,
    *,
    default: str = "",
    help: str | None = None,
    required: bool = False,
    option_primary: str = "underscore",
) -> None:
    """Add ``--json_out`` / ``--json-out`` with canonical dest ``json_out``."""

    kwargs: dict[str, Any] = {"default": default}
    if help is not None:
        kwargs["help"] = help
    if required:
        kwargs["required"] = True
    add_dual_option(parser, "json_out", primary=option_primary, **kwargs)


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def write_json_output(
    path: str | os.PathLike[str],
    payload: dict[str, Any],
    *,
    indent: int = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = True,
    allow_nan: bool = True,
    skip_empty_path: bool = True,
    transform: Callable[[Any], Any] | None = None,
) -> None:
    """Write JSON with parameterized dump options for diagnostics callers.

    Defaults match the historical indent=2 / ensure_ascii=True / no sort_keys
    shape used by most diagnostics writers, including skipping empty paths.
    """

    if skip_empty_path and not path:
        return
    out_path = os.path.abspath(os.fspath(path))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    data: Any = transform(payload) if transform is not None else payload
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            allow_nan=allow_nan,
        )
        f.write("\n")


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def finite_float_or_none(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def mean_finite(values: Iterable[float]) -> float:
    """Mean of finite values; empty/all-non-finite -> nan (fire_timing style)."""

    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    return float(sum(finite) / len(finite))


@contextlib.contextmanager
def native_stdout_to_stderr():
    """Keep CLI stdout machine-readable while native runtime logs are emitted."""

    sys.stdout.flush()
    saved_stdout_fd = os.dup(1)
    try:
        os.dup2(2, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout_fd, 1)
        os.close(saved_stdout_fd)


def merge_timing_sums(acc: dict[str, float], timing: dict[str, float] | None, *, scale: float = 1.0) -> None:
    if not isinstance(timing, dict):
        return
    factor = float(scale)
    for key, value in timing.items():
        try:
            acc[str(key)] = float(acc.get(str(key), 0.0) + float(value) * factor)
        except Exception:
            pass


def average_timing_sums(acc: dict[str, float], *, count: int) -> dict[str, float]:
    if count <= 0:
        return {}
    denom = float(count)
    return {key: float(value) / denom for key, value in acc.items()}


@dataclass(frozen=True)
class EpisodeStepTransition:
    episode: int
    step: int
    observation: Any
    next_observation: Any
    action: Any
    reward: Any
    terminated: bool
    truncated: bool
    info: Any
    context: Any

    @property
    def done(self) -> bool:
        return bool(self.terminated or self.truncated)


@dataclass(frozen=True)
class EpisodeEnd:
    episode: int
    steps: int
    final_observation: Any
    terminated: bool
    truncated: bool

    @property
    def done(self) -> bool:
        return bool(self.terminated or self.truncated)


def collect_episode_steps(
    env: Any,
    *,
    episodes: int,
    max_steps: int,
    seed: int,
    prepare_step: Callable[[int, int, Any, Any], tuple[Any, Any]],
    on_step: Callable[[EpisodeStepTransition, Any], None],
    fallback_max_steps: Callable[[Any], int] | None = None,
    on_episode_start: Callable[[int, Any], Any] | None = None,
    on_episode_end: Callable[[EpisodeEnd, Any], None] | None = None,
) -> list[int]:
    """Run the shared reset/step/termination/close shell for diagnostics collectors.

    Callers retain all domain-specific state. ``prepare_step`` returns the action
    plus arbitrary context that is delivered with the post-step transition.
    ``on_episode_end`` is the hook for terminal handling such as value bootstrap.
    """

    episode_lengths: list[int] = []
    try:
        for episode in range(int(episodes)):
            observation, _reset_info = env.reset(seed=int(seed) + int(episode))
            requested_max_steps = int(max_steps)
            if requested_max_steps > 0:
                episode_max_steps = requested_max_steps
            else:
                if fallback_max_steps is not None:
                    configured_max_steps = fallback_max_steps(env)
                else:
                    configured_max_steps = getattr(
                        getattr(env, "unwrapped", env),
                        "max_steps",
                        0,
                    )
                episode_max_steps = int(configured_max_steps or 1200)
            episode_state = (
                on_episode_start(int(episode), observation)
                if on_episode_start is not None
                else None
            )
            steps = 0
            terminated = False
            truncated = False
            for step in range(1, episode_max_steps + 1):
                action, context = prepare_step(
                    int(episode),
                    int(step),
                    observation,
                    episode_state,
                )
                next_observation, reward, terminated_raw, truncated_raw, info = env.step(
                    action
                )
                terminated = bool(terminated_raw)
                truncated = bool(truncated_raw)
                on_step(
                    EpisodeStepTransition(
                        episode=int(episode),
                        step=int(step),
                        observation=observation,
                        next_observation=next_observation,
                        action=action,
                        reward=reward,
                        terminated=terminated,
                        truncated=truncated,
                        info=info,
                        context=context,
                    ),
                    episode_state,
                )
                observation = next_observation
                steps += 1
                if bool(terminated or truncated):
                    break
            episode_lengths.append(int(steps))
            if on_episode_end is not None:
                on_episode_end(
                    EpisodeEnd(
                        episode=int(episode),
                        steps=int(steps),
                        final_observation=observation,
                        terminated=bool(terminated),
                        truncated=bool(truncated),
                    ),
                    episode_state,
                )
    finally:
        try:
            env.close()
        except Exception:
            pass
    return episode_lengths


def _ef_py():
    from python.runtime_bootstrap import ensure_repo_imports

    ensure_repo_imports()
    import ef_py

    return ef_py


def gpu_device_info_dict() -> dict[str, object]:
    ef_py = _ef_py()
    if not hasattr(ef_py, "probe_gpu_device"):
        return {"binding_available": False}
    try:
        info = ef_py.probe_gpu_device()
    except Exception as ex:
        return {
            "binding_available": True,
            "probe_error": str(ex),
        }
    return {
        "binding_available": True,
        "cuda_runtime_built": bool(getattr(info, "cuda_runtime_built", False)),
        "cuda_runtime_available": bool(getattr(info, "cuda_runtime_available", False)),
        "device_count": int(getattr(info, "device_count", 0)),
        "active_device": int(getattr(info, "active_device", -1)),
        "compute_major": int(getattr(info, "compute_major", 0)),
        "compute_minor": int(getattr(info, "compute_minor", 0)),
        "runtime_version": int(getattr(info, "runtime_version", 0)),
        "total_global_mem_bytes": int(getattr(info, "total_global_mem_bytes", 0)),
        "free_global_mem_bytes": int(getattr(info, "free_global_mem_bytes", 0)),
        "device_name": str(getattr(info, "device_name", "")),
        "error_message": str(getattr(info, "error_message", "")),
    }


def visual_runtime_stats_dict() -> dict[str, object]:
    ef_py = _ef_py()
    if not hasattr(ef_py, "last_visual_experiment_stats"):
        return {"binding_available": False}
    try:
        stats = ef_py.last_visual_experiment_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


def flight_shaping_runtime_stats_dict() -> dict[str, object]:
    ef_py = _ef_py()
    if not hasattr(ef_py, "last_flight_shaping_stats"):
        return {"binding_available": False}
    try:
        stats = ef_py.last_flight_shaping_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }
