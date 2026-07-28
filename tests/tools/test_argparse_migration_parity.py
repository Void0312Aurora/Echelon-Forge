"""Attribute-level "old parser vs. new parser" equivalence tests for a
representative subset of the T5 second-batch argparse migration call sites.

``test_argparse_migration_help_parity.py`` pins ``--help`` text (a
byte-parity proxy) for all sixteen migrated files. This module goes one
level deeper for the three call sites that expose their parser construction
as a standalone, argv-free function (so a reference "as it was before
migration" parser can be built side by side with the real one and compared
action-by-action, including ``required``/``choices``/``default``/``type``,
not just rendered help text): ``naval_station_policy_eval._build_parser``,
``sb3_eval_base.add_common_sb3_eval_args`` (both its ``single`` and
``cooperative`` shapes, as consumed by ``policy_execution_eval.py``), and
``eval_utils.add_common_env_args`` (as consumed by ``task_eval_driver.py``).

It also carries targeted subprocess regression checks, for the files whose
parser construction is inline in ``main()`` (no standalone builder to call
without a full CLI invocation), proving the specific defect this iteration
found and fixed: a ``required=True`` dual-alias destination (``train_config``)
now accepts *either* spelling and rejects omission, instead of only
accepting the literal historical spelling while silently requiring the
hidden alias too.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.eval import eval_utils
from tools.eval import naval_station_policy_eval
from tools.eval import sb3_eval_base

REPO_ROOT = Path(__file__).resolve().parents[2]


def _effectively_required(parser: argparse.ArgumentParser, action: argparse.Action) -> bool:
    """True if omitting *action* (and every dest-sharing alias) fails parsing.

    A plain action reports this via ``action.required``. A dual-alias
    destination promoted to a required mutually exclusive group (this
    iteration's fix for the required + dual-alias defect) reports
    ``action.required is False`` on each member instead; the requiredness
    lives on the group.
    """

    if action.required:
        return True
    return any(
        action in group._group_actions and group.required for group in parser._mutually_exclusive_groups
    )


def _spec(parser: argparse.ArgumentParser, action: argparse.Action) -> dict[str, object]:
    return {
        "option_strings": tuple(action.option_strings),
        "dest": action.dest,
        "default": action.default,
        "required": _effectively_required(parser, action),
        "type": action.type,
        "choices": list(action.choices) if action.choices is not None else None,
        "help": action.help,
    }


def _visible_specs(parser: argparse.ArgumentParser) -> dict[str, dict[str, object]]:
    """dest -> spec for every action except -h/--help and suppressed aliases."""

    return {
        action.dest: _spec(parser, action)
        for action in parser._actions
        if action.dest != "help" and action.help != argparse.SUPPRESS
    }


class TestNavalStationPolicyEvalParserParity:
    def _reference_parser(self) -> argparse.ArgumentParser:
        """Reproduces the pre-migration ``_build_parser`` body verbatim."""

        parser = argparse.ArgumentParser(description="Evaluate maintained naval station cooperative policy gates.")
        parser.add_argument("--scenario", required=True)
        parser.add_argument("--train_config", required=True)
        parser.add_argument("--steps", type=int, default=1200)
        parser.add_argument("--seed", type=int, default=20260525)
        parser.add_argument("--worker_threads", type=int, default=1)
        parser.add_argument("--json_out", default="")
        parser.add_argument(
            "--mode",
            choices=["baseline", "offstation_probe"],
            default="baseline",
            help=(
                "baseline runs the zero-action station hold gate; offstation_probe checks "
                "station-order reward-reference closure."
            ),
        )
        parser.add_argument("--station_radius_offset_m", type=float, default=-1800.0)
        return parser

    def test_visible_actions_match_the_pre_migration_reference(self) -> None:
        reference = _visible_specs(self._reference_parser())
        # The real parser also carries the newer --report-envelope flag
        # (T5's opt-in report envelope slice); exclude it from this
        # argparse-consolidation-only comparison.
        actual = _visible_specs(naval_station_policy_eval._build_parser())
        actual.pop("report_envelope", None)
        assert actual == reference

    def test_scenario_and_train_config_accept_either_spelling(self) -> None:
        parser = naval_station_policy_eval._build_parser()
        args = parser.parse_args(["--scenario", "s.json", "--train-config", "t.json"])
        assert args.scenario == "s.json"
        assert args.train_config == "t.json"

    def test_missing_train_config_fails_closed(self) -> None:
        parser = naval_station_policy_eval._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--scenario", "s.json"])


class TestSb3EvalBaseParserParity:
    def _reference_parser(self, *, include_runtime_overrides: bool, cooperative: bool, **kwargs) -> argparse.ArgumentParser:
        """Reproduces the pre-migration ``add_common_sb3_eval_args`` body."""

        episodes_default = kwargs.get("episodes_default", 8)
        seed_default = kwargs.get("seed_default", 0)
        episodes_help = kwargs.get("episodes_help")
        seed_help = kwargs.get("seed_help")

        parser = argparse.ArgumentParser()
        parser.add_argument("--scenario", required=True)
        parser.add_argument("--train_config", required=True)
        parser.add_argument("--model", required=True, help="Path to SB3 model zip.")
        parser.add_argument("--algo", default="auto", help="auto / AdaptiveKLPPO / PPO")
        parser.add_argument("--episodes", type=int, default=int(episodes_default), help=episodes_help)
        parser.add_argument("--seed", type=int, default=int(seed_default), help=seed_help)
        parser.add_argument("--stochastic", action="store_true")
        parser.add_argument("--device", type=str, default="auto", help="Policy inference device: auto / cpu / cuda")
        parser.add_argument(
            "--include_visual", action=argparse.BooleanOptionalAction, default=None,
            help="Override env visual flag from train config.",
        )
        parser.add_argument(
            "--include_proprio", action=argparse.BooleanOptionalAction, default=None,
            help="Override env proprio flag from train config.",
        )
        from python.mission_obs_taxonomy import (
            BASE_MISSION_OBS_MODES,
            COOPERATIVE_MISSION_OBS_MODES,
            NAVAL_MISSION_OBS_MODES,
        )

        mission_choices = list(BASE_MISSION_OBS_MODES)
        if cooperative:
            mission_choices.extend(COOPERATIVE_MISSION_OBS_MODES)
        mission_choices.extend(NAVAL_MISSION_OBS_MODES)
        parser.add_argument("--mission_obs_mode", type=str, default=None, choices=mission_choices)
        parser.add_argument("--visual_downsample", type=int, default=None)
        parser.add_argument("--visual_update_interval", type=int, default=None)
        parser.add_argument("--temporal_history_len", type=int, default=None)
        from python.env_config import ACTION_MODES

        parser.add_argument("--action_mode", type=str, default=None, choices=list(ACTION_MODES))
        if include_runtime_overrides:
            from python.env_config import EXECUTION_STEP_RUNTIME_MODES, FLIGHT_SHAPING_BACKENDS, STEP_INFO_MODES

            parser.add_argument(
                "--execution_step_runtime_mode", type=str, default=None,
                choices=list(EXECUTION_STEP_RUNTIME_MODES),
            )
            parser.add_argument("--step_info_mode", type=str, default=None, choices=list(STEP_INFO_MODES))
            parser.add_argument(
                "--flight_shaping_backend", type=str, default=None, choices=list(FLIGHT_SHAPING_BACKENDS)
            )
        parser.add_argument("--json_out", default="", help="Optional JSON output path.")
        return parser

    @pytest.mark.parametrize("cooperative", [False, True])
    def test_visible_actions_match_the_pre_migration_reference(self, cooperative: bool) -> None:
        reference = self._reference_parser(
            include_runtime_overrides=cooperative,
            cooperative=cooperative,
            episodes_default=8,
            seed_default=0,
        )
        actual_parser = argparse.ArgumentParser()
        sb3_eval_base.add_common_sb3_eval_args(
            actual_parser,
            include_runtime_overrides=cooperative,
            cooperative=cooperative,
            episodes_default=8,
            seed_default=0,
        )
        assert _visible_specs(actual_parser) == _visible_specs(reference)

    def test_custom_episodes_and_seed_defaults_and_help_propagate(self) -> None:
        reference = self._reference_parser(
            include_runtime_overrides=False,
            cooperative=False,
            episodes_default=8,
            seed_default=0,
            episodes_help="Number of world episodes to evaluate.",
            seed_help="Starting seed. Each episode increments by 1.",
        )
        actual_parser = argparse.ArgumentParser()
        sb3_eval_base.add_common_sb3_eval_args(
            actual_parser,
            include_runtime_overrides=False,
            cooperative=False,
            episodes_default=8,
            seed_default=0,
            episodes_help="Number of world episodes to evaluate.",
            seed_help="Starting seed. Each episode increments by 1.",
        )
        assert _visible_specs(actual_parser) == _visible_specs(reference)

    def test_train_config_and_model_accept_either_spelling_and_reject_omission(self) -> None:
        parser = argparse.ArgumentParser()
        sb3_eval_base.add_common_sb3_eval_args(parser, include_runtime_overrides=False, cooperative=False)
        args = parser.parse_args(["--scenario", "s", "--train-config", "t", "--model", "m"])
        assert args.train_config == "t"
        with pytest.raises(SystemExit):
            parser.parse_args(["--scenario", "s", "--model", "m"])


class TestEvalUtilsParserParity:
    def _reference_parser(self, **kwargs) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument("--scenario", required=True)
        parser.add_argument("--episodes", type=int, default=int(kwargs["episodes_default"]))
        parser.add_argument("--max_steps", type=int, default=int(kwargs["max_steps_default"]))
        parser.add_argument("--seed", type=int, default=int(kwargs["seed_default"]))
        parser.add_argument(
            "--action_mode", type=str, default=str(kwargs["default_action_mode"]), choices=eval_utils.ACTION_MODE_CHOICES
        )
        parser.add_argument("--include_visual", action="store_true")
        parser.add_argument("--include_proprio", action="store_true")
        if kwargs.get("include_no_randomization"):
            parser.add_argument("--no_randomization", action="store_true")
        return parser

    @pytest.mark.parametrize("include_no_randomization", [False, True])
    def test_visible_actions_match_the_pre_migration_reference(self, include_no_randomization: bool) -> None:
        kwargs = dict(
            episodes_default=20,
            max_steps_default=2000,
            seed_default=0,
            default_action_mode="full",
            include_no_randomization=include_no_randomization,
        )
        reference = self._reference_parser(**kwargs)
        actual_parser = argparse.ArgumentParser()
        eval_utils.add_common_env_args(actual_parser, **kwargs)
        assert _visible_specs(actual_parser) == _visible_specs(reference)

    def test_max_steps_then_seed_ordering_is_preserved(self) -> None:
        """The shared group's canonical order is scenario/episodes/seed/
        max_steps, but this call site's pre-migration code (and every
        caller of it) declared max_steps before seed; the migrated call
        passes an explicit ``include=`` list to keep that exact order."""

        parser = argparse.ArgumentParser()
        eval_utils.add_common_env_args(
            parser, episodes_default=1, max_steps_default=1, seed_default=1, default_action_mode="full"
        )
        destinations = [a.dest for a in parser._actions if a.dest not in ("help",)]
        assert destinations.index("max_steps") < destinations.index("seed")


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, *argv], cwd=str(REPO_ROOT), capture_output=True, text=True, env=env, check=False
    )


class TestInlineConstructedParsersAcceptEitherTrainConfigSpelling:
    """Files whose argparse construction is inline inside ``main()`` (no
    standalone builder to call directly) are checked end-to-end instead:
    the actual defect found in this iteration was that a hand-written
    ``required={"train_config": True}`` call site silently required *both*
    ``--train_config`` and its hidden ``--train-config`` alias. Each of
    these should now accept either spelling and reject omission cleanly
    (exit code 2, not a traceback).
    """

    @pytest.mark.parametrize(
        "argv_prefix,extra",
        [
            (
                ["tools/diagnostics/ablate_visual_training_effect.py"],
                ["--scenario", "s.json"],
            ),
            (
                ["tools/diagnostics/diagnose_cooperative_trajectory.py"],
                ["--task", "takeoff", "--scenario", "s.json", "--scripted", "--output", "o.png"],
            ),
            (
                ["tools/diagnostics/flight_trajectory/takeoff_to_landing.py"],
                ["--scenario", "s.json", "--scripted", "--output", "o.png"],
            ),
            (
                ["tools/diagnostics/leader_perf_probe.py"],
                ["--scenario", "s.json"],
            ),
        ],
        ids=["ablate_visual_training_effect", "diagnose_cooperative_trajectory", "takeoff_to_landing", "leader_perf_probe"],
    )
    def test_train_config_hyphen_alias_is_accepted_by_argparse(self, argv_prefix: list[str], extra: list[str]) -> None:
        # Only argparse's own accept/reject behavior is under test here (not
        # full execution, which needs real scenario/runtime fixtures), so a
        # bogus --train-config value is enough: a rejection would show up as
        # argparse's usage/error text on stderr with exit code 2, not as a
        # later runtime failure.
        proc = _run([*argv_prefix, *extra, "--train-config", "definitely-not-a-real-path.json"])
        assert "unrecognized arguments" not in proc.stderr
        assert "the following arguments are required: --train-config" not in proc.stderr
        assert "one of the arguments" not in proc.stderr

    @pytest.mark.parametrize(
        "argv_prefix",
        [
            ["tools/diagnostics/ablate_visual_training_effect.py", "--scenario", "s.json"],
            ["tools/diagnostics/leader_perf_probe.py", "--scenario", "s.json"],
        ],
        ids=["ablate_visual_training_effect", "leader_perf_probe"],
    )
    def test_omitting_train_config_entirely_still_fails_closed(self, argv_prefix: list[str]) -> None:
        proc = _run(argv_prefix)
        assert proc.returncode == 2
        assert "required" in proc.stderr
