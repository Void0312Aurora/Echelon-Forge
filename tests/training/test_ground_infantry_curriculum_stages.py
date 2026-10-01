"""Curriculum S1/S2 stage runner over the native single-soldier probe.

Stage configs are data; admission thresholds resolve by key from the retained
field-acceptance report; the scripted heading-to-goal baseline must satisfy
each stage's acceptance block. The optional PPO smoke is pipeline evidence
only, not a learning result.
"""

from __future__ import annotations

import json

import pytest

from python.rl.ground.curriculum import (
    DEFAULT_STAGES_PATH,
    CurriculumStageError,
    load_stage_config,
    run_stage,
    stage_cases,
)
from python.rl.ground.fixture_cases import ArnisInfantryFixture


_CONTRACT = (
    DEFAULT_STAGES_PATH.parent / "eastern_plain_infantry_single_v1.contract.json"
)


@pytest.fixture(scope="module")
def config() -> dict:
    return load_stage_config()


# The fixture view, its derived cases, and the scripted rollouts are session
# fixtures (tests/training/conftest.py) shared with the acceptance matrix, so
# a stage row reuses the matrix's rollout of the same case and seed.
@pytest.fixture
def fixture(ground_infantry_fixture: ArnisInfantryFixture) -> ArnisInfantryFixture:
    return ground_infantry_fixture


def test_stage_config_is_native_probe_tooling_aligned_with_the_training_contract(config: dict) -> None:
    contract = json.loads(_CONTRACT.read_text(encoding="utf-8"))
    curriculum = {stage["stage"]: stage for stage in contract["curriculum"]}
    assert config["authority"] == "native_probe_only"
    assert config["production_boundary"] == "not_world_batch"
    assert config["env"]["reward"] == "native_env_contract_unchanged"
    assert config["env"]["termination"] == "native_env_contract_unchanged"
    assert [stage["stage"] for stage in config["stages"]] == ["S1_flat_waypoint", "S2_terrain_cost"]
    for stage in config["stages"]:
        assert stage["contract_goal"] == curriculum[stage["stage"]]["goal"]
    assert {"route_planning", "line_of_sight", "cover", "sensing", "multi_agent"} <= set(config["held"])


def test_stage_thresholds_are_sourced_from_field_acceptance(config: dict, fixture: ArnisInfantryFixture) -> None:
    for stage in config["stages"]:
        for key in ("max_segment_slope", "landcover_codes"):
            reference = stage["admit"][key]
            if reference is None:
                continue
            section = reference["source"].split(".", 1)[1]
            assert reference["key"] in fixture.field_acceptance[section]


def test_s1_admits_only_flat_open_reach_cases(
    config: dict, fixture: ArnisInfantryFixture, ground_acceptance_cases
) -> None:
    cases, rejected = stage_cases(
        "S1_flat_waypoint", config=config, fixture=fixture, cases=ground_acceptance_cases
    )
    threshold = fixture.field_acceptance["thresholds"]["max_slope_p95_deg"]
    open_codes = set(fixture.field_acceptance["landcover"]["open_landcover_codes"])
    assert cases
    for case in cases:
        assert case.expected == "reach"
        assert not case.requires_bridge_admission
        cells = fixture.segment_cells(case)
        assert max(fixture.stride_slope_at(cell) for cell in cells) <= threshold
        assert {int(fixture.landcover[cell]) for cell in cells} <= open_codes
    assert all(case_id in rejected for case_id in ("bridge:0:0:crossing", "landcover:tree_cover"))


def test_s2_admits_terrain_cost_bridge_and_blocked_cases_but_not_held(
    config: dict, fixture: ArnisInfantryFixture, ground_acceptance_cases
) -> None:
    cases, rejected = stage_cases(
        "S2_terrain_cost", config=config, fixture=fixture, cases=ground_acceptance_cases
    )
    categories = {case.category for case in cases}
    assert {"slope_band", "water_or_obstacle", "bridge"} <= categories
    assert {case.expected for case in cases} == {"reach", "block"}
    assert all(case_id.startswith("held:") for case_id in rejected)


def test_unknown_stage_fails_closed(
    config: dict, fixture: ArnisInfantryFixture, ground_acceptance_cases
) -> None:
    with pytest.raises(CurriculumStageError, match="unknown curriculum stage"):
        stage_cases(
            "S3_tree_line_and_settlement_observation",
            config=config,
            fixture=fixture,
            cases=ground_acceptance_cases,
        )


def test_unsourced_threshold_fails_closed(
    config: dict, fixture: ArnisInfantryFixture, ground_acceptance_cases
) -> None:
    tampered = json.loads(json.dumps(config))
    tampered["stages"][0]["admit"]["max_segment_slope"] = {"source": "inline", "key": "max_slope_p95_deg"}
    with pytest.raises(CurriculumStageError, match="unsupported threshold source"):
        stage_cases("S1_flat_waypoint", config=tampered, fixture=fixture, cases=ground_acceptance_cases)


@pytest.mark.parametrize("stage_id", ["S1_flat_waypoint", "S2_terrain_cost"])
def test_scripted_baseline_satisfies_each_stage(
    config: dict,
    fixture: ArnisInfantryFixture,
    ground_acceptance_cases,
    ground_acceptance_seed: int,
    ground_rollouts: dict,
    ground_acceptance_matrix: dict,
    stage_id: str,
) -> None:
    report = run_stage(
        stage_id,
        seed=ground_acceptance_seed,
        config=config,
        fixture=fixture,
        cases=ground_acceptance_cases,
        rollouts=ground_rollouts,
    )
    matrix_rows = {row["case_id"]: row for row in ground_acceptance_matrix["rows"]}
    failing = {row["case_id"]: row["failures"] for row in report["rows"] if row["verdict"] != "pass"}
    assert not failing, failing
    assert report["valid"] is True
    assert report["authority"] == "native_probe_only"
    assert report["baseline"]["pass"] == report["admitted_cases"]
    for row in report["rows"]:
        assert (row["termination_reason"] is None) != (row["truncation_reason"] is None)
        # A stage row is the matrix row of the same case and seed, plus the
        # stage's own acceptance gates.
        assert row["trace_sha256"] == matrix_rows[row["case_id"]]["trace_sha256"]
    if stage_id == "S1_flat_waypoint":
        assert report["baseline"]["block"] == 0
    else:
        assert report["baseline"]["block"] > 0
        assert report["open_decisions"]


def test_stage_ppo_smoke_consumes_the_native_stage_env(
    config: dict, fixture: ArnisInfantryFixture, ground_acceptance_cases, ground_acceptance_seed: int
) -> None:
    pytest.importorskip("stable_baselines3")
    from python.rl.ground.curriculum import ppo_smoke

    cases, _rejected = stage_cases(
        "S1_flat_waypoint", config=config, fixture=fixture, cases=ground_acceptance_cases
    )
    smoke = ppo_smoke(cases[0], seed=ground_acceptance_seed, total_timesteps=8)
    assert smoke["total_timesteps"] == 8
    assert smoke["claim"] == "pipeline_smoke_only_not_a_learning_result"
