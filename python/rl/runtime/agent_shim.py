from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


MAINTAINED = "maintained"
COMPATIBILITY_ADAPTER = "compatibility_adapter"
DIAGNOSTICS_ONLY = "diagnostics_only"

ALLOWED_MAINTAINED_STATUSES = (
    MAINTAINED,
    COMPATIBILITY_ADAPTER,
    DIAGNOSTICS_ONLY,
)

MERGE_LAST_WRITE_WINS = "last_write_wins"
MERGE_PRIORITY_OVERRIDE = "priority_override"
MERGE_REJECT_ON_CONFLICT = "reject_on_conflict"
MERGE_BY_FIELD = "merge_by_field"
MERGE_APPEND_ONLY = "append_only"

ALLOWED_MERGE_POLICIES = (
    MERGE_LAST_WRITE_WINS,
    MERGE_PRIORITY_OVERRIDE,
    MERGE_REJECT_ON_CONFLICT,
    MERGE_BY_FIELD,
    MERGE_APPEND_ONLY,
)

OBS_FACADE_OBSERVATION_PACKET = "facade_observation_packet"
OBS_AGENT_OBSERVATION_COMPAT = "agent_observation_compat"
OBS_RAW_WORLD_TRUTH = "raw_world_truth"
OBS_DIAGNOSTICS_ORACLE = "diagnostics_oracle"

OBSERVATION_PROVENANCE_LABELS = MappingProxyType(
    {
        OBS_FACADE_OBSERVATION_PACKET: {
            "information_state_layer": "AgentObservation",
            "source_surface": "ObservationBatchPacket",
            "maintained_status": MAINTAINED,
        },
        OBS_AGENT_OBSERVATION_COMPAT: {
            "information_state_layer": "AgentObservation",
            "source_surface": "get_agent_observation or get_agent_observations_batch",
            "maintained_status": COMPATIBILITY_ADAPTER,
        },
        OBS_RAW_WORLD_TRUTH: {
            "information_state_layer": "WorldTruth",
            "source_surface": "raw runtime or SimulationKernel",
            "maintained_status": DIAGNOSTICS_ONLY,
        },
        OBS_DIAGNOSTICS_ORACLE: {
            "information_state_layer": "DecisionBelief",
            "source_surface": "teacher, oracle, debug, or privileged helper",
            "maintained_status": DIAGNOSTICS_ONLY,
        },
    }
)


def _normalize_status(value: str) -> str:
    normalized = str(value).strip()
    if normalized not in ALLOWED_MAINTAINED_STATUSES:
        raise ValueError(f"unknown maintained status: {value!r}")
    return normalized


def _normalize_merge_policy(value: str) -> str:
    normalized = str(value).strip()
    if normalized not in ALLOWED_MERGE_POLICIES:
        raise ValueError(f"unknown merge policy: {value!r}")
    return normalized


def _copy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


@dataclass(frozen=True)
class ObservationProvenance:
    """Passive label describing whether an observation/belief input is policy-safe."""

    label: str
    information_state_layer: str
    source_surface: str
    maintained_status: str = COMPATIBILITY_ADAPTER
    source_layer: str = "adapter"
    consumed_snapshot_version: str | None = None
    observation_packet_id: str | None = None
    diagnostics_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", str(self.label))
        object.__setattr__(self, "information_state_layer", str(self.information_state_layer))
        object.__setattr__(self, "source_surface", str(self.source_surface))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "source_layer", str(self.source_layer))
        object.__setattr__(self, "diagnostics_note", str(self.diagnostics_note))

    @property
    def is_maintained(self) -> bool:
        return self.maintained_status == MAINTAINED

    @property
    def is_diagnostics_only(self) -> bool:
        return self.maintained_status == DIAGNOSTICS_ONLY

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "information_state_layer": self.information_state_layer,
            "source_surface": self.source_surface,
            "maintained_status": self.maintained_status,
            "source_layer": self.source_layer,
            "consumed_snapshot_version": self.consumed_snapshot_version,
            "observation_packet_id": self.observation_packet_id,
            "diagnostics_note": self.diagnostics_note,
        }


def observation_provenance(
    label: str,
    *,
    consumed_snapshot_version: str | None = None,
    observation_packet_id: str | None = None,
    diagnostics_note: str = "",
    source_layer: str = "adapter",
) -> ObservationProvenance:
    """Build a provenance label from the WP4-H maintained/compat/oracle vocabulary."""

    spec = OBSERVATION_PROVENANCE_LABELS.get(str(label))
    if spec is None:
        raise ValueError(f"unknown observation provenance label: {label!r}")
    return ObservationProvenance(
        label=str(label),
        information_state_layer=str(spec["information_state_layer"]),
        source_surface=str(spec["source_surface"]),
        maintained_status=str(spec["maintained_status"]),
        source_layer=str(source_layer),
        consumed_snapshot_version=consumed_snapshot_version,
        observation_packet_id=observation_packet_id,
        diagnostics_note=diagnostics_note,
    )


