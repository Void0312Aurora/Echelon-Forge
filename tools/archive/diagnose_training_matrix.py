#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path


RE_MEAN_REWARD = re.compile(r"Mean Reward:\s*([-0-9.]+)")
RE_SUCCESS = re.compile(r"Success Rate:\s*([-0-9.]+)%")
RE_SURVIVAL = re.compile(r"Survival Rate:\s*([-0-9.]+)%")
RE_LENGTH = re.compile(r"Mean Length:\s*([-0-9.]+)")


def run_eval(eval_py, scenario, model, algo, episodes, include_visual, action_mode, seed=None):
    cmd = [
        sys.executable,
        str(eval_py),
        "--scenario",
        str(scenario),
        "--model",
        str(model),
        "--algo",
        algo,
        "--episodes",
        str(episodes),
        "--action_mode",
        action_mode,
    ]
    if include_visual:
        cmd.append("--include_visual")
    if seed is not None:
        cmd.extend(["--seed", str(seed)])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + "\n" + proc.stderr

    def extract(rx):
        m = rx.search(out)
        return float(m.group(1)) if m else None

    return {
        "returncode": proc.returncode,
        "mean_reward": extract(RE_MEAN_REWARD),
        "success_rate": extract(RE_SUCCESS),
        "survival_rate": extract(RE_SURVIVAL),
        "mean_length": extract(RE_LENGTH),
        "raw": out,
        "cmd": " ".join(cmd),
    }


def main():
    parser = argparse.ArgumentParser(description="Archived evaluation matrix helper for legacy evaluate.py output.")
    parser.add_argument("--eval_py", default="evaluate.py")
    parser.add_argument("--algo", default="AdaptiveKLPPO")
    parser.add_argument("--episodes", type=int, default=8)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--action_mode", default="full", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument(
        "--pair",
        action="append",
        nargs=2,
        metavar=("MODEL", "SCENARIO"),
        help="A model/scenario pair. Repeat --pair for matrix rows.",
    )
    args = parser.parse_args()

    if not args.pair:
        print("No --pair provided.")
        sys.exit(2)

    eval_py = Path(args.eval_py).resolve()
    if not eval_py.exists():
        print(f"evaluate.py not found: {eval_py}")
        sys.exit(2)

    rows = []
    for model, scenario in args.pair:
        model_p = Path(model)
        scenario_p = Path(scenario)
        result = run_eval(
            eval_py,
            scenario_p,
            model_p,
            args.algo,
            args.episodes,
            args.include_visual,
            args.action_mode,
            args.seed,
        )
        rows.append((model, scenario, result))

    print("=== Evaluation Matrix Summary ===")
    print("model\tscenario\tret\tsucc%\tsurv%\tlen\trc")
    for model, scenario, r in rows:
        print(
            f"{model}\t{scenario}\t{r['mean_reward']}\t{r['success_rate']}\t"
            f"{r['survival_rate']}\t{r['mean_length']}\t{r['returncode']}"
        )

    failed = [r for _, _, r in rows if r["returncode"] != 0 or r["mean_reward"] is None]
    if failed:
        print("\n=== Failures ===")
        for idx, (model, scenario, r) in enumerate(rows, 1):
            if r["returncode"] != 0 or r["mean_reward"] is None:
                print(f"[{idx}] model={model} scenario={scenario} rc={r['returncode']}")
                print(r["cmd"])
                print(r["raw"][-1200:])


if __name__ == "__main__":
    main()
