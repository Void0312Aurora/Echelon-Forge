from __future__ import annotations

import copy
import json

from tools.diagnostics import kill_chain_decoupling_probe as probe


def test_guidance_case_generates_decoupled_stage_abstractions(tmp_path) -> None:
  report = probe.generate_report(
    guidance_cases=(
      {
        "case_id": "aim120_8km_right_30deg_smoke",
        "range_m": 8000.0,
        "bearing_deg": 30.0,
      },
    ),
    proximity_distances_m=(),
    include_guidance=True,
    include_proximity=False,
  )

  assert report["schema_version"] == "a2.kill_chain_decoupling_probe.v1"
  assert report["authority_boundary"]["runtime_dto_authority"] is True
  assert report["authority_boundary"]["runtime_parameter_retuning"] is False
  assert report["authority_boundary"]["calibration_authority"] is False
  audit = report["completion_audit"]
  assert audit["schema_version"] == "a2.kill_chain_completion_audit.v1"
  assert audit["goal_complete"] is False
  assert "P6" not in audit["blocked_item_ids"]
  audit_rows = {str(row["item_id"]): row for row in audit["items"]}
  assert audit_rows["P0"]["closed"] is True
  assert audit_rows["P6"]["status"] == "closed"
  assert audit_rows["P6"]["closed"] is True
  assert audit_rows["P6"]["partial_surface_closed"] is True
  assert (
    audit_rows["P6"]["evidence"]["engineering_proxy_evidence_present"]
    is True
  )
  assert audit_rows["P6"]["evidence"]["engineering_proxy_record_count"] == 2
  admission = report["calibration_admission"]
  assert admission["schema_version"] == "a2.kill_chain_calibration_admission.v1"
  assert admission["admission_granted"] is True
  assert admission["admission_mode"] == "engineering_proxy_single_layer_guarded"
  assert admission["prerequisites"]["stage_report_available"] is True
  assert admission["prerequisites"]["runtime_dto_authority"] is True
  assert admission["prerequisites"]["component_response_rows_available"] is True
  assert (
    admission["prerequisites"]["legacy_fuze_quality_damage_multiplier_removed"]
    is True
  )
  assert admission["prerequisites"]["load_rows_response_owner_clean"] is True
  assert (
    admission["prerequisites"]["external_calibration_evidence_present"]
    is True
  )
  assert admission["external_evidence"]["report_available"] is True
  assert (
    admission["external_evidence"]["report_schema_version"]
    == "mlf10.calibration_admission_report.v1"
  )
  assert admission["external_evidence"]["admitted_record_count"] == 0
  assert admission["external_evidence"]["admitted_authority_fields"] == []
  assert admission["external_evidence"]["engineering_proxy_evidence_present"] is True
  assert admission["external_evidence"]["engineering_proxy_record_count"] == 2
  assert admission["external_evidence"]["engineering_proxy_record_ids"] == [
    "MLF10-CURRENT-MLF6-STRUCTURAL-PROXY",
    "MLF10-CURRENT-MLF9-SYNTHETIC-TRENDS",
  ]
  assert set(admission["external_evidence"]["engineering_proxy_layer_ids"]) == {
    "fuze_data",
    "warhead_data",
    "target_response_data",
    "consequence_data",
  }
  assert admission["external_evidence"]["real_world_authority_blocked_by"] == [
    "no_admitted_external_calibration_evidence"
  ]
  assert "effect_scale_authority" in admission["external_evidence"][
    "missing_authority_fields"
  ]
  gap_rows = {
    str(row["layer_id"]): row
    for row in admission["external_evidence"]["layer_gap_summary"]
  }
  assert gap_rows["warhead_data"]["missing_authority_fields"] == [
    "effect_scale_authority"
  ]
  assert "MLF10-CURRENT-BECO-RECALCULATED-BLAST" in gap_rows["warhead_data"][
    "blocked_evidence_ids"
  ]
  assert (
    gap_rows["warhead_data"]["blocking_reason_counts"]["validation_not_passed"]
    >= 1
  )
  assert admission["external_evidence"]["blocked_by"] == []
  unblock_queue = admission["external_evidence"]["evidence_unblock_queue"]
  assert [row["evidence_id"] for row in unblock_queue] == [
    "MLF10-CURRENT-BECO-RECALCULATED-BLAST",
    "MLF10-CURRENT-STAGE-B-EFFECT-SCALE",
    "MLF10-CURRENT-STAGE-C-COMPONENT-PROBABILITY",
    "MLF10-CURRENT-TP21-SELECTED-DEBRIS",
  ]
  warhead_unblock = {
    row["evidence_id"]: row for row in unblock_queue
  }["MLF10-CURRENT-STAGE-B-EFFECT-SCALE"]
  assert warhead_unblock["target_layer_ids"] == ["warhead_data"]
  assert warhead_unblock["requested_authority_fields"] == [
    "effect_scale_authority"
  ]
  assert warhead_unblock["admission_candidate_after_closeout"] is True
  assert {
    action["reason"] for action in warhead_unblock["unblock_actions"]
  } >= {"rights_not_release_grade_admitted", "validation_not_passed"}
  plan = admission["single_layer_calibration_plan"]
  assert (
    plan["schema_version"]
    == "a2.kill_chain_single_layer_calibration_plan.v1"
  )
  assert plan["plan_available"] is True
  assert plan["admitted_layer_count"] == 4
  assert len(plan["plans"]) == 4
  assert plan["blocked_by"] == []
  assert plan["authority_boundary"]["runtime_parameter_retuning"] is False
  assert plan["authority_boundary"]["calibration_authority"] is False
  assert "p5_load_rows_still_carry_response_fields" not in admission["blocked_by"]
  assert admission["blocked_by"] == []
  assert (
    admission["cross_layer_leakage_guard"]["single_layer_mutation_required"]
    is True
  )
  assert (
    admission["cross_layer_leakage_guard"]["blocked_if_unrelated_stage_changes"]
    is True
  )
  assert {
    str(row["layer_id"]) for row in admission["layer_admission"]
  } == {
    "fuze_data",
    "warhead_data",
    "target_response_data",
    "consequence_data",
  }
  assert {
    str(row["admission_source"]) for row in admission["layer_admission"]
  } == {"engineering_proxy"}
  assert all(
    bool(row["engineering_proxy_admission_granted"])
    for row in admission["layer_admission"]
  )
  report_path = tmp_path / "report.json"
  audit_path = tmp_path / "audit.json"
  report_path.write_text(json.dumps(report), encoding="utf-8")
  assert (
    probe.main(
      [
        "--completion-audit-report",
        str(report_path),
        "--output",
        str(audit_path),
      ]
    )
    == 0
  )
  audit_from_cli = json.loads(audit_path.read_text(encoding="utf-8"))
  assert audit_from_cli["schema_version"] == "a2.kill_chain_completion_audit.v1"
  assert audit_from_cli["goal_complete"] is False
  assert "P6" not in audit_from_cli["blocked_item_ids"]
  assert report["guidance_case_count"] == 1
  case = report["guidance_cases"][0]
  assert case["case_type"] == "aim120_offset_guidance"
  assert float(case["range_m"]) == 8000.0
  assert float(case["bearing_deg"]) == 30.0
  runtime_facade = case["runtime_facade"]
  assert runtime_facade["schema_name"] == "a2.kill_chain_runtime_facade.v1"
  assert runtime_facade["runtime_dto_available"] is True
  assert runtime_facade["runtime_dto_authority"] is True
  assert runtime_facade["runtime_parameter_retuning"] is False
  assert runtime_facade["calibration_authority"] is False
  assert "component_response_runtime_owner_migrated" not in runtime_facade
  assert "component_response_source" not in runtime_facade
  assert runtime_facade["approach_fact"]["owner_stage"] == "approach"
  assert runtime_facade["fuze_decision"]["owner_stage"] == "fuze_decision"
  assert (
    runtime_facade["warhead_load_field"]["owner_stage"]
    == "warhead_load_field"
  )
  assert (
    runtime_facade["target_susceptibility"]["owner_stage"]
    == "target_susceptibility"
  )
  assert (
    runtime_facade["consequence_projection"]["owner_stage"]
    == "consequence_projection"
  )
  assert runtime_facade["component_response_row_count"] > 0
  assert runtime_facade["component_load_row_count"] == (
    runtime_facade["component_response_row_count"]
  )
  runtime_load = runtime_facade["warhead_load_field"]["component_loads"][0]
  assert runtime_load["spatial_intersection_fraction"] is not None
  assert runtime_load["pattern_weight"] is not None
  assert runtime_load["orientation_weight"] is not None
  assert runtime_load["receiver_exposure_fraction"] is not None
  assert runtime_load["armor_transmission"] is not None
  assert runtime_load["sampling_confidence"] is not None
  assert runtime_load["load_intensity_scale"] is not None
  assert (
    runtime_facade["component_responses"][0]["owner_stage"]
    == "component_response"
  )
  assert (
    runtime_facade["component_responses"][0]["source_current_owner_stage"]
    == "component_response_row"
  )
  assert (
    runtime_facade["component_response"]["probability_owner_source"]
    == "effects_event_component_response_rows"
  )
  assert case["decoupled_facade"]["schema_version"] == "a2.kill_chain_decoupled_facade.v1"
  assert case["decoupled_facade"]["facade_status"] == "runtime_dto_backed"
  assert (
    case["decoupled_facade"]["authority_boundary"]["runtime_dto_authority"]
    is True
  )
  assert float(case["nearest_miss_distance_m"]) < 15.0
  assert case["fuze_triggered"] is True
  assert case["effect"]["outcome_state"] in {"damage_applied", "detonated_no_effect"}
  assert case["effect"]["mechanism_armor_scale"] is not None
  assert case["effect"]["mechanism_exposure_scale"] is not None
  assert case["effect"]["component_threshold_scale"] is not None
  assert case["effect"]["vulnerability_effect_scale"] is not None
  assert case["component_load_factor_summary"]["row_count"] > 0
  assert (
    case["component_load_factor_summary"]["authority_boundary"][
      "runtime_parameter_retuning"
    ]
    is False
  )
  assert (
    case["component_load_factor_summary"]["authority_boundary"][
      "calibration_authority"
    ]
    is False
  )
  assert (
    case["component_load_factor_summary"][
      "max_abs_effect_scale_residual_to_load_factor_product_proxy"
    ]
    is not None
  )
  assert (
    case["component_load_factor_summary"]["field_boundary_status"]
    == "diagnostic_boundary_only"
  )
  assert (
    "distance_m"
    in case["component_load_factor_summary"]["load_only_field_names_present"]
  )
  assert (
    "effect_scale"
    in case["component_load_factor_summary"][
      "aggregate_coupled_load_field_names_present"
    ]
  )
  assert (
    case["component_load_factor_summary"][
      "response_field_names_present_on_load_rows"
    ]
    == []
  )
  assert (
    case["component_load_factor_summary"][
      "response_owner_violation_field_counts"
    ]
    == {}
  )
  assert len(case["component_load_factor_rows"]) == int(
    case["effect"]["component_hit_count"]
  )
  factor_row = case["component_load_factor_rows"][0]
  assert factor_row["effect_scale"] is not None
  assert factor_row["load_factor_product_proxy"] is not None
  assert factor_row["effect_scale_ratio_to_load_factor_product_proxy"] is not None
  assert "distance_m" in factor_row["load_only_fields"]
  assert "effect_scale" in factor_row["aggregate_coupled_load_fields"]
  assert factor_row["response_fields"] == []
  assert factor_row["response_owner_violation_fields"] == []
  assert factor_row["authority_boundary"]["calibration_authority"] is False
  facade_response = case["decoupled_facade"]["component_response"]
  assert facade_response["owner_stage"] == "component_response"
  assert facade_response["row_count"] == len(case["component_load_factor_rows"])
  assert facade_response["runtime_dto_authority"] is True
  assert (
    facade_response["probability_owner_source"]
    == "effects_event_component_response_rows"
  )
  assert facade_response["rows"][0]["owner_stage"] == "component_response"
  assert facade_response["rows"][0]["source_current_owner_stage"] == "component_response_row"

  abstraction_stages = {
    str(row["abstraction_stage"]) for row in case["stage_abstractions"]
  }
  assert abstraction_stages == {
    "approach",
    "fuze_decision",
    "warhead_load_field",
    "component_response",
    "consequence_projection",
  }
  assert (
    case["decoupling_summary"]["authority_boundary"]["real_world_pk"] is False
  )
  assert "component_load_row_contains_response_probability" not in (
    case["decoupling_summary"]["coupling_flag_counts"]
  )
  assert "component_response_inferred_from_load_row_candidate" not in (
    case["decoupling_summary"]["coupling_flag_counts"]
  )
  scalar_ids = {str(row["scalar_id"]) for row in case["scalar_coupling_ledger"]}
  assert "effects_event.fuze_quality" in scalar_ids
  assert "effects_event.fuze_quality_damage_multiplier_applied" not in scalar_ids
  assert "effects_event.fuze_quality_damage_multiplier" not in scalar_ids
  assert "effects_event.warhead_damage_scalar_before_fuze_quality" not in scalar_ids
  assert "effects_event.warhead_damage_scalar_after_fuze_quality" not in scalar_ids
  assert "effects_event.spatial_effect_scale" in scalar_ids
  assert "effects_event.mechanism_armor_scale" in scalar_ids
  assert "effects_event.mechanism_exposure_scale" in scalar_ids
  assert "effects_event.component_threshold_scale" in scalar_ids
  assert "effects_event.vulnerability_effect_scale" in scalar_ids
  assert "component_load.effect_scale" in scalar_ids
  assert "component_load.spatial_intersection_fraction" in scalar_ids
  assert "component_load.pattern_weight" in scalar_ids
  assert "component_load.orientation_weight" in scalar_ids
  assert "component_load.receiver_exposure_fraction" in scalar_ids
  assert "component_load.armor_transmission" in scalar_ids
  assert "component_load.sampling_confidence" in scalar_ids
  assert "component_load.load_intensity_scale" in scalar_ids
  assert "component_response.failure_probability" in scalar_ids
  assert "fuze_quality_damage_multiplier_candidate" not in (
    case["scalar_coupling_summary"]["coupling_flag_counts"]
  )
  assert "fuze_quality_damage_multiplier_explicit_policy" not in (
    case["scalar_coupling_summary"]["coupling_flag_counts"]
  )
  assert (
    case["scalar_coupling_summary"]["coupling_flag_counts"][
      "effect_scale_decomposition_factor_available"
    ]
    >= 1
  )
  assert (
    case["scalar_coupling_summary"]["coupling_flag_counts"][
      "component_load_named_factor_available"
    ]
    >= 1
  )
  assert (
    case["scalar_coupling_summary"]["coupling_flag_counts"][
      "vulnerability_response_factor_aggregated_in_effects_event"
    ]
    >= 1
  )
  assert "response_probability_in_load_row" not in (
    case["scalar_coupling_summary"]["coupling_flag_counts"]
  )
  assert "component_response_inferred_from_load_row" not in (
    case["scalar_coupling_summary"]["coupling_flag_counts"]
  )
  assert (
    case["scalar_coupling_summary"]["coupling_flag_counts"][
      "composite_effect_scale_crosses_stage_boundary"
    ]
    >= 1
  )


