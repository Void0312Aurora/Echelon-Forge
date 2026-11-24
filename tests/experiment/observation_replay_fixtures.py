"""Pure DTO fixtures shared by observation replay and session tests."""

from __future__ import annotations

from types import SimpleNamespace

from python.experiment.observation_replay import AGENT_OBSERVATION_FLOAT_FIELDS


def make_observation_packet(ref, step, *, scope="baseline") -> SimpleNamespace:
    """Build a full single-Agent packet without importing a native binding."""
    observation = SimpleNamespace(**dict.fromkeys(AGENT_OBSERVATION_FLOAT_FIELDS, 0.0))
    observation.id = ref.entity_id
    observation.sim_time = float(step)
    observation.health = 100.0
    observation.speed = 120.0
    observation.missiles_remaining = 0
    observation.can_fire = False
    observation.contacts = []
    observation.rwr_warnings = []
    observation.esm_detections = []
    version = 1 if scope == "baseline" else step + 1
    packet_id = f"obs:facade:{version}" if scope == "baseline" else f"obs:branch:{scope}:{version}"
    source_version = f"global:{version}" if scope == "baseline" else f"branch:{scope}:{version}"
    return SimpleNamespace(
        snapshot_version=version,
        barrier_id="export",
        source_time_s=float(step),
        refs=[SimpleNamespace(world_index=ref.world_index, entity_id=ref.entity_id)],
        agent_observations=[observation],
        instrument_states=[],
        provenance=SimpleNamespace(
            information_state_layer="AgentObservation",
            source_label="facade_observation_packet",
            maintained_status="maintained",
            observation_packet_ids=[packet_id],
            source_observation_versions=[source_version],
            diagnostics_reason="",
        ),
    )
