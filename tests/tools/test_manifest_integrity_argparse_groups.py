"""Equivalence tests for the shared retained-gate output CLI group added to
``tools/maintenance/retained_artifacts/manifest_integrity.py`` (I19's owner)
as part of the T5 second argparse batch.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.maintenance.retained_artifacts.manifest_integrity import add_retained_gate_output_args


def _action_for(parser: argparse.ArgumentParser, option_string: str) -> argparse.Action:
    for action in parser._actions:
        if option_string in action.option_strings:
            return action
    raise AssertionError(f"no action registers {option_string!r}")


class TestAddRetainedGateOutputArgs:
    def test_registers_output_dir_then_stdout(self) -> None:
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(parser, retained_dir_default=Path("/tmp/retained"))
        destinations = [a.dest for a in parser._actions if a.dest != "help"]
        assert destinations == ["output_dir", "stdout"]

    def test_output_dir_defaults_to_the_caller_supplied_path_and_is_path_typed(self) -> None:
        default_dir = Path("/tmp/retained_default")
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(parser, retained_dir_default=default_dir)
        action = _action_for(parser, "--output-dir")
        assert action.default == default_dir
        assert action.type is Path

    def test_stdout_is_a_store_true_flag_defaulting_to_false(self) -> None:
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(parser, retained_dir_default=Path("/tmp/retained"))
        args = parser.parse_args([])
        assert args.stdout is False
        args = parser.parse_args(["--stdout"])
        assert args.stdout is True

    def test_default_help_text_matches_the_most_common_wording(self) -> None:
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(parser, retained_dir_default=Path("/tmp/retained"))
        assert _action_for(parser, "--output-dir").help == "Directory for retained JSON artifacts."
        assert (
            _action_for(parser, "--stdout").help
            == "Also print the gate JSON to stdout after writing retained artifacts."
        )

    def test_per_caller_help_overrides_are_independent(self) -> None:
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(
            parser,
            retained_dir_default=Path("/tmp/retained"),
            output_dir_help="Directory for retained JSON artifacts. Defaults to the candidate retained-artifacts gate directory.",
            stdout_help="Also print the gate JSON after writing retained artifacts.",
        )
        assert _action_for(parser, "--output-dir").help == (
            "Directory for retained JSON artifacts. Defaults to the candidate retained-artifacts gate directory."
        )
        assert _action_for(parser, "--stdout").help == "Also print the gate JSON after writing retained artifacts."

    def test_no_underscore_hyphen_dual_alias_kept_conservative(self) -> None:
        parser = argparse.ArgumentParser()
        add_retained_gate_output_args(parser, retained_dir_default=Path("/tmp/retained"))
        assert _action_for(parser, "--output-dir").option_strings == ["--output-dir"]