def test_calibration_admission_consumes_external_report_by_layer(tmp_path) -> None:
  evidence_report = {
    "schema_version": "mlf10.calibration_admission_report.v1",
    "status": "calibration_admission_audit_complete",
    "source_manifest_ref": "synthetic/test_manifest.json",
    "record_count": 1,
    "decision_counts": {
      "engineering_proxy": 0,
      "retained_non_authoritative": 0,
      "calibration_candidate": 0,
      "admitted": 1,
      "rejected": 0,
      "blocked": 0,
    },
    "admitted_authorities": [
      {
        "evidence_id": "SYNTH-WARHEAD",
        "authority_field": "effect_scale_authority",
        "scope": {
          "target_type": "synthetic_target_scope",
          "weapon_family": "synthetic_weapon_scope",
          "mechanism_family": "blast_fragmentation",
          "aspect_bucket": "test",
          "closure_bucket": "test",
          "miss_distance_bucket": "test",
        },
      }
    ],
    "authority_boundary": {
      "admitted_record_count": 1,
      "real_world_pk": False,
      "deterministic_fuze_reliability": False,
      "reward_authority": False,
      "entity_deletion_authority": False,
    },
  }
  evidence_path = tmp_path / "external_evidence_report.json"
  evidence_path.write_text(json.dumps(evidence_report), encoding="utf-8")

  report = probe.generate_report(
    guidance_cases=(
      {
        "case_id": "aim120_8km_right_30deg_evidence_smoke",
        "range_m": 8000.0,
        "bearing_deg": 30.0,
      },
    ),
    proximity_distances_m=(),
    include_guidance=True,
    include_proximity=False,
    external_evidence_report_path=evidence_path,
  )

  admission = report["calibration_admission"]
  assert admission["admission_granted"] is True
  assert admission["admission_mode"] == "admitted_single_layer_guarded"
  assert (
    admission["prerequisites"]["external_calibration_evidence_present"]
    is True
  )
  assert admission["external_evidence"]["admitted_record_count"] == 1
  assert admission["external_evidence"]["admitted_authority_fields"] == [
    "effect_scale_authority"
  ]
  assert admission["external_evidence"]["evidence_unblock_queue"] == []
  assert (
    "effect_scale_authority"
    not in admission["external_evidence"]["missing_authority_fields"]
  )
  gap_rows = {
    str(row["layer_id"]): row
    for row in admission["external_evidence"]["layer_gap_summary"]
  }
  assert gap_rows["warhead_data"]["gap_status"] == "admitted"
  assert gap_rows["warhead_data"]["missing_authority_fields"] == []
  assert gap_rows["fuze_data"]["gap_status"] == "missing_admitted_authority"
  layer_rows = {
    str(row["layer_id"]): row for row in admission["layer_admission"]
  }
  assert layer_rows["warhead_data"]["admission_granted"] is True
  assert layer_rows["warhead_data"]["admitted_authority_fields"] == [
    "effect_scale_authority"
  ]
  assert layer_rows["fuze_data"]["admission_granted"] is False
  assert layer_rows["target_response_data"]["admission_granted"] is False
  assert layer_rows["consequence_data"]["admission_granted"] is False
  plan = admission["single_layer_calibration_plan"]
  assert plan["plan_available"] is True
  assert plan["dry_run_only"] is True
  assert plan["admitted_layer_count"] == 1
  assert plan["blocked_by"] == []
  assert len(plan["plans"]) == 1
  warhead_plan = plan["plans"][0]
  assert warhead_plan["layer_id"] == "warhead_data"
  assert warhead_plan["owner_stage"] == "warhead_load_field"
  assert warhead_plan["mutation_scope"] == "single_layer_only"
  assert warhead_plan["dry_run_only"] is True
  assert warhead_plan["runtime_parameter_retuning"] is False
  assert warhead_plan["default_database_modified"] is False
  assert warhead_plan["admitted_authority_fields"] == ["effect_scale_authority"]
  assert "warhead_load_field" not in warhead_plan["frozen_stage_ids"]
  assert "component_response" in warhead_plan["reject_if_changed_stage_ids"]
  assert (
    warhead_plan["required_comparison"]["unrelated_stage_delta_allowed"]
    is False
  )

  after_report = copy.deepcopy(report)
  for row in after_report["guidance_cases"][0]["stage_abstractions"]:
    if row["abstraction_stage"] == "warhead_load_field":
      row["observed"]["fragment_energy_j"] = (
        float(row["observed"]["fragment_energy_j"]) + 1.0
      )
      break
  guard = probe.calibration_delta_guard(
    report,
    after_report,
    layer_id="warhead_data",
  )
  assert guard["schema_version"] == "a2.kill_chain_calibration_delta_guard.v1"
  assert guard["guard_passed"] is True
  assert guard["target_stage_id"] == "warhead_load_field"
  assert guard["changed_stage_ids"] == ["warhead_load_field"]
  assert guard["blocked_by"] == []
  assert guard["authority_boundary"]["runtime_parameter_retuning"] is False

  bad_after_report = copy.deepcopy(report)
  for row in bad_after_report["guidance_cases"][0]["stage_abstractions"]:
    if row["abstraction_stage"] == "approach":
      row["observed"]["miss_distance_m"] = (
        float(row["observed"]["miss_distance_m"]) + 1.0
      )
      break
  bad_guard = probe.calibration_delta_guard(
    report,
    bad_after_report,
    layer_id="warhead_data",
  )
  assert bad_guard["guard_passed"] is False
  assert "frozen_stage_changed:approach" in bad_guard["blocked_by"]
  assert "target_stage_delta_missing" in bad_guard["blocked_by"]

  before_path = tmp_path / "before_report.json"
  after_path = tmp_path / "after_report.json"
  guard_path = tmp_path / "delta_guard.json"
  before_path.write_text(json.dumps(report), encoding="utf-8")
  after_path.write_text(json.dumps(after_report), encoding="utf-8")
  assert (
    probe.main(
      [
        "--delta-guard-before",
        str(before_path),
        "--delta-guard-after",
        str(after_path),
        "--delta-guard-layer",
        "warhead_data",
        "--output",
        str(guard_path),
      ]
    )
    == 0
  )
  guard_from_cli = json.loads(guard_path.read_text(encoding="utf-8"))
  assert guard_from_cli["schema_version"] == "a2.kill_chain_calibration_delta_guard.v1"
  assert guard_from_cli["guard_passed"] is True
  assert guard_from_cli["changed_stage_ids"] == ["warhead_load_field"]


