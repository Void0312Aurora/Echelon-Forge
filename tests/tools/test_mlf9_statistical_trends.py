from __future__ import annotations

import math
from statistics import NormalDist

import pytest
from tools.diagnostics import mlf9_statistical_trends as mlf9


def _row(chain_id: int, stage: str, **overrides):
    row = {
        "episode": chain_id,
        "step": 1,
        "sim_time_s": float(chain_id),
        "chain_id": chain_id,
        "event_id": chain_id * 10,
        "parent_event_id": 0,
        "stage": stage,
        "source_event_kind": f"{stage}Fixture",
        "source_event_id": chain_id * 10,
        "munition_id": 100 + chain_id,
        "target_id": 200,
        "evidence_level": "training_synthetic",
        "observation_mode": "sampled_runtime",
        "consumer_visibility": "diagnostics_and_training",
        "miss_distance_m": math.nan,
        "fuze_triggered": 1,
    }
    row.update(overrides)
    return row


def _fixture_rows():
    return [
        _row(1, "nearest_approach", miss_distance_m=4.0),
        _row(1, "fuze", fuze_triggered=1),
        _row(1, "warhead_mechanism", mechanism_family="blast_fragmentation"),
        _row(1, "component_damage", component_system="flight_control"),
        _row(
            1,
            "structural_breakup",
            break_mode="wing_loss",
            detached_part_ref="left_wing",
            detached_part_count=1,
            airframe_breakup=1,
        ),
        _row(1, "platform_consequence", mission_kill=1),
        _row(1, "lifecycle", lifecycle_terminal=1, ground_lifecycle="crashed_wreck"),
        _row(2, "nearest_approach", miss_distance_m=12.0),
        _row(2, "fuze", fuze_triggered=1),
        _row(2, "component_damage", component_system="flight_control"),
        _row(2, "platform_consequence", mission_kill=0),
        _row(3, "nearest_approach", miss_distance_m=40.0),
        _row(3, "fuze", fuze_triggered=0, reason="fuze_no_detonation"),
    ]


def _rate(payload, outcome: str, denominator: str):
    rates = payload["groups"][0]["rates"]
    return next(
        item
        for item in rates
        if item["outcome"] == outcome and item["denominator"] == denominator
    )


def test_mlf9_summary_reports_denominators_outcomes_and_non_claims():
    payload = mlf9.summarize_trends(
        _fixture_rows(),
        sample_source="controlled_fixture_rows",
        report_surface="unit_test_retained_artifact",
    )
    group = payload["groups"][0]

    assert payload["schema_version"] == "mlf9.statistical_trends.v1"
    assert math.isclose(
        payload["confidence_z"],
        NormalDist().inv_cdf((1.0 + payload["confidence_level"]) / 2.0),
    )
    assert payload["sample_source"] == "controlled_fixture_rows"
    assert payload["report_surface"] == "unit_test_retained_artifact"
    assert payload["source_row_count"] == len(_fixture_rows())
    assert payload["authority_boundary"]["synthetic_simulation_trend"] is True
    assert payload["authority_boundary"]["real_world_pk"] is False
    assert group["denominator_counts"]["chain_count"] == 3
    assert group["denominator_counts"]["component_damage_chain_count"] == 2
    assert group["denominator_counts"]["structural_breakup_chain_count"] == 1
    assert group["outcome_counts"]["fuze_negative"] == 1
    assert group["outcome_counts"]["effective_component_damage"] == 2
    assert group["outcome_counts"]["structural_breakup"] == 1
    assert group["outcome_counts"]["airframe_breakup"] == 1
    assert group["outcome_counts"]["terminal_lifecycle"] == 1

    structural_given_component = _rate(
        payload, "structural_breakup", "component_damage_chain_count"
    )
    assert structural_given_component["success_count"] == 1
    assert structural_given_component["sample_count"] == 2
    assert structural_given_component["rate"] == 0.5
    assert 0.0 <= structural_given_component["ci_low"] <= structural_given_component["ci_high"] <= 1.0

    terminal_given_structural = _rate(
        payload, "terminal_lifecycle", "structural_breakup_chain_count"
    )
    assert terminal_given_structural["success_count"] == 1
    assert terminal_given_structural["sample_count"] == 1
    assert terminal_given_structural["rate"] == 1.0


def test_mlf9_summary_keeps_duplicate_chain_ids_separate_across_episodes():
    rows = [
        _row(301, "nearest_approach", episode=0, event_id=1, source_event_id=1),
        _row(301, "fuze", episode=0, event_id=2, source_event_id=2, fuze_triggered=1),
        _row(
            301,
            "nearest_approach",
            episode=1,
            event_id=11,
            source_event_id=11,
            miss_distance_m=18.0,
        ),
        _row(
            301,
            "fuze",
            episode=1,
            event_id=12,
            source_event_id=12,
            fuze_triggered=0,
            reason="fuze_no_detonation",
        ),
    ]

    payload = mlf9.summarize_trends(rows)
    group = payload["groups"][0]

    assert payload["chain_count"] == 2
    assert group["denominator_counts"]["chain_count"] == 2
    assert group["outcome_counts"]["fuze_negative"] == 1
    assert group["chain_ids"] == [301, 301]
    assert group["chain_identities"] == [
        {"episode": 0, "chain_id": 301},
        {"episode": 1, "chain_id": 301},
    ]


def test_mlf9_summary_rejects_invalid_confidence_levels():
    with pytest.raises(ValueError, match="confidence_level"):
        mlf9.summarize_trends(_fixture_rows(), confidence_level=1.5)

    with pytest.raises(ValueError, match="confidence_level"):
        mlf9.summarize_trends(_fixture_rows(), confidence_level=0.0)


def test_mlf9_summary_uses_requested_confidence_level_exactly():
    payload = mlf9.summarize_trends(_fixture_rows(), confidence_level=0.975)

    assert payload["confidence_level"] == 0.975
    assert math.isclose(
        payload["confidence_z"],
        NormalDist().inv_cdf((1.0 + 0.975) / 2.0),
    )


def test_mlf9_summary_can_group_by_miss_distance_bucket_and_break_mode():
    payload = mlf9.summarize_trends(
        _fixture_rows(),
        group_by=mlf9.normalize_group_by("miss_distance_bucket, break_mode"),
    )
    groups = {tuple(group["group"].items()): group for group in payload["groups"]}

    near_wing = groups[
        (
            ("miss_distance_bucket", "near_0_5m"),
            ("break_mode", "wing_loss"),
        )
    ]
    far_unknown = groups[
        (
            ("miss_distance_bucket", "far_gt_35m"),
            ("break_mode", "unknown"),
        )
    ]

    assert near_wing["denominator_counts"]["chain_count"] == 1
    assert near_wing["outcome_counts"]["structural_breakup"] == 1
    assert far_unknown["denominator_counts"]["chain_count"] == 1
    assert far_unknown["outcome_counts"]["fuze_negative"] == 1
