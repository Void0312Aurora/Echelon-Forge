"""Qualification-only typed mechanism port graph prototype.

The compiler validates a small semantic graph before any native/provider
publication.  It does not execute mechanisms or admit plugins; production
composition and scheduler evidence remain owned by the native contracts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "echelon_forge.mechanism_ports.v1"


@dataclass(frozen=True)
class PortSpec:
    name: str
    schema: str
    unit: str | None = None
    frame: str | None = None
    visibility: str = "belief"
    required: bool = True

    def __post_init__(self) -> None:
        for field_name in ("name", "schema", "visibility"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit.strip()):
            raise ValueError("unit must be a non-empty string when supplied")
        if self.frame is not None and (not isinstance(self.frame, str) or not self.frame.strip()):
            raise ValueError("frame must be a non-empty string when supplied")
        if type(self.required) is not bool:
            raise TypeError("required must be a bool")
        if self.visibility not in {"belief", "truth", "agent_observation", "effect"}:
            raise ValueError(f"unsupported visibility: {self.visibility!r}")


@dataclass(frozen=True)
class MechanismSpec:
    mechanism_id: str
    version: str
    inputs: tuple[PortSpec, ...] = ()
    outputs: tuple[PortSpec, ...] = ()
    stateful: bool = False
    clock: str = "window"
    delay_windows: int = 0
    implementation_ref: str = "qualification.stub"
    required_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.mechanism_id.strip() or not self.version.strip():
            raise ValueError("mechanism_id and version are required")
        if self.clock not in {"window", "per_second", "per_tick"}:
            raise ValueError(f"unsupported mechanism clock: {self.clock!r}")
        if isinstance(self.delay_windows, bool) or self.delay_windows < 0:
            raise ValueError("delay_windows must be a non-negative integer")
        if not isinstance(self.stateful, bool):
            raise TypeError("stateful must be a bool")
        for ports, side in ((self.inputs, "input"), (self.outputs, "output")):
            if len({port.name for port in ports}) != len(ports):
                raise ValueError(f"duplicate {side} port name")
        if self.clock == "per_second" and not self.stateful:
            raise ValueError("per_second mechanism must declare stateful=True")

    def port(self, name: str, *, output: bool) -> PortSpec | None:
        ports = self.outputs if output else self.inputs
        return next((port for port in ports if port.name == name), None)


@dataclass(frozen=True)
class GraphEdge:
    source_node: str
    source_port: str
    target_node: str
    target_port: str
    delayed: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (self.source_node, self.source_port, self.target_node, self.target_port)):
            raise ValueError("graph edge node and port names are required")
        if not isinstance(self.delayed, bool):
            raise TypeError("delayed must be a bool")


@dataclass(frozen=True)
class GraphDiagnostic:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class CompiledMechanismGraph:
    graph_id: str
    nodes: tuple[tuple[str, MechanismSpec], ...]
    edges: tuple[GraphEdge, ...]
    diagnostics: tuple[GraphDiagnostic, ...]
    identity_digest: str
    schema_version: str = SCHEMA_VERSION

    @property
    def valid(self) -> bool:
        return not self.diagnostics

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_id": self.graph_id,
            "nodes": [
                {
                    "id": node_id,
                    "mechanism_id": spec.mechanism_id,
                    "version": spec.version,
                    "inputs": [_port_dict(port) for port in spec.inputs],
                    "outputs": [_port_dict(port) for port in spec.outputs],
                    "stateful": spec.stateful,
                    "clock": spec.clock,
                    "delay_windows": spec.delay_windows,
                    "implementation_ref": spec.implementation_ref,
                    "required_capabilities": list(spec.required_capabilities),
                }
                for node_id, spec in self.nodes
            ],
            "edges": [edge.__dict__ for edge in self.edges],
            "diagnostics": [diagnostic.__dict__ for diagnostic in self.diagnostics],
            "identity_digest": self.identity_digest,
        }


class MechanismGraphError(ValueError):
    """Raised only when graph construction inputs are malformed."""


def _port_dict(port: PortSpec) -> dict[str, Any]:
    return {
        "name": port.name,
        "schema": port.schema,
        "unit": port.unit,
        "frame": port.frame,
        "visibility": port.visibility,
        "required": port.required,
    }


def _identity_payload(graph_id: str, nodes: Mapping[str, MechanismSpec], edges: Sequence[GraphEdge]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_id": graph_id,
        "nodes": {
            node_id: {
                "mechanism_id": spec.mechanism_id,
                "version": spec.version,
                "inputs": [_port_dict(port) for port in spec.inputs],
                "outputs": [_port_dict(port) for port in spec.outputs],
                "stateful": spec.stateful,
                "clock": spec.clock,
                "delay_windows": spec.delay_windows,
                "implementation_ref": spec.implementation_ref,
                "required_capabilities": sorted(spec.required_capabilities),
            }
            for node_id, spec in sorted(nodes.items())
        },
        "edges": [edge.__dict__ for edge in sorted(edges, key=lambda item: (item.source_node, item.source_port, item.target_node, item.target_port, item.delayed))],
    }


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compile_mechanism_graph(
    graph_id: str,
    nodes: Mapping[str, MechanismSpec],
    edges: Sequence[GraphEdge],
    *,
    external_inputs: frozenset[str] = frozenset(),
) -> CompiledMechanismGraph:
    """Validate a graph and return a non-published qualification artifact."""

    if not graph_id.strip():
        raise MechanismGraphError("graph_id is required")
    if not nodes:
        raise MechanismGraphError("at least one mechanism node is required")
    diagnostics: list[GraphDiagnostic] = []
    incoming: dict[tuple[str, str], list[GraphEdge]] = {}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge_index, edge in enumerate(edges):
        path = f"edges[{edge_index}]"
        source = nodes.get(edge.source_node)
        target = nodes.get(edge.target_node)
        if source is None:
            diagnostics.append(GraphDiagnostic("mechanism.node_unknown", f"{path}.source_node", edge.source_node))
            continue
        if target is None:
            diagnostics.append(GraphDiagnostic("mechanism.node_unknown", f"{path}.target_node", edge.target_node))
            continue
        source_port = source.port(edge.source_port, output=True)
        target_port = target.port(edge.target_port, output=False)
        if source_port is None:
            diagnostics.append(GraphDiagnostic("mechanism.output_unknown", f"{path}.source_port", edge.source_port))
        if target_port is None:
            diagnostics.append(GraphDiagnostic("mechanism.input_unknown", f"{path}.target_port", edge.target_port))
        if source_port is None or target_port is None:
            continue
        if source_port.schema != target_port.schema:
            diagnostics.append(GraphDiagnostic("mechanism.schema_incompatible", path, f"{source_port.schema} -> {target_port.schema}"))
        if source_port.unit != target_port.unit:
            diagnostics.append(GraphDiagnostic("mechanism.unit_incompatible", path, f"{source_port.unit!r} -> {target_port.unit!r}"))
        if source_port.frame != target_port.frame:
            diagnostics.append(GraphDiagnostic("mechanism.frame_incompatible", path, f"{source_port.frame!r} -> {target_port.frame!r}"))
        if source_port.visibility == "truth" and target_port.visibility == "agent_observation":
            diagnostics.append(GraphDiagnostic("mechanism.truth_boundary_violation", path, "truth output cannot directly feed agent observation"))
        incoming.setdefault((edge.target_node, edge.target_port), []).append(edge)
        if not edge.delayed:
            adjacency[edge.source_node].append(edge.target_node)

    for node_id, spec in nodes.items():
        for port in spec.inputs:
            key = (node_id, port.name)
            if port.required and key not in incoming and f"{node_id}.{port.name}" not in external_inputs:
                diagnostics.append(GraphDiagnostic("mechanism.required_input_missing", f"nodes.{node_id}.inputs.{port.name}", "no producer or declared external input"))

    # A DFS over instantaneous edges rejects same-window cycles. Delayed edges
    # are intentionally excluded and therefore represent an explicit feedback
    # boundary rather than an accidental recursive execution path.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: tuple[str, ...]) -> None:
        if node_id in visiting:
            diagnostics.append(GraphDiagnostic("mechanism.instantaneous_cycle", "graph", " -> ".join(path + (node_id,))))
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in adjacency[node_id]:
            visit(child, path + (node_id,))
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in nodes:
        visit(node_id, ())

    payload = _identity_payload(graph_id, nodes, edges)
    return CompiledMechanismGraph(
        graph_id=graph_id,
        nodes=tuple(sorted(nodes.items())),
        edges=tuple(edges),
        diagnostics=tuple(diagnostics),
        identity_digest=_digest(payload),
    )


def compose_graph_as_mechanism(
    graph: CompiledMechanismGraph,
    *,
    mechanism_id: str,
    version: str,
    inputs: tuple[PortSpec, ...],
    outputs: tuple[PortSpec, ...],
) -> MechanismSpec:
    """Export a valid graph as a reusable, non-executing composite node."""

    if not graph.valid:
        raise MechanismGraphError("cannot compose an invalid mechanism graph")
    if not mechanism_id.strip() or not version.strip():
        raise MechanismGraphError("composite mechanism identity is required")
    return MechanismSpec(
        mechanism_id=mechanism_id,
        version=version,
        inputs=inputs,
        outputs=outputs,
        stateful=any(spec.stateful for _, spec in graph.nodes),
        clock="window",
        delay_windows=0,
        implementation_ref=f"composite:{graph.identity_digest}",
    )


__all__ = [
    "CompiledMechanismGraph",
    "GraphDiagnostic",
    "GraphEdge",
    "MechanismGraphError",
    "MechanismSpec",
    "PortSpec",
    "SCHEMA_VERSION",
    "compile_mechanism_graph",
    "compose_graph_as_mechanism",
]