def test_external_evidence_preflight_cli_reports_unblock_queue(tmp_path) -> None:
  evidence_report = {
    "schema_version": "mlf10.calibration_admission_report.v1",
    "status": "calibration_admission_audit_complete",
    "source_manifest_ref": "synthetic/blocked_manifest.json",
    "record_count": 1,
    "decision_counts": {
      "engineering_proxy": 0,
      "retained_non_authoritative": 0,
      "calibration_candidate": 0,
      "admitted": 0,
      "rejected": 0,
      "blocked": 1,
    },
    "decisions": [
      {
        "evidence_id": "SYNTH-BLOCKED-WARHEAD",
        "classification": "blocked",
        "gate_status": "fail_closed",
        "blocking_reasons": [
          "rights_not_release_grade_admitted",
          "validation_not_passed",
        ],
        "residuals": ["synthetic validation closeout missing"],
        "admitted_authority_fields": [],
        "authority_decisions": {
          "effect_scale_authority": {
            "requested": True,
            "decision": "blocked",
            "reasons": [
              "rights_not_release_grade_admitted",
              "validation_not_passed",
            ],
          }
        },
      }
    ],
    "admitted_authorities": [],
    "authority_boundary": {
      "admitted_record_count": 0,
      "real_world_pk": False,
      "deterministic_fuze_reliability": False,
      "reward_authority": False,
      "entity_deletion_authority": False,
    },
  }
  evidence_path = tmp_path / "blocked_evidence_report.json"
  output_path = tmp_path / "preflight.json"
  evidence_path.write_text(json.dumps(evidence_report), encoding="utf-8")

  assert (
    probe.main(
      [
        "--external-evidence-preflight",
        "--external-evidence-report",
        str(evidence_path),
        "--output",
        str(output_path),
      ]
    )
    == 0
  )
  preflight = json.loads(output_path.read_text(encoding="utf-8"))
  assert (
    preflight["schema_version"]
    == "a2.kill_chain_calibration_evidence_preflight.v1"
  )
  assert preflight["status"] == "blocked_or_missing_evidence"
  assert preflight["evidence_unblock_queue_count"] == 1
  assert preflight["admitted_layer_count"] == 0
  assert preflight["simulation_run_required_for_final_admission"] is True
  assert "external_calibration_evidence_missing" in preflight["blocked_by"]
  queue = preflight["external_evidence"]["evidence_unblock_queue"]
  assert queue[0]["evidence_id"] == "SYNTH-BLOCKED-WARHEAD"
  assert queue[0]["target_layer_ids"] == ["warhead_data"]
  assert queue[0]["requested_authority_fields"] == ["effect_scale_authority"]
  assert {
    action["reason"] for action in queue[0]["unblock_actions"]
  } == {
    "residuals_present",
    "rights_not_release_grade_admitted",
    "validation_not_passed",
  }
  gap_rows = {
    str(row["layer_id"]): row
    for row in preflight["external_evidence"]["layer_gap_summary"]
  }
  assert gap_rows["warhead_data"]["related_evidence_ids"] == [
    "SYNTH-BLOCKED-WARHEAD"
  ]
  assert gap_rows["fuze_data"]["related_evidence_ids"] == []


