#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from typing import Callable


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval.task_eval_driver import (
    TaskCliConfig,
    add_stable_flight_args,
    add_takeoff_roll_args,
    build_task_eval_parser,
    run_task_eval,
)


TASK_CHOICES = ("stable_flight", "takeoff_roll", "centerline", "waypoint_nav")
BACKEND_CHOICES = ("world_model", "scripted")


def _task_cli_config(task: str, backend: str) -> tuple[TaskCliConfig, Callable[[argparse.ArgumentParser], None] | None]:
    task_name = str(task).strip().lower()
    backend_name = str(backend).strip().lower()
    if task_name == "stable_flight":
        return (
            TaskCliConfig(
                description="Unified stable-flight task evaluator",
                episodes_default=20,
                max_steps_default=2000,
                seed_default=0,
                default_action_mode="full",
                include_no_randomization=True,
                world_model_device_default="cuda",
            ),
            add_stable_flight_args,
        )
    if task_name == "takeoff_roll":
        return (
            TaskCliConfig(
                description="Unified takeoff-roll task evaluator",
                episodes_default=50,
                max_steps_default=2000,
                seed_default=140,
                default_action_mode="takeoff4",
                include_no_randomization=True,
                world_model_device_default="cpu" if backend_name == "world_model" else "cuda",
            ),
            add_takeoff_roll_args,
        )
    if task_name == "centerline":
        return (
            TaskCliConfig(
                description="Unified centerline task evaluator",
                episodes_default=50,
                max_steps_default=2000,
                seed_default=140,
                default_action_mode="takeoff4" if backend_name == "world_model" else "full",
                include_no_randomization=True,
                world_model_device_default="cuda",
            ),
            None,
        )
    if task_name == "waypoint_nav":
        return (
            TaskCliConfig(
                description="Unified waypoint navigation task evaluator",
                episodes_default=10,
                max_steps_default=6000,
                seed_default=0,
                default_action_mode="full",
                include_no_randomization=(backend_name == "world_model"),
                world_model_device_default="cuda",
            ),
            None,
        )
    raise ValueError(f"unknown task {task!r}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified task evaluation CLI for scripted and world-model backends.",
        add_help=False,
    )
    parser.add_argument("--task", required=True, choices=TASK_CHOICES)
    parser.add_argument("--backend", required=True, choices=BACKEND_CHOICES)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    if any(flag in argv_list for flag in ("-h", "--help")) and not any(arg.startswith("--task") for arg in argv_list):
        parser = argparse.ArgumentParser(description="Unified task evaluation CLI for scripted and world-model backends.")
        parser.add_argument("--task", required=True, choices=TASK_CHOICES)
        parser.add_argument("--backend", required=True, choices=BACKEND_CHOICES)
        parser.print_help()
        return 0

    base_parser = build_arg_parser()
    base_args, _remaining = base_parser.parse_known_args(argv_list)
    config, add_task_args = _task_cli_config(base_args.task, base_args.backend)
    parser = build_task_eval_parser(backend=base_args.backend, config=config)
    parser.description = f"{config.description} (task={base_args.task}, backend={base_args.backend})"
    parser.add_argument("--task", required=True, choices=TASK_CHOICES)
    parser.add_argument("--backend", required=True, choices=BACKEND_CHOICES)
    if add_task_args is not None:
        add_task_args(parser)
    args = parser.parse_args(argv_list)
    return run_task_eval(task=base_args.task, backend=base_args.backend, args=args)


if __name__ == "__main__":
    raise SystemExit(main())
