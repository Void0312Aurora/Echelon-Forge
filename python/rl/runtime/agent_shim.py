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
OBS_DECISION_BELIEF_PACKET = "decision_belief_packet"

LAW14_MAINTAINED_READ_LABEL_ALLOWLIST = (
    OBS_FACADE_OBSERVATION_PACKET,
    OBS_DECISION_BELIEF_PACKET,
)

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
        OBS_DECISION_BELIEF_PACKET: {
            "information_state_layer": "DecisionBelief",
            "source_surface": "DecisionBelief",
            "maintained_status": MAINTAINED,
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
    maintained_status: str = MAINTAINED
    source_layer: str = "facade"
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

    def as_information_state_source(self) -> dict[str, Any]:
        packet_ids = []
        if self.observation_packet_id is not None:
            packet_ids.append(self.observation_packet_id)
        versions = []
        if self.consumed_snapshot_version is not None:
            versions.append(self.consumed_snapshot_version)
        return {
            "information_state_layer": self.information_state_layer,
            "source_label": self.label,
            "maintained_status": self.maintained_status,
            "observation_packet_ids": packet_ids,
            "source_observation_versions": versions,
            "diagnostics_reason": self.diagnostics_note,
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


def _validate_maintained_consumer_source(
    information_state_source: ObservationProvenance,
    *,
    consumer_status: str,
) -> None:
    if consumer_status != MAINTAINED:
        return
    if information_state_source.maintained_status != MAINTAINED:
        raise ValueError(
            "maintained consumer fixtures must use provenance-labeled ObservationPacket/DecisionBelief inputs"
        )
    if information_state_source.information_state_layer not in {"AgentObservation", "DecisionBelief"}:
        raise ValueError(
            "maintained consumer fixtures may only consume AgentObservation or DecisionBelief provenance"
        )
    if not information_state_source.label.strip():
        raise ValueError("maintained consumer fixtures require a non-empty provenance label")
    if information_state_source.label not in LAW14_MAINTAINED_READ_LABEL_ALLOWLIST:
        raise ValueError(
            "maintained consumer fixtures may only use the Law 14 ObservationPacket/DecisionBelief read-side allowlist"
        )
    expected_surface = OBSERVATION_PROVENANCE_LABELS[information_state_source.label]["source_surface"]
    if information_state_source.source_surface != expected_surface:
        raise ValueError("maintained consumer fixtures must not relabel privileged or raw surfaces as maintained")


def _validate_maintained_entry_point_role(role: "AgentRole", *, entry_point: str) -> None:
    if role.maintained_status != MAINTAINED:
        raise ValueError(
            f"{entry_point} maintained business entry points require roles with explicit maintained "
            "ObservationPacket/DecisionBelief provenance"
        )
    _validate_maintained_consumer_source(
        role.information_state_source,
        consumer_status=MAINTAINED,
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
    maintained_status: str = MAINTAINED
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", str(self.role_id))
        object.__setattr__(self, "role_type", str(self.role_type))
        object.__setattr__(self, "authority_scope", _copy_mapping(self.authority_scope))
        object.__setattr__(self, "decision_model_ref", _copy_mapping(self.decision_model_ref))
        object.__setattr__(self, "action_interface", str(self.action_interface))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "metadata", _copy_mapping(self.metadata))
        _validate_maintained_consumer_source(
            self.information_state_source,
            consumer_status=self.maintained_status,
        )

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

    def as_contract(self) -> dict[str, Any]:
        authority_scope = dict(self.authority_scope)
        world_index = authority_scope.get("world_index")
        return {
            "role": {
                "role_id": self.role_id,
                "role_type": self.role_type,
            },
            "authority_scope": {
                "scope": str(authority_scope.get("scope", "unspecified")),
                "world_index": 0 if world_index is None else int(world_index),
                "has_world_index": world_index is not None,
                "entity_ids": [int(value) for value in authority_scope.get("entity_ids", ())],
                "roster_id": str(authority_scope.get("roster_id", "")),
                "command_family": str(authority_scope.get("command_family", "")),
            },
            "information_state_source": self.information_state_source.as_information_state_source(),
            "decision_model_ref": dict(self.decision_model_ref),
            "action_interface": {
                "kind": self.action_interface,
                "payload_type": str(self.metadata.get("payload_type", "compatibility_payload")),
            },
        }


def single_agent_role(
    *,
    agent_id: int,
    world_index: int | None = None,
    role_type: str = "autopilot_controller",
    information_state_source: ObservationProvenance | None = None,
    decision_model_kind: str = "external_policy",
    decision_model_id: str = "caller_supplied",
    action_interface: str = "PilotActionAssignmentCompat",
    maintained_status: str = MAINTAINED,
) -> AgentRole:
    authority_scope: dict[str, Any] = {"entity_ids": [int(agent_id)]}
    if world_index is not None:
        authority_scope["world_index"] = int(world_index)
    return AgentRole(
        role_id=f"agent:{'' if world_index is None else f'{int(world_index)}:'}{int(agent_id)}",
        role_type=role_type,
        authority_scope=authority_scope,
        information_state_source=information_state_source
        or observation_provenance(OBS_FACADE_OBSERVATION_PACKET),
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
    maintained_status: str = MAINTAINED,
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
        or observation_provenance(OBS_FACADE_OBSERVATION_PACKET),
        decision_model_ref={
            "kind": "policy_route" if policy_route else "external_policy",
            "id": str(policy_route or "caller_supplied"),
        },
        action_interface="PilotActionAssignmentCompat",
        maintained_status=maintained_status,
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
    maintained_status: str = MAINTAINED
    diagnostics_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_layer", str(self.source_layer))
        object.__setattr__(self, "source_id", str(self.source_id or self.role.role_id))
        object.__setattr__(self, "merge_policy", _normalize_merge_policy(self.merge_policy))
        object.__setattr__(self, "action_family", str(self.action_family))
        object.__setattr__(self, "payload_kind", str(self.payload_kind))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "diagnostics_note", str(self.diagnostics_note))
        if self.maintained_status == MAINTAINED:
            _validate_maintained_entry_point_role(
                self.role,
                entry_point="ActionIntentCompat",
            )

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
        maintained_status: str = MAINTAINED,
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
            maintained_status=maintained_status,
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

    def as_contract(self) -> dict[str, Any]:
        contract = {
            "source_id": self.source_id,
            "effective_time_s": 0.0 if self.effective_time is None else float(self.effective_time),
            "valid_until_s": 0.0 if self.valid_until is None else float(self.valid_until),
            "target": {
                "world_index": 0 if self.target_world_index is None else int(self.target_world_index),
                "entity_id": 0 if self.target_entity_id is None else int(self.target_entity_id),
            },
            "action_family": self.action_family,
            "merge_policy": self.merge_policy,
            "action_interface": {
                "kind": self.payload_kind,
                "payload_type": "pilot_action" if "PilotAction" in self.payload_kind else "mission_command",
            },
            "has_pilot_action": "PilotAction" in self.payload_kind,
            "has_mission_command": "MissionCommand" in self.payload_kind,
        }
        return contract


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
    maintained_status: str = MAINTAINED
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
        if self.maintained_status == MAINTAINED:
            _validate_maintained_entry_point_role(
                self.role,
                entry_point="CoordinationIntentCompat",
            )

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

    def as_contract(self) -> dict[str, Any]:
        authority_scope = dict(self.role.authority_scope)
        world_index = self.roster_scope.get("world_index", authority_scope.get("world_index"))
        produced_tasking_refs = []
        if self.task_order is not None or self.mission_command is not None:
            produced_tasking_refs.append(
                {
                    "kind": "tasking",
                    "reference_id": self.source_id,
                    "target": {
                        "world_index": 0 if world_index is None else int(world_index),
                        "entity_id": 0,
                    },
                }
            )
        produced_leader_intent_refs = []
        if self.leader_intent is not None:
            produced_leader_intent_refs.append(
                {
                    "kind": "leader_intent",
                    "reference_id": self.source_id,
                    "target": {
                        "world_index": 0 if world_index is None else int(world_index),
                        "entity_id": 0,
                    },
                }
            )
        return {
            "source_type": self.source_layer,
            "source_id": self.source_id,
            "target_roster": {
                "world_index": 0 if world_index is None else int(world_index),
                "has_world_index": world_index is not None,
                "roster_id": str(self.roster_scope.get("roster_id", "")),
                "entity_ids": [int(value) for value in self.roster_scope.get("entity_ids", ())],
                "role_ids": [str(value) for value in self.roster_scope.get("role_ids", ())],
            },
            "update_clock": self.update_clock,
            "merge_policy": self.merge_policy,
            "produced_tasking_refs": produced_tasking_refs,
            "produced_leader_intent_refs": produced_leader_intent_refs,
        }


@dataclass(frozen=True)
class DecisionBeliefCompat:
    """Passive Python-side sketch of the DecisionBelief contract boundary."""

    belief_id: str
    source_observation_versions: tuple[str, ...] = ()
    memory_or_estimator_ref: str = ""
    confidence_kind: str = "unspecified"
    confidence: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    maintained_status: str = MAINTAINED
    diagnostics_reason: str = ""
    uses_truth_state: bool = False
    uses_raw_ecs: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "belief_id", str(self.belief_id))
        object.__setattr__(
            self,
            "source_observation_versions",
            tuple(str(value) for value in self.source_observation_versions),
        )
        object.__setattr__(self, "memory_or_estimator_ref", str(self.memory_or_estimator_ref))
        object.__setattr__(self, "confidence_kind", str(self.confidence_kind))
        object.__setattr__(self, "maintained_status", _normalize_status(self.maintained_status))
        object.__setattr__(self, "diagnostics_reason", str(self.diagnostics_reason))

        if (self.uses_truth_state or self.uses_raw_ecs) and self.maintained_status != DIAGNOSTICS_ONLY:
            raise ValueError("truth/raw ECS belief inputs must remain diagnostics_only")

    def as_dict(self) -> dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "source_observation_versions": self.source_observation_versions,
            "memory_or_estimator_ref": self.memory_or_estimator_ref,
            "confidence_shape": {
                "kind": self.confidence_kind,
                "confidence": self.confidence,
                "lower_bound": self.lower_bound,
                "upper_bound": self.upper_bound,
            },
            "maintained_status": self.maintained_status,
            "diagnostics_reason": self.diagnostics_reason,
            "uses_truth_state": self.uses_truth_state,
            "uses_raw_ecs": self.uses_raw_ecs,
        }

    def as_consumable_provenance(
        self,
        *,
        source_layer: str = "policy",
    ) -> ObservationProvenance:
        if self.maintained_status != MAINTAINED:
            raise ValueError("only maintained DecisionBelief inputs may be promoted to maintained read-side provenance")
        return ObservationProvenance(
            label=OBS_DECISION_BELIEF_PACKET,
            information_state_layer="DecisionBelief",
            source_surface="DecisionBelief",
            maintained_status=MAINTAINED,
            source_layer=source_layer,
            consumed_snapshot_version=self.source_observation_versions[-1]
            if self.source_observation_versions
            else None,
            observation_packet_id=self.belief_id,
            diagnostics_note=self.diagnostics_reason,
        )


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
    "OBS_DECISION_BELIEF_PACKET",
    "OBS_DIAGNOSTICS_ORACLE",
    "OBS_FACADE_OBSERVATION_PACKET",
    "OBS_RAW_WORLD_TRUTH",
    "LAW14_MAINTAINED_READ_LABEL_ALLOWLIST",
    "OBSERVATION_PROVENANCE_LABELS",
    "ActionIntentCompat",
    "AgentRole",
    "CoordinationIntentCompat",
    "DecisionBeliefCompat",
    "ObservationProvenance",
    "observation_provenance",
    "roster_slot_role",
    "single_agent_role",
]
