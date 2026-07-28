from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.testing.contracts import common


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict[str, object]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_spec_prefers_spec_directory_then_falls_back_to_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  spec_dir = tmp_path / "specs"
  repo_root = tmp_path / "repo"
  spec_path = spec_dir / "child.json"
  local_base = spec_dir / "base.json"
  repo_base = repo_root / "base.json"
  _write_json(local_base, {"base_source": "local"})
  _write_json(repo_base, {"base_source": "repo"})
  _write_json(spec_path, {"extends": "base.json", "child_value": 1})
  monkeypatch.setattr(
    common, "resolve_repo_path", lambda *parts: str(repo_root.joinpath(*parts))
  )

  assert common._load_spec(str(spec_path)) == {
    "base_source": "local",
    "child_value": 1,
  }

  local_base.unlink()

  assert common._load_spec(str(spec_path)) == {
    "base_source": "repo",
    "child_value": 1,
  }


def test_load_spec_deep_merges_dicts_and_replaces_lists(tmp_path: Path) -> None:
  base_path = tmp_path / "base.json"
  spec_path = tmp_path / "child.json"
  _write_json(
    base_path,
    {
      "type": "unit_regression",
      "checks": {
        "shared": {"min": 1, "max": 5},
        "base_only": {"abs_max": 3},
      },
      "values": [1, 2],
    },
  )
  _write_json(
    spec_path,
    {
      "extends": "base.json",
      "checks": {
        "shared": {"max": 4},
        "child_only": {"min": 9},
      },
      "values": [7],
    },
  )

  assert common._load_spec(str(spec_path)) == {
    "type": "unit_regression",
    "checks": {
      "shared": {"min": 1, "max": 4},
      "base_only": {"abs_max": 3},
      "child_only": {"min": 9},
    },
    "values": [7],
  }


def test_load_spec_rejects_extends_cycles(tmp_path: Path) -> None:
  first = tmp_path / "first.json"
  second = tmp_path / "second.json"
  _write_json(first, {"extends": "second.json", "first": True})
  _write_json(second, {"extends": "first.json", "second": True})

  with pytest.raises(ValueError, match="extends cycle"):
    common._load_spec(str(first))


def test_load_spec_allows_four_extends_but_rejects_a_fifth(tmp_path: Path) -> None:
  for index in range(6):
    payload: dict[str, object] = {f"level_{index}": index}
    if index:
      payload["extends"] = f"spec_{index - 1}.json"
    _write_json(tmp_path / f"spec_{index}.json", payload)

  assert common._load_spec(str(tmp_path / "spec_4.json")) == {
    f"level_{index}": index for index in range(5)
  }

  with pytest.raises(ValueError, match="maximum extends depth"):
    common._load_spec(str(tmp_path / "spec_5.json"))


NAVAL_SCREEN_THREAT_ROE_GEOMETRY_REFERENCE = json.loads(
  """
  {
    "type": "unit_regression",
    "check_kind": "naval_screen_threat_roe",
    "scenario": "scenarios/naval/ddg51_take1_screen_threat_roe_v1.json",
    "seed": 20260516,
    "screen_entity": "Blue_Screen_DDG51",
    "hvu_entity": "Blue_HVU_TAKE1",
    "contact_entity": "Red_Surface_Contact",
    "max_steps": 240,
    "continue_after_contact_chain": true,
    "report_message_type": "ReportTrack",
    "forbid_hvu_local_source": true,
    "expected_runtime_mission_command": {
      "active": true,
      "roe_state": 1,
      "engagement_authority_holder_id": 5101,
      "engagement_authority_grantor_id": 5101,
      "assigned_target_entity": "Red_Surface_Contact",
      "authorization_to_fire": false
    },
    "checks": {
      "initial_screen_hvu_separation_m": {"min": 14000.0, "max": 15500.0},
      "initial_screen_contact_range_m": {"max": 46300.0},
      "initial_hvu_contact_range_m": {"min": 39000.0, "max": 41000.0},
      "screen_first_detection_step": {"max": 80},
      "hvu_first_shared_track_step": {"max": 80},
      "hvu_first_report_step": {"max": 80},
      "mission_command_first_active_step": {"max": 5},
      "screen_hvu_separation_m_min": {"min": 14000.0},
      "screen_hvu_separation_m_max": {"max": 15500.0},
      "hvu_contact_closest_approach_m": {"min": 37000.0, "max": 38000.0},
      "contact_health_delta": {"abs_max": 0.0},
      "contact_damage_delta": {"abs_max": 0.0},
      "screen_weapon_inventory_delta": {"abs_max": 0.0}
    }
  }
  """
)