def test_external_evidence_preflight_accepts_supplemental_authority_fields(
  tmp_path,
) -> None:
  evidence_report = {
    "schema_version": "mlf10.calibration_admission_report.v1",
    "status": "calibration_admission_audit_complete",
    "source_manifest_ref": "synthetic/supplemental_admission.json",
    "record_count": 2,
    "decision_counts": {
      "engineering_proxy": 0,
      "retained_non_authoritative": 0,
      "calibration_candidate": 0,
      "admitted": 2,
      "rejected": 0,
      "blocked": 0,
    },
    "admitted_authorities": [
      {
        "evidence_id": "SYNTH-FUZE",
        "authority_field": "deterministic_fuze_authority",
        "scope": {"decision_scope": "detonation_decision"},
      },
      {
        "evidence_id": "SYNTH-CONSEQUENCE",
        "authority_field": "pk_authority",
        "scope": {"decision_scope": "simulation_consequence_projection"},
      },
    ],
    "authority_boundary": {
      "admitted_record_count": 2,
      "real_world_pk": False,
      "deterministic_fuze_reliability": False,
      "reward_authority": False,
      "entity_deletion_authority": False,
    },
  }
  evidence_path = tmp_path / "supplemental_admission_report.json"
  output_path = tmp_path / "supplemental_preflight.json"
  evidence_path.write_text(json.dumps(evidence_report), encoding="utf-8")

  assert (
    probe.main(
      [
        "--external-evidence-preflight",
        "--external-evidence-report",
        str(evidence_path),
        "--output",
        str(output_path),
      ]
    )
    == 0
  )
  preflight = json.loads(output_path.read_text(encoding="utf-8"))
  assert preflight["status"] == "admitted_evidence_available"
  assert preflight["blocked_by"] == []
  assert preflight["admitted_layer_count"] == 2
  assert preflight["missing_layer_count"] == 2
  assert preflight["external_evidence"]["admitted_authority_fields"] == [
    "deterministic_fuze_authority",
    "pk_authority",
  ]
  gap_rows = {
    str(row["layer_id"]): row
    for row in preflight["external_evidence"]["layer_gap_summary"]
  }
  assert gap_rows["fuze_data"]["gap_status"] == "admitted"
  assert gap_rows["consequence_data"]["gap_status"] == "admitted"
  assert gap_rows["warhead_data"]["gap_status"] == "missing_admitted_authority"
  assert (
    gap_rows["target_response_data"]["gap_status"]
    == "missing_admitted_authority"
  )
  layer_rows = {
    str(row["layer_id"]): row
    for row in preflight["layer_admission_if_runtime_prerequisites_clean"]
  }
  assert layer_rows["fuze_data"]["admission_granted"] is True
  assert layer_rows["consequence_data"]["admission_granted"] is True
  assert layer_rows["warhead_data"]["admission_granted"] is False
  assert layer_rows["target_response_data"]["admission_granted"] is False


