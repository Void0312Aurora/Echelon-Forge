"""Equivalence tests for the shared argparse group builders in
``tools/diagnostics/common.py`` (I20's owner, extended by the T5 second
argparse batch).

Covers, per shared group:

* ``add_dual_option`` -- the underscore/hyphen dual-alias primitive,
  including a regression test for the ``required=True`` + dual-alias defect
  found and fixed in this iteration (see module docstring in ``common.py``).
* ``add_probe_run_args`` / ``add_model_load_args`` / ``add_json_out_arg`` --
  I20's three groups, including the new ``choices=`` passthrough this
  iteration adds.
* ``add_kces_before_report_args`` -- the new KCES before-report group.

``test_argparse_migration_parity.py`` covers the individual migrated call
sites (old hand-written parser vs. the actual current module).
"""

from __future__ import annotations

import argparse

import pytest

from tools.diagnostics.common import (
    add_dual_option,
    add_json_out_arg,
    add_kces_before_report_args,
    add_model_load_args,
    add_probe_run_args,
)


def _action_for(parser: argparse.ArgumentParser, option_string: str) -> argparse.Action:
    for action in parser._actions:
        if option_string in action.option_strings:
            return action
    raise AssertionError(f"no action registers {option_string!r}; parser has {parser._actions!r}")


def _actions_for_dest(parser: argparse.ArgumentParser, dest: str) -> list[argparse.Action]:
    return [action for action in parser._actions if action.dest == dest]


def _visible_destinations(parser: argparse.ArgumentParser) -> list[str]:
    """Registration order of non-help, non-suppressed-alias destinations.

    Dual-option destinations (see ``_DUAL_OPTION_DESTS``) register a second,
    ``help=SUPPRESS`` alias action sharing the same ``dest``; excluding
    suppressed actions here keeps this a one-entry-per-visible-option view.
    """

    return [
        action.dest
        for action in parser._actions
        if action.dest != "help" and action.help != argparse.SUPPRESS
    ]


class TestAddDualOption:
    def test_underscore_primary_registers_visible_underscore_and_suppressed_hyphen(self) -> None:
        parser = argparse.ArgumentParser()
        add_dual_option(parser, "train_config", default="x")

        visible = _action_for(parser, "--train_config")
        alias = _action_for(parser, "--train-config")
        assert visible.dest == alias.dest == "train_config"
        assert visible.help != argparse.SUPPRESS
        assert alias.help == argparse.SUPPRESS

    def test_hyphen_primary_flips_which_spelling_is_visible(self) -> None:
        parser = argparse.ArgumentParser()
        add_dual_option(parser, "max_steps", primary="hyphen", type=int, default=0)

        visible = _action_for(parser, "--max-steps")
        alias = _action_for(parser, "--max_steps")
        assert visible.help != argparse.SUPPRESS
        assert alias.help == argparse.SUPPRESS

    def test_both_spellings_parse_to_the_same_dest_value(self) -> None:
        parser = argparse.ArgumentParser()
        add_dual_option(parser, "json_out", default="")

        assert parser.parse_args(["--json_out", "a.json"]).json_out == "a.json"
        assert parser.parse_args(["--json-out", "b.json"]).json_out == "b.json"

    def test_single_token_dest_gets_exactly_one_option_string(self) -> None:
        parser = argparse.ArgumentParser()
        add_dual_option(parser, "scenario", required=True)

        action = _action_for(parser, "--scenario")
        assert action.option_strings == ["--scenario"]
        # No accidental "--scenario" alias registration.
        assert len({a.dest for a in parser._actions if a.dest == "scenario"}) == 1
        assert len(_actions_for_dest(parser, "scenario")) == 1

    def test_invalid_primary_value_raises(self) -> None:
        parser = argparse.ArgumentParser()
        with pytest.raises(ValueError):
            add_dual_option(parser, "train_config", primary="bogus")

    def test_non_required_dual_option_last_provided_spelling_wins(self) -> None:
        """Regression guard: the required-only MEG fix must not change the
        long-standing (non-required) dual-option behavior of "last spelling
        provided on the command line wins", which several already-shipped
        I20 call sites (none of which pass required=True) depend on."""

        parser = argparse.ArgumentParser()
        add_dual_option(parser, "train_config", default="fallback.json")

        args = parser.parse_args(["--train_config", "a.json", "--train-config", "b.json"])
        assert args.train_config == "b.json"

    def test_required_dual_option_accepts_either_spelling(self) -> None:
        """Regression test for the defect this iteration found: two
        independently `required=True` actions sharing one dest previously
        forced callers to spell out *both* forms (argparse tracks "seen" per
        action, not per dest)."""

        parser = argparse.ArgumentParser(prog="demo")
        add_dual_option(parser, "train_config", required=True)

        assert parser.parse_args(["--train_config", "a.json"]).train_config == "a.json"
        assert parser.parse_args(["--train-config", "b.json"]).train_config == "b.json"

    def test_required_dual_option_errors_when_neither_spelling_is_supplied(self) -> None:
        parser = argparse.ArgumentParser(prog="demo")
        add_dual_option(parser, "train_config", required=True)

        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args([])
        assert excinfo.value.code == 2

    def test_required_dual_option_rejects_both_spellings_at_once(self) -> None:
        """Documented, acceptable behavior change: supplying both spellings
        of a *required* dual option is now a parse error (mutually
        exclusive group), rather than silently letting the second spelling
        win. There was no working "both provided" precedent to preserve --
        the pre-fix code raised a spurious "missing" error even when one
        spelling was supplied, so this is a strict improvement, not a
        parity break."""

        parser = argparse.ArgumentParser(prog="demo")
        add_dual_option(parser, "train_config", required=True)

        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["--train_config", "a.json", "--train-config", "b.json"])
        assert excinfo.value.code == 2

    def test_required_help_output_is_unaffected_by_the_mutually_exclusive_group(self) -> None:
        with_fix = argparse.ArgumentParser(prog="demo")
        add_dual_option(with_fix, "train_config", required=True, help="Train config JSON.")

        reference = argparse.ArgumentParser(prog="demo")
        reference.add_argument("--train_config", dest="train_config", required=True, help="Train config JSON.")

        assert with_fix.format_help() == reference.format_help()


