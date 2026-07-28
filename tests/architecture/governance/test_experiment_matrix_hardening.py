"""Load-bearing negative gates for the three I30 experiment-matrix residuals.

I36 closed the three review residuals recorded in the I30 register row
(object-key escaping, bool-vs-int literal-override equality, and the full
experiment -> scenario pairing table) and added first-generation regression
tests next to the freshness gate. The tests in this file go one step
further, as required by this iteration's queue row: each residual gets a
negative test that *injects* the defect class and proves the detection
machinery goes red, so a silent regression of the hardening -- or of the
gate assertion itself -- cannot stay green.

Everything here is pure standard library plus the repository's own
declarative modules; no build directory or ``ef_py`` import is required,
and no generated matrix file is read or written.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from python.experiment.air_combat_matrix import (
  CONFIG_BASE_ID,
  MATRIX_DIR,
  MATRIX_ENTRIES,
  MatrixEntry,
  RenderStyle,
  composed_config,
)
from python.experiment.definition import (
  ConfigComposition,
  Experiment,
  ScenarioRef,
  SeedSpec,
)
from tools.maintenance.experiment_matrix import generate as experiment_matrix_generate

REPO_ROOT = Path(__file__).resolve().parents[3]

_FRESHNESS_GATE_PATH = Path(__file__).resolve().parent / "test_experiment_matrix_freshness.py"

_EXISTING_SCENARIO = "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"


def _load_freshness_gate_module() -> ModuleType:
  """Load the freshness gate module to reuse its reviewed pairing table.

  The 24-row experiment -> scenario table is pinned exactly once, in the
  freshness gate; importing it by file path keeps this file from becoming a
  second, independently-drifting copy of the same table.
  """
  spec = importlib.util.spec_from_file_location(
    "_experiment_matrix_freshness_gate_for_hardening", _FRESHNESS_GATE_PATH
  )
  assert spec is not None and spec.loader is not None
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def _strictly_equal(actual: Any, expected: Any) -> bool:
  """Independent referee: type-identity-aware, key-order-pinning equality.

  Deliberately local (not the generator's ``_strict_json_equal``) so a
  regression of the generator's own comparator cannot weaken the referee
  that judges its output.
  """
  if isinstance(actual, dict) and isinstance(expected, dict):
    return list(actual) == list(expected) and all(
      _strictly_equal(actual[key], expected[key]) for key in actual
    )
  if isinstance(actual, list) and isinstance(expected, list):
    return len(actual) == len(expected) and all(
      _strictly_equal(a, b) for a, b in zip(actual, expected)
    )
  return type(actual) is type(expected) and actual == expected


def _synthetic_matrix_entry(
  experiment_id: str,
  delta: dict[str, object],
  render: RenderStyle,
) -> MatrixEntry:
  experiment = Experiment(
    experiment_id,
    ScenarioRef(_EXISTING_SCENARIO),
    ConfigComposition(CONFIG_BASE_ID, delta),
    SeedSpec(),
    "probe",
  )
  return MatrixEntry(
    experiment=experiment,
    output_path=f"{MATRIX_DIR}/{experiment_id}.json",
    render=render,
  )


# --- Residual (a): JSON object-key escaping -------------------------------

# (key, naive interpolation emits illegal JSON). The pre-I36 renderer wrote
# object keys as f'"{key}"'; every True row below turns that into a JSON
# parse error, which is exactly what makes this input load-bearing. The
# unicode row is legal either way and only pins escape coverage.
_HOSTILE_KEYS: tuple[tuple[str, bool], ...] = (
  ('weird "quoted" key', True),
  ("back\\slash", True),
  ("newline\nkey", True),
  ("tab\tkey", True),
  ("unicode 键", False),
)


def test_hostile_object_keys_survive_a_strict_render_round_trip() -> None:
  """Inject quote/backslash/control-character keys; the render must stay
  strict JSON that round-trips to the composed config, key order included."""
  delta: dict[str, object] = {
    key: index for index, (key, _) in enumerate(_HOSTILE_KEYS)
  }
  delta["nested"] = {key: True for key, _ in _HOSTILE_KEYS}
  entry = _synthetic_matrix_entry(
    "synthetic_hostile_key_probe_v1", delta, RenderStyle()
  )

  rendered = experiment_matrix_generate.render_entry_bytes(entry).decode("utf-8")
  parsed = json.loads(rendered)  # a naive f'"{key}"' renderer dies here
  assert _strictly_equal(parsed, composed_config(entry))

  # Defect injection: prove the naive pre-fix interpolation is illegal JSON
  # for every load-bearing key, so a regression cannot pass this test.
  for key, naive_is_illegal in _HOSTILE_KEYS:
    naive_fragment = "{" + f'"{key}"' + ": 1}"
    if naive_is_illegal:
      with pytest.raises(json.JSONDecodeError):
        json.loads(naive_fragment)
    else:
      assert json.loads(naive_fragment) == {key: 1}


def test_every_registered_entry_round_trips_as_strict_json() -> None:
  """Corpus-wide backstop: all registered entries must render to JSON that
  strictly equals their composed config (types and key order pinned)."""
  for entry in MATRIX_ENTRIES:
    parsed = json.loads(experiment_matrix_generate.render_entry_bytes(entry))
    assert _strictly_equal(parsed, composed_config(entry)), entry.output_path


# --- Residual (b): bool-vs-int literal-override equality ------------------

# Every pair passes Python's plain ``==`` (bool is an int subtype and
# int == float), so a bare ``json.loads(literal) != value`` gate -- the
# pre-I36 comparison -- stays green for all of them. The hardened generator
# must reject each one.
_TYPE_DRIFT_PAIRS: tuple[tuple[object, str], ...] = (
  (1, "true"),
  (0, "false"),
  (True, "1"),
  (False, "0"),
  (1.0, "1"),
  (1, "1.0"),
  ([0, 1], "[false, true]"),
  ({"flag": 1}, '{"flag": true}'),
)


@pytest.mark.parametrize(("composed_value", "literal"), _TYPE_DRIFT_PAIRS)
def test_literal_override_type_drift_is_rejected_where_plain_equality_passes(
  composed_value: object, literal: str
) -> None:
  # Defect injection: prove the pair is genuinely hazardous -- the pre-fix
  # plain-equality gate would accept it silently.
  assert json.loads(literal) == composed_value

  entry = _synthetic_matrix_entry(
    "synthetic_type_drift_probe_v1",
    {"synthetic_field": composed_value},
    RenderStyle(literal_overrides={("synthetic_field",): literal}),
  )
  with pytest.raises(ValueError, match="does not equal the composed"):
    experiment_matrix_generate.render_entry_bytes(entry)


def test_literal_override_type_drift_is_rejected_at_nested_paths() -> None:
  entry = _synthetic_matrix_entry(
    "synthetic_nested_type_drift_probe_v1",
    {"synthetic_block": {"flag": 1}},
    RenderStyle(literal_overrides={("synthetic_block", "flag"): "true"}),
  )
  with pytest.raises(ValueError, match="does not equal the composed"):
    experiment_matrix_generate.render_entry_bytes(entry)


def test_literal_override_with_matching_type_still_renders_verbatim() -> None:
  """Positive control pinning the real corpus dialect: a float-for-float
  literal (the ten-entry plain-decimal learning rate) must keep working."""
  entry = _synthetic_matrix_entry(
    "synthetic_decimal_literal_probe_v1",
    {"synthetic_field": 3e-05},
    RenderStyle(literal_overrides={("synthetic_field",): "0.00003"}),
  )
  rendered = experiment_matrix_generate.render_entry_bytes(entry).decode("utf-8")
  assert '"synthetic_field": 0.00003' in rendered


# --- Residual (c): experiment -> scenario mapping completeness ------------


def test_scenario_pairing_gate_detects_swap_drop_and_unregistered_addition(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """Inject the three drift shapes existence-only checks cannot see and
  prove the reviewed pairing table goes red on each of them.

  The earlier regression test only compared two local dict copies; it stays
  green under any registry or gate regression. This test drives the actual
  detection path: a patched ``MATRIX_ENTRIES`` flows through
  ``manifest_payload()`` -- the same projection the freshness gate asserts
  against -- and is judged by the same reviewed table.
  """
  gate = _load_freshness_gate_module()
  expected: dict[str, str] = gate.EXPECTED_EXPERIMENT_SCENARIOS

  def pairing() -> dict[str, str]:
    payload = experiment_matrix_generate.manifest_payload()
    return {entry["experiment_id"]: entry["scenario"] for entry in payload["entries"]}

  # Baseline: the live registry equals the reviewed table in both
  # directions (no missing and no unreviewed experiments).
  assert pairing() == expected

  # (1) Swap two experiments across two real scenario files.
  first = MATRIX_ENTRIES[0]
  second = next(
    entry
    for entry in MATRIX_ENTRIES
    if entry.experiment.scenario.path != first.experiment.scenario.path
  )
  swapped_entries: list[MatrixEntry] = []
  for entry in MATRIX_ENTRIES:
    if entry is first:
      target = second.experiment.scenario
    elif entry is second:
      target = first.experiment.scenario
    else:
      swapped_entries.append(entry)
      continue
    swapped_entries.append(
      dataclasses.replace(
        entry, experiment=dataclasses.replace(entry.experiment, scenario=target)
      )
    )
  monkeypatch.setattr(
    experiment_matrix_generate, "MATRIX_ENTRIES", tuple(swapped_entries)
  )
  swapped = pairing()
  # The defect is invisible to per-entry existence checks: every referenced
  # scenario is still a real file.
  for scenario in swapped.values():
    assert (REPO_ROOT / scenario).is_file(), scenario
  assert swapped != expected
  drifted = {key for key in expected if swapped[key] != expected[key]}
  assert drifted == {
    first.experiment.experiment_id,
    second.experiment.experiment_id,
  }

  # (2) Drop one experiment: completeness must fail in the missing
  # direction, not just on value mismatches.
  monkeypatch.setattr(
    experiment_matrix_generate, "MATRIX_ENTRIES", MATRIX_ENTRIES[:-1]
  )
  dropped = pairing()
  assert set(expected) - set(dropped) == {MATRIX_ENTRIES[-1].experiment.experiment_id}
  assert dropped != expected

  # (3) Add an unreviewed experiment pointing at a real scenario file:
  # completeness must fail in the extra direction too.
  extra = _synthetic_matrix_entry(
    "synthetic_unregistered_probe_v1", {}, RenderStyle()
  )
  monkeypatch.setattr(
    experiment_matrix_generate, "MATRIX_ENTRIES", MATRIX_ENTRIES + (extra,)
  )
  added = pairing()
  assert (REPO_ROOT / added["synthetic_unregistered_probe_v1"]).is_file()
  assert set(added) - set(expected) == {"synthetic_unregistered_probe_v1"}
  assert added != expected