def test_external_evidence_template_cli_marks_eligible_and_separate_contract_layers(
  tmp_path,
) -> None:
  output_path = tmp_path / "evidence_template.json"
  assert (
    probe.main(
      [
        "--external-evidence-template",
        "--output",
        str(output_path),
      ]
    )
    == 0
  )
  template = json.loads(output_path.read_text(encoding="utf-8"))
  assert (
    template["schema_version"]
    == "a2.kill_chain_calibration_evidence_template.v1"
  )
  assert template["status"] == "template_only_not_evidence"
  assert template["authority_boundary"]["calibration_authority"] is False
  rows = {str(row["layer_id"]): row for row in template["layer_templates"]}
  assert set(rows) == {
    "fuze_data",
    "warhead_data",
    "target_response_data",
    "consequence_data",
  }
  warhead_template = rows["warhead_data"]["mlf10_v1_manifest_record_template"]
  assert warhead_template["schema_version"] == "mlf10.calibration_evidence.v1"
  assert warhead_template["authority_requests"] == {
    "effect_scale_authority": True
  }
  assert warhead_template["rights_status"] == "release_grade_admitted"
  assert warhead_template["source_gate_status"] == "passed"
  assert warhead_template["validation_status"] == "passed"
  response_template = rows["target_response_data"][
    "mlf10_v1_manifest_record_template"
  ]
  assert response_template["authority_requests"] == {
    "component_failure_probability_authority": True
  }
  assert rows["fuze_data"]["mlf10_v1_manifest_record_template"] is None
  assert rows["fuze_data"]["separate_contract_required_authority_fields"] == [
    "deterministic_fuze_authority"
  ]
  assert rows["fuze_data"]["supplemental_contract_templates"][0][
    "authority_field"
  ] == "deterministic_fuze_authority"
  assert rows["consequence_data"]["mlf10_v1_manifest_record_template"] is None
  assert rows["consequence_data"]["separate_contract_required_authority_fields"] == [
    "pk_authority"
  ]
  assert rows["consequence_data"]["supplemental_contract_templates"][0][
    "authority_field"
  ] == "pk_authority"


