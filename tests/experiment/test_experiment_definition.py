from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from python.experiment.air_combat_matrix import (
  CONFIG_BASE_ID,
  EVALUATION_PROTOCOLS,
  MATRIX_DIR,
  MATRIX_ENTRIES,
  REGISTRY,
  composed_config,
)
from python.experiment.composition import (
  compose_config,
  ensure_json_value,
  freeze_json_mapping,
  normalize_trailing_keys,
)
from python.experiment.definition import (
  ConfigComposition,
  EvaluationProtocol,
  Experiment,
  ExperimentRegistry,
  ScenarioRef,
  SeedSpec,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _experiment(
  experiment_id: str = "example_experiment_v1",
  scenario: str = "scenarios/example/example_v1.json",
  base_id: str = "example_base_v1",
  delta: dict | None = None,
  seeds: SeedSpec | None = None,
  protocol: str = "probe",
) -> Experiment:
  return Experiment(
    experiment_id=experiment_id,
    scenario=ScenarioRef(scenario),
    config=ConfigComposition(base_id, delta or {}),
    seeds=seeds or SeedSpec(),
    evaluation_protocol=protocol,
  )


class TestScenarioRef:
  def test_accepts_repo_relative_posix_json_path(self) -> None:
    assert ScenarioRef("scenarios/air_combat/a_v1.json").path.endswith(".json")

  @pytest.mark.parametrize(
    "path",
    [
      "",
      "/abs/scenario.json",
      "C:/abs/scenario.json",
      "scenarios\\air_combat\\a_v1.json",
      "scenarios/../secrets.json",
      "scenarios//a_v1.json",
      "scenarios/a_v1.yaml",
    ],
  )
  def test_rejects_illegal_paths(self, path: str) -> None:
    with pytest.raises(ValueError):
      ScenarioRef(path)


class TestSeedSpec:
  def test_normalize_sorts_and_deduplicates(self) -> None:
    assert SeedSpec.normalize([7, 1, 7, 3, 1]).values == (1, 3, 7)

  def test_empty_seed_set_is_legal_and_normal(self) -> None:
    assert SeedSpec().values == ()
    assert SeedSpec.normalize([]).values == ()

  def test_direct_construction_requires_normal_form(self) -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
      SeedSpec((3, 1))
    with pytest.raises(ValueError, match="strictly increasing"):
      SeedSpec((1, 1))

  @pytest.mark.parametrize("bad", [True, 1.5, "1", None])
  def test_rejects_non_int_seeds(self, bad: object) -> None:
    with pytest.raises(TypeError):
      SeedSpec.normalize([bad])  # type: ignore[list-item]

  def test_rejects_negative_seeds(self) -> None:
    with pytest.raises(ValueError, match="non-negative"):
      SeedSpec((-1,))


class TestConfigComposition:
  def test_delta_is_deep_frozen(self) -> None:
    composition = ConfigComposition("base_v1", {"env": {"action_mode": "full"}})
    with pytest.raises(TypeError):
      composition.delta["env"]["action_mode"] = "other"  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
      composition.base_id = "other"  # type: ignore[misc]

  def test_rejects_illegal_base_id(self) -> None:
    with pytest.raises(ValueError, match="config base id"):
      ConfigComposition("Not-Valid", {})

  def test_rejects_non_json_delta_values(self) -> None:
    with pytest.raises(TypeError, match="unsupported JSON value type"):
      ConfigComposition("base_v1", {"weights": {1, 2}})
    with pytest.raises(ValueError, match="non-finite float"):
      ConfigComposition("base_v1", {"coef": float("nan")})
    with pytest.raises(TypeError, match="non-empty strings"):
      ConfigComposition("base_v1", {1: "x"})  # type: ignore[dict-item]

  def test_ensure_json_value_reports_offending_path(self) -> None:
    with pytest.raises(TypeError, match=r"hyperparameters\.policy_kwargs"):
      ensure_json_value({"hyperparameters": {"policy_kwargs": object()}})


class TestExperimentValidation:
  def test_valid_experiment_constructs(self) -> None:
    experiment = _experiment()
    assert experiment.config.base_id == "example_base_v1"

  def test_rejects_illegal_experiment_id(self) -> None:
    with pytest.raises(ValueError, match="experiment id"):
      _experiment(experiment_id="Bad Id")

  def test_rejects_untyped_axes(self) -> None:
    with pytest.raises(TypeError, match="ScenarioRef"):
      Experiment("x_v1", "scenarios/a.json", ConfigComposition("b_v1"), SeedSpec(), "probe")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SeedSpec"):
      Experiment(
        "x_v1",
        ScenarioRef("scenarios/a.json"),
        ConfigComposition("b_v1"),
        (1, 2),  # type: ignore[arg-type]
        "probe",
      )


class TestExperimentRegistry:
  def _registry(self) -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.register_config_base("example_base_v1", {"n_envs": 4})
    registry.register_evaluation_protocol(EvaluationProtocol("probe"))
    return registry

  def test_registration_round_trip(self) -> None:
    registry = self._registry()
    registry.register_experiment(_experiment())
    assert registry.experiment("example_experiment_v1").evaluation_protocol == "probe"
    assert registry.config_base_ids == ("example_base_v1",)
    assert registry.evaluation_protocol_names == ("probe",)

  def test_duplicate_registrations_fail_fast(self) -> None:
    registry = self._registry()
    with pytest.raises(ValueError, match="duplicate config base"):
      registry.register_config_base("example_base_v1", {})
    with pytest.raises(ValueError, match="duplicate evaluation protocol"):
      registry.register_evaluation_protocol(EvaluationProtocol("probe"))
    registry.register_experiment(_experiment())
    with pytest.raises(ValueError, match="duplicate experiment"):
      registry.register_experiment(_experiment())

  def test_dangling_references_fail_fast(self) -> None:
    registry = self._registry()
    with pytest.raises(ValueError, match="unregistered config base"):
      registry.register_experiment(_experiment(base_id="missing_base_v1"))
    with pytest.raises(ValueError, match="unregistered evaluation protocol"):
      registry.register_experiment(_experiment(protocol="missing_protocol"))

  def test_unknown_lookups_raise_key_error(self) -> None:
    registry = self._registry()
    with pytest.raises(KeyError):
      registry.config_base("missing")
    with pytest.raises(KeyError):
      registry.evaluation_protocol("missing")
    with pytest.raises(KeyError):
      registry.experiment("missing")

  def test_registered_base_is_frozen(self) -> None:
    registry = self._registry()
    with pytest.raises(TypeError):
      registry.config_base("example_base_v1")["n_envs"] = 8  # type: ignore[index]


class TestComposeConfig:
  BASE = {"a": 1, "nested": {"x": 1, "y": 2}, "tail": True}

  def test_merge_is_deterministic_and_repeatable(self) -> None:
    delta = {"nested": {"z": 3, "x": 9}, "new_key": "v"}
    first = compose_config(self.BASE, delta)
    second = compose_config(self.BASE, delta)
    assert first == second
    assert list(first) == list(second) == ["a", "nested", "tail", "new_key"]
    assert list(first["nested"]) == ["x", "y", "z"]

  def test_override_keeps_base_position_and_novel_keys_append_in_delta_order(self) -> None:
    merged = compose_config(self.BASE, {"second_new": 2, "a": 5, "first_new": 1})
    assert list(merged) == ["a", "nested", "tail", "second_new", "first_new"]
    assert merged["a"] == 5

  def test_non_mapping_values_replace_wholesale(self) -> None:
    merged = compose_config({"arr": [1, 2, 3], "nested": {"x": 1}}, {"arr": [9], "nested": 7})
    assert merged["arr"] == [9]
    assert merged["nested"] == 7

  def test_inputs_are_not_mutated_and_output_is_detached(self) -> None:
    base = {"nested": {"x": 1}}
    delta = {"nested": {"y": 2}}
    merged = compose_config(base, delta)
    merged["nested"]["x"] = 99
    assert base == {"nested": {"x": 1}}
    assert delta == {"nested": {"y": 2}}

  def test_frozen_mappings_compose(self) -> None:
    frozen_base = freeze_json_mapping({"nested": {"x": 1}, "arr": [1, 2]})
    merged = compose_config(frozen_base, freeze_json_mapping({"nested": {"y": 2}}))
    assert merged == {"nested": {"x": 1, "y": 2}, "arr": [1, 2]}
    assert isinstance(merged["arr"], list)


class TestNormalizeTrailingKeys:
  SPEC = {(): ("hyperparameters",), ("hyperparameters",): ("device", "policy_kwargs")}

  def test_moves_declared_keys_last_in_declared_order(self) -> None:
    config = {
      "hyperparameters": {"device": "cuda", "lr": 0.1, "policy_kwargs": {"k": 1}},
      "env": {},
    }
    normalized = normalize_trailing_keys(config, self.SPEC)
    assert list(normalized) == ["env", "hyperparameters"]
    assert list(normalized["hyperparameters"]) == ["lr", "device", "policy_kwargs"]

  def test_idempotent_and_missing_keys_are_skipped(self) -> None:
    config = {"env": {"a": 1}}
    once = normalize_trailing_keys(config, self.SPEC)
    twice = normalize_trailing_keys(once, self.SPEC)
    assert once == twice == {"env": {"a": 1}}


class TestAirCombatMatrixRegistry:
  def test_matrix_registers_exactly_the_on_disk_files(self) -> None:
    registered = {entry.output_path for entry in MATRIX_ENTRIES}
    on_disk = {
      path.relative_to(REPO_ROOT).as_posix()
      for path in (REPO_ROOT / MATRIX_DIR).glob("*.json")
    }
    assert len(MATRIX_ENTRIES) == 24
    assert registered == on_disk

  def test_experiment_axes_follow_matrix_facts(self) -> None:
    protocol_counts = {"smoke": 0, "probe": 0}
    for entry in MATRIX_ENTRIES:
      experiment = entry.experiment
      assert experiment.config.base_id == CONFIG_BASE_ID
      assert experiment.seeds.values == ()
      assert (REPO_ROOT / experiment.scenario.path).is_file(), experiment.scenario.path
      protocol_counts[experiment.evaluation_protocol] += 1
    assert protocol_counts == {"smoke": 2, "probe": 22}
    assert {protocol.name for protocol in EVALUATION_PROTOCOLS} == {"smoke", "probe"}

  def test_composed_configs_match_checked_in_content(self) -> None:
    for entry in MATRIX_ENTRIES:
      checked_in = json.loads((REPO_ROOT / entry.output_path).read_text(encoding="utf-8"))
      assert composed_config(entry) == checked_in, entry.output_path

  def test_literal_overrides_round_trip_to_composed_values(self) -> None:
    for entry in MATRIX_ENTRIES:
      config = composed_config(entry)
      for path, literal in entry.render.literal_overrides.items():
        value: object = config
        for key in path:
          value = value[key]  # type: ignore[index]
        assert json.loads(literal) == value, (entry.output_path, path)

  def test_registry_is_reconstructible_and_frozen(self) -> None:
    from python.experiment.air_combat_matrix import build_registry

    rebuilt = build_registry()
    assert {e.experiment_id for e in rebuilt.experiments} == {
      e.experiment_id for e in REGISTRY.experiments
    }
    with pytest.raises(TypeError):
      REGISTRY.config_base(CONFIG_BASE_ID)["n_envs"] = 8  # type: ignore[index]
    sample = MATRIX_ENTRIES[0].experiment
    with pytest.raises(TypeError):
      sample.config.delta["env"]["action_mode"] = "hacked"  # type: ignore[index]
