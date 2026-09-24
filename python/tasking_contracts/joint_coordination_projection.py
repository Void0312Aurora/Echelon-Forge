"""Optional projection from the neutral joint intent to the compiled DTO.

The neutral producer stays dependency-terminal. Callers supply the compiled
binding module explicitly, so this adapter can be tested with a local build
without making the scripted runtime depend on native bindings. Fields absent
from the current ``CoordinationIntentPacket`` are reported as residuals
instead of being silently encoded into unrelated DTO fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .joint_scripted_coordination import ScriptedJointCoordinationIntent


@dataclass(frozen=True)
class JointCoordinationPacketProjection:
    """Compiled packet plus common fields not represented by the DTO yet."""

    packet: Any
    omitted_fields: tuple[str, ...]


def project_joint_intent_to_compiled_packet(
    intent: ScriptedJointCoordinationIntent,
    *,
    binding_module: Any,
) -> JointCoordinationPacketProjection:
    """Build a ``CoordinationIntentPacket`` without importing ``ef_py`` here."""

    if not isinstance(intent, ScriptedJointCoordinationIntent):
        raise TypeError("joint coordination projection requires ScriptedJointCoordinationIntent")
    packet_type = getattr(binding_module, "CoordinationIntentPacket", None)
    ref_type = getattr(binding_module, "ProducedIntentRef", None)
    if not callable(packet_type) or not callable(ref_type):
        raise TypeError("binding module must expose CoordinationIntentPacket and ProducedIntentRef")

    packet = packet_type()
    packet.source_type = "scripted"
    packet.source_id = str(intent.producer_id)
    packet.update_clock = "runtime_clock"
    packet.merge_policy = "last_write_wins"
    packet.target_roster.roster_id = str(intent.graph_id)
    packet.produced_tasking_refs = [
        _make_tasking_ref(ref_type, node_id) for node_id in intent.target_node_ids
    ]
    return JointCoordinationPacketProjection(
        packet=packet,
        omitted_fields=(
            "task_group_id",
            "coordination_mode",
            "clock_s",
            "observation_version",
            "communication_state",
            "authority_scope",
        ),
    )


def _make_tasking_ref(ref_type: Any, node_id: str) -> Any:
    ref = ref_type()
    ref.kind = "joint_task_node"
    ref.reference_id = str(node_id)
    return ref


__all__ = [
    "JointCoordinationPacketProjection",
    "project_joint_intent_to_compiled_packet",
]