def test_external_evidence_template_check_cli_validates_placeholders_and_ready_record(
  tmp_path,
) -> None:
  template_path = tmp_path / "template.json"
  template_check_path = tmp_path / "template_check.json"
  probe.main(
    [
      "--external-evidence-template",
      "--output",
      str(template_path),
    ]
  )
  assert (
    probe.main(
      [
        "--external-evidence-template-check",
        str(template_path),
        "--output",
        str(template_check_path),
      ]
    )
    == 0
  )
  template_check = json.loads(template_check_path.read_text(encoding="utf-8"))
  assert (
    template_check["schema_version"]
    == "a2.kill_chain_calibration_evidence_template_check.v1"
  )
  assert template_check["ready_for_mlf10_audit"] is False
  assert template_check["record_count"] == 2
  assert "placeholder_values_present" in template_check["blocked_by"]
  assert {
    row["layer_id"] for row in template_check["non_record_layer_notes"]
  } == {"fuze_data", "consequence_data"}

  ready_record = {
    "schema_version": "mlf10.calibration_evidence.v1",
    "evidence_id": "SYNTH-READY-WARHEAD",
    "evidence_class": "calibration_candidate",
    "source_kind": "external_calibration_dataset",
    "source_ref": "synthetic/source",
    "provenance": "synthetic release-grade test record",
    "rights_status": "release_grade_admitted",
    "source_gate_status": "passed",
    "validation_status": "passed",
    "scope": {
      "target_type": "synthetic_target",
      "weapon_family": "synthetic_weapon",
      "mechanism_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss",
    },
    "population": {
      "identity": "synthetic population",
      "denominator_name": "synthetic_case_count",
      "sample_count": 3,
      "filters": "synthetic filters",
      "independence_assumption": "synthetic independence assumption",
    },
    "uncertainty": {
      "method": "synthetic_interval",
      "coverage": "synthetic coverage",
      "residuals": [],
    },
    "independent_review": {
      "status": "passed",
      "reviewer_ref": "synthetic/reviewer",
    },
    "authority_requests": {"effect_scale_authority": True},
    "non_claims": [
      "real_world_pk",
      "deterministic_fuze_reliability",
      "reward_authority",
      "entity_deletion_authority",
      "out_of_scope_weapon_truth",
      "out_of_scope_target_truth",
    ],
    "residuals": [],
  }
  record_path = tmp_path / "ready_record.json"
  record_check_path = tmp_path / "ready_record_check.json"
  record_path.write_text(json.dumps(ready_record), encoding="utf-8")
  assert (
    probe.main(
      [
        "--external-evidence-template-check",
        str(record_path),
        "--output",
        str(record_check_path),
      ]
    )
    == 0
  )
  record_check = json.loads(record_check_path.read_text(encoding="utf-8"))
  assert record_check["ready_for_mlf10_audit"] is True
  assert record_check["ready_record_count"] == 1
  assert record_check["blocked_by"] == []
  assert record_check["records"][0]["requested_authority_fields"] == [
    "effect_scale_authority"
  ]