class TestAddProbeRunArgs:
    def test_default_include_registers_all_four_names_in_canonical_order(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser)
        assert _visible_destinations(parser) == ["scenario", "episodes", "seed", "max_steps"]

    def test_include_list_order_controls_registration_order(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser, include=["max_steps", "scenario"])
        assert _visible_destinations(parser) == ["max_steps", "scenario"]

    def test_episodes_seed_max_steps_default_to_int_type_scenario_does_not(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser)
        assert _action_for(parser, "--episodes").type is int
        assert _action_for(parser, "--seed").type is int
        assert _action_for(parser, "--max_steps").type is int
        assert _action_for(parser, "--scenario").type is None

    def test_types_override_the_default_type(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser, include=["seed"], types={"seed": str})
        assert _action_for(parser, "--seed").type is str

    def test_defaults_and_helps_and_choices_are_forwarded_per_name(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(
            parser,
            include=["episodes"],
            defaults={"episodes": 7},
            helps={"episodes": "custom help"},
            choices={"episodes": [1, 7, 14]},
        )
        action = _action_for(parser, "--episodes")
        assert action.default == 7
        assert action.help == "custom help"
        assert action.choices == [1, 7, 14]

    def test_required_true_on_scenario_uses_plain_required_not_a_group(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser, include=["scenario"], required={"scenario": True})
        action = _action_for(parser, "--scenario")
        assert action.required is True
        assert not parser._mutually_exclusive_groups

    def test_unknown_include_name_raises(self) -> None:
        parser = argparse.ArgumentParser()
        with pytest.raises(ValueError):
            add_probe_run_args(parser, include=["not_a_real_field"])

    def test_unknown_exclude_name_raises(self) -> None:
        parser = argparse.ArgumentParser()
        with pytest.raises(ValueError):
            add_probe_run_args(parser, exclude=["not_a_real_field"])

    def test_exclude_removes_a_name_from_the_default_set(self) -> None:
        parser = argparse.ArgumentParser()
        add_probe_run_args(parser, exclude=["max_steps"])
        destinations = {a.dest for a in parser._actions if a.dest != "help"}
        assert destinations == {"scenario", "episodes", "seed"}


class TestAddModelLoadArgs:
    def test_default_include_registers_all_four_names_in_canonical_order(self) -> None:
        parser = argparse.ArgumentParser()
        add_model_load_args(parser)
        assert _visible_destinations(parser) == ["train_config", "model", "algo", "device"]

    def test_no_implicit_type_coercion_unlike_probe_run_args(self) -> None:
        parser = argparse.ArgumentParser()
        add_model_load_args(parser)
        for option in ("--train_config", "--model", "--algo", "--device"):
            assert _action_for(parser, option).type is None

    def test_choices_are_forwarded(self) -> None:
        parser = argparse.ArgumentParser()
        add_model_load_args(parser, include=["algo"], choices={"algo": ["PPO", "AdaptiveKLPPO"]})
        assert _action_for(parser, "--algo").choices == ["PPO", "AdaptiveKLPPO"]

    def test_required_train_config_accepts_either_spelling_end_to_end(self) -> None:
        """Direct regression test through the public group builder (not just
        add_dual_option) for the defect this iteration found while migrating
        naval_station_policy_eval.py and friends."""

        parser = argparse.ArgumentParser(prog="demo")
        add_model_load_args(parser, include=["train_config"], required={"train_config": True})

        assert parser.parse_args(["--train_config", "a.json"]).train_config == "a.json"
        assert parser.parse_args(["--train-config", "b.json"]).train_config == "b.json"
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_required_model_uses_plain_required_since_model_has_no_underscore(self) -> None:
        parser = argparse.ArgumentParser()
        add_model_load_args(parser, include=["model"], required={"model": True})
        action = _action_for(parser, "--model")
        assert action.required is True
        assert not parser._mutually_exclusive_groups


class TestAddJsonOutArg:
    def test_default_is_empty_string_dual_registered(self) -> None:
        parser = argparse.ArgumentParser()
        add_json_out_arg(parser)
        assert _action_for(parser, "--json_out").default == ""
        assert _action_for(parser, "--json-out").help == argparse.SUPPRESS

    def test_custom_default_and_help_and_required(self) -> None:
        parser = argparse.ArgumentParser(prog="demo")
        add_json_out_arg(parser, default="out.json", help="Where to write.", required=True)
        action = _action_for(parser, "--json_out")
        assert action.default == "out.json"
        assert action.help == "Where to write."
        # required=True on json_out must also survive the dual-alias fix.
        assert parser.parse_args(["--json-out", "x.json"]).json_out == "x.json"


class TestAddKcesBeforeReportArgs:
    def _parser(self, **overrides) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="demo")
        kwargs = dict(
            variant_default="REV-RUNTIME-PROJECTION",
            target_motion_layer_default="nonmaneuvering_constant_velocity",
            date_stamp_example="20260628",
        )
        kwargs.update(overrides)
        add_kces_before_report_args(parser, **kwargs)
        return parser

    def test_registers_the_six_shared_options_in_order(self) -> None:
        parser = self._parser()
        destinations = [a.dest for a in parser._actions if a.dest != "help"]
        assert destinations == [
            "input",
            "output_dir",
            "prefix",
            "variant",
            "target_motion_layer",
            "date_stamp",
        ]

    def test_input_is_required_and_type_path(self) -> None:
        from pathlib import Path

        parser = self._parser()
        action = _action_for(parser, "--input")
        assert action.required is True
        assert action.type is Path

    def test_variant_and_target_motion_layer_use_the_caller_supplied_defaults(self) -> None:
        parser = self._parser(variant_default="CUSTOM-VARIANT", target_motion_layer_default="custom_layer")
        assert _action_for(parser, "--variant").default == "CUSTOM-VARIANT"
        assert _action_for(parser, "--target-motion-layer").default == "custom_layer"

    def test_date_stamp_help_interpolates_the_per_caller_example(self) -> None:
        parser = self._parser(date_stamp_example="20260706")
        action = _action_for(parser, "--date-stamp")
        assert action.help == "Filename date stamp, for example 20260706. Defaults to today."

    def test_prefix_default_is_shared_verbatim_across_all_callers(self) -> None:
        parser = self._parser()
        assert _action_for(parser, "--prefix").default == "kces_anchor_cv"

    def test_input_help_is_overridable(self) -> None:
        parser = self._parser(input_help="Custom input help.")
        assert _action_for(parser, "--input").help == "Custom input help."

    def test_no_dual_alias_registration_kept_conservative_hyphen_only(self) -> None:
        """This new group intentionally does not extend I20's underscore/
        hyphen dual-alias machinery: every original caller used the
        hyphenated spelling exclusively, so the shared builder keeps that as
        the sole accepted surface instead of speculatively widening it."""

        parser = self._parser()
        for dest in ("output_dir", "target_motion_layer", "date_stamp"):
            actions = _actions_for_dest(parser, dest)
            assert len(actions) == 1
            assert len(actions[0].option_strings) == 1