@dataclass(frozen=True)
class AgentRole:
    """Passive Python-side sketch of the WP4 AgentRole five-element boundary."""

    role_id: str
    role_type: str
    authority_scope: Mapping[str, Any]
    information_state_source: ObservationProvenance
    decision_model_ref: Mapping[str, Any]
    action_interface: str
    maintained_status: str = COMPATIBILITY_ADAPTER
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", str(self.role_id))
        object.__setattr__(self, "role_type", str(self.role_type))
        object.__setattr__(self, "authority_scope", _copy_mapping(self.authority_scope))
        object.__setattr__(self, "decision_model_ref", _copy_mapping(self.decision_model_ref))
        object.__setattr__(self, "action_interface", str(self.action_interface))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "metadata", _copy_mapping(self.metadata))

    def five_elements(self) -> dict[str, Any]:
        return {
            "role": {
                "role_id": self.role_id,
                "role_type": self.role_type,
            },
            "authority_scope": dict(self.authority_scope),
            "information_state_source": self.information_state_source.as_dict(),
            "decision_model_ref": dict(self.decision_model_ref),
            "action_interface": self.action_interface,
        }

    def as_dict(self) -> dict[str, Any]:
        out = self.five_elements()
        out["maintained_status"] = self.maintained_status
        out["metadata"] = dict(self.metadata)
        return out


def single_agent_role(
    *,
    agent_id: int,
    world_index: int | None = None,
    role_type: str = "autopilot_controller",
    information_state_source: ObservationProvenance | None = None,
    decision_model_kind: str = "external_policy",
    decision_model_id: str = "caller_supplied",
    action_interface: str = "PilotActionAssignmentCompat",
    maintained_status: str = COMPATIBILITY_ADAPTER,
) -> AgentRole:
    authority_scope: dict[str, Any] = {"entity_ids": [int(agent_id)]}
    if world_index is not None:
        authority_scope["world_index"] = int(world_index)
    return AgentRole(
        role_id=f"agent:{'' if world_index is None else f'{int(world_index)}:'}{int(agent_id)}",
        role_type=role_type,
        authority_scope=authority_scope,
        information_state_source=information_state_source
        or observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
        decision_model_ref={"kind": decision_model_kind, "id": decision_model_id},
        action_interface=action_interface,
        maintained_status=maintained_status,
    )


def roster_slot_role(
    *,
    world_index: int,
    entity_id: int,
    roster_index: int,
    role_code: int | None = None,
    formation_role_id: str | None = None,
    policy_route: str | None = None,
    information_state_source: ObservationProvenance | None = None,
) -> AgentRole:
    role_type = "roster_slot"
    if formation_role_id:
        role_type = str(formation_role_id)
    return AgentRole(
        role_id=f"roster:{int(world_index)}:{int(roster_index)}:{int(entity_id)}",
        role_type=role_type,
        authority_scope={
            "world_index": int(world_index),
            "entity_ids": [int(entity_id)],
            "roster_index": int(roster_index),
            "role_code": None if role_code is None else int(role_code),
            "formation_role_id": formation_role_id,
        },
        information_state_source=information_state_source
        or observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
        decision_model_ref={
            "kind": "policy_route" if policy_route else "external_policy",
            "id": str(policy_route or "caller_supplied"),
        },
        action_interface="PilotActionAssignmentCompat",
        maintained_status=COMPATIBILITY_ADAPTER,
    )


