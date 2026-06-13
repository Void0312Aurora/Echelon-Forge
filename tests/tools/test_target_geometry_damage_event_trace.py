from __future__ import annotations

from tools.geometry import target_geometry_damage_event_trace as trace


def test_tg_p7_damage_event_trace_observes_all_split_receivers() -> None:
  report = trace.generate_report()

  assert report["schema_version"] == "a2.target_geometry_damage_event_trace.v1"
  assert report["status"] == "target_geometry_damage_event_trace_generated_tg_p7_r5"

  inventory = report["component_inventory"]
  assert inventory["default_database_component_count"] == 26
  assert inventory["proxy_database_component_count"] == 32
  assert inventory["component_count_delta"] == 6
  assert inventory["default_split_receiver_count"] == 0
  assert inventory["proxy_split_receiver_count"] == 8
  assert inventory["default_retired_parent_count"] == 2
  assert inventory["proxy_retired_parent_count"] == 0
  assert inventory["duplicate_proxy_component_names"] == []

  metrics = report["metrics"]
  assert metrics["trace_case_count"] == 8
  assert metrics["split_receiver_component_count"] == 8
  assert metrics["proxy_observed_split_receiver_count"] == 8
  assert metrics["all_expected_split_receivers_observed_in_proxy"] is True
  assert metrics["no_expected_split_receiver_observed_in_default"] is True
  assert metrics["proxy_retired_parent_rows_absent"] is True
  assert metrics["all_trace_cases_pass"] is True
  assert set(metrics["proxy_observed_split_receivers"]) == set(
    trace.SPLIT_RECEIVER_NAMES
  )
  assert metrics["default_observed_split_receivers"] == []
  assert metrics["proxy_observed_retired_parent_components"] == []

  for case in report["trace_cases"]:
    expected = case["expected_split_receiver"]
    retired_parent = case["retired_parent_component"]
    default_names = set(case["default_event"]["component_mechanism_row_names"])
    default_names.update(case["default_event"]["component_load_event_names"])
    default_names.update(case["default_event"]["component_damage_event_names"])
    proxy_names = set(case["proxy_event"]["component_mechanism_row_names"])
    proxy_names.update(case["proxy_event"]["component_load_event_names"])
    proxy_names.update(case["proxy_event"]["component_damage_event_names"])

    assert expected not in default_names
    assert expected in proxy_names
    assert retired_parent not in proxy_names
    assert case["checks"]["case_pass"] is True
    assert case["proxy_event"]["warhead_profile_synthetic"] is True
    assert case["proxy_event"]["damage_scalar_synthetic"] is True
    assert case["proxy_event"]["vulnerability_pk_authority"] is False
    assert case["proxy_event"]["vulnerability_deterministic_fuze_authority"] is False