def test_supplemental_evidence_contract_cli_covers_non_mlf10_layers(
  tmp_path,
) -> None:
  contract_path = tmp_path / "supplemental_contract.json"
  contract_check_path = tmp_path / "supplemental_contract_check.json"
  assert (
    probe.main(
      [
        "--external-evidence-supplemental-contract",
        "--output",
        str(contract_path),
      ]
    )
    == 0
  )
  contract = json.loads(contract_path.read_text(encoding="utf-8"))
  assert (
    contract["schema_version"]
    == "a2.kill_chain_calibration_supplemental_evidence_contract.v1"
  )
  assert contract["status"] == "template_only_not_evidence"
  assert contract["contract_record_count"] == 2
  records = {str(row["authority_field"]): row for row in contract["contract_records"]}
  assert set(records) == {"deterministic_fuze_authority", "pk_authority"}
  assert records["deterministic_fuze_authority"]["layer_id"] == "fuze_data"
  assert records["deterministic_fuze_authority"]["owner_stage"] == "fuze_decision"
  assert records["pk_authority"]["layer_id"] == "consequence_data"
  assert records["pk_authority"]["owner_stage"] == "consequence_projection"
  assert (
    records["pk_authority"]["authority_scope"]
    == "simulation_consequence_projection_only"
  )
  assert records["pk_authority"]["stage_delta_requirements"][
    "delta_guard_schema_version"
  ] == "a2.kill_chain_calibration_delta_guard.v1"
  assert contract["authority_boundary"]["real_world_pk"] is False
  assert contract["authority_boundary"]["deterministic_fuze_authority"] is False

  assert (
    probe.main(
      [
        "--external-evidence-supplemental-contract-check",
        str(contract_path),
        "--output",
        str(contract_check_path),
      ]
    )
    == 0
  )
  contract_check = json.loads(contract_check_path.read_text(encoding="utf-8"))
  assert (
    contract_check["schema_version"]
    == "a2.kill_chain_calibration_supplemental_evidence_contract_check.v1"
  )
  assert contract_check["ready_for_authority_admission"] is False
  assert contract_check["record_count"] == 2
  assert "placeholder_values_present" in contract_check["blocked_by"]
  assert "population_fields_invalid" in contract_check["blocked_by"]

  ready_record = copy.deepcopy(records["deterministic_fuze_authority"])
  ready_record["evidence_id"] = "SYNTH-READY-FUZE"
  ready_record["source_ref"] = "synthetic/fuze_authority"
  ready_record["provenance"] = "synthetic release-grade fuze authority package"
  ready_record["scope"] = {
    "target_type": "synthetic_target",
    "weapon_family": "synthetic_weapon",
    "mechanism_family": "proximity_fuze",
    "aspect_bucket": "beam",
    "closure_bucket": "high",
    "miss_distance_bucket": "near_miss",
    "decision_scope": "detonation_decision",
  }
  ready_record["population"] = {
    "identity": "synthetic fuze population",
    "denominator_name": "synthetic_fuze_trials",
    "sample_count": 5,
    "filters": "synthetic filters",
    "independence_assumption": "synthetic independence assumption",
  }
  ready_record["uncertainty"] = {
    "method": "synthetic_interval",
    "coverage": "synthetic coverage",
    "residuals": [],
  }
  ready_record["independent_review"] = {
    "status": "passed",
    "reviewer_ref": "synthetic/fuze_reviewer",
  }
  ready_record_path = tmp_path / "ready_fuze_contract_record.json"
  ready_record_check_path = tmp_path / "ready_fuze_contract_record_check.json"
  ready_record_path.write_text(json.dumps(ready_record), encoding="utf-8")
  assert (
    probe.main(
      [
        "--external-evidence-supplemental-contract-check",
        str(ready_record_path),
        "--output",
        str(ready_record_check_path),
      ]
    )
    == 0
  )
  ready_check = json.loads(ready_record_check_path.read_text(encoding="utf-8"))
  assert ready_check["ready_for_authority_admission"] is True
  assert ready_check["ready_record_count"] == 1
  assert ready_check["blocked_by"] == []
  assert ready_check["records"][0]["authority_field"] == "deterministic_fuze_authority"


