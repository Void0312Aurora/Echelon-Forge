from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from python.mission_obs_taxonomy import mission_observation_field_index
from python.simulation.air.engagement import AirEngagementFacts
from python.simulation.air.observation import (
    AIR_SCRIPTED_MISSION_MODE,
    build_air_contact_matrix,
    build_air_esm_matrix,
    build_air_instrument_vector,
    build_air_mission_vector,
    build_air_scripted_observation,
)


def _instrument() -> SimpleNamespace:
    return SimpleNamespace(
        ias=180.0,
        mach=0.55,
        alt_baro=1200.0,
        alt_radar=1195.0,
        vvi=2.0,
        aoa=4.0,
        beta=0.1,
        pitch=3.0,
        roll=-2.0,
        heading=90.0,
        g_load=1.0,
        g_load_axial=0.0,
        p=0.1,
        q=0.2,
        r=0.3,
        engine_rpm=80.0,
        fuel_internal=1000.0,
        fuel_external=100.0,
        fuel_flow=4.0,
        gear_pos=1.0,
        flaps_pos=0.2,
        speedbrake_pos=0.0,
        cmd_heading=90.0,
        cmd_alt=1500.0,
        cmd_speed=200.0,
        lat=1.0,
        lon=2.0,
        vn=0.0,
        ve=180.0,
        vd=0.0,
        ground_speed=180.0,
        ground_track=90.0,
        wind_speed=5.0,
        wind_dir=270.0,
        oat=15.0,
        gps_available=True,
        position_uncertainty=10.0,
        rwr_active=False,
        missiles_remaining=4,
    )


def test_air_observation_projection_keeps_named_instrument_and_mission_fields() -> None:
    command = SimpleNamespace(
        shared_core=SimpleNamespace(
            command_code=1,
            cmd_heading_deg=90.0,
            cmd_altitude_m=1500.0,
            cmd_speed_mps=200.0,
            roe_state=2,
            authorization_to_fire=True,
            assigned_target_id=42,
        ),
        air_takeoff=SimpleNamespace(
            takeoff_procedure_id=3,
            takeoff_clearance_id=4,
            takeoff_interval_s=12.0,
            runway_slot_id=5,
        ),
    )
    vector = build_air_instrument_vector(_instrument(), ils=(1.0, 2.0, 3.0, 4.0))
    mission = build_air_mission_vector(command)

    assert vector.shape == (42,)
    assert np.allclose(vector[[0, 3, 9, 37, 38, 39, 40, 41]], [180.0, 1195.0, 90.0, 4.0, 1.0, 2.0, 3.0, 4.0])
    assert mission[mission_observation_field_index(AIR_SCRIPTED_MISSION_MODE, "command_code")] == 1.0
    assert mission[mission_observation_field_index(AIR_SCRIPTED_MISSION_MODE, "target_altitude_m")] == 1500.0
    takeoff_mode = "nav_v2_cooperative_takeoff_v1"
    takeoff = build_air_mission_vector(command, mode=takeoff_mode)
    assert takeoff[mission_observation_field_index(takeoff_mode, "takeoff_clearance_code")] == 4.0
    with pytest.raises(ValueError, match="Unknown mission observation field"):
        mission_observation_field_index(AIR_SCRIPTED_MISSION_MODE, "takeoff_clearance_code")


def test_air_observation_projection_pads_native_contacts_and_rwr() -> None:
    observation = SimpleNamespace(
        contacts=[SimpleNamespace(range=12000.0, azimuth=4.0, elevation=-1.0, closing_speed=100.0, time_since_update=0.5)],
        rwr_warnings=[SimpleNamespace(bearing=-20.0, signal_strength=0.8, is_lock=True, is_launch=False)],
    )
    projected = build_air_scripted_observation(observation, _instrument(), None)

    assert projected["contacts"].shape == (8, 5)
    assert projected["rwr"].shape == (8, 4)
    assert np.allclose(projected["contacts"][0], [12000.0, 4.0, -1.0, 100.0, 0.5])
    assert np.allclose(projected["rwr"][0], [-20.0, 0.8, 1.0, 0.0])
    assert np.count_nonzero(projected["contacts"][1:]) == 0


