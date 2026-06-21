"""Scalar producer/consumer ledger for decoupled lethality diagnostics."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from tools.diagnostics import lethality_chain_contract as chain_contract
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    _finite_float,
)


SCALAR_LEDGER_SCHEMA_VERSION = "kill_chain_scalar_coupling_ledger.v1"


def _finite_or_none(value: Any) -> float | None:
    out = _finite_float(value, float("nan"))
    return out if math.isfinite(out) else None


def _latest_row(rows: list[dict[str, Any]], stage: str) -> dict[str, Any] | None:
    matches = [row for row in rows if str(row.get("stage", "") or "") == str(stage)]
    return matches[-1] if matches else None


def _rows_by_chain(rows: list[dict[str, Any]]) -> dict[tuple[int, int], list[dict[str, Any]]]:
    out: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in rows:
        chain_id = int(row.get("chain_id", 0) or 0)
        if chain_id <= 0:
            continue
        episode = int(row.get("episode", 0) or 0)
        out.setdefault((episode, chain_id), []).append(row)
    return out


def _value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "string"


def _entry(
    *,
    episode: int,
    chain_id: int,
    scalar_id: str,
    current_owner_stage: str,
    intended_owner_stage: str,
    producer_stage: str,
    producer_field: str,
    observed_value: Any,
    semantic_role: str,
    consumer_fields: list[str] | None = None,
    coupling_flags: list[str] | None = None,
    migration_hint: str = "",
    calibration_ready: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": SCALAR_LEDGER_SCHEMA_VERSION,
        "episode": int(episode),
        "chain_id": int(chain_id),
        "scalar_id": str(scalar_id),
        "current_owner_stage": str(current_owner_stage),
        "intended_owner_stage": str(intended_owner_stage),
        "producer_stage": str(producer_stage),
        "producer_field": str(producer_field),
        "observed_value": observed_value,
        "observed_value_kind": _value_kind(observed_value),
        "semantic_role": str(semantic_role),
        "consumer_fields": list(consumer_fields or []),
        "coupling_flags": list(coupling_flags or []),
        "migration_hint": str(migration_hint),
        "calibration_ready": bool(calibration_ready),
    }


def _add_numeric_entry(
    out: list[dict[str, Any]],
    *,
    row: dict[str, Any] | None,
    field: str,
    scalar_id: str,
    current_owner_stage: str,
    intended_owner_stage: str,
    semantic_role: str,
    consumer_fields: list[str] | None = None,
    coupling_flags: list[str] | None = None,
    migration_hint: str = "",
    calibration_ready: bool = False,
) -> None:
    if row is None:
        return
    value = _finite_or_none(row.get(field, float("nan")))
    if value is None:
        return
    out.append(
        _entry(
            episode=int(row.get("episode", 0) or 0),
            chain_id=int(row.get("chain_id", 0) or 0),
            scalar_id=scalar_id,
            current_owner_stage=current_owner_stage,
            intended_owner_stage=intended_owner_stage,
            producer_stage=str(row.get("stage", current_owner_stage) or current_owner_stage),
            producer_field=field,
            observed_value=value,
            semantic_role=semantic_role,
            consumer_fields=consumer_fields,
            coupling_flags=coupling_flags,
            migration_hint=migration_hint,
            calibration_ready=calibration_ready,
        )
    )


def _parse_effect_scale_from_trace(trace: str) -> float | None:
    match = re.search(r"(?:^|,)effect_scale=([-+0-9.eE]+)", str(trace or ""))
    if not match:
        return None
    return _finite_or_none(match.group(1))


def _chain_scalar_ledger(
    chain_rows: list[dict[str, Any]],
    component_response_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    nearest = _latest_row(chain_rows, chain_contract.STAGE_NEAREST_APPROACH)
    fuze = _latest_row(chain_rows, chain_contract.STAGE_FUZE)
    warhead = _latest_row(chain_rows, chain_contract.STAGE_WARHEAD_MECHANISM)
    spatial = _latest_row(chain_rows, chain_contract.STAGE_SPATIAL_COVERAGE)
    component_load = _latest_row(chain_rows, chain_contract.STAGE_COMPONENT_LOAD)
    component_damage = _latest_row(chain_rows, chain_contract.STAGE_COMPONENT_DAMAGE)
    platform = _latest_row(chain_rows, chain_contract.STAGE_PLATFORM_CONSEQUENCE)

    out: list[dict[str, Any]] = []
    _add_numeric_entry(
        out,
        row=nearest,
        field="miss_distance_m",
        scalar_id="approach.miss_distance_m",
        current_owner_stage="approach",
        intended_owner_stage="approach",
        semantic_role="nearest approach geometry",
        consumer_fields=[
            "fuze_decision.sensor_opportunity_score",
            "fuze_decision.mechanism_coverage_score",
            "warhead_load_field.component_distance_m",
            "warhead_load_field.component_effect_scale",
        ],
        coupling_flags=["range_geometry_reused_across_stages"],
        migration_hint="keep as approach fact; downstream stages should consume named geometry input",
        calibration_ready=False,
    )
    _add_numeric_entry(
        out,
        row=nearest,
        field="closure_mps",
        scalar_id="approach.closure_mps",
        current_owner_stage="approach",
        intended_owner_stage="approach",
        semantic_role="closing-speed geometry",
        consumer_fields=[
            "fuze_decision.target_detection_confidence",
            "warhead_load_field.fragment_energy_j",
            "consequence_projection.vulnerability_scale_trace",
        ],
        coupling_flags=["closure_reused_across_stages"],
        migration_hint="keep as approach fact; do not hide closure inside generic effect scales",
    )

    _add_numeric_entry(
        out,
        row=fuze,
        field="fuze_reliability",
        scalar_id="fuze.reliability",
        current_owner_stage="fuze_decision",
        intended_owner_stage="fuze_decision",
        semantic_role="fuze reliability / detonation gate",
        consumer_fields=["fuze_decision.detonation_probability"],
        migration_hint="retain in fuze decision only",
        calibration_ready=True,
    )
    _add_numeric_entry(
        out,
        row=fuze,
        field="fuze_expected_detonation_probability",
        scalar_id="fuze.detonation_probability",
        current_owner_stage="fuze_decision",
        intended_owner_stage="fuze_decision",
        semantic_role="expected detonation probability",
        consumer_fields=["fuze_decision.sampled_outcome"],
        migration_hint="retain as fuze outcome probability, not warhead load scalar",
        calibration_ready=True,
    )
    _add_numeric_entry(
        out,
        row=fuze,
        field="fuze_sensor_opportunity_score",
        scalar_id="fuze.sensor_opportunity_score",
        current_owner_stage="fuze_decision",
        intended_owner_stage="fuze_decision",
        semantic_role="sensor window score",
        consumer_fields=["fuze_decision.detonation_probability"],
        migration_hint="retain in fuze decision diagnostics",
        calibration_ready=True,
    )
    _add_numeric_entry(
        out,
        row=fuze,
        field="fuze_mechanism_coverage_score",
        scalar_id="fuze.mechanism_coverage_score",
        current_owner_stage="fuze_decision",
        intended_owner_stage="warhead_load_field",
        semantic_role="mechanism coverage leaking through fuze event",
        consumer_fields=["fuze_decision.target_detection_confidence", "effects_event.quality"],
        coupling_flags=["mechanism_coverage_produced_in_fuze_stage"],
        migration_hint="move mechanism coverage into named warhead/load-field factors",
        calibration_ready=False,
    )

    for field, scalar_id, role in (
        ("lethal_radius_m", "warhead.lethal_radius_m", "warhead lethal/projection radius"),
        ("fragment_energy_j", "warhead.fragment_energy_j", "fragment kinetic energy load"),
        ("fragment_density_per_m2", "warhead.fragment_density_per_m2", "fragment areal density"),
        ("blast_overpressure_kpa", "warhead.blast_overpressure_kpa", "blast overpressure load"),
        ("blast_impulse_kpa_ms", "warhead.blast_impulse_kpa_ms", "blast impulse load"),
        ("penetration_margin", "warhead.penetration_margin", "fragment penetration margin"),
        ("rod_cut_margin", "warhead.rod_cut_margin", "continuous rod cut margin"),
    ):
        _add_numeric_entry(
            out,
            row=warhead,
            field=field,
            scalar_id=scalar_id,
            current_owner_stage="warhead_load_field",
            intended_owner_stage="warhead_load_field",
            semantic_role=role,
            consumer_fields=["component_response.failure_probability"],
            migration_hint="retain as load fact; response probability belongs downstream",
            calibration_ready=True,
        )

    for field, scalar_id, role in (
        ("spatial_hit_estimate", "spatial.hit_estimate", "spatial receiver hit estimate"),
        ("spatial_hit_fraction", "spatial.hit_fraction", "spatial receiver hit fraction"),
        ("spatial_energy_scale", "spatial.energy_scale", "spatial energy transmission"),
        ("spatial_pattern_scale", "spatial.pattern_scale", "warhead pattern weight"),
    ):
        _add_numeric_entry(
            out,
            row=spatial,
            field=field,
            scalar_id=scalar_id,
            current_owner_stage="warhead_load_field",
            intended_owner_stage="warhead_load_field",
            semantic_role=role,
            consumer_fields=["warhead_load_field.component_effect_scale"],
            migration_hint="keep as named load-field factor instead of opaque effect scale",
            calibration_ready=True,
        )

    _add_numeric_entry(
        out,
        row=component_load,
        field="component_distance_m",
        scalar_id="component_load.distance_m",
        current_owner_stage="warhead_load_field",
        intended_owner_stage="warhead_load_field",
        semantic_role="component-specific standoff distance",
        consumer_fields=["component_load.component_effect_scale", "component_response.failure_probability"],
        coupling_flags=["component_distance_reused_by_load_and_response"],
        migration_hint="keep as load geometry fact; avoid repeated response-layer range penalties",
    )
    _add_numeric_entry(
        out,
        row=component_load,
        field="component_effect_scale",
        scalar_id="component_load.effect_scale",
        current_owner_stage="warhead_load_field",
        intended_owner_stage="warhead_load_field",
        semantic_role="opaque composite projection/load scale",
        consumer_fields=[
            "component_response.failure_probability",
            "component_response.integrity_delta",
            "consequence_projection.vulnerability_scale_trace",
        ],
        coupling_flags=["composite_effect_scale_crosses_stage_boundary"],
        migration_hint="split into spatial_intersection, pattern, exposure, armor, sampling, and load intensity factors",
        calibration_ready=False,
    )
    for field, scalar_id, role in (
        (
            "component_spatial_intersection_fraction",
            "component_load.spatial_intersection_fraction",
            "component-level spatial intersection/load coverage factor",
        ),
        (
            "component_pattern_weight",
            "component_load.pattern_weight",
            "component-level warhead pattern weight",
        ),
        (
            "component_orientation_weight",
            "component_load.orientation_weight",
            "component-level orientation factor",
        ),
        (
            "component_receiver_exposure_fraction",
            "component_load.receiver_exposure_fraction",
            "component-level receiver exposure factor",
        ),
        (
            "component_armor_transmission",
            "component_load.armor_transmission",
            "component-level armor/transmission factor",
        ),
        (
            "component_sampling_confidence",
            "component_load.sampling_confidence",
            "component-level load projection confidence",
        ),
        (
            "component_load_intensity_scale",
            "component_load.load_intensity_scale",
            "component-level aggregate load-intensity factor",
        ),
    ):
        _add_numeric_entry(
            out,
            row=component_load,
            field=field,
            scalar_id=scalar_id,
            current_owner_stage="warhead_load_field",
            intended_owner_stage="warhead_load_field",
            semantic_role=role,
            consumer_fields=[
                "component_load.effect_scale_decomposition",
                "component_response.failure_probability",
            ],
            coupling_flags=["component_load_named_factor_available"],
            migration_hint="use named load factors before retuning opaque component_load.effect_scale",
            calibration_ready=False,
        )
    response_sources = list(component_response_rows or [])
    if not response_sources and component_damage is not None:
        response_sources = [component_damage]
    for response_source in response_sources:
        _add_numeric_entry(
            out,
            row=response_source,
            field="failure_probability",
            scalar_id="component_response.failure_probability",
            current_owner_stage="component_response",
            intended_owner_stage="component_response",
            semantic_role="component failure probability",
            consumer_fields=[
                "component_response.sampled_failure",
                "consequence_projection.system_delta",
            ],
            coupling_flags=[],
            migration_hint="make this the only probability-producing stage",
            calibration_ready=True,
        )
        if "failure_probability" not in response_source:
            _add_numeric_entry(
                out,
                row=response_source,
                field="component_failure_probability",
                scalar_id="component_response.failure_probability",
                current_owner_stage="component_response",
                intended_owner_stage="component_response",
                semantic_role="component failure probability",
                consumer_fields=[
                    "component_response.sampled_failure",
                    "consequence_projection.system_delta",
                ],
                coupling_flags=[],
                migration_hint="make this the only probability-producing stage",
                calibration_ready=True,
            )
        before = _finite_or_none(
            response_source.get(
                "integrity_before",
                response_source.get("component_integrity_before"),
            )
        )
        after = _finite_or_none(
            response_source.get(
                "integrity_after",
                response_source.get("component_integrity_after"),
            )
        )
        if before is not None and after is not None:
            out.append(
                _entry(
                    episode=int(response_source.get("episode", 0) or 0),
                    chain_id=int(response_source.get("chain_id", 0) or 0),
                    scalar_id="component_response.integrity_delta",
                    current_owner_stage="component_response",
                    intended_owner_stage="component_response",
                    producer_stage=str(
                        response_source.get("stage", "component_response") or ""
                    ),
                    producer_field="component_integrity_after-before",
                    observed_value=after - before,
                    semantic_role="component integrity state change",
                    consumer_fields=["consequence_projection.system_delta"],
                    migration_hint="retain as response state fact",
                    calibration_ready=True,
                )
            )

    if platform is not None:
        trace = str(platform.get("vulnerability_scale_trace", "") or "")
        vulnerability_effect_scale = _parse_effect_scale_from_trace(trace)
        if vulnerability_effect_scale is not None:
            out.append(
                _entry(
                    episode=int(platform.get("episode", 0) or 0),
                    chain_id=int(platform.get("chain_id", 0) or 0),
                    scalar_id="consequence.vulnerability_effect_scale",
                    current_owner_stage="consequence_projection",
                    intended_owner_stage="component_response",
                    producer_stage=str(platform.get("stage", "platform_consequence") or ""),
                    producer_field="vulnerability_scale_trace.effect_scale",
                    observed_value=vulnerability_effect_scale,
                    semantic_role="vulnerability/effect scaling visible in consequence trace",
                    consumer_fields=["consequence_projection.system_delta"],
                    coupling_flags=["vulnerability_effect_scale_visible_in_consequence"],
                    migration_hint="keep target susceptibility in response layer, consequence should consume response facts",
                    calibration_ready=False,
                )
            )
        for field, scalar_id in (
            ("system_health_delta", "consequence.system_health_delta"),
            ("mission_capability_delta", "consequence.mission_capability_delta"),
            ("mobility_capability_delta", "consequence.mobility_capability_delta"),
            ("sensor_capability_delta", "consequence.sensor_capability_delta"),
            ("survivability_margin_delta", "consequence.survivability_margin_delta"),
        ):
            _add_numeric_entry(
                out,
                row=platform,
                field=field,
                scalar_id=scalar_id,
                current_owner_stage="consequence_projection",
                intended_owner_stage="consequence_projection",
                semantic_role="platform consequence delta",
                consumer_fields=[],
                migration_hint="retain as consequence-only output",
                calibration_ready=False,
            )

    return out


def _lethality_chain_scalar_ledger(
    chain_rows: list[dict[str, Any]],
    component_response_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    rows_by_chain = _rows_by_chain(chain_rows)
    response_rows_by_chain = _rows_by_chain(list(component_response_rows or []))
    for key in sorted(set(rows_by_chain) | set(response_rows_by_chain)):
        ledger.extend(
            _chain_scalar_ledger(
                rows_by_chain.get(key, []),
                component_response_rows=response_rows_by_chain.get(key, []),
            )
        )
    return ledger


def _effect_summary_scalar_ledger(
    *,
    effect_summary: dict[str, Any],
    episode: int = 0,
    chain_id: int = 0,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(
        scalar_id: str,
        field: str,
        *,
        current_owner_stage: str,
        intended_owner_stage: str,
        semantic_role: str,
        consumer_fields: list[str] | None = None,
        coupling_flags: list[str] | None = None,
        migration_hint: str = "",
        calibration_ready: bool = False,
    ) -> None:
        value = _finite_or_none(effect_summary.get(field))
        if value is None:
            return
        out.append(
            _entry(
                episode=int(episode),
                chain_id=int(chain_id),
                scalar_id=scalar_id,
                current_owner_stage=current_owner_stage,
                intended_owner_stage=intended_owner_stage,
                producer_stage="effects_event",
                producer_field=field,
                observed_value=value,
                semantic_role=semantic_role,
                consumer_fields=consumer_fields,
                coupling_flags=coupling_flags,
                migration_hint=migration_hint,
                calibration_ready=calibration_ready,
            )
        )

    add(
        "effects_event.fuze_quality",
        "quality",
        current_owner_stage="effects_event",
        intended_owner_stage="fuze_decision",
        semantic_role="fuze quality carried into effects event",
        consumer_fields=["fuze_decision.quality"],
        coupling_flags=[],
        migration_hint="retain as fuze confidence/diagnostic only",
        calibration_ready=False,
    )
    add(
        "effects_event.spatial_effect_scale",
        "spatial_effect_scale",
        current_owner_stage="effects_event",
        intended_owner_stage="warhead_load_field",
        semantic_role="aggregate spatial effect scale",
        consumer_fields=[
            "component_response.failure_probability",
            "component_response.integrity_delta",
            "consequence_projection.vulnerability_scale_trace",
        ],
        coupling_flags=["aggregate_spatial_effect_scale_crosses_stage_boundary"],
        migration_hint="replace with named load-field factors",
        calibration_ready=False,
    )
    for scalar_id, field, role in (
        (
            "effects_event.warhead_spatial_hit_estimate",
            "warhead_spatial_hit_estimate",
            "spatial intersection estimate for effect-scale decomposition",
        ),
        (
            "effects_event.warhead_spatial_hit_fraction",
            "warhead_spatial_hit_fraction",
            "spatial hit fraction for effect-scale decomposition",
        ),
        (
            "effects_event.warhead_spatial_energy_scale",
            "warhead_spatial_energy_scale",
            "spatial energy-transfer factor for effect-scale decomposition",
        ),
        (
            "effects_event.warhead_spatial_pattern_scale",
            "warhead_spatial_pattern_scale",
            "spatial pattern factor for effect-scale decomposition",
        ),
        (
            "effects_event.warhead_orientation_pattern_scale",
            "warhead_orientation_pattern_scale",
            "orientation pattern factor for effect-scale decomposition",
        ),
    ):
        add(
            scalar_id,
            field,
            current_owner_stage="effects_event",
            intended_owner_stage="warhead_load_field",
            semantic_role=role,
            consumer_fields=[
                "warhead_load_field.component_effect_scale",
                "component_response.failure_probability",
            ],
            coupling_flags=["effect_scale_decomposition_factor_available"],
            migration_hint="surface as named load-field input before retuning aggregate effect_scale",
            calibration_ready=False,
        )
    for scalar_id, field, role in (
        (
            "effects_event.mechanism_armor_scale",
            "mechanism_armor_scale",
            "armor attenuation factor for mechanism/load decomposition",
        ),
        (
            "effects_event.mechanism_exposure_scale",
            "mechanism_exposure_scale",
            "component exposure factor for mechanism/load decomposition",
        ),
    ):
        add(
            scalar_id,
            field,
            current_owner_stage="effects_event",
            intended_owner_stage="warhead_load_field",
            semantic_role=role,
            consumer_fields=[
                "effects_event.mechanism_effect_scale",
                "component_load.effect_scale",
                "component_response.failure_probability",
            ],
            coupling_flags=["effect_scale_decomposition_factor_available"],
            migration_hint="split aggregate mechanism/effect scale into named physical factors",
            calibration_ready=False,
        )
    add(
        "effects_event.mechanism_effect_scale",
        "mechanism_effect_scale",
        current_owner_stage="effects_event",
        intended_owner_stage="warhead_load_field",
        semantic_role="aggregate mechanism/load scale",
        consumer_fields=["component_response.failure_probability", "consequence_projection.system_delta"],
        coupling_flags=["aggregate_mechanism_scale_crosses_stage_boundary"],
        migration_hint="replace with explicit fragment/blast/rod load channels",
        calibration_ready=False,
    )
    add(
        "effects_event.component_threshold_scale",
        "component_threshold_scale",
        current_owner_stage="effects_event",
        intended_owner_stage="component_response",
        semantic_role="component fragility/threshold response factor",
        consumer_fields=[
            "component_response.failure_probability",
            "component_response.failure_mode",
        ],
        coupling_flags=["component_threshold_response_factor_aggregated_in_effects_event"],
        migration_hint="keep as response-layer susceptibility input, not load-field intensity",
        calibration_ready=False,
    )
    add(
        "effects_event.component_failure_probability",
        "component_failure_probability",
        current_owner_stage="effects_event",
        intended_owner_stage="component_response",
        semantic_role="effects-event aggregate response probability",
        consumer_fields=["component_response.sampled_failure", "consequence_projection.system_delta"],
        coupling_flags=["effects_event_aggregates_response_probability"],
        migration_hint="prefer component_response rows as probability authority",
        calibration_ready=True,
    )
    add(
        "effects_event.component_max_failure_probability",
        "component_max_failure_probability",
        current_owner_stage="effects_event",
        intended_owner_stage="component_response",
        semantic_role="max component-row response probability",
        consumer_fields=["diagnostics.max_probability_summary"],
        coupling_flags=["effects_event_aggregates_response_probability"],
        migration_hint="keep as diagnostic summary, not load-field input",
        calibration_ready=True,
    )
    for scalar_id, field, role in (
        (
            "effects_event.vulnerability_family_scale",
            "vulnerability_family_scale",
            "target-family susceptibility factor",
        ),
        (
            "effects_event.vulnerability_aspect_scale",
            "vulnerability_aspect_scale",
            "target-aspect susceptibility factor",
        ),
        (
            "effects_event.vulnerability_closure_scale",
            "vulnerability_closure_scale",
            "closure-speed susceptibility factor",
        ),
        (
            "effects_event.vulnerability_miss_distance_scale",
            "vulnerability_miss_distance_scale",
            "miss-distance susceptibility factor",
        ),
        (
            "effects_event.vulnerability_effect_scale",
            "vulnerability_effect_scale",
            "aggregate vulnerability/effect response scale",
        ),
    ):
        add(
            scalar_id,
            field,
            current_owner_stage="effects_event",
            intended_owner_stage="component_response",
            semantic_role=role,
            consumer_fields=[
                "component_response.failure_probability",
                "consequence_projection.vulnerability_scale_trace",
            ],
            coupling_flags=["vulnerability_response_factor_aggregated_in_effects_event"],
            migration_hint="keep susceptibility factors in component_response before consequence projection",
            calibration_ready=False,
        )
    return out


def _scalar_coupling_summary(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    flag_counts = Counter(
        str(flag)
        for row in ledger
        for flag in list(row.get("coupling_flags", []) or [])
    )
    owner_counts = Counter(str(row.get("current_owner_stage", "") or "") for row in ledger)
    intended_counts = Counter(str(row.get("intended_owner_stage", "") or "") for row in ledger)
    cross_owner_rows = [
        str(row.get("scalar_id", "") or "")
        for row in ledger
        if str(row.get("current_owner_stage", "") or "")
        != str(row.get("intended_owner_stage", "") or "")
    ]
    return {
        "schema_version": SCALAR_LEDGER_SCHEMA_VERSION,
        "scalar_count": len(ledger),
        "current_owner_counts": dict(sorted(owner_counts.items())),
        "intended_owner_counts": dict(sorted(intended_counts.items())),
        "coupling_flag_counts": dict(sorted(flag_counts.items())),
        "cross_owner_scalar_ids": sorted(set(cross_owner_rows)),
        "calibration_ready_scalar_count": int(
            sum(1 for row in ledger if bool(row.get("calibration_ready", False)))
        ),
        "authority_boundary": {
            "runtime_parameter_retuning": False,
            "real_world_pk": False,
            "deterministic_fuze_authority": False,
            "calibration_authority": False,
        },
    }