NAVAL_SCREEN_THREAT_ROE_OFFSTATION_RECOVERY_REFERENCE = json.loads(
  """
  {
    "type": "unit_regression",
    "check_kind": "naval_screen_threat_roe",
    "scenario": "scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json",
    "seed": 20260516,
    "screen_entity": "Blue_Screen_DDG51",
    "hvu_entity": "Blue_HVU_TAKE1",
    "contact_entity": "Red_Surface_Contact",
    "max_steps": 240,
    "continue_after_contact_chain": true,
    "report_message_type": "ReportTrack",
    "forbid_hvu_local_source": true,
    "expected_runtime_mission_command": {
      "active": true,
      "roe_state": 1,
      "engagement_authority_holder_id": 5101,
      "engagement_authority_grantor_id": 5101,
      "assigned_target_entity": "Red_Surface_Contact",
      "authorization_to_fire": false
    },
    "checks": {
      "initial_screen_hvu_separation_m": {"min": 12500.0, "max": 13250.0},
      "initial_screen_contact_range_m": {"max": 46300.0},
      "initial_hvu_contact_range_m": {"min": 39000.0, "max": 41000.0},
      "screen_first_detection_step": {"max": 80},
      "hvu_first_shared_track_step": {"max": 80},
      "hvu_first_report_step": {"max": 80},
      "mission_command_first_active_step": {"max": 5},
      "screen_hvu_separation_m_min": {"min": 12500.0},
      "screen_hvu_separation_m_max": {"max": 15000.0},
      "hvu_contact_closest_approach_m": {"min": 37000.0, "max": 38000.0},
      "contact_health_delta": {"abs_max": 0.0},
      "contact_damage_delta": {"abs_max": 0.0},
      "screen_weapon_inventory_delta": {"abs_max": 0.0}
    }
  }
  """
)

SCRIPTED_TAKEOFF_TAKEOFF2_THROTTLE_REFERENCE = json.loads(
  """
  {
    "type": "unit_regression",
    "check_kind": "scripted_takeoff_takeoff2_throttle",
    "obs": {
      "mission": [0.0, 90.0, 0.0, 0.0],
      "instruments": [
        95.0, 0.0, 0.0, 20.0, 0.0, 0.0, 0.0, 0.0, 0.0, 70.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        70.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0
      ]
    }
  }
  """
)

SCRIPTED_TAKEOFF_CLEARANCE_HOLD_REFERENCE = json.loads(
  """
  {
    "type": "unit_regression",
    "check_kind": "scripted_takeoff_clearance_hold",
    "obs": {
      "instruments": [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 90.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
        0.0, 90.0, 500.0, 180.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        90.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
        0.0, 0.0
      ],
      "mission": [
        1.0, 90.0, 500.0, 180.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        2.0, 1.0, 5.0, 2.0,
        0.0, 0.0, 0.0,
        22.0, 2.0, 12.0, 11.0
      ]
    }
  }
  """
)


@pytest.mark.parametrize(
  ("relative_spec", "reference"),
  [
    (
      Path("tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json"),
      NAVAL_SCREEN_THREAT_ROE_GEOMETRY_REFERENCE,
    ),
    (
      Path(
        "tests/contracts/unit/naval/"
        "naval_screen_threat_roe_offstation_recovery.json"
      ),
      NAVAL_SCREEN_THREAT_ROE_OFFSTATION_RECOVERY_REFERENCE,
    ),
    (
      Path(
        "tests/contracts/unit/controllers/"
        "scripted_takeoff_takeoff2_throttle.json"
      ),
      SCRIPTED_TAKEOFF_TAKEOFF2_THROTTLE_REFERENCE,
    ),
    (
      Path(
        "tests/contracts/unit/controllers/"
        "scripted_takeoff_clearance_hold.json"
      ),
      SCRIPTED_TAKEOFF_CLEARANCE_HOLD_REFERENCE,
    ),
  ],
)
def test_converged_specs_match_embedded_pre_extends_references(
    relative_spec: Path, reference: dict[str, object]
) -> None:
  assert common._load_spec(str(REPO_ROOT / relative_spec)) == reference


def test_naval_geometry_leaf_keeps_raw_pre_fire_marker_keys() -> None:
  raw_spec = json.loads(
    (
      REPO_ROOT
      / "tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json"
    ).read_text(encoding="utf-8")
  )
  raw_text = json.dumps(raw_spec, ensure_ascii=True).lower()

  for marker in ("authorization_to_fire", "roe_state", "assigned_target"):
    assert marker in raw_text
