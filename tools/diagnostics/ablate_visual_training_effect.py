#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)


def _parse_int_list(text: str) -> list[int]:
    values: list[int] = []
    for raw in str(text).split(","):
        token = raw.strip()
        if not token:
            continue
        values.append(int(token))
    if not values:
        raise ValueError("expected at least one integer value")
    return values


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def _save_json(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")


def _patch_train_config(
    base_cfg: dict[str, Any],
    *,
    visual_downsample: int,
    visual_update_interval: int | None,
    total_timesteps: int | None,
    device: str | None,
) -> dict[str, Any]:
    cfg = json.loads(json.dumps(base_cfg))
    hyper = cfg.get("hyperparameters", {})
    if not isinstance(hyper, dict):
        raise ValueError("train config hyperparameters must be a dict")
    policy_kwargs = hyper.get("policy_kwargs", {})
    if not isinstance(policy_kwargs, dict):
        raise ValueError("train config hyperparameters.policy_kwargs must be a dict")
    extractor = str(policy_kwargs.get("features_extractor_class", "")).strip()
    if extractor != "TransformerVisualExtractor":
        raise ValueError(
            "visual-resolution ablation requires features_extractor_class=TransformerVisualExtractor"
        )

    env_cfg = cfg.get("env", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    env_cfg["include_visual"] = True
    env_cfg["visual_downsample"] = int(max(1, visual_downsample))
    if visual_update_interval is not None:
        env_cfg["visual_update_interval"] = int(max(1, visual_update_interval))
    cfg["env"] = env_cfg

    if device is not None:
        hyper["device"] = str(device)
    if total_timesteps is not None:
        cfg["total_timesteps"] = int(max(1, total_timesteps))
    return cfg


def _run_subprocess(cmd: list[str], *, cwd: str, stdout_path: str, stderr_path: str) -> tuple[int, float]:
    start = time.perf_counter()
    with open(stdout_path, "w", encoding="utf-8") as out_f, open(stderr_path, "w", encoding="utf-8") as err_f:
        proc = subprocess.run(cmd, cwd=cwd, stdout=out_f, stderr=err_f, text=True)
    elapsed = time.perf_counter() - start
    return int(proc.returncode), float(elapsed)


def _read_json_if_exists(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    try:
        return _load_json(path)
    except Exception:
        return None


def _aggregate_by_factor(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        ds = int(row["visual_downsample"])
        grouped.setdefault(ds, []).append(row)

    out: list[dict[str, Any]] = []
    for ds in sorted(grouped):
        items = grouped[ds]
        ok = [r for r in items if bool(r.get("train_ok", False)) and bool(r.get("eval_ok", False))]
        success = [float(r["eval_summary"]["success_rate"]) for r in ok if r.get("eval_summary")]
        reward = [float(r["eval_summary"]["mean_reward"]) for r in ok if r.get("eval_summary")]
        steps = [float(r["eval_summary"]["mean_steps"]) for r in ok if r.get("eval_summary")]
        out.append(
            {
                "visual_downsample": int(ds),
                "runs": int(len(items)),
                "completed_runs": int(len(ok)),
                "mean_success_rate": None if not success else float(sum(success) / len(success)),
                "mean_reward": None if not reward else float(sum(reward) / len(reward)),
                "mean_steps": None if not steps else float(sum(steps) / len(steps)),
            }
        )
    return out


def _print_summary_table(rows: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> None:
    print("Per-run results")
    print("ds  seed  train_rc  eval_rc  train_s  success  reward    steps   run_name")
    print("--------------------------------------------------------------------------")
    for row in rows:
        summary = row.get("eval_summary") or {}
        success = summary.get("success_rate")
        reward = summary.get("mean_reward")
        steps = summary.get("mean_steps")
        success_s = "n/a" if success is None else f"{float(success):.3f}"
        reward_s = "n/a" if reward is None else f"{float(reward):.2f}"
        steps_s = "n/a" if steps is None else f"{float(steps):.1f}"
        print(
            f"{int(row['visual_downsample']):>2}  "
            f"{int(row['seed']):>4}  "
            f"{int(row['train_returncode']):>8}  "
            f"{int(row['eval_returncode']):>7}  "
            f"{float(row['train_wall_time_s']):>7.1f}  "
            f"{success_s:>7}  "
            f"{reward_s:>8}  "
            f"{steps_s:>7}  "
            f"{row['run_name']}"
        )

    print()
    print("Aggregated by visual_downsample")
    print("ds  runs  done  success_mean  reward_mean  steps_mean")
    print("------------------------------------------------------")
    for row in aggregates:
        success_s = "n/a" if row["mean_success_rate"] is None else f"{float(row['mean_success_rate']):.3f}"
        reward_s = "n/a" if row["mean_reward"] is None else f"{float(row['mean_reward']):.2f}"
        steps_s = "n/a" if row["mean_steps"] is None else f"{float(row['mean_steps']):.1f}"
        print(
            f"{int(row['visual_downsample']):>2}  "
            f"{int(row['runs']):>4}  "
            f"{int(row['completed_runs']):>4}  "
            f"{success_s:>12}  "
            f"{reward_s:>11}  "
            f"{steps_s:>10}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train/evaluate a visual_downsample ablation matrix for execution-layer visual policies."
    )
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--factors", default="1,2,4", help="Comma-separated visual_downsample values.")
    parser.add_argument("--seeds", default="0", help="Comma-separated training seeds.")
    parser.add_argument("--total_timesteps", type=int, default=None, help="Override total_timesteps in copied configs.")
    parser.add_argument("--device", default=None, help="Optional hyperparameters.device override for copied configs.")
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--n_envs", type=int, default=None)
    parser.add_argument("--eval_episodes", type=int, default=4)
    parser.add_argument("--eval_seed", type=int, default=1000)
    parser.add_argument("--eval_max_steps", type=int, default=None)
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--output_base", default="experiments_ablation")
    parser.add_argument("--run_prefix", default="visual_ds_ablation")
    parser.add_argument("--skip_existing", action="store_true", help="Skip training when final_model.zip already exists.")
    parser.add_argument("--json_out", default="", help="Optional aggregate JSON output path.")
    args = parser.parse_args()

    scenario_path = os.path.abspath(args.scenario)
    train_config_path = os.path.abspath(args.train_config)
    base_cfg = _load_json(train_config_path)

    output_base = os.path.abspath(args.output_base)
    config_dir = os.path.join(output_base, "_ablation_configs")
    os.makedirs(config_dir, exist_ok=True)

    rows: list[dict[str, Any]] = []
    factors = _parse_int_list(args.factors)
    seeds = _parse_int_list(args.seeds)

    for ds in factors:
        for seed in seeds:
            run_name = f"{args.run_prefix}_ds{int(ds)}_seed{int(seed)}"
            run_dir = os.path.join(output_base, run_name)
            cfg_copy = _patch_train_config(
                base_cfg,
                visual_downsample=int(ds),
                visual_update_interval=args.visual_update_interval,
                total_timesteps=args.total_timesteps,
                device=args.device,
            )
            cfg_copy_path = os.path.join(config_dir, f"{run_name}.json")
            _save_json(cfg_copy_path, cfg_copy)

            train_stdout = os.path.join(run_dir, "train.stdout.log")
            train_stderr = os.path.join(run_dir, "train.stderr.log")
            eval_stdout = os.path.join(run_dir, "eval.stdout.log")
            eval_stderr = os.path.join(run_dir, "eval.stderr.log")
            eval_json = os.path.join(run_dir, "eval_summary.json")
            final_model = os.path.join(run_dir, "final_model.zip")

            train_cmd = [
                sys.executable,
                resolve_repo_path("train.py"),
                "--scenario",
                scenario_path,
                "--train_config",
                cfg_copy_path,
                "--run_name",
                run_name,
                "--output_base",
                output_base,
                "--seed",
                str(int(seed)),
            ]
            if args.n_envs is not None:
                train_cmd.extend(["--n_envs", str(int(args.n_envs))])

            if bool(args.skip_existing) and os.path.exists(final_model):
                train_rc = 0
                train_wall = 0.0
            else:
                os.makedirs(run_dir, exist_ok=True)
                train_rc, train_wall = _run_subprocess(
                    train_cmd,
                    cwd=REPO_ROOT,
                    stdout_path=train_stdout,
                    stderr_path=train_stderr,
                )

            eval_cmd = [
                sys.executable,
                resolve_repo_path("tools", "eval", "policy_execution_eval.py"),
                "--mode",
                "single",
                "--scenario",
                scenario_path,
                "--train_config",
                cfg_copy_path,
                "--model",
                final_model,
                "--algo",
                str(args.algo),
                "--episodes",
                str(int(args.eval_episodes)),
                "--seed",
                str(int(args.eval_seed)),
                "--json_out",
                eval_json,
            ]
            if args.eval_max_steps is not None:
                eval_cmd.extend(["--max_steps", str(int(args.eval_max_steps))])

            if train_rc == 0 and os.path.exists(final_model):
                eval_rc, eval_wall = _run_subprocess(
                    eval_cmd,
                    cwd=REPO_ROOT,
                    stdout_path=eval_stdout,
                    stderr_path=eval_stderr,
                )
            else:
                eval_rc, eval_wall = 1, 0.0

            eval_summary = _read_json_if_exists(eval_json)
            rows.append(
                {
                    "visual_downsample": int(ds),
                    "seed": int(seed),
                    "run_name": run_name,
                    "run_dir": run_dir,
                    "config_copy": cfg_copy_path,
                    "train_command": train_cmd,
                    "train_returncode": int(train_rc),
                    "train_ok": bool(train_rc == 0 and os.path.exists(final_model)),
                    "train_wall_time_s": float(train_wall),
                    "final_model": final_model,
                    "eval_command": eval_cmd,
                    "eval_returncode": int(eval_rc),
                    "eval_ok": bool(eval_rc == 0 and eval_summary is not None),
                    "eval_wall_time_s": float(eval_wall),
                    "eval_summary": eval_summary,
                }
            )

    aggregates = _aggregate_by_factor(rows)
    payload = {
        "scenario": scenario_path,
        "train_config": train_config_path,
        "factors": [int(x) for x in factors],
        "seeds": [int(x) for x in seeds],
        "total_timesteps": args.total_timesteps,
        "visual_update_interval": args.visual_update_interval,
        "eval_episodes": int(args.eval_episodes),
        "eval_seed": int(args.eval_seed),
        "rows": rows,
        "aggregates": aggregates,
    }

    print(json.dumps(payload, indent=2, ensure_ascii=True))
    print()
    _print_summary_table(rows, aggregates)

    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        _save_json(out_path, payload)
        print()
        print(f"Wrote JSON report to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
