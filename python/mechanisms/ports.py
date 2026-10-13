"""Qualification-only typed mechanism port graph prototype.

The compiler validates a small semantic graph before any native/provider
publication.  It does not execute mechanisms or admit plugins; production
composition and scheduler evidence remain owned by the native contracts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from python.experiment.composition import freeze_json_mapping, freeze_json_value, thaw_json_value

SCHEMA_VERSION = "echelon_forge.mechanism_ports.v1"


@dataclass(frozen=True)
class PortSpec:
    name: str
    schema: str
    unit: str | None = None
    frame: str | None = None
    visibility: str = "belief"
    required: bool = True
    freshness: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("name", "schema", "visibility"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit.strip()):
            raise ValueError("unit must be a non-empty string when supplied")
        if self.frame is not None and (not isinstance(self.frame, str) or not self.frame.strip()):
            raise ValueError("frame must be a non-empty string when supplied")
        if self.freshness is not None and (
            not isinstance(self.freshness, str) or not self.freshness.strip()
        ):
            raise ValueError("freshness must be a non-empty string when supplied")
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
    parameters: Mapping[str, Any] = field(default_factory=dict)
    backend_ref: str = "qualification.unspecified"
    clock_policy: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mechanism_id.strip() or not self.version.strip():
            raise ValueError("mechanism_id and version are required")
        if self.clock not in {"window", "per_second", "per_tick"}:
            raise ValueError(f"unsupported mechanism clock: {self.clock!r}")
        if (
            isinstance(self.delay_windows, bool)
            or not isinstance(self.delay_windows, int)
            or self.delay_windows < 0
        ):
            raise ValueError("delay_windows must be a non-negative integer")
        if not isinstance(self.stateful, bool):
            raise TypeError("stateful must be a bool")
        for ports, side in ((self.inputs, "input"), (self.outputs, "output")):
            if len({port.name for port in ports}) != len(ports):
                raise ValueError(f"duplicate {side} port name")
        if self.clock == "per_second" and not self.stateful:
            raise ValueError("per_second mechanism must declare stateful=True")
        for name in ("implementation_ref", "backend_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        object.__setattr__(self, "parameters", freeze_json_mapping(self.parameters))
        object.__setattr__(self, "clock_policy", freeze_json_mapping(self.clock_policy))

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
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.source_node, self.source_port, self.target_node, self.target_port)
        ):
            raise ValueError("graph edge node and port names are required")
        if not isinstance(self.delayed, bool):
            raise TypeError("delayed must be a bool")


@dataclass(frozen=True)
class GraphDiagnostic:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class NativeStageContractProjection:
    """One authored node mapped to an immutable owner manifest snapshot.

    The projection is evidence for qualification only.  It contains no
    callable, scheduler handle or provider installation request.
    """

    node_id: str
    stage_node_id: str
    owner_module: str
    authored_node: Mapping[str, Any]
    owner_contract: Mapping[str, Any]
    identity_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "stage_node_id": self.stage_node_id,
            "owner_module": self.owner_module,
            "authored_node": thaw_json_value(self.authored_node),
            "owner_contract": thaw_json_value(self.owner_contract),
            "identity_digest": self.identity_digest,
        }


@dataclass(frozen=True)
class StageManifestQualificationProjection:
    """Static graph-to-native contract evidence with a stable identity.

    ``qualification_only`` and ``executable`` are deliberately explicit so a
    downstream consumer cannot mistake this artifact for an executable native
    graph or a scheduler installation plan.
    """

    graph_identity_digest: str
    manifest_registry_digest: str
    node_contracts: tuple[NativeStageContractProjection, ...]
    edge_bindings: tuple[GraphEdge, ...]
    identity_digest: str
    qualification_only: bool = True
    executable: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "graph_identity_digest": self.graph_identity_digest,
            "manifest_registry_digest": self.manifest_registry_digest,
            "node_contracts": [contract.as_dict() for contract in self.node_contracts],
            "edge_bindings": [edge.__dict__ for edge in self.edge_bindings],
            "identity_digest": self.identity_digest,
            "qualification_only": self.qualification_only,
            "executable": self.executable,
        }


@dataclass(frozen=True)
class SchemaVocabularyEntry:
    """One owner-declared schema and the native contract that owns it."""

    schema: str
    owner_ref: str

    def __post_init__(self) -> None:
        for field_name in ("schema", "owner_ref"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class MechanismSchemaVocabulary:
    """Immutable owner vocabulary used to qualify mechanism port schemas.

    This is a qualification artifact.  It identifies the native owner of each
    schema, but it does not publish a dispatcher or create an executable
    contract on its own.
    """

    vocabulary_id: str
    version: str
    entries: tuple[SchemaVocabularyEntry, ...]

    def __post_init__(self) -> None:
        for field_name in ("vocabulary_id", "version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        entries = tuple(self.entries)
        if not entries:
            raise ValueError("entries must not be empty")
        if any(not isinstance(entry, SchemaVocabularyEntry) for entry in entries):
            raise TypeError("entries must contain SchemaVocabularyEntry values")
        schemas = [entry.schema for entry in entries]
        if len(set(schemas)) != len(schemas):
            raise ValueError("schema vocabulary entries must use unique schema names")
        object.__setattr__(self, "entries", entries)

    @property
    def schema_names(self) -> frozenset[str]:
        return frozenset(entry.schema for entry in self.entries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "vocabulary_id": self.vocabulary_id,
            "version": self.version,
            "entries": [
                {"schema": entry.schema, "owner_ref": entry.owner_ref}
                for entry in sorted(self.entries, key=lambda item: item.schema)
            ],
        }

    @property
    def identity_digest(self) -> str:
        return _digest(self.as_dict())


@dataclass(frozen=True)
class MechanismSchemaVocabularyRegistry:
    """Merge owner-supplied schema vocabularies without inventing ownership.

    A registry is still a qualification input.  Every entry must come from an
    explicit owner vocabulary, and conflicting owners for one schema fail
    closed.  It does not make a schema executable or publish a dispatcher.
    """

    registry_id: str
    version: str
    vocabularies: tuple[MechanismSchemaVocabulary, ...]
    entries: tuple[SchemaVocabularyEntry, ...] = field(init=False)

    def __post_init__(self) -> None:
        for field_name in ("registry_id", "version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        vocabularies = tuple(self.vocabularies)
        if not vocabularies:
            raise ValueError("vocabularies must not be empty")
        if any(not isinstance(item, MechanismSchemaVocabulary) for item in vocabularies):
            raise TypeError("vocabularies must contain MechanismSchemaVocabulary values")
        vocabulary_ids = [item.vocabulary_id for item in vocabularies]
        if len(set(vocabulary_ids)) != len(vocabulary_ids):
            raise ValueError("schema vocabulary registry ids must be unique")
        owners: dict[str, str] = {}
        for vocabulary in vocabularies:
            for entry in vocabulary.entries:
                previous = owners.get(entry.schema)
                if previous is not None and previous != entry.owner_ref:
                    raise ValueError(
                        f"schema registry owner conflict for {entry.schema!r}: "
                        f"{previous!r} versus {entry.owner_ref!r}"
                    )
                owners[entry.schema] = entry.owner_ref
        object.__setattr__(
            self,
            "vocabularies",
            tuple(sorted(vocabularies, key=lambda item: item.vocabulary_id)),
        )
        object.__setattr__(
            self,
            "entries",
            tuple(
                SchemaVocabularyEntry(schema, owner_ref)
                for schema, owner_ref in sorted(owners.items())
            ),
        )

    @property
    def vocabulary_id(self) -> str:
        return self.registry_id

    @property
    def schema_names(self) -> frozenset[str]:
        return frozenset(entry.schema for entry in self.entries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "vocabularies": [item.as_dict() for item in self.vocabularies],
            "entries": [
                {"schema": entry.schema, "owner_ref": entry.owner_ref}
                for entry in self.entries
            ],
        }

    @property
    def identity_digest(self) -> str:
        return _digest(self.as_dict())


SchemaVocabulary = MechanismSchemaVocabulary | MechanismSchemaVocabularyRegistry


@dataclass(frozen=True)
class FreshnessVocabularyEntry:
    """One owner-declared sampling/freshness label."""

    freshness: str
    owner_ref: str

    def __post_init__(self) -> None:
        for field_name in ("freshness", "owner_ref"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class FreshnessVocabulary:
    """Immutable owner vocabulary for port sampling/freshness semantics."""

    vocabulary_id: str
    version: str
    entries: tuple[FreshnessVocabularyEntry, ...]

    def __post_init__(self) -> None:
        for field_name in ("vocabulary_id", "version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        entries = tuple(self.entries)
        if not entries:
            raise ValueError("entries must not be empty")
        if any(not isinstance(entry, FreshnessVocabularyEntry) for entry in entries):
            raise TypeError("entries must contain FreshnessVocabularyEntry values")
        freshness_names = [entry.freshness for entry in entries]
        if len(set(freshness_names)) != len(freshness_names):
            raise ValueError("freshness vocabulary entries must use unique labels")
        object.__setattr__(self, "entries", entries)

    @property
    def freshness_names(self) -> frozenset[str]:
        return frozenset(entry.freshness for entry in self.entries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "vocabulary_id": self.vocabulary_id,
            "version": self.version,
            "entries": [
                {"freshness": entry.freshness, "owner_ref": entry.owner_ref}
                for entry in sorted(self.entries, key=lambda item: item.freshness)
            ],
        }

    @property
    def identity_digest(self) -> str:
        return _digest(self.as_dict())


@dataclass(frozen=True)
class CompiledMechanismGraph:
    graph_id: str
    nodes: tuple[tuple[str, MechanismSpec], ...]
    edges: tuple[GraphEdge, ...]
    diagnostics: tuple[GraphDiagnostic, ...]
    identity_digest: str
    external_inputs: frozenset[str] = frozenset()
    schema_version: str = SCHEMA_VERSION
    schema_vocabulary_ref: str | None = None
    schema_vocabulary_version: str | None = None
    schema_vocabulary_digest: str | None = None
    freshness_vocabulary_ref: str | None = None
    freshness_vocabulary_version: str | None = None
    freshness_vocabulary_digest: str | None = None

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
                    "parameters": thaw_json_value(spec.parameters),
                    "backend_ref": spec.backend_ref,
                    "clock_policy": thaw_json_value(spec.clock_policy),
                }
                for node_id, spec in self.nodes
            ],
            "edges": [edge.__dict__ for edge in self.edges],
            "external_inputs": sorted(self.external_inputs),
            "schema_vocabulary": (
                None
                if self.schema_vocabulary_ref is None
                else {
                    "vocabulary_id": self.schema_vocabulary_ref,
                    "version": self.schema_vocabulary_version,
                    "identity_digest": self.schema_vocabulary_digest,
                }
            ),
            "freshness_vocabulary": (
                None
                if self.freshness_vocabulary_ref is None
                else {
                    "vocabulary_id": self.freshness_vocabulary_ref,
                    "version": self.freshness_vocabulary_version,
                    "identity_digest": self.freshness_vocabulary_digest,
                }
            ),
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
        "freshness": port.freshness,
    }


def _identity_payload(
    graph_id: str,
    nodes: Mapping[str, MechanismSpec],
    edges: Sequence[GraphEdge],
    *,
    external_inputs: frozenset[str],
    schema_vocabulary: SchemaVocabulary | None = None,
    freshness_vocabulary: FreshnessVocabulary | None = None,
) -> dict[str, Any]:
    payload = {
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
                "parameters": thaw_json_value(spec.parameters),
                "backend_ref": spec.backend_ref,
                "clock_policy": thaw_json_value(spec.clock_policy),
            }
            for node_id, spec in sorted(nodes.items())
        },
        "edges": [
            edge.__dict__
            for edge in sorted(
                edges,
                key=lambda item: (
                    item.source_node,
                    item.source_port,
                    item.target_node,
                    item.target_port,
                    item.delayed,
                ),
            )
        ],
        "external_inputs": sorted(external_inputs),
    }
    if schema_vocabulary is not None:
        payload["schema_vocabulary"] = {
            "vocabulary_id": schema_vocabulary.vocabulary_id,
            "version": schema_vocabulary.version,
            "identity_digest": schema_vocabulary.identity_digest,
        }
    if freshness_vocabulary is not None:
        payload["freshness_vocabulary"] = {
            "vocabulary_id": freshness_vocabulary.vocabulary_id,
            "version": freshness_vocabulary.version,
            "identity_digest": freshness_vocabulary.identity_digest,
        }
    return payload


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compile_mechanism_graph(
    graph_id: str,
    nodes: Mapping[str, MechanismSpec],
    edges: Sequence[GraphEdge],
    *,
    external_inputs: frozenset[str] = frozenset(),
    known_schemas: frozenset[str] | None = None,
    schema_vocabulary: SchemaVocabulary | None = None,
    freshness_vocabulary: FreshnessVocabulary | None = None,
) -> CompiledMechanismGraph:
    """Validate a graph and return a non-published qualification artifact."""

    if not graph_id.strip():
        raise MechanismGraphError("graph_id is required")
    if not nodes:
        raise MechanismGraphError("at least one mechanism node is required")
    if known_schemas is not None and schema_vocabulary is not None:
        raise MechanismGraphError("known_schemas and schema_vocabulary are mutually exclusive")
    if freshness_vocabulary is not None and not isinstance(
        freshness_vocabulary, FreshnessVocabulary
    ):
        raise TypeError("freshness_vocabulary must be a FreshnessVocabulary")
    diagnostics: list[GraphDiagnostic] = []
    normalized_external_inputs = frozenset(external_inputs)
    effective_schemas = (
        schema_vocabulary.schema_names if schema_vocabulary is not None else known_schemas
    )
    if effective_schemas is not None:
        for node_id, spec in nodes.items():
            for side, ports in (("inputs", spec.inputs), ("outputs", spec.outputs)):
                for port in ports:
                    if port.schema not in effective_schemas:
                        diagnostics.append(
                            GraphDiagnostic(
                                "mechanism.schema_unknown",
                                f"nodes.{node_id}.{side}.{port.name}",
                                f"schema is not present in the owner vocabulary: {port.schema}",
                            )
                        )
    if freshness_vocabulary is not None:
        for node_id, spec in nodes.items():
            for side, ports in (("inputs", spec.inputs), ("outputs", spec.outputs)):
                for port in ports:
                    if (
                        port.freshness is not None
                        and port.freshness not in freshness_vocabulary.freshness_names
                    ):
                        diagnostics.append(
                            GraphDiagnostic(
                                "mechanism.freshness_unknown",
                                f"nodes.{node_id}.{side}.{port.name}",
                                "freshness is not present in the owner vocabulary: "
                                + port.freshness,
                            )
                        )
    for external_ref in sorted(normalized_external_inputs):
        if not isinstance(external_ref, str) or external_ref.count(".") != 1:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.external_input_unknown", "external_inputs", str(external_ref)
                )
            )
            continue
        node_id, port_name = external_ref.split(".", 1)
        node = nodes.get(node_id)
        if node is None or node.port(port_name, output=False) is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.external_input_unknown", "external_inputs", external_ref)
            )
    incoming: dict[tuple[str, str], list[GraphEdge]] = {}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge_index, edge in enumerate(edges):
        path = f"edges[{edge_index}]"
        source = nodes.get(edge.source_node)
        target = nodes.get(edge.target_node)
        if source is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.node_unknown", f"{path}.source_node", edge.source_node)
            )
            continue
        if target is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.node_unknown", f"{path}.target_node", edge.target_node)
            )
            continue
        source_port = source.port(edge.source_port, output=True)
        target_port = target.port(edge.target_port, output=False)
        if source_port is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.output_unknown", f"{path}.source_port", edge.source_port)
            )
        if target_port is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.input_unknown", f"{path}.target_port", edge.target_port)
            )
        if source_port is None or target_port is None:
            continue
        if source_port.schema != target_port.schema:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.schema_incompatible",
                    path,
                    f"{source_port.schema} -> {target_port.schema}",
                )
            )
        if source_port.unit != target_port.unit:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.unit_incompatible",
                    path,
                    f"{source_port.unit!r} -> {target_port.unit!r}",
                )
            )
        if source_port.frame != target_port.frame:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.frame_incompatible",
                    path,
                    f"{source_port.frame!r} -> {target_port.frame!r}",
                )
            )
        if source_port.freshness != target_port.freshness and (
            source_port.freshness is not None or target_port.freshness is not None
        ):
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.freshness_incompatible",
                    path,
                    f"{source_port.freshness!r} -> {target_port.freshness!r}",
                )
            )
        if source_port.visibility == "truth" and target_port.visibility == "agent_observation":
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.truth_boundary_violation",
                    path,
                    "truth output cannot directly feed agent observation",
                )
            )
        elif source_port.visibility != target_port.visibility:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.visibility_incompatible",
                    path,
                    "information-layer conversion requires an explicit adapter",
                )
            )
        if source.clock != target.clock:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.clock_incompatible",
                    path,
                    f"{source.clock} -> {target.clock}: explicit temporal adapter required",
                )
            )
        incoming.setdefault((edge.target_node, edge.target_port), []).append(edge)
        if not edge.delayed:
            adjacency[edge.source_node].append(edge.target_node)

    for node_id, spec in nodes.items():
        for port in spec.inputs:
            key = (node_id, port.name)
            if (
                port.required
                and key not in incoming
                and f"{node_id}.{port.name}" not in external_inputs
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.required_input_missing",
                        f"nodes.{node_id}.inputs.{port.name}",
                        "no producer or declared external input",
                    )
                )
            if len(incoming.get(key, ())) > 1 or (
                key in incoming and f"{node_id}.{port.name}" in external_inputs
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.input_multiple_producers",
                        f"nodes.{node_id}.inputs.{port.name}",
                        "an explicit fusion mechanism is required",
                    )
                )

    # A DFS over instantaneous edges rejects same-window cycles. Delayed edges
    # are intentionally excluded and therefore represent an explicit feedback
    # boundary rather than an accidental recursive execution path.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: tuple[str, ...]) -> None:
        if node_id in visiting:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.instantaneous_cycle", "graph", " -> ".join(path + (node_id,))
                )
            )
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

    payload = _identity_payload(
        graph_id,
        nodes,
        edges,
        external_inputs=normalized_external_inputs,
        schema_vocabulary=schema_vocabulary,
        freshness_vocabulary=freshness_vocabulary,
    )
    return CompiledMechanismGraph(
        graph_id=graph_id,
        nodes=tuple(sorted(nodes.items())),
        edges=tuple(edges),
        diagnostics=tuple(diagnostics),
        identity_digest=_digest(payload),
        external_inputs=normalized_external_inputs,
        schema_vocabulary_ref=(schema_vocabulary.vocabulary_id if schema_vocabulary else None),
        schema_vocabulary_version=(schema_vocabulary.version if schema_vocabulary else None),
        schema_vocabulary_digest=(schema_vocabulary.identity_digest if schema_vocabulary else None),
        freshness_vocabulary_ref=(
            freshness_vocabulary.vocabulary_id if freshness_vocabulary else None
        ),
        freshness_vocabulary_version=(
            freshness_vocabulary.version if freshness_vocabulary else None
        ),
        freshness_vocabulary_digest=(
            freshness_vocabulary.identity_digest if freshness_vocabulary else None
        ),
    )


def compose_graph_as_mechanism(
    graph: CompiledMechanismGraph,
    *,
    mechanism_id: str,
    version: str,
    inputs: tuple[PortSpec, ...],
    outputs: tuple[PortSpec, ...],
    input_bindings: Mapping[str, str] | None = None,
    output_bindings: Mapping[str, str] | None = None,
) -> MechanismSpec:
    """Export a valid graph as a reusable, non-executing composite node."""

    if not graph.valid:
        raise MechanismGraphError("cannot compose an invalid mechanism graph")
    if not mechanism_id.strip() or not version.strip():
        raise MechanismGraphError("composite mechanism identity is required")
    clocks = {spec.clock for _, spec in graph.nodes}
    if len(clocks) != 1:
        raise MechanismGraphError("composite clock policy requires an explicit temporal boundary")
    backends = {spec.backend_ref for _, spec in graph.nodes}
    if len(backends) != 1:
        raise MechanismGraphError("composite backend policy requires an explicit native boundary")
    input_bindings = dict(input_bindings or {})
    output_bindings = dict(output_bindings or {})
    input_names = {port.name for port in inputs}
    output_names = {port.name for port in outputs}
    if set(input_bindings) != input_names:
        raise MechanismGraphError("composite input bindings must cover every declared public input")
    if set(output_bindings) != output_names:
        raise MechanismGraphError(
            "composite output bindings must cover every declared public output"
        )

    def resolve(ref: str, *, output: bool, kind: str) -> PortSpec:
        if not isinstance(ref, str) or ref.count(".") != 1:
            raise MechanismGraphError(f"composite {kind} binding must be a node.port reference")
        node_id, port_name = ref.split(".", 1)
        spec = dict(graph.nodes).get(node_id)
        if spec is None:
            raise MechanismGraphError(f"composite {kind} binding references unknown node: {ref}")
        port = spec.port(port_name, output=output)
        if port is None:
            raise MechanismGraphError(f"composite {kind} binding references unknown port: {ref}")
        return port

    def compatible(public: PortSpec, internal: PortSpec) -> bool:
        return (
            public.schema == internal.schema
            and public.unit == internal.unit
            and public.frame == internal.frame
            and public.visibility == internal.visibility
            and public.freshness == internal.freshness
        )

    for public in inputs:
        internal_ref = input_bindings[public.name]
        if internal_ref not in graph.external_inputs:
            raise MechanismGraphError(
                f"composite input {public.name!r} is not bound to a declared graph external input: {internal_ref}"
            )
        internal = resolve(internal_ref, output=False, kind="input")
        if not compatible(public, internal):
            raise MechanismGraphError(
                f"composite input type mismatch: {public.name} -> {internal_ref}"
            )
    if set(input_bindings.values()) != set(graph.external_inputs):
        raise MechanismGraphError(
            "composite external input closure must cover every graph external input"
        )
    for public in outputs:
        internal_ref = output_bindings[public.name]
        internal = resolve(internal_ref, output=True, kind="output")
        if not compatible(public, internal):
            raise MechanismGraphError(
                f"composite output type mismatch: {public.name} -> {internal_ref}"
            )
    composite_identity = _digest(
        {
            "graph": graph.identity_digest,
            "mechanism_id": mechanism_id,
            "version": version,
            "inputs": [_port_dict(port) for port in inputs],
            "outputs": [_port_dict(port) for port in outputs],
            "input_bindings": sorted(input_bindings.items()),
            "output_bindings": sorted(output_bindings.items()),
        }
    )
    return MechanismSpec(
        mechanism_id=mechanism_id,
        version=version,
        inputs=inputs,
        outputs=outputs,
        stateful=any(spec.stateful for _, spec in graph.nodes),
        clock=next(iter(clocks)),
        delay_windows=0,
        implementation_ref=f"composite:{composite_identity}",
        required_capabilities=tuple(
            sorted({cap for _, spec in graph.nodes for cap in spec.required_capabilities})
        ),
        backend_ref=next(iter(backends)),
        clock_policy={"derived_from_graph": graph.identity_digest},
    )


_STAGE_MANIFEST_PROJECTION_FIELDS = (
    "node_id",
    "semantic_stage",
    "owner_module",
    "input_packets",
    "output_packets",
    "read_state_shards",
    "write_state_shards",
    "read_snapshot_policy",
    "write_commit_policy",
    "clock_domain",
    "latency_policy",
    "sync_policy",
    "allowed_same_window_edges",
    "required_barriers",
    "event_families_emitted",
    "diagnostic_trace_obligations",
    "facade_visibility",
    "adapter_projection_allowed",
    # Legacy evidence fixtures may carry an explicit realized system name.
    # The native StageNodeManifest itself does not, so this stays optional.
    "native_system",
)


def _manifest_field(manifest: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(manifest, Mapping):
        return manifest.get(field_name, default)
    return getattr(manifest, field_name, default)


def _manifest_contract_payload(manifest: Any) -> Mapping[str, Any]:
    values: dict[str, Any] = {}
    for field_name in _STAGE_MANIFEST_PROJECTION_FIELDS:
        value = _manifest_field(manifest, field_name)
        if value is not None:
            values[field_name] = thaw_json_value(freeze_json_value(value))
    return freeze_json_mapping(values)


def _authored_node_payload(spec: MechanismSpec) -> Mapping[str, Any]:
    return freeze_json_mapping(
        {
            "mechanism_id": spec.mechanism_id,
            "version": spec.version,
            "inputs": [_port_dict(port) for port in spec.inputs],
            "outputs": [_port_dict(port) for port in spec.outputs],
            "stateful": spec.stateful,
            "clock": spec.clock,
            "delay_windows": spec.delay_windows,
            "implementation_ref": spec.implementation_ref,
            "required_capabilities": list(spec.required_capabilities),
            "backend_ref": spec.backend_ref,
            "clock_policy": thaw_json_value(spec.clock_policy),
        }
    )


def project_stage_manifest_qualification(
    graph: CompiledMechanismGraph,
    *,
    node_stage_bindings: Mapping[str, str],
    stage_manifests: Mapping[str, Any],
    pipeline_order: Sequence[str] = (),
) -> StageManifestQualificationProjection:
    """Project an authored graph onto owner StageNodeManifest snapshots.

    This is a deterministic, non-executing qualification artifact.  It fails
    closed on any validation diagnostic and never lowers authored nodes into a
    native scheduler or provider request.
    """

    diagnostics = validate_stage_manifest_bindings(
        graph,
        node_stage_bindings=node_stage_bindings,
        stage_manifests=stage_manifests,
        pipeline_order=pipeline_order,
        require_native_contract=True,
    )
    if diagnostics:
        summary = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in diagnostics)
        raise MechanismGraphError(f"native stage qualification rejected: {summary}")

    node_contracts: list[NativeStageContractProjection] = []
    for node_id, spec in graph.nodes:
        stage_node_id = node_stage_bindings[node_id]
        manifest = stage_manifests[stage_node_id]
        owner_contract = _manifest_contract_payload(manifest)
        owner_module = _manifest_field(manifest, "owner_module")
        node_payload = _authored_node_payload(spec)
        node_identity = _digest(
            {
                "node_id": node_id,
                "stage_node_id": stage_node_id,
                "owner_module": owner_module,
                "authored_node": thaw_json_value(node_payload),
                "owner_contract": thaw_json_value(owner_contract),
            }
        )
        node_contracts.append(
            NativeStageContractProjection(
                node_id=node_id,
                stage_node_id=stage_node_id,
                owner_module=owner_module,
                authored_node=node_payload,
                owner_contract=owner_contract,
                identity_digest=node_identity,
            )
        )

    node_contracts_tuple = tuple(node_contracts)
    registry_payload = {
        "manifests": [
            {
                "stage_node_id": contract.stage_node_id,
                "owner_contract": thaw_json_value(contract.owner_contract),
            }
            for contract in node_contracts_tuple
        ]
    }
    manifest_registry_digest = _digest(registry_payload)
    identity_payload = {
        "graph_identity_digest": graph.identity_digest,
        "manifest_registry_digest": manifest_registry_digest,
        "node_contracts": [contract.as_dict() for contract in node_contracts_tuple],
        "edge_bindings": [edge.__dict__ for edge in graph.edges],
        "qualification_only": True,
        "executable": False,
    }
    return StageManifestQualificationProjection(
        graph_identity_digest=graph.identity_digest,
        manifest_registry_digest=manifest_registry_digest,
        node_contracts=node_contracts_tuple,
        edge_bindings=tuple(graph.edges),
        identity_digest=_digest(identity_payload),
    )


def validate_realized_order(
    graph: CompiledMechanismGraph,
    *,
    node_systems: Mapping[str, str],
    pipeline_order: Sequence[str],
) -> tuple[GraphDiagnostic, ...]:
    """Check an explicit owner adapter against an exported Flecs projection.

    This does not realize a graph or enforce StageNodeManifest clock domains.
    It is evidence about same-window order in the supplied exact snapshot.
    """
    if not graph.valid:
        raise MechanismGraphError("cannot qualify an invalid mechanism graph")
    diagnostics: list[GraphDiagnostic] = []
    positions = {system: index for index, system in enumerate(pipeline_order)}
    for index, edge in enumerate(graph.edges):
        if edge.delayed:
            continue
        source = node_systems.get(edge.source_node)
        target = node_systems.get(edge.target_node)
        if source not in positions or target not in positions:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.realized_order_unresolved",
                    f"edges[{index}]",
                    "owned native system mapping is missing from the realized projection",
                )
            )
        elif positions[source] >= positions[target]:
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.realized_order_mismatch",
                    f"edges[{index}]",
                    f"claimed {source} before {target} is not realized",
                )
            )
    return tuple(diagnostics)


def validate_stage_manifest_bindings(
    graph: CompiledMechanismGraph,
    *,
    node_stage_bindings: Mapping[str, str],
    stage_manifests: Mapping[str, Mapping[str, Any]],
    pipeline_order: Sequence[str] = (),
    require_native_contract: bool = False,
) -> tuple[GraphDiagnostic, ...]:
    """Qualify a graph against an owner-provided native stage snapshot.

    The snapshot is consumed as evidence. This adapter does not construct a
    provider, install a scheduler node or infer a native manifest from Python.
    """

    if not graph.valid:
        raise MechanismGraphError("cannot qualify an invalid mechanism graph")
    expected_nodes = {node_id for node_id, _ in graph.nodes}
    if set(node_stage_bindings) != expected_nodes:
        raise MechanismGraphError("native stage bindings must cover every graph node exactly")
    if len(set(node_stage_bindings.values())) != len(node_stage_bindings):
        raise MechanismGraphError("native stage bindings must be one-to-one")

    diagnostics: list[GraphDiagnostic] = []
    node_systems: dict[str, str] = {}
    write_shard_owners: dict[str, str] = {}
    required_native_fields = (
        "input_packets",
        "output_packets",
        "read_state_shards",
        "write_state_shards",
        "read_snapshot_policy",
        "write_commit_policy",
        "clock_domain",
        "latency_policy",
        "sync_policy",
        "required_barriers",
        "diagnostic_trace_obligations",
        "facade_visibility",
    )
    required_nonempty_sequences = frozenset(
        {
            "input_packets",
            "output_packets",
            "read_state_shards",
            "required_barriers",
            "diagnostic_trace_obligations",
        }
    )
    sequence_fields = frozenset(
        {
            "semantic_stage",
            "input_packets",
            "output_packets",
            "read_state_shards",
            "write_state_shards",
            "allowed_same_window_edges",
            "required_barriers",
            "event_families_emitted",
            "diagnostic_trace_obligations",
        }
    )
    string_fields = frozenset(
        {
            "node_id",
            "owner_module",
            "read_snapshot_policy",
            "write_commit_policy",
            "clock_domain",
            "latency_policy",
            "sync_policy",
            "facade_visibility",
        }
    )
    for node_id, spec in graph.nodes:
        stage_id = node_stage_bindings[node_id]
        manifest = stage_manifests.get(stage_id)
        path = f"nodes.{node_id}"
        if manifest is None:
            diagnostics.append(
                GraphDiagnostic("mechanism.native_stage_manifest_missing", path, stage_id)
            )
            continue
        if _manifest_field(manifest, "node_id") != stage_id:
            diagnostics.append(
                GraphDiagnostic("mechanism.native_stage_manifest_identity_mismatch", path, stage_id)
            )
        if not _manifest_field(manifest, "semantic_stage") or not _manifest_field(
            manifest, "owner_module"
        ):
            diagnostics.append(
                GraphDiagnostic("mechanism.native_stage_manifest_incomplete", path, stage_id)
            )
        if require_native_contract:
            missing = []
            for field_name in required_native_fields:
                value = _manifest_field(manifest, field_name)
                if value is None:
                    missing.append(field_name)
                    continue
                if field_name in string_fields and (
                    not isinstance(value, str) or not value.strip()
                ):
                    diagnostics.append(
                        GraphDiagnostic(
                            "mechanism.native_stage_contract_field_invalid",
                            f"{path}.{field_name}",
                            "owner field must be a non-empty string",
                        )
                    )
                    continue
                if field_name in sequence_fields:
                    if not isinstance(value, (list, tuple)) or any(
                        not isinstance(item, str) or not item.strip() for item in value
                    ):
                        diagnostics.append(
                            GraphDiagnostic(
                                "mechanism.native_stage_contract_field_invalid",
                                f"{path}.{field_name}",
                                "owner field must be a sequence of non-empty strings",
                            )
                        )
                        continue
                    if field_name in required_nonempty_sequences and not value:
                        missing.append(field_name)
            adapter_projection_allowed = _manifest_field(manifest, "adapter_projection_allowed")
            if adapter_projection_allowed is not None and type(adapter_projection_allowed) is not bool:
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_contract_field_invalid",
                        f"{path}.adapter_projection_allowed",
                        "owner field must be a bool",
                    )
                )
            if missing:
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_contract_incomplete",
                        path,
                        "missing owner fields: " + ", ".join(missing),
                    )
                )
            write_policy = _manifest_field(manifest, "write_commit_policy")
            latency_policy = _manifest_field(manifest, "latency_policy")
            required_barriers = _manifest_field(manifest, "required_barriers", ())
            if (
                isinstance(write_policy, str)
                and isinstance(latency_policy, str)
                and isinstance(required_barriers, (list, tuple))
                and (
                    write_policy == "stage_publish"
                    or "same_window" in latency_policy
                    or "stage_publish" in required_barriers
                )
                and not _manifest_field(manifest, "allowed_same_window_edges")
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_same_window_edges_missing",
                        path,
                        "same-window publish claims require allowed_same_window_edges",
                    )
                )
            if (
                write_policy == "stage_publish"
                and isinstance(required_barriers, (list, tuple))
                and "stage_publish" not in required_barriers
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_publish_barrier_missing",
                        path,
                        "stage_publish manifests must declare the stage_publish barrier",
                    )
                )
            if (
                _manifest_field(manifest, "facade_visibility") == "adapter_projection"
                and adapter_projection_allowed is not True
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_projection_not_allowed",
                        path,
                        "adapter_projection visibility requires adapter_projection_allowed",
                    )
                )
            output_packets = _manifest_field(manifest, "output_packets", ())
            if (
                isinstance(output_packets, (list, tuple))
                and any(
                    isinstance(packet, str)
                    and (packet.endswith("Event") or packet.endswith("Report"))
                    for packet in output_packets
                )
                and not _manifest_field(manifest, "event_families_emitted")
            ):
                diagnostics.append(
                    GraphDiagnostic(
                        "mechanism.native_stage_event_families_missing",
                        path,
                        "event-emitting manifests must declare event_families_emitted",
                    )
                )
        if _manifest_field(manifest, "facade_visibility") in {
            "adapter_projection",
            "diagnostics_only",
        }:
            diagnostics.append(
                GraphDiagnostic("mechanism.native_stage_not_scheduler_truth", path, stage_id)
            )
        native_system = _manifest_field(manifest, "native_system")
        if native_system is None:
            native_system = _manifest_field(manifest, "owner_module")
        if not isinstance(native_system, str) or not native_system.strip():
            diagnostics.append(
                GraphDiagnostic("mechanism.native_stage_system_missing", path, stage_id)
            )
        else:
            node_systems[node_id] = native_system
        write_shards = _manifest_field(manifest, "write_state_shards", ())
        if not isinstance(write_shards, (list, tuple)) or any(
            not isinstance(shard, str) or not shard.strip() for shard in write_shards
        ):
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.native_stage_write_shards_invalid",
                    path,
                    "write_state_shards must be a sequence of non-empty strings",
                )
            )
        else:
            for shard in write_shards:
                previous = write_shard_owners.get(shard)
                if previous is not None and previous != node_id:
                    diagnostics.append(
                        GraphDiagnostic(
                            "mechanism.native_stage_write_shard_conflict",
                            path,
                            f"state shard {shard!r} is written by both {previous} and {node_id}",
                        )
                    )
                else:
                    write_shard_owners[shard] = node_id
        if spec.implementation_ref.startswith("qualification."):
            diagnostics.append(
                GraphDiagnostic(
                    "mechanism.native_implementation_qualification_only",
                    path,
                    spec.implementation_ref,
                )
            )

    if pipeline_order and len(node_systems) == len(expected_nodes):
        diagnostics.extend(
            validate_realized_order(graph, node_systems=node_systems, pipeline_order=pipeline_order)
        )
    return tuple(diagnostics)


__all__ = [
    "CompiledMechanismGraph",
    "FreshnessVocabulary",
    "FreshnessVocabularyEntry",
    "GraphDiagnostic",
    "GraphEdge",
    "MechanismGraphError",
    "MechanismSchemaVocabularyRegistry",
    "MechanismSpec",
    "NativeStageContractProjection",
    "PortSpec",
    "SCHEMA_VERSION",
    "StageManifestQualificationProjection",
    "compile_mechanism_graph",
    "compose_graph_as_mechanism",
    "project_stage_manifest_qualification",
    "validate_realized_order",
    "validate_stage_manifest_bindings",
]
