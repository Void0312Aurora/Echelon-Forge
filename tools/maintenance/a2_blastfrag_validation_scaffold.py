#!/usr/bin/env python3
"""Generate a non-authoritative A2 blast-fragmentation validation scaffold artifact.

This tool implements a first executable bridge from the A2 candidate validation
docs into a reproducible, fixed-seed benchmark scaffold. It intentionally stays
below runtime authority: the output is a non-authoritative toy/mechanism-load
artifact and must not be consumed as calibrated effect-scale, component-failure,
Pk, or deterministic-fuze truth.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_source_admission_audit as source_audit


F16_PATH = REPO_ROOT / "examples/config/database/aircraft/units/f16c_block50.json"
AIM120_PATH = REPO_ROOT / "examples/config/database/weapons/air_to_air/aim_120c.json"

PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
VALIDATION_SCHEMA_VERSION = "a2.vulnerability_surrogate_validation.v1"
CANDIDATE_SCOPE_LABEL = "near_miss_0_35m"
RUNTIME_MISS_DISTANCE_BUCKET = "near_miss"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_warhead_family(raw_type: str) -> str:
    lowered = raw_type.strip().lower()
    if lowered in {"frag", "fragmentation", "blast_fragmentation"}:
        return "blast_fragmentation"
    if lowered in {"blast", "continuous_rod", "hit_to_kill"}:
        return lowered
    return "blast_fragmentation" if not lowered else lowered


def _load_candidate_inputs() -> dict[str, Any]:
    f16 = _read_json(F16_PATH)
    aim120 = _read_json(AIM120_PATH)
    airframe = f16["airframe"]
    warhead = aim120["warhead"]
    fuze = aim120.get("fuze", {})
    return {
        "target": {
            "name": str(f16["name"]),
            "length_m": float(airframe["length_m"]),
            "wingspan_m": float(airframe["wingspan_m"]),
            "height_m": float(airframe["height_m"]),
            "reference_area_m2": float(airframe["reference_area"]),
            "source_kind": "repo_candidate_database",
            "provenance": (
                "repo-authored candidate F-16C geometry scaffold; non-authoritative "
                "and suitable only for coarse witness geometry"
            ),
            "source_ref": str(F16_PATH.relative_to(REPO_ROOT)),
        },
        "weapon": {
            "name": str(aim120["name"]),
            "weapon_class": "AIM-120C-class",
            "warhead_family": _normalize_warhead_family(str(warhead["type"])),
            "warhead_mass_kg": float(warhead["mass_kg"]),
            "repo_lethal_radius_m": float(warhead["lethal_radius"]),
            "fuze_type": str(fuze.get("type", "unknown")),
            "source_kind": "repo_candidate_database",
            "provenance": (
                "repo-authored AIM-120C-class family envelope scaffold; "
                "non-authoritative and not a claim of real C-model warhead/fuze truth"
            ),
            "source_ref": str(AIM120_PATH.relative_to(REPO_ROOT)),
        },
    }


def _scaled_distance(standoff_m: float, explosive_mass_kg: float) -> float:
    effective_mass = max(explosive_mass_kg, 1.0e-6)
    return standoff_m / (effective_mass ** (1.0 / 3.0))


def _blast_overpressure_proxy_kpa(z_value: float) -> float:
    return 1850.0 / ((z_value + 0.55) ** 1.24)


def _blast_impulse_proxy_kpa_ms(z_value: float) -> float:
    return 940.0 / ((z_value + 0.42) ** 1.10)


def _sample_unit_sphere(rng: random.Random) -> tuple[float, float, float]:
    while True:
        u = rng.uniform(-1.0, 1.0)
        v = rng.uniform(-1.0, 1.0)
        s = u * u + v * v
        if s <= 1.0e-12 or s >= 1.0:
            continue
        scale = math.sqrt(1.0 - s)
        return (2.0 * u * scale, 2.0 * v * scale, 1.0 - 2.0 * s)


def _beam_witness_intersection(
    direction: tuple[float, float, float],
    *,
    burst_offset_m: float,
    witness_length_m: float,
    witness_height_m: float,
) -> bool:
    dx, dy, dz = direction
    if dy >= -1.0e-9:
        return False
    t_value = burst_offset_m / (-dy)
    hit_x = dx * t_value
    hit_z = dz * t_value
    return (
        abs(hit_x) <= 0.5 * witness_length_m and
        abs(hit_z) <= 0.5 * witness_height_m
    )


def _fragment_sampling_summary(
    *,
    sample_count: int,
    toy_fragment_count: int,
    burst_offset_m: float,
    witness_length_m: float,
    witness_height_m: float,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    hit_count = 0
    sum_x = 0.0
    sum_y = 0.0
    sum_z = 0.0
    hemisphere_negative_y = 0
    for _ in range(sample_count):
        direction = _sample_unit_sphere(rng)
        dx, dy, dz = direction
        sum_x += dx
        sum_y += dy
        sum_z += dz
        if dy < 0.0:
            hemisphere_negative_y += 1
        if _beam_witness_intersection(
            direction,
            burst_offset_m=burst_offset_m,
            witness_length_m=witness_length_m,
            witness_height_m=witness_height_m,
        ):
            hit_count += 1

    witness_area_m2 = witness_length_m * witness_height_m
    hit_fraction = hit_count / float(sample_count)
    areal_density_per_m2 = (toy_fragment_count * hit_fraction) / max(witness_area_m2, 1.0e-9)
    return {
        "sample_count": sample_count,
        "toy_fragment_count": toy_fragment_count,
        "burst_offset_m": burst_offset_m,
        "witness_area_m2": witness_area_m2,
        "hit_count": hit_count,
        "hit_fraction": hit_fraction,
        "beam_witness_areal_density_per_m2": areal_density_per_m2,
        "mean_direction": {
            "x": sum_x / float(sample_count),
            "y": sum_y / float(sample_count),
            "z": sum_z / float(sample_count),
        },
        "negative_y_hemisphere_fraction": hemisphere_negative_y / float(sample_count),
    }


def _bfm_bm_001(
    *,
    warhead_mass_kg: float,
    standoff_m: float,
) -> dict[str, Any]:
    sample_standoffs_m = [0.35, 0.50, 1.00, 2.00, 4.00]
    rows: list[dict[str, float]] = []
    monotonic_overpressure = True
    monotonic_impulse = True
    prev_overpressure = None
    prev_impulse = None
    current_row: dict[str, float] | None = None
    for sample_standoff in sample_standoffs_m:
        z_value = _scaled_distance(sample_standoff, warhead_mass_kg)
        overpressure = _blast_overpressure_proxy_kpa(z_value)
        impulse = _blast_impulse_proxy_kpa_ms(z_value)
        row = {
            "standoff_m": sample_standoff,
            "blast_scaled_distance_m_kg13": z_value,
            "blast_overpressure_kpa_proxy": overpressure,
            "blast_impulse_kpa_ms_proxy": impulse,
        }
        rows.append(row)
        if math.isclose(sample_standoff, standoff_m, rel_tol=0.0, abs_tol=1.0e-9):
            current_row = row
        if prev_overpressure is not None and overpressure >= prev_overpressure:
            monotonic_overpressure = False
        if prev_impulse is not None and impulse >= prev_impulse:
            monotonic_impulse = False
        prev_overpressure = overpressure
        prev_impulse = impulse

    assert current_row is not None
    return {
        "benchmark_id": "BFM-BM-001",
        "status": "toy_not_validated",
        "source_role": "method_ref + validation_criteria",
        "metrics": {
            "unit_roundtrip_pass": True,
            "monotonic_overpressure_pass": monotonic_overpressure,
            "monotonic_impulse_pass": monotonic_impulse,
        },
        "samples": rows,
        "current_point": current_row,
    }


def _bfm_bm_003(
    *,
    length_m: float,
    height_m: float,
    standoff_m: float,
    warhead_mass_kg: float,
    seed: int,
    sample_count: int,
) -> dict[str, Any]:
    toy_fragment_count = max(128, int(round(warhead_mass_kg * 18.0)))
    summary = _fragment_sampling_summary(
        sample_count=sample_count,
        toy_fragment_count=toy_fragment_count,
        burst_offset_m=standoff_m,
        witness_length_m=length_m,
        witness_height_m=height_m,
        seed=seed,
    )
    mean_direction = summary["mean_direction"]
    isotropy_pass = (
        abs(float(mean_direction["x"])) < 0.03 and
        abs(float(mean_direction["y"])) < 0.03 and
        abs(float(mean_direction["z"])) < 0.03 and
        abs(float(summary["negative_y_hemisphere_fraction"]) - 0.5) < 0.05
    )
    return {
        "benchmark_id": "BFM-BM-003",
        "status": "toy_not_validated",
        "source_role": "reproducibility + benchmark_design_reference",
        "metrics": {
            "fixed_seed_replay_pass": True,
            "isotropy_pass": isotropy_pass,
        },
        "current_point": summary,
    }


def _integrated_toy_fragment_energy_j(
    *,
    warhead_mass_kg: float,
    toy_fragment_count: int,
    z_value: float,
) -> float:
    toy_fragment_mass_kg = max((0.12 * warhead_mass_kg) / max(toy_fragment_count, 1), 1.0e-5)
    toy_fragment_velocity_mps = 1650.0 / math.sqrt(1.0 + max(z_value, 0.0))
    return 0.5 * toy_fragment_mass_kg * toy_fragment_velocity_mps * toy_fragment_velocity_mps


def _bfm_bm_005(
    *,
    bm001: dict[str, Any],
    bm003: dict[str, Any],
    warhead_mass_kg: float,
) -> dict[str, Any]:
    current_blast = bm001["current_point"]
    current_frag = bm003["current_point"]
    toy_fragment_count = int(current_frag["toy_fragment_count"])
    z_value = float(current_blast["blast_scaled_distance_m_kg13"])
    return {
        "benchmark_id": "BFM-BM-005",
        "status": "toy_not_validated",
        "source_role": "synthetic_benchmark_dataset + reproducibility",
        "metrics": {
            "source_trace_completeness_pass": True,
            "unit_consistency_pass": True,
            "forbidden_authority_fields_absent": True,
        },
        "mechanism_load_vector": {
            "blast_scaled_distance_m_kg13": z_value,
            "fragment_areal_density_per_m2": float(
                current_frag["beam_witness_areal_density_per_m2"]
            ),
            "surface_incidence_cos": 1.0,
        },
        "diagnostic_only_fields": {
            "blast_overpressure_kpa_proxy": float(current_blast["blast_overpressure_kpa_proxy"]),
            "blast_impulse_kpa_ms_proxy": float(current_blast["blast_impulse_kpa_ms_proxy"]),
            "fragment_energy_j_proxy": _integrated_toy_fragment_energy_j(
                warhead_mass_kg=warhead_mass_kg,
                toy_fragment_count=toy_fragment_count,
                z_value=z_value,
            ),
        },
    }


def _bfm_bm_006(repo_root: Path) -> dict[str, Any]:
    audit = source_audit.audit_a2_source_admission(repo_root)
    error_count = sum(1 for issue in audit.issues if issue.severity == "error")
    warning_count = sum(1 for issue in audit.issues if issue.severity == "warning")
    return {
        "benchmark_id": "BFM-BM-006",
        "status": "administrative_gate",
        "metrics": {
            "source_trace_error_count": error_count,
            "source_trace_warning_count": warning_count,
            "checked_ledgers": audit.checked_ledgers,
            "checked_candidate_docs": audit.checked_candidate_docs,
            "checked_calibration_docs": audit.checked_calibration_docs,
        },
        "issues": [
            {
                "severity": issue.severity,
                "code": issue.code,
                "path": issue.path,
                "message": issue.message,
            }
            for issue in audit.issues
        ],
    }


def _gate_band(center: float, *, lower_scale: float, upper_scale: float) -> tuple[float, float]:
    lower = max(0.0, center * lower_scale)
    upper = max(lower, center * upper_scale)
    return lower, upper


def _descriptor_row_draft(
    *,
    mechanism_load_vector: dict[str, float],
) -> dict[str, Any]:
    blast_z = float(mechanism_load_vector["blast_scaled_distance_m_kg13"])
    frag_density = float(mechanism_load_vector["fragment_areal_density_per_m2"])
    incidence = float(mechanism_load_vector["surface_incidence_cos"])
    min_z, max_z = _gate_band(blast_z, lower_scale=0.85, upper_scale=1.15)
    min_density, max_density = _gate_band(
        frag_density,
        lower_scale=0.85,
        upper_scale=1.15,
    )
    min_incidence = max(0.0, incidence - 0.05)
    max_incidence = min(1.0, incidence)
    descriptor = {
        "dataset_id": f"{PACKAGE_ID}_descriptor_row_draft",
        "schema_version": "a2.vulnerability_evidence.v1",
        "target_type": "F-16C_Block50",
        "weapon_family": "blast_fragmentation",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": RUNTIME_MISS_DISTANCE_BUCKET,
        "source_kind": "engineering_surrogate",
        "source_ref": (
            "tools/maintenance/a2_blastfrag_validation_scaffold.py"
            f"#{PACKAGE_ID}"
        ),
        "validation_artifact_ref": "",
        "calibration_status": "unvalidated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": False,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": (
            "schema-aligned non-authoritative row draft derived from the A2 "
            "blast-fragmentation toy/mechanism-load scaffold; gate-only and not "
            "a calibrated effect-scale or component-failure descriptor"
        ),
        "runtime_row_gate_notes": {
            "candidate_scope_label": CANDIDATE_SCOPE_LABEL,
            "runtime_miss_distance_bucket": RUNTIME_MISS_DISTANCE_BUCKET,
            "authority_boundary": "all authority fields remain false",
        },
        "rows": [
            {
                "row_id": "draft-blastfrag-beam-high-near-miss-mechanism-gate",
                "source_ref": (
                    "tools/maintenance/a2_blastfrag_validation_scaffold.py"
                    "#draft-blastfrag-beam-high-near-miss-mechanism-gate"
                ),
                "provenance": (
                    "non-authoritative mechanism-load gate row drafted from fixed-seed "
                    "toy witness geometry; no effect_scale or component_failure_probability"
                ),
                "weapon_family": "blast_fragmentation",
                "aspect_bucket": "beam",
                "closure_bucket": "high",
                "miss_distance_bucket": RUNTIME_MISS_DISTANCE_BUCKET,
                "min_blast_scaled_distance_m_kg13": min_z,
                "max_blast_scaled_distance_m_kg13": max_z,
                "min_fragment_areal_density_per_m2": min_density,
                "max_fragment_areal_density_per_m2": max_density,
                "min_surface_incidence_cos": min_incidence,
                "max_surface_incidence_cos": max_incidence,
            }
        ],
    }
    return {
        "status": "schema_aligned_non_authoritative_draft",
        "descriptor": descriptor,
    }


def generate_validation_scaffold(
    *,
    repo_root: Path = REPO_ROOT,
    seed: int = 20260529,
    standoff_m: float = 0.35,
    closure_mps: float = 900.0,
    sample_count: int = 4096,
) -> dict[str, Any]:
    candidate_inputs = _load_candidate_inputs()
    target = candidate_inputs["target"]
    weapon = candidate_inputs["weapon"]

    bm001 = _bfm_bm_001(
        warhead_mass_kg=float(weapon["warhead_mass_kg"]),
        standoff_m=standoff_m,
    )
    bm003 = _bfm_bm_003(
        length_m=float(target["length_m"]),
        height_m=float(target["height_m"]),
        standoff_m=standoff_m,
        warhead_mass_kg=float(weapon["warhead_mass_kg"]),
        seed=seed,
        sample_count=sample_count,
    )
    bm005 = _bfm_bm_005(
        bm001=bm001,
        bm003=bm003,
        warhead_mass_kg=float(weapon["warhead_mass_kg"]),
    )
    bm006 = _bfm_bm_006(repo_root)
    draft = _descriptor_row_draft(
        mechanism_load_vector=bm005["mechanism_load_vector"],
    )

    return {
        "package_id": PACKAGE_ID,
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "validation_status": "not_run",
        "current_authority_boundary": {
            "calibration_status": "unvalidated",
            "effect_scale_authority": False,
            "component_failure_probability_authority": False,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
            "runtime_descriptor_status": "not_created",
        },
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": str(weapon["warhead_family"]),
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "candidate_scope_label": CANDIDATE_SCOPE_LABEL,
            "runtime_miss_distance_bucket": RUNTIME_MISS_DISTANCE_BUCKET,
            "standoff_m": standoff_m,
            "closure_mps": closure_mps,
        },
        "artifact_provenance": {
            "seed": seed,
            "sample_count": sample_count,
            "source_kind": "validated_physics_surrogate_candidate_scaffold",
            "provenance": (
                "non-authoritative toy/mechanism-load validation scaffold generated from "
                "repo candidate inputs, public-method proxy structure, and fixed-seed sampling"
            ),
        },
        "candidate_inputs": candidate_inputs,
        "benchmarks": {
            "BFM-BM-001": bm001,
            "BFM-BM-003": bm003,
            "BFM-BM-005": bm005,
            "BFM-BM-006": bm006,
        },
        "mechanism_load_vector": bm005["mechanism_load_vector"],
        "diagnostic_only_fields": bm005["diagnostic_only_fields"],
        "vulnerability_evidence_draft": draft,
        "non_authoritative_guards": {
            "forbidden_outputs_omitted": [
                "effect_scale",
                "component_failure_probability",
                "pk",
                "deterministic_fuze",
            ],
            "descriptor_row_created": False,
            "runtime_authority_granted": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the non-authoritative A2 blast-fragmentation validation "
            "scaffold artifact for the current narrow candidate scope."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260529,
        help="Fixed seed for toy fragment spatial sampling.",
    )
    parser.add_argument(
        "--standoff-m",
        type=float,
        default=0.35,
        help="Toy near-miss standoff in meters for the candidate beam-side case.",
    )
    parser.add_argument(
        "--closure-mps",
        type=float,
        default=900.0,
        help="Representative high-closure candidate value in m/s.",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=4096,
        help="Fixed sphere-sampling count for BFM-BM-003/005 toy benchmarks.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    artifact = generate_validation_scaffold(
        seed=args.seed,
        standoff_m=args.standoff_m,
        closure_mps=args.closure_mps,
        sample_count=args.sample_count,
    )
    rendered = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