def test_esm_observation_projection_preserves_age_confidence_and_classification_boundary() -> None:
    observation = SimpleNamespace(
        esm_detections=[
            SimpleNamespace(
                bearing_deg=-25.0,
                received_power_dbm=-71.0,
                has_rf_power=True,
                sensitivity_margin_db=14.0,
                age_s=0.25,
                confidence=0.5,
                classification_known=False,
                is_jammer=True,
                is_lock=False,
                is_guidance=False,
                range=1.0,
                target_id=99,
            )
        ]
    )

    matrix = build_air_esm_matrix(observation)
    projected = build_air_scripted_observation(observation, _instrument(), None, include_esm=True)

    assert matrix.shape == (8, 10)
    assert np.allclose(matrix[0], [-25.0, -71.0, 1.0, 14.0, 0.25, 0.5, 0.0, 0.0, 0.0, 0.0])
    assert np.count_nonzero(matrix[1:]) == 0
    assert np.array_equal(projected["esm"], matrix)
    assert "esm" not in build_air_scripted_observation(observation, _instrument(), None)


def test_air_observation_projection_accepts_declared_combat_facts() -> None:
    command = SimpleNamespace(
        authorization_to_fire=True,
        assigned_target_id=0,
        assigned_target_track_id=0,
        assigned_target_source_id=0,
        engagement_authority_holder_id=0,
        engagement_authority_grantor_id=0,
        roe_state=0,
    )
    projected = build_air_scripted_observation(
        SimpleNamespace(contacts=[], rwr_warnings=[]),
        _instrument(),
        command,
        mode="air_combat_c2_roe_v2",
        mission_facts={
            "authorization_to_fire": 1.0,
            "target_contact_present": 1.0,
            "fire_mask_open": 1.0,
            "launch_window_open": 1.0,
            "quality_window_ready": 1.0,
            "shot_budget_remaining": 4.0,
            "target_range_m": 16000.0,
        },
    )

    mission = projected["mission"]
    assert mission[mission_observation_field_index("air_combat_c2_roe_v2", "target_contact_present")] == 1.0
    assert mission[mission_observation_field_index("air_combat_c2_roe_v2", "launch_window_open")] == 1.0
    assert mission[mission_observation_field_index("air_combat_c2_roe_v2", "target_range_m")] == 16000.0


def test_air_observation_rejects_conflicting_command_owned_target_fact() -> None:
    command = SimpleNamespace(assigned_target_id=42)
    with pytest.raises(ValueError, match="assigned_target_id"):
        build_air_mission_vector(
            command,
            mode="air_combat_c2_roe_v2",
            mission_facts={"assigned_target_id": 43},
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (("shot_budget_remaining", -1.0), ("target_range_m", float("inf")), ("assigned_target_id", -2)),
)
def test_air_engagement_facts_reject_malformed_provider_values(field: str, value: float) -> None:
    kwargs = {
        "authorization_to_fire": False,
        "target_contact_present": False,
        "fire_mask_open": False,
        "launch_window_open": False,
        "quality_window_ready": False,
        "shot_budget_remaining": 0.0,
        field: value,
    }
    with pytest.raises(ValueError, match=field):
        AirEngagementFacts(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("assigned_target_id", 0),
        ("assigned_target_track_id", 0),
        ("engagement_authority_holder_id", 0),
    ),
)
def test_air_engagement_facts_reject_incomplete_fire_admission(field: str, value: int) -> None:
    kwargs = {
        "authorization_to_fire": True,
        "target_contact_present": True,
        "fire_mask_open": True,
        "launch_window_open": True,
        "quality_window_ready": True,
        "shot_budget_remaining": 1.0,
        "assigned_target_id": 17,
        "assigned_target_track_id": 17,
        "engagement_authority_holder_id": 23,
    }
    kwargs[field] = value
    with pytest.raises(ValueError, match=field):
        AirEngagementFacts(**kwargs)


def test_coasting_esm_is_not_a_current_lock_or_guidance_warning() -> None:
    row = SimpleNamespace(bearing_deg=10.0, age_s=0.1, confidence=1.0,
                          classification_known=True, is_jammer=True,
                          is_lock=True, is_guidance=True)
    matrix = build_air_esm_matrix(SimpleNamespace(esm_detections=[row]))
    assert np.array_equal(matrix[0, 6:], [1.0, 1.0, 0.0, 0.0])