@dataclass(frozen=True)
class ActionIntentCompat:
    """Metadata wrapper for existing PilotAction / WorldPilotActionAssignment paths."""

    role: AgentRole
    payload: Any
    source_layer: str = "policy"
    source_id: str | None = None
    input_snapshot_version: str | None = None
    effective_time: float | None = None
    valid_until: float | None = None
    merge_policy: str = MERGE_LAST_WRITE_WINS
    action_family: str = "direct_control"
    target_entity_id: int | None = None
    target_world_index: int | None = None
    payload_kind: str = "PilotActionAssignmentCompat"
    maintained_status: str = COMPATIBILITY_ADAPTER
    diagnostics_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_layer", str(self.source_layer))
        object.__setattr__(self, "source_id", str(self.source_id or self.role.role_id))
        object.__setattr__(self, "merge_policy", _normalize_merge_policy(self.merge_policy))
        object.__setattr__(self, "action_family", str(self.action_family))
        object.__setattr__(self, "payload_kind", str(self.payload_kind))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "diagnostics_note", str(self.diagnostics_note))

    @classmethod
    def from_pilot_assignment(
        cls,
        assignment: Any,
        *,
        role: AgentRole,
        source_layer: str = "policy",
        source_id: str | None = None,
        input_snapshot_version: str | None = None,
        effective_time: float | None = None,
        valid_until: float | None = None,
        merge_policy: str = MERGE_LAST_WRITE_WINS,
    ) -> "ActionIntentCompat":
        return cls(
            role=role,
            payload=getattr(assignment, "action", assignment),
            source_layer=source_layer,
            source_id=source_id,
            input_snapshot_version=input_snapshot_version,
            effective_time=effective_time,
            valid_until=valid_until,
            merge_policy=merge_policy,
            target_entity_id=getattr(assignment, "entity_id", None),
            target_world_index=getattr(assignment, "world_index", None),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role.role_id,
            "source_layer": self.source_layer,
            "source_id": self.source_id,
            "input_snapshot_version": self.input_snapshot_version,
            "effective_time": self.effective_time,
            "valid_until": self.valid_until,
            "merge_policy": self.merge_policy,
            "action_family": self.action_family,
            "target_entity_id": self.target_entity_id,
            "target_world_index": self.target_world_index,
            "payload_kind": self.payload_kind,
            "maintained_status": self.maintained_status,
            "diagnostics_note": self.diagnostics_note,
        }


@dataclass(frozen=True)
class CoordinationIntentCompat:
    """Metadata wrapper for current command-chain assignment paths."""

    role: AgentRole
    mission_command: Any = None
    task_order: Any = None
    leader_intent: Any = None
    pilot_report: Any = None
    source_layer: str = "policy"
    source_id: str | None = None
    input_snapshot_version: str | None = None
    effective_time: float | None = None
    valid_until: float | None = None
    update_clock: str = "adapter_step"
    merge_policy: str = MERGE_LAST_WRITE_WINS
    roster_scope: Mapping[str, Any] = field(default_factory=dict)
    payload_kind: str = "CommandChainAssignmentCompat"
    maintained_status: str = COMPATIBILITY_ADAPTER
    diagnostics_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_layer", str(self.source_layer))
        object.__setattr__(self, "source_id", str(self.source_id or self.role.role_id))
        object.__setattr__(self, "update_clock", str(self.update_clock))
        object.__setattr__(self, "merge_policy", _normalize_merge_policy(self.merge_policy))
        object.__setattr__(self, "roster_scope", _copy_mapping(self.roster_scope))
        object.__setattr__(self, "payload_kind", str(self.payload_kind))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "diagnostics_note", str(self.diagnostics_note))

    def payload_fields(self) -> tuple[str, ...]:
        fields = []
        if self.mission_command is not None:
            fields.append("mission_command")
        if self.task_order is not None:
            fields.append("task_order")
        if self.leader_intent is not None:
            fields.append("leader_intent")
        if self.pilot_report is not None:
            fields.append("pilot_report")
        return tuple(fields)

    def as_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role.role_id,
            "source_layer": self.source_layer,
            "source_id": self.source_id,
            "input_snapshot_version": self.input_snapshot_version,
            "effective_time": self.effective_time,
            "valid_until": self.valid_until,
            "update_clock": self.update_clock,
            "merge_policy": self.merge_policy,
            "roster_scope": dict(self.roster_scope),
            "payload_fields": self.payload_fields(),
            "payload_kind": self.payload_kind,
            "maintained_status": self.maintained_status,
            "diagnostics_note": self.diagnostics_note,
        }


__all__ = [
    "ALLOWED_MAINTAINED_STATUSES",
    "ALLOWED_MERGE_POLICIES",
    "COMPATIBILITY_ADAPTER",
    "DIAGNOSTICS_ONLY",
    "MAINTAINED",
    "MERGE_APPEND_ONLY",
    "MERGE_BY_FIELD",
    "MERGE_LAST_WRITE_WINS",
    "MERGE_PRIORITY_OVERRIDE",
    "MERGE_REJECT_ON_CONFLICT",
    "OBS_AGENT_OBSERVATION_COMPAT",
    "OBS_DIAGNOSTICS_ORACLE",
    "OBS_FACADE_OBSERVATION_PACKET",
    "OBS_RAW_WORLD_TRUTH",
    "OBSERVATION_PROVENANCE_LABELS",
    "ActionIntentCompat",
    "AgentRole",
    "CoordinationIntentCompat",
    "ObservationProvenance",
    "observation_provenance",
    "roster_slot_role",
    "single_agent_role",
]
