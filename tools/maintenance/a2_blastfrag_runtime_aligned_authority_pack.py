#!/usr/bin/env python3
"""Generate a runtime-aligned A2 blast-fragmentation authority exercise pack.

This tool bridges the existing non-authoritative A2 blast-fragmentation scaffold
and the current structured-air runtime by sampling a stock near-miss event and
drafting two test-local validated-surrogate descriptor candidates:

1. effect-scale authority only
2. component-specific component-failure-probability authority only

The output is intentionally bounded to temporary test-local database exercises.
It must not be treated as stock-database authority, project-calibrated truth,
Pk authority, or deterministic-fuze authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import configure_sim_log_level, resolve_repo_path

from tools.maintenance import a2_blastfrag_validation_scaffold as scaffold


configure_sim_log_level("warn")

import ef_py  # noqa: E402


PACK_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_runtime_aligned_authority_exercise_v0"
)
PACK_SCHEMA_VERSION = "a2.vulnerability_authority_exercise.v1"
PACKAGE_SCOPE = {
    "target_type": "F-16C_Block50",
    "weapon_class": "AIM-120C-class",
    "weapon_family": "blast_fragmentation",
    "aspect_bucket": "beam",
    "closure_bucket": "high",
    "candidate_scope_label": "near_miss_0_35m",
    "runtime_miss_distance_bucket": "near_miss",
}
DEFAULT_LOCAL_POINT = (-0.753, 6.0, 0.0)
DEFAULT_MISSILE_VELOCITY = (900.0, -250.0, 0.0)
DEFAULT_DAMAGE = 90.0
DEFAULT_RADIUS_M = 35.0
DEFAULT_EFFECT_SCALE = 1.11
DEFAULT_COMPONENT_FAILURE_PROBABILITY = 0.67


def _runtime_gate_band(
    value: float,
    *,
    lower_scale: float = 0.85,
    upper_scale: float = 1.15,
) -> tuple[float, float]:
    lower = max(0.0, float(value) * lower_scale)
    upper = max(lower, float(value) * upper_scale)
    return lower, upper


def _validated_surrogate_manifest_patch() -> dict[str, Any]:
    return {
        "validation_manifest": {
            "schema_version": "a2.vulnerability_surrogate_validation.v1",
            "validation_status": "validated",
            "validation_artifact_sha256": (
                "0123456789abcdef0123456789abcdef"
                "0123456789abcdef0123456789abcdef"
            ),
            "validated_surrogate_model_ref": "fixture://surrogate/model/f16-aim120-v1",
            "validation_benchmark_ref": "fixture://surrogate/benchmark/f16-aim120-v1",
            "validation_metrics_ref": "fixture://surrogate/metrics/f16-aim120-v1",
            "validation_acceptance_criteria_ref": (
                "fixture://surrogate/acceptance/f16-aim120-v1"
            ),
            "validation_scope": {
                "target_type": PACKAGE_SCOPE["target_type"],
                "weapon_family": PACKAGE_SCOPE["weapon_family"],
                "aspect_bucket": PACKAGE_SCOPE["aspect_bucket"],
                "closure_bucket": PACKAGE_SCOPE["closure_bucket"],
                "miss_distance_bucket": PACKAGE_SCOPE["runtime_miss_distance_bucket"],
            },
        }
    }


def _spawn_structured_f16_pair(sim: ef_py.SimulationKernel) -> tuple[int, int]:
    attacker_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            5000.0,
            0.0,
            0.0,
            0.0,
            0.0,
            250.0,
            0.0,
        )
    )
    target_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            500.0,
            5000.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -250.0,
            0.0,
        )
    )
    return attacker_id, target_id


def _make_warhead_profile(
    *,
    family: str = "blast_fragmentation",
    damage: float = DEFAULT_DAMAGE,
    radius_m: float = DEFAULT_RADIUS_M,
) -> ef_py.WarheadProfile:
    profile = ef_py.WarheadProfile()
    profile.family = str(family)
    profile.mass_kg = 12.0
    profile.lethal_radius_m = float(radius_m)
    profile.damage_scalar = float(damage)
    profile.synthetic = False
    profile.damage_scalar_synthetic = False
    profile.provenance = f"maintenance_{family}_profile"
    return profile


def _sample_stock_near_miss_event(
    *,
    database_path: str,
    local_point: tuple[float, float, float] = DEFAULT_LOCAL_POINT,
    missile_velocity: tuple[float, float, float] = DEFAULT_MISSILE_VELOCITY,
    damage: float = DEFAULT_DAMAGE,
    radius_m: float = DEFAULT_RADIUS_M,
    seed: int = 20260526,
) -> object:
    sim = ef_py.SimulationKernel()
    sim.reset(seed)
    if not sim.load_database(database_path):
        raise AssertionError(f"failed to load runtime database from {database_path}")
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _make_warhead_profile(
        family="blast_fragmentation",
        damage=damage,
        radius_m=radius_m,
    )
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        float(local_point[0]),
        float(local_point[1]),
        float(local_point[2]),
        profile,
        float(missile_velocity[0]),
        float(missile_velocity[1]),
        float(missile_velocity[2]),
    )
    if not ok:
        raise AssertionError("runtime-aligned authority pack failed to apply stock near-miss event")
    events = sim.export_recent_engagement_events()
    if len(events.effects_events) != 1:
        raise AssertionError("expected exactly one effects event in runtime-aligned authority pack")
    return events.effects_events[0]


def _component_rows_summary(event: object) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in event.component_mechanism_load_rows:
        rows.append(
            {
                "component_name": str(row.component_name),
                "component_system": str(row.component_system),
                "component_redundancy_group_id": str(row.component_redundancy_group_id),
                "direct_hit": bool(row.direct_hit),
                "distance_m": float(row.distance_m),
                "effect_scale": float(row.effect_scale),
                "component_threshold_scale": float(row.component_threshold_scale),
                "component_failure_probability": float(row.component_failure_probability),
                "component_failure_probability_source": str(
                    row.component_failure_probability_source
                ),
                "mechanism_fragment_areal_density_per_m2": float(
                    row.mechanism_fragment_areal_density_per_m2
                ),
                "mechanism_blast_scaled_distance_m_kg13": float(
                    row.mechanism_blast_scaled_distance_m_kg13
                ),
                "mechanism_surface_incidence_cos": float(
                    row.mechanism_surface_incidence_cos
                ),
            }
        )
    return rows


def _baseline_event_summary(event: object) -> dict[str, Any]:
    return {
        "direct_hitbox_intersection": bool(event.direct_hitbox_intersection),
        "projected_hitbox_count": int(event.projected_hitbox_count),
        "component_hit_count": int(event.component_hit_count),
        "component_primary_name": str(event.component_primary_name),
        "component_primary_system": str(event.component_primary_system),
        "component_primary_redundancy_group_id": str(
            event.component_primary_redundancy_group_id
        ),
        "spatial_effect_scale": float(event.spatial_effect_scale),
        "vulnerability_effect_scale": float(event.vulnerability_effect_scale),
        "vulnerability_effect_scale_source": str(event.vulnerability_effect_scale_source),
        "component_failure_probability": float(event.component_failure_probability),
        "component_failure_probability_source": str(
            event.component_failure_probability_source
        ),
        "mechanism_blast_scaled_distance_m_kg13": float(
            event.mechanism_blast_scaled_distance_m_kg13
        ),
        "mechanism_fragment_areal_density_per_m2": float(
            event.mechanism_fragment_areal_density_per_m2
        ),
        "mechanism_surface_incidence_cos": float(
            event.mechanism_surface_incidence_cos
        ),
        "component_primary_mechanism_blast_scaled_distance_m_kg13": float(
            event.component_primary_mechanism_blast_scaled_distance_m_kg13
        ),
        "component_primary_mechanism_fragment_areal_density_per_m2": float(
            event.component_primary_mechanism_fragment_areal_density_per_m2
        ),
        "component_primary_mechanism_surface_incidence_cos": float(
            event.component_primary_mechanism_surface_incidence_cos
        ),
    }


def _build_effect_scale_descriptor(
    *,
    scaffold_descriptor: dict[str, Any],
    baseline_event: object,
    effect_scale: float,
) -> dict[str, Any]:
    blast_scaled_distance = float(baseline_event.mechanism_blast_scaled_distance_m_kg13)
    fragment_areal_density = float(baseline_event.mechanism_fragment_areal_density_per_m2)
    surface_incidence = float(baseline_event.mechanism_surface_incidence_cos)
    min_z, max_z = _runtime_gate_band(blast_scaled_distance)
    min_density, max_density = _runtime_gate_band(fragment_areal_density)
    min_incidence, max_incidence = _runtime_gate_band(
        surface_incidence,
        lower_scale=0.90,
        upper_scale=1.10,
    )
    max_incidence = min(1.0, max_incidence)
    return {
        "dataset_id": "unit_test_a2_blastfrag_runtime_aligned_effect_scale",
        "schema_version": "a2.vulnerability_evidence.v1",
        "target_type": PACKAGE_SCOPE["target_type"],
        "weapon_family": PACKAGE_SCOPE["weapon_family"],
        "aspect_bucket": PACKAGE_SCOPE["aspect_bucket"],
        "closure_bucket": PACKAGE_SCOPE["closure_bucket"],
        "miss_distance_bucket": PACKAGE_SCOPE["runtime_miss_distance_bucket"],
        "source_kind": "validated_physics_surrogate",
        "source_ref": (
            f"{scaffold_descriptor['source_ref']}#runtime-aligned-validated-surrogate"
        ),
        "validation_artifact_ref": (
            "fixture://a2-blastfrag/runtime-aligned-validated-surrogate-report"
        ),
        "calibration_status": "calibrated",
        "effect_scale_authority": True,
        "component_failure_probability_authority": False,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": (
            "runtime-aligned validated_surrogate descriptor candidate derived from "
            "stock A2 blast-fragmentation near-miss event load; effect-scale "
            "authority only and test-local only"
        ),
        **_validated_surrogate_manifest_patch(),
        "rows": [
            {
                "row_id": "a2-runtime-aligned-blastfrag-effect-scale",
                "source_ref": (
                    f"{scaffold_descriptor['source_ref']}"
                    "#a2-runtime-aligned-blastfrag-effect-scale"
                ),
                "provenance": (
                    "runtime-aligned effect-scale row candidate derived from stock "
                    "A2 blast-fragmentation near-miss event load"
                ),
                "weapon_family": PACKAGE_SCOPE["weapon_family"],
                "aspect_bucket": PACKAGE_SCOPE["aspect_bucket"],
                "closure_bucket": PACKAGE_SCOPE["closure_bucket"],
                "miss_distance_bucket": PACKAGE_SCOPE["runtime_miss_distance_bucket"],
                "effect_scale": float(effect_scale),
                "min_blast_scaled_distance_m_kg13": min_z,
                "max_blast_scaled_distance_m_kg13": max_z,
                "min_fragment_areal_density_per_m2": min_density,
                "max_fragment_areal_density_per_m2": max_density,
                "min_surface_incidence_cos": min_incidence,
                "max_surface_incidence_cos": max_incidence,
            }
        ],
    }


def _build_component_probability_descriptor(
    *,
    scaffold_descriptor: dict[str, Any],
    primary_row: dict[str, Any],
    probability: float,
) -> dict[str, Any]:
    min_z, max_z = _runtime_gate_band(
        float(primary_row["mechanism_blast_scaled_distance_m_kg13"])
    )
    min_density, max_density = _runtime_gate_band(
        float(primary_row["mechanism_fragment_areal_density_per_m2"])
    )
    min_incidence, max_incidence = _runtime_gate_band(
        float(primary_row["mechanism_surface_incidence_cos"]),
        lower_scale=0.90,
        upper_scale=1.10,
    )
    max_incidence = min(1.0, max_incidence)
    return {
        "dataset_id": "unit_test_a2_blastfrag_runtime_aligned_component_probability",
        "schema_version": "a2.vulnerability_evidence.v1",
        "target_type": PACKAGE_SCOPE["target_type"],
        "weapon_family": PACKAGE_SCOPE["weapon_family"],
        "aspect_bucket": PACKAGE_SCOPE["aspect_bucket"],
        "closure_bucket": PACKAGE_SCOPE["closure_bucket"],
        "miss_distance_bucket": PACKAGE_SCOPE["runtime_miss_distance_bucket"],
        "source_kind": "validated_physics_surrogate",
        "source_ref": (
            f"{scaffold_descriptor['source_ref']}#runtime-aligned-component-probability"
        ),
        "validation_artifact_ref": (
            "fixture://a2-blastfrag/runtime-aligned-component-probability-report"
        ),
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": (
            "runtime-aligned validated_surrogate descriptor candidate derived from "
            "stock A2 blast-fragmentation near-miss projected component load; "
            "component-specific probability authority only and test-local only"
        ),
        **_validated_surrogate_manifest_patch(),
        "rows": [
            {
                "row_id": "a2-runtime-aligned-blastfrag-component-probability",
                "source_ref": (
                    f"{scaffold_descriptor['source_ref']}"
                    "#a2-runtime-aligned-blastfrag-component-probability"
                ),
                "provenance": (
                    "runtime-aligned component-probability row candidate derived from "
                    "stock A2 blast-fragmentation near-miss projected component load"
                ),
                "weapon_family": PACKAGE_SCOPE["weapon_family"],
                "aspect_bucket": PACKAGE_SCOPE["aspect_bucket"],
                "closure_bucket": PACKAGE_SCOPE["closure_bucket"],
                "miss_distance_bucket": PACKAGE_SCOPE["runtime_miss_distance_bucket"],
                "component_name": str(primary_row["component_name"]),
                "component_system": str(primary_row["component_system"]),
                "component_redundancy_group_id": str(
                    primary_row["component_redundancy_group_id"]
                ),
                "component_failure_probability": float(probability),
                "min_blast_scaled_distance_m_kg13": min_z,
                "max_blast_scaled_distance_m_kg13": max_z,
                "min_fragment_areal_density_per_m2": min_density,
                "max_fragment_areal_density_per_m2": max_density,
                "min_surface_incidence_cos": min_incidence,
                "max_surface_incidence_cos": max_incidence,
            }
        ],
    }


def generate_runtime_aligned_authority_pack(
    *,
    repo_root: Path = REPO_ROOT,
    local_point: tuple[float, float, float] = DEFAULT_LOCAL_POINT,
    missile_velocity: tuple[float, float, float] = DEFAULT_MISSILE_VELOCITY,
    damage: float = DEFAULT_DAMAGE,
    radius_m: float = DEFAULT_RADIUS_M,
    effect_scale: float = DEFAULT_EFFECT_SCALE,
    component_failure_probability: float = DEFAULT_COMPONENT_FAILURE_PROBABILITY,
) -> dict[str, Any]:
    validation_scaffold = scaffold.generate_validation_scaffold(repo_root=repo_root)
    scaffold_descriptor = validation_scaffold["vulnerability_evidence_draft"]["descriptor"]
    database_path = resolve_repo_path("examples", "config", "database")
    baseline_event = _sample_stock_near_miss_event(
        database_path=database_path,
        local_point=local_point,
        missile_velocity=missile_velocity,
        damage=damage,
        radius_m=radius_m,
    )
    baseline_summary = _baseline_event_summary(baseline_event)
    component_rows = _component_rows_summary(baseline_event)
    primary_name = str(baseline_summary["component_primary_name"])
    primary_rows = [
        row for row in component_rows if str(row["component_name"]) == primary_name
    ]
    if not primary_rows:
        raise AssertionError(
            "runtime-aligned authority pack expected a projected primary component row"
        )
    primary_row = primary_rows[0]
    return {
        "package_id": PACK_ID,
        "schema_version": PACK_SCHEMA_VERSION,
        "status": "test_local_authority_exercise_only",
        "scope": dict(PACKAGE_SCOPE),
        "authority_boundary": {
            "stock_database_authority_granted": False,
            "effect_scale_authority_candidate": True,
            "component_failure_probability_authority_candidate": True,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
            "runtime_database_integration": "forbidden_by_default",
            "allowed_runtime_surface": "temporary test-local database only",
        },
        "candidate_inputs_ref": validation_scaffold["candidate_inputs"],
        "source_scaffold_ref": {
            "package_id": validation_scaffold["package_id"],
            "descriptor_dataset_id": scaffold_descriptor["dataset_id"],
            "source_ref": scaffold_descriptor["source_ref"],
        },
        "baseline_event_summary": baseline_summary,
        "baseline_component_rows": component_rows,
        "effect_scale_descriptor_candidate": _build_effect_scale_descriptor(
            scaffold_descriptor=scaffold_descriptor,
            baseline_event=baseline_event,
            effect_scale=effect_scale,
        ),
        "component_failure_probability_descriptor_candidate": (
            _build_component_probability_descriptor(
                scaffold_descriptor=scaffold_descriptor,
                primary_row=primary_row,
                probability=component_failure_probability,
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a runtime-aligned A2 blast-fragmentation authority "
            "exercise pack for test-local Stage B/C descriptor candidates."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--effect-scale",
        type=float,
        default=DEFAULT_EFFECT_SCALE,
        help="Effect-scale row value for the Stage B descriptor candidate.",
    )
    parser.add_argument(
        "--component-failure-probability",
        type=float,
        default=DEFAULT_COMPONENT_FAILURE_PROBABILITY,
        help="Component-specific probability value for the Stage C descriptor candidate.",
    )
    args = parser.parse_args()

    artifact = generate_runtime_aligned_authority_pack(
        effect_scale=float(args.effect_scale),
        component_failure_probability=float(args.component_failure_probability),
    )
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
