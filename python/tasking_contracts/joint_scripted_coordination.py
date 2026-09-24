"""Neutral scripted coordination producer for a declared cross-domain task graph.

This module owns only the common task-graph declaration and a small
coordination intent payload. Domain execution, geometry, sensors, weapons, and
effects remain outside the producer. The implementation is dependency-terminal
and does not import RL, NumPy, native bindings, or a simulation runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .scripted_registry import (
    ScriptedDecisionModel,
    ScriptedModelRegistration,
    ScriptedModelRegistry,
)


SCRIPTED_JOINT_TASK_GRAPH_VERSION = "scripted_joint_task_graph.v1"
JOINT_SCRIPTED_COORDINATION_MODEL_ID = "joint.coordination.task_graph_scripted"


def _text(value: Any, *, field_name: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"joint task graph {field_name} must be non-empty")
    return result


def _positive_int(value: Any, *, field_name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"joint task graph {field_name} must be a positive integer") from exc
    if result <= 0:
        raise ValueError(f"joint task graph {field_name} must be a positive integer")
    return result


def _string_tuple(raw: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise TypeError(f"joint task graph {field_name} must be a list")
    values = tuple(_text(item, field_name=field_name) for item in raw)
    if len(set(values)) != len(values):
        raise ValueError(f"joint task graph {field_name} must be unique")
    return values


@dataclass(frozen=True)
class ScriptedJointNodeSpec:
    """Common metadata for one domain-owned node in a joint task graph."""

    node_id: str
    domain: str
    role_id: str
    service_profile: str
    task_group_id: int
    coordination_mode: str
    authority_scope: str
    payload_ref: str
    active: bool = True

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ScriptedJointNodeSpec":
        if not isinstance(raw, Mapping):
            raise TypeError("joint task graph node must be a mapping")
        return cls(
            node_id=_text(raw.get("node_id"), field_name="node_id"),
            domain=_text(raw.get("domain"), field_name="domain").lower(),
            role_id=_text(raw.get("role_id"), field_name="role_id"),
            service_profile=_text(raw.get("service_profile"), field_name="service_profile"),
            task_group_id=_positive_int(raw.get("task_group_id"), field_name="task_group_id"),
            coordination_mode=_text(raw.get("coordination_mode"), field_name="coordination_mode"),
            authority_scope=_text(raw.get("authority_scope"), field_name="authority_scope"),
            payload_ref=_text(raw.get("payload_ref"), field_name="payload_ref"),
            active=bool(raw.get("active", True)),
        )


@dataclass(frozen=True)
class ScriptedJointAuthorityEdge:
    """Authority or support relationship between two declared graph nodes."""

    parent_node_id: str
    child_node_id: str
    relationship: str
    supporting_node_id: str | None = None
    supported_node_id: str | None = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ScriptedJointAuthorityEdge":
        if not isinstance(raw, Mapping):
            raise TypeError("joint task graph authority edge must be a mapping")
        supporting = raw.get("supporting_node_id")
        supported = raw.get("supported_node_id")
        return cls(
            parent_node_id=_text(raw.get("parent_node_id"), field_name="parent_node_id"),
            child_node_id=_text(raw.get("child_node_id"), field_name="child_node_id"),
            relationship=_text(raw.get("relationship"), field_name="relationship"),
            supporting_node_id=None if supporting is None else _text(supporting, field_name="supporting_node_id"),
            supported_node_id=None if supported is None else _text(supported, field_name="supported_node_id"),
        )


@dataclass(frozen=True)
class ScriptedJointTaskGraph:
    """Versioned common task graph; domain payloads remain referenced only."""

    version: str
    graph_id: str
    task_group_id: int
    coordination_mode: str
    nodes: tuple[ScriptedJointNodeSpec, ...]
    authority_edges: tuple[ScriptedJointAuthorityEdge, ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ScriptedJointTaskGraph":
        if not isinstance(raw, Mapping):
            raise TypeError("joint task graph must be a mapping")
        version = _text(raw.get("version"), field_name="version")
        if version != SCRIPTED_JOINT_TASK_GRAPH_VERSION:
            raise ValueError(f"unsupported joint task graph version: {version!r}")
        raw_nodes = raw.get("nodes")
        if not isinstance(raw_nodes, (list, tuple)) or not raw_nodes:
            raise ValueError("joint task graph nodes must be a non-empty list")
        nodes = tuple(ScriptedJointNodeSpec.from_mapping(item) for item in raw_nodes)
        node_ids = tuple(node.node_id for node in nodes)
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("joint task graph node_id values must be unique")
        raw_edges = raw.get("authority_edges", [])
        if not isinstance(raw_edges, (list, tuple)):
            raise TypeError("joint task graph authority_edges must be a list")
        edges = tuple(ScriptedJointAuthorityEdge.from_mapping(item) for item in raw_edges)
        node_id_set = set(node_ids)
        for edge in edges:
            endpoints = (edge.parent_node_id, edge.child_node_id)
            if any(endpoint not in node_id_set for endpoint in endpoints):
                raise ValueError("joint task graph authority edge references an unknown node")
            for support_node in (edge.supporting_node_id, edge.supported_node_id):
                if support_node is not None and support_node not in node_id_set:
                    raise ValueError("joint task graph support edge references an unknown node")
        task_group_id = _positive_int(raw.get("task_group_id"), field_name="task_group_id")
        if any(node.task_group_id != task_group_id for node in nodes):
            raise ValueError("joint task graph node task_group_id must match graph task_group_id")
        return cls(
            version=version,
            graph_id=_text(raw.get("graph_id"), field_name="graph_id"),
            task_group_id=task_group_id,
            coordination_mode=_text(raw.get("coordination_mode"), field_name="coordination_mode"),
            nodes=nodes,
            authority_edges=edges,
        )

    def active_node_ids(self) -> tuple[str, ...]:
        return tuple(node.node_id for node in self.nodes if node.active)


@dataclass(frozen=True)
class ScriptedJointCoordinationIntent:
    """Opaque action payload emitted by the joint producer."""

    producer_id: str
    graph_id: str
    task_group_id: int
    coordination_mode: str
    target_node_ids: tuple[str, ...]
    clock_s: float
    observation_version: str
    communication_state: str
    authority_scope: str


class ScriptedJointCoordinationModel:
    """Emit graph-scoped coordination intents without reading domain geometry."""

    def __init__(self, *, producer_id: str = "joint:director") -> None:
        self.producer_id = _text(producer_id, field_name="producer_id")
        self._graph: ScriptedJointTaskGraph | None = None
        self._closed = False

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("joint scripted coordination reset requires a mapping context")
        raw_graph = context.get("task_graph")
        if isinstance(raw_graph, ScriptedJointTaskGraph):
            graph = raw_graph
        elif isinstance(raw_graph, Mapping):
            graph = ScriptedJointTaskGraph.from_mapping(raw_graph)
        else:
            raise TypeError("joint scripted coordination reset requires context['task_graph']")
        self.producer_id = _text(context.get("agent_id", self.producer_id), field_name="agent_id")
        self._graph = graph
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> ScriptedJointCoordinationIntent:
        del observation, dt
        if self._closed:
            raise RuntimeError("joint scripted coordination model is closed")
        if self._graph is None:
            raise RuntimeError("joint scripted coordination model must be reset before deciding")
        model_context = context if isinstance(context, Mapping) else {}
        return ScriptedJointCoordinationIntent(
            producer_id=self.producer_id,
            graph_id=self._graph.graph_id,
            task_group_id=self._graph.task_group_id,
            coordination_mode=self._graph.coordination_mode,
            target_node_ids=self._graph.active_node_ids(),
            clock_s=float(model_context.get("clock_s", 0.0)),
            observation_version=str(model_context.get("observation_version", "")),
            communication_state=str(model_context.get("communication_state", "available")),
            authority_scope=str(model_context.get("authority_scope", "unspecified")),
        )

    def close(self) -> None:
        self._graph = None
        self._closed = True


def make_joint_scripted_coordination_model(**kwargs: Any) -> ScriptedJointCoordinationModel:
    return ScriptedJointCoordinationModel(**kwargs)


JOINT_SCRIPTED_MODEL_REGISTRY = ScriptedModelRegistry(
    (
        ScriptedModelRegistration(
            model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
            domain="joint",
            role_ids=("joint_coordination_director",),
            factory=make_joint_scripted_coordination_model,
            status="adapter",
            note=(
                "Versioned task-graph coordination producer; domain execution "
                "and command-link consumers remain open."
            ),
        ),
    )
)


__all__ = [
    "JOINT_SCRIPTED_COORDINATION_MODEL_ID",
    "JOINT_SCRIPTED_MODEL_REGISTRY",
    "SCRIPTED_JOINT_TASK_GRAPH_VERSION",
    "ScriptedJointAuthorityEdge",
    "ScriptedJointCoordinationIntent",
    "ScriptedJointCoordinationModel",
    "ScriptedJointNodeSpec",
    "ScriptedJointTaskGraph",
    "make_joint_scripted_coordination_model",
]
