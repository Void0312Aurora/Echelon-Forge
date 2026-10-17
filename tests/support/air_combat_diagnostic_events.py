from __future__ import annotations

from types import SimpleNamespace


def _entity(entity_id: int) -> SimpleNamespace:
  return SimpleNamespace(entity_id=int(entity_id), world_index=0)


def _header(
  *,
  chain_id: int,
  event_id: int,
  parent_event_id: int,
  stage: str,
  status: str,
  reason: str,
  munition_id: int = 501,
  target_id: int = 200,
  consumer_visibility: str | None = None,
) -> SimpleNamespace:
  values = {
    "schema_version": 1,
    "chain_id": int(chain_id),
    "event_id": int(event_id),
    "parent_event_id": int(parent_event_id),
    "stage": str(stage),
    "status": str(status),
    "reason": str(reason),
    "source_time_s": 4.25,
    "source_frame": 0,
    "munition": _entity(munition_id),
    "shooter": _entity(100),
    "target": _entity(target_id),
    "producer_node_id": "test",
    "fidelity_mode": "runtime",
    "evidence_level": "observed_runtime",
    "confidence": 1.0,
  }
  if consumer_visibility is not None:
    values["consumer_visibility"] = str(consumer_visibility)
  return SimpleNamespace(**values)


def _standard_warhead_event(
  *, consumer_visibility: str | None = None
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=104,
      parent_event_id=101,
      stage="warhead_mechanism",
      status="applied",
      reason="generic_research_warhead_profile",
      target_id=200,
      consumer_visibility=consumer_visibility,
    ),
    mechanism_family="blast_fragmentation",
    warhead_mass_kg=12.0,
    lethal_radius_m=35.0,
    fragment_energy_j=540.0,
    fragment_density_per_m2=17.0,
    blast_overpressure_kpa=18.0,
    blast_impulse_kpa_ms=41.0,
    blast_scaled_distance_m_kg13=2.5,
    rod_cut_margin=0.0,
    penetration_margin=0.35,
    surface_incidence_cos=0.8,
  )


def _standard_component_load_event(
  *, consumer_visibility: str | None = None
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=106,
      parent_event_id=101,
      stage="component_load",
      status="projected",
      reason="generic_research_component_load_projection",
      target_id=200,
      consumer_visibility=consumer_visibility,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    direct_hit=True,
    distance_m=0.7,
    effect_scale=0.83,
    fragment_energy_j=420.0,
    fragment_density_per_m2=13.0,
    blast_overpressure_kpa=14.0,
    blast_impulse_kpa_ms=32.0,
    blast_scaled_distance_m_kg13=2.7,
    rod_cut_margin=0.0,
    penetration_margin=0.25,
    surface_incidence_cos=0.9,
    load_source="direct_component_hit",
  )


def _standard_component_damage_event(
  *, consumer_visibility: str | None = None
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=107,
      parent_event_id=106,
      stage="component_damage",
      status="sampled",
      reason="generic_research_component_damage_candidate",
      target_id=200,
      consumer_visibility=consumer_visibility,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    component_redundancy_group_id="flight_control:right_aileron",
    integrity_before=1.0,
    integrity_after=0.68,
    failure_mode="cut",
    failure_severity=0.74,
    failure_probability=0.82,
    failure_sample=0.21,
  )