def test_proximity_sweep_reports_load_and_response_by_distance() -> None:
  report = probe.generate_report(
    guidance_cases=(),
    proximity_distances_m=(0.5, 10.96),
    include_guidance=False,
    include_proximity=True,
  )

  assert report["proximity_case_count"] == 2
  close, far = report["proximity_sweep"]
  assert close["case_type"] == "profiled_local_proximity"
  assert far["case_type"] == "profiled_local_proximity"
  assert float(close["distance_m"]) == 0.5
  assert float(far["distance_m"]) == 10.96
  assert close["effect"]["spatial_effect_scale"] is not None
  assert far["effect"]["spatial_effect_scale"] is not None
  assert (
    float(close["effect"]["spatial_effect_scale"])
    > float(far["effect"]["spatial_effect_scale"])
  )
  assert close["effect"]["component_max_failure_probability"] is not None
  assert far["effect"]["component_max_failure_probability"] is not None
  assert (
    float(close["effect"]["component_max_failure_probability"])
    > float(far["effect"]["component_max_failure_probability"])
  )
  assert (
    far["decoupling_summary"]["authority_boundary"]["calibration_authority"] is False
  )
  assert report["scalar_coupling_summary"]["scalar_count"] >= (
    len(close["scalar_coupling_ledger"]) + len(far["scalar_coupling_ledger"])
  )
  assert (
    report["scalar_coupling_summary"]["coupling_flag_counts"][
      "aggregate_spatial_effect_scale_crosses_stage_boundary"
    ]
    >= 2
  )
  assert (
    report["scalar_coupling_summary"]["coupling_flag_counts"][
      "effect_scale_decomposition_factor_available"
    ]
    >= 2
  )
  assert report["component_load_factor_summary"]["row_count"] >= (
    len(close["component_load_factor_rows"]) + len(far["component_load_factor_rows"])
  )
  assert (
    report["component_load_factor_summary"]["authority_boundary"][
      "runtime_parameter_retuning"
    ]
    is False
  )
  assert report["component_load_factor_summary"]["rows_with_response_fields_on_load_row"] == 0
  assert (
    report["component_load_factor_summary"][
      "response_field_names_present_on_load_rows"
    ]
    == []
  )
  assert (
    report["component_load_factor_summary"][
      "response_owner_violation_field_counts"
    ]
    == {}
  )
  assert report["decoupled_facade_summary"]["schema_version"] == (
    "a2.kill_chain_decoupled_facade.v1"
  )
  assert report["decoupled_facade_summary"]["runtime_facade_schema_version"] == (
    "a2.kill_chain_runtime_facade.v1"
  )
  assert report["decoupled_facade_summary"]["facade_status"] == "runtime_dto_backed"
  assert (
    report["decoupled_facade_summary"]["authority_boundary"][
      "runtime_dto_authority"
    ]
    is True
  )
  assert report["decoupled_facade_summary"]["runtime_response_rows_available"] is True
  assert report["decoupled_facade_summary"]["component_response_row_count"] >= (
    len(close["component_load_factor_rows"]) + len(far["component_load_factor_rows"])
  )
  assert close["runtime_facade"]["runtime_dto_available"] is True
  assert far["runtime_facade"]["runtime_dto_available"] is True
  assert close["decoupled_facade"]["component_response"]["runtime_dto_authority"] is True
  assert far["decoupled_facade"]["component_response"]["runtime_dto_authority"] is True
