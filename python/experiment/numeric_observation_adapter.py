"""Agent-centered numeric learner export for audited experiment projections.

The trace projection deliberately contains no fabricated observation vectors.
This module adds the next boundary: a caller supplies packets read by one
declared Agent observation interface and an explicit action/reward encoding
policy. The adapter validates alignment and writes ordinary ``EpisodeStore``
episodes together with a sidecar that preserves the Agent identity, packet
provenance, source projection digest, split, and branch lineage.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Any, Callable, Mapping, Protocol, Sequence

import numpy as np

from python.experiment.contracts import ContractError, content_digest
from python.experiment.trace_projection import ProjectionRow, TraceProjection
from python.tasking_contracts.common.agent_contracts import OBS_DECISION_BELIEF_PACKET
from python.tasking_contracts.common.agent_contracts import OBS_FACADE_OBSERVATION_PACKET
from python.world_model.replay import DatasetSpec, Episode, EpisodeStore


NUMERIC_EXPORT_SCHEMA_VERSION = "echelon_forge.experiment_numeric_export.v1"
AGENT_PACKET_SCHEMA_VERSION = "echelon_forge.agent_observation_packet.v1"
AGENT_PACKET_PROVENANCE = (OBS_FACADE_OBSERVATION_PACKET, OBS_DECISION_BELIEF_PACKET)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
ActionEncoder = Callable[[ProjectionRow], Sequence[float]]
RewardEncoder = Callable[[ProjectionRow], float]


def _require_digest(value: object, name: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ContractError(f"{name} must be a lowercase SHA-256 digest")


def _numeric_vector(value: object, name: str) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} must contain numeric values") from exc
    if vector.ndim != 1 or vector.size == 0:
        raise ContractError(f"{name} must be a non-empty one-dimensional vector")
    if not bool(np.all(np.isfinite(vector))):
        raise ContractError(f"{name} must contain only finite values")
    return vector


@dataclass(frozen=True)
class AgentObservationPacket:
    """One numeric packet returned by the declared Agent observation surface."""

    agent_id: str
    packet_id: str
    observation_version: str
    provenance: str
    values: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.agent_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_]*", self.agent_id
        ):
            raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
        for name, value in (
            ("packet_id", self.packet_id),
            ("observation_version", self.observation_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{name} must be a non-empty string")
        if self.provenance not in AGENT_PACKET_PROVENANCE:
            raise ContractError(
                f"provenance must be one of {AGENT_PACKET_PROVENANCE}, got {self.provenance!r}"
            )
        values = _numeric_vector(self.values, "packet values")
        values = np.array(values, dtype=np.float32, copy=True)
        values.setflags(write=False)
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class AgentObservationSeries:
    """Packets for one Agent on one manifest branch, including both endpoints."""

    manifest_digest: str
    branch_digest: str
    agent_id: str
    packets: tuple[AgentObservationPacket, ...]

    def __post_init__(self) -> None:
        _require_digest(self.manifest_digest, "manifest_digest")
        _require_digest(self.branch_digest, "branch_digest")
        if not isinstance(self.agent_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_]*", self.agent_id
        ):
            raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
        if not isinstance(self.packets, tuple) or not self.packets:
            raise ContractError("packets must be a non-empty tuple")
        if any(not isinstance(packet, AgentObservationPacket) for packet in self.packets):
            raise ContractError("packets must contain AgentObservationPacket values")
        if any(packet.agent_id != self.agent_id for packet in self.packets):
            raise ContractError("all packets must belong to the declared agent")
        if len({packet.provenance for packet in self.packets}) != 1:
            raise ContractError("all packets must share one observation provenance")
        dimensions = {packet.values.shape[0] for packet in self.packets}
        if len(dimensions) != 1:
            raise ContractError("all packets must share one observation dimension")
        packet_ids = [packet.packet_id for packet in self.packets]
        if len(set(packet_ids)) != len(packet_ids):
            raise ContractError("packet_id values must be unique within a series")

    @property
    def values(self) -> np.ndarray:
        values = np.stack([packet.values for packet in self.packets])
        values.setflags(write=False)
        return values


class AgentObservationPacketReader(Protocol):
    """Maintained reader surface used by the Agent packet bridge."""

    def read_observation_packet(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
    ) -> Any: ...


def _packet_texts(packet: Any, field: str, name: str) -> tuple[str, ...]:
    provenance = getattr(packet, "provenance", None)
    values = getattr(provenance, field, None)
    if values is None:
        raise ContractError(f"observation packet is missing provenance.{field}")
    if not isinstance(values, (tuple, list)):
        try:
            values = tuple(values)
        except TypeError as exc:
            raise ContractError(f"observation packet {name} must contain non-empty values") from exc
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise ContractError(f"observation packet {name} must contain non-empty values")
    return tuple(values)


def read_agent_observation_packet(
    reader: AgentObservationPacketReader,
    ref: Any,
    *,
    agent_id: str,
    fields: Sequence[str],
) -> AgentObservationPacket:
    """Read one Agent packet through the maintained facade observation API.

    The caller supplies the Agent identity and the numeric field catalogue. The
    bridge refuses raw fallback reads, missing provenance, ambiguous refs, and
    packets that do not identify exactly one observation.
    """

    if not callable(getattr(reader, "read_observation_packet", None)):
        raise ContractError("reader must expose read_observation_packet")
    if not isinstance(agent_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_]*", agent_id):
        raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
    selected_fields = tuple(fields)
    if (
        not selected_fields
        or len(set(selected_fields)) != len(selected_fields)
        or any(not isinstance(field, str) or not field.strip() for field in selected_fields)
    ):
        raise ContractError("fields must be a non-empty unique sequence of names")
    try:
        try:
            packet = reader.read_observation_packet(
                [ref], include_agent_observations=True, include_instrument_states=False
            )
        except TypeError:
            # Candidate shadow packet bindings expose the same maintained
            # packet DTO but only accept the ref vector; they have no legacy
            # truth fallback and remain on this packet path.
            packet = reader.read_observation_packet([ref])
    except Exception as exc:
        raise ContractError("maintained observation packet read failed") from exc
    return agent_observation_packet_from_dto(packet, ref, agent_id=agent_id, fields=selected_fields)


def agent_observation_packet_from_dto(
    packet: Any,
    ref: Any | None,
    *,
    agent_id: str,
    fields: Sequence[str],
) -> AgentObservationPacket:
    """Validate one packet captured at an export barrier."""

    if not isinstance(agent_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_]*", agent_id):
        raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
    selected_fields = tuple(fields)
    if (
        not selected_fields
        or len(set(selected_fields)) != len(selected_fields)
        or any(not isinstance(field, str) or not field.strip() for field in selected_fields)
    ):
        raise ContractError("fields must be a non-empty unique sequence of names")
    refs = tuple(getattr(packet, "refs", ()))
    observations = tuple(getattr(packet, "agent_observations", ()))
    if len(refs) != 1 or len(observations) != 1:
        raise ContractError("Agent packet bridge requires exactly one ref and observation")
    actual_identity = (
        getattr(refs[0], "world_index", None),
        getattr(refs[0], "entity_id", None),
    )
    expected_identity = (
        getattr(ref, "world_index", None),
        getattr(ref, "entity_id", None),
    ) if ref is not None else actual_identity
    if expected_identity != actual_identity:
        raise ContractError("observation packet ref does not match requested Agent ref")
    provenance = getattr(packet, "provenance", None)
    if getattr(provenance, "information_state_layer", None) != "AgentObservation":
        raise ContractError("observation packet is not an AgentObservation layer")
    source_label = getattr(provenance, "source_label", None)
    if source_label not in AGENT_PACKET_PROVENANCE:
        raise ContractError("observation packet provenance is not maintained")
    if getattr(provenance, "maintained_status", None) != "maintained":
        raise ContractError("observation packet provenance is not maintained")
    packet_ids = _packet_texts(packet, "observation_packet_ids", "ids")
    versions = _packet_texts(packet, "source_observation_versions", "versions")
    if len(packet_ids) != 1 or len(versions) != 1:
        raise ContractError("Agent packet bridge requires one packet id and one version")
    observation = observations[0]
    values: list[float] = []
    for field in selected_fields:
        try:
            value = getattr(observation, field)
            if isinstance(value, bool):
                raise TypeError("boolean observation fields are not numeric")
            numeric = float(value)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ContractError(f"Agent observation field {field!r} is not numeric") from exc
        if not np.isfinite(numeric):
            raise ContractError(f"Agent observation field {field!r} is not finite")
        values.append(numeric)
    return AgentObservationPacket(
        agent_id=agent_id,
        packet_id=packet_ids[0],
        observation_version=versions[0],
        provenance=source_label,
        values=np.asarray(values, dtype=np.float32),
    )


def read_agent_observation_series_from_packets(
    packets: Sequence[Any],
    *,
    manifest_digest: str,
    branch_digest: str,
    agent_id: str,
    fields: Sequence[str],
) -> AgentObservationSeries:
    """Build a series from packets captured at their original export barriers."""

    packets = tuple(packets)
    if not packets:
        raise ContractError("packets must contain at least one captured Agent packet")
    parsed_items: list[AgentObservationPacket] = []
    for packet in packets:
        refs = tuple(getattr(packet, "refs", ()))
        if len(refs) != 1:
            raise ContractError("captured Agent packet must contain exactly one ref")
        parsed_items.append(
            agent_observation_packet_from_dto(
                packet, refs[0], agent_id=agent_id, fields=fields
            )
        )
    parsed = tuple(parsed_items)
    return AgentObservationSeries(
        manifest_digest=manifest_digest,
        branch_digest=branch_digest,
        agent_id=agent_id,
        packets=parsed,
    )


def read_agent_observation_series(
    reader: AgentObservationPacketReader,
    refs: Sequence[Any],
    *,
    manifest_digest: str,
    branch_digest: str,
    agent_id: str,
    fields: Sequence[str],
) -> AgentObservationSeries:
    """Collect one Agent packet per endpoint through the maintained reader."""

    refs = tuple(refs)
    if not refs:
        raise ContractError("refs must contain at least one Agent observation ref")
    packets = tuple(
        read_agent_observation_packet(reader, ref, agent_id=agent_id, fields=fields)
        for ref in refs
    )
    return AgentObservationSeries(
        manifest_digest=manifest_digest,
        branch_digest=branch_digest,
        agent_id=agent_id,
        packets=packets,
    )


def collect_agent_observation_sources(
    reader: AgentObservationPacketReader,
    refs_by_branch: Mapping[tuple[str, str], Sequence[Any]],
    *,
    agent_id: str,
    fields: Sequence[str],
    selected_branch_digests: Sequence[str],
) -> dict[tuple[str, str], AgentObservationSeries]:
    """Collect selected branch ref sequences through the maintained packet API.

    The mapping is the explicit join between trace branch identity and runtime
    entity refs. No branch identity or ref is inferred from packet contents.
    """

    selected = tuple(selected_branch_digests)
    if not selected or len(set(selected)) != len(selected):
        raise ContractError("selected_branch_digests must be non-empty and unique")
    if any(_DIGEST.fullmatch(value) is None for value in selected):
        raise ContractError("selected_branch_digests must contain lowercase SHA-256 digests")
    expected = {key for key in refs_by_branch if key[1] in selected}
    if len(expected) != len(selected):
        raise ContractError("selected_branch_digests must identify ref sequences")
    if set(refs_by_branch) != expected:
        missing = sorted(expected - set(refs_by_branch))
        extra = sorted(set(refs_by_branch) - expected)
        raise ContractError(f"branch ref keys differ: missing={missing}, extra={extra}")
    return {
        key: read_agent_observation_series(
            reader,
            refs,
            manifest_digest=key[0],
            branch_digest=key[1],
            agent_id=agent_id,
            fields=fields,
        )
        for key, refs in sorted(refs_by_branch.items())
    }


def collect_agent_observation_sources_by_branch_reader(
    reader_sources: Mapping[tuple[str, str], tuple[AgentObservationPacketReader, Sequence[Any]]],
    *,
    agent_id: str,
    fields: Sequence[str],
    selected_branch_digests: Sequence[str],
) -> dict[tuple[str, str], AgentObservationSeries]:
    """Read selected Agent branches when each branch owns its packet reader."""

    selected = tuple(selected_branch_digests)
    if not selected or len(set(selected)) != len(selected):
        raise ContractError("selected_branch_digests must be non-empty and unique")
    if any(_DIGEST.fullmatch(value) is None for value in selected):
        raise ContractError("selected_branch_digests must contain lowercase SHA-256 digests")
    expected = {key for key in reader_sources if key[1] in selected}
    if len(expected) != len(selected):
        raise ContractError("selected_branch_digests must identify packet reader sources")
    if set(reader_sources) != expected:
        missing = sorted(expected - set(reader_sources))
        extra = sorted(set(reader_sources) - expected)
        raise ContractError(f"branch packet reader keys differ: missing={missing}, extra={extra}")
    result: dict[tuple[str, str], AgentObservationSeries] = {}
    for key, pair in sorted(reader_sources.items()):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ContractError("branch packet reader sources must be (reader, refs) pairs")
        reader, refs = pair
        result[key] = read_agent_observation_series(
            reader,
            refs,
            manifest_digest=key[0],
            branch_digest=key[1],
            agent_id=agent_id,
            fields=fields,
        )
    return result


def collect_agent_observation_sources_from_packets(
    packets_by_branch: Mapping[tuple[str, str], Sequence[Any]],
    *,
    agent_id: str,
    fields: Sequence[str],
    selected_branch_digests: Sequence[str],
) -> dict[tuple[str, str], AgentObservationSeries]:
    """Build selected Agent sources from packets captured at each branch endpoint."""

    selected = tuple(selected_branch_digests)
    if not selected or len(set(selected)) != len(selected):
        raise ContractError("selected_branch_digests must be non-empty and unique")
    if any(_DIGEST.fullmatch(value) is None for value in selected):
        raise ContractError("selected_branch_digests must contain lowercase SHA-256 digests")
    expected = {key for key in packets_by_branch if key[1] in selected}
    if len(expected) != len(selected):
        raise ContractError("selected_branch_digests must identify packet sources")
    if set(packets_by_branch) != expected:
        missing = sorted(expected - set(packets_by_branch))
        extra = sorted(set(packets_by_branch) - expected)
        raise ContractError(f"branch packet keys differ: missing={missing}, extra={extra}")
    return {
        key: read_agent_observation_series_from_packets(
            packets,
            manifest_digest=key[0],
            branch_digest=key[1],
            agent_id=agent_id,
            fields=fields,
        )
        for key, packets in sorted(packets_by_branch.items())
    }


@dataclass(frozen=True)
class NumericEpisodeExport:
    """One learner episode plus the audit identity that produced it."""

    split: str
    seed: int
    manifest_digest: str
    branch_digest: str
    projection_digest: str
    agent_id: str
    packet_ids: tuple[str, ...]
    observation_versions: tuple[str, ...]
    observation_provenance: str
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    dones: np.ndarray

    def __post_init__(self) -> None:
        if self.split not in {"training", "evaluation"}:
            raise ContractError("split must be training or evaluation")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ContractError("seed must be a non-negative integer")
        for name, value in (
            ("manifest_digest", self.manifest_digest),
            ("branch_digest", self.branch_digest),
            ("projection_digest", self.projection_digest),
        ):
            _require_digest(value, name)
        if not isinstance(self.agent_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9_]*", self.agent_id
        ):
            raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
        if not isinstance(self.packet_ids, tuple) or not self.packet_ids:
            raise ContractError("packet_ids must be a non-empty tuple")
        if not isinstance(self.observation_versions, tuple) or not self.observation_versions:
            raise ContractError("observation_versions must be a non-empty tuple")
        if len(self.packet_ids) != len(self.observation_versions):
            raise ContractError("packet ids and versions must have equal lengths")
        if self.observation_provenance not in AGENT_PACKET_PROVENANCE:
            raise ContractError("observation_provenance is not an Agent packet provenance")
        try:
            observations = np.asarray(self.observations, dtype=np.float32)
            actions = np.asarray(self.actions, dtype=np.float32)
            rewards = np.asarray(self.rewards, dtype=np.float32)
            dones = np.asarray(self.dones, dtype=np.bool_)
        except (TypeError, ValueError) as exc:
            raise ContractError("learner arrays have invalid values") from exc
        if observations.ndim != 2 or actions.ndim != 2 or rewards.ndim != 1 or dones.ndim != 1:
            raise ContractError("learner arrays have invalid ranks")
        if observations.shape[0] != actions.shape[0] + 1:
            raise ContractError("observations must contain one more row than actions")
        if len(self.packet_ids) != observations.shape[0]:
            raise ContractError("packet metadata must contain one entry per observation")
        if actions.shape[0] != rewards.shape[0] or actions.shape[0] != dones.shape[0]:
            raise ContractError("actions, rewards, and dones must have equal lengths")
        if actions.shape[1] == 0 or observations.shape[1] == 0:
            raise ContractError("learner arrays must have non-empty feature dimensions")
        if not bool(np.all(np.isfinite(observations))) or not bool(np.all(np.isfinite(actions))):
            raise ContractError("observations and actions must contain only finite values")
        for name, value in (
            ("observations", observations),
            ("actions", actions),
            ("rewards", rewards),
        ):
            value = np.array(value, dtype=np.float32, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        for name, value in (("dones", dones),):
            value = np.array(value, dtype=np.bool_, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)

    def to_episode(self) -> Episode:
        return Episode(
            obs_vec=np.array(self.observations, copy=True),
            actions=np.array(self.actions, copy=True),
            rewards=np.array(self.rewards, copy=True),
            dones=np.array(self.dones, copy=True),
        )

    def metadata(self, relative_path: str) -> dict[str, object]:
        return {
            "path": relative_path,
            "split": self.split,
            "seed": self.seed,
            "manifest_digest": self.manifest_digest,
            "branch_digest": self.branch_digest,
            "projection_digest": self.projection_digest,
            "agent_id": self.agent_id,
            "packet_ids": list(self.packet_ids),
            "observation_versions": list(self.observation_versions),
            "observation_provenance": self.observation_provenance,
            "transition_count": int(self.actions.shape[0]),
            "observation_dim": int(self.observations.shape[1]),
            "action_dim": int(self.actions.shape[1]),
        }


@dataclass(frozen=True)
class NumericExportReceipt:
    root_dir: str
    metadata_path: str
    metadata_digest: str
    episode_paths: tuple[str, ...]


def build_numeric_exports(
    projection: TraceProjection,
    observation_sources: Mapping[tuple[str, str], AgentObservationSeries],
    *,
    agent_id: str,
    selected_branch_digests: Sequence[str],
    action_encoder: ActionEncoder,
    reward_encoder: RewardEncoder,
) -> tuple[NumericEpisodeExport, ...]:
    """Build learner episodes for explicitly selected branches of one Agent.

    ``observation_sources`` is deliberately keyed by manifest and branch
    digest. The caller therefore has to identify the Agent and selected
    training branches explicitly; replay and baseline branches are not
    silently converted into learner episodes.
    """

    if not isinstance(projection, TraceProjection):
        raise ContractError("projection must be a TraceProjection")
    if not callable(action_encoder) or not callable(reward_encoder):
        raise ContractError("action_encoder and reward_encoder must be callable")
    if not isinstance(agent_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_]*", agent_id):
        raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
    selected = tuple(selected_branch_digests)
    if not selected or len(set(selected)) != len(selected):
        raise ContractError("selected_branch_digests must be non-empty and unique")
    if any(_DIGEST.fullmatch(value) is None for value in selected):
        raise ContractError("selected_branch_digests must contain lowercase SHA-256 digests")
    rows_by_branch: dict[tuple[str, str], list[ProjectionRow]] = {}
    for row in projection.rows:
        key = (row.manifest_digest, row.branch_digest)
        rows_by_branch.setdefault(key, []).append(row)
    expected = {key for key in rows_by_branch if key[1] in selected}
    if len(expected) != len(selected):
        raise ContractError("selected_branch_digests must identify projected branches")
    supplied = set(observation_sources)
    if supplied != expected:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise ContractError(f"observation source keys differ: missing={missing}, extra={extra}")

    exports: list[NumericEpisodeExport] = []
    for key in sorted(expected):
        manifest_digest, branch_digest = key
        rows = sorted(rows_by_branch[key], key=lambda row: row.step)
        if [row.step for row in rows] != list(range(rows[0].step, rows[0].step + len(rows))):
            raise ContractError(f"branch {branch_digest} has non-contiguous projected steps")
        source = observation_sources[key]
        if not isinstance(source, AgentObservationSeries):
            raise ContractError("observation_sources values must be AgentObservationSeries")
        if (source.manifest_digest, source.branch_digest) != key:
            raise ContractError("observation source identity does not match its mapping key")
        if source.agent_id != agent_id:
            raise ContractError("observation source agent does not match agent_id")
        if len(source.packets) != len(rows) + 1:
            raise ContractError(
                f"branch {branch_digest} needs {len(rows) + 1} observations, "
                f"got {source.values.shape[0]}"
            )
        try:
            actions = np.stack(
                [_numeric_vector(action_encoder(row), "encoded action") for row in rows]
            )
            rewards = np.asarray([float(reward_encoder(row)) for row in rows], dtype=np.float32)
        except ContractError:
            raise
        except (TypeError, ValueError) as exc:
            raise ContractError("action or reward encoder returned invalid values") from exc
        if not bool(np.all(np.isfinite(rewards))):
            raise ContractError("encoded rewards must contain only finite values")
        if any(row.split != rows[0].split or row.seed != rows[0].seed for row in rows):
            raise ContractError("one branch cannot cross split or seed boundaries")
        exports.append(
            NumericEpisodeExport(
                split=rows[0].split,
                seed=rows[0].seed,
                manifest_digest=manifest_digest,
                branch_digest=branch_digest,
                projection_digest=projection.digest,
                agent_id=source.agent_id,
                packet_ids=tuple(packet.packet_id for packet in source.packets),
                observation_versions=tuple(
                    packet.observation_version for packet in source.packets
                ),
                observation_provenance=source.packets[0].provenance,
                observations=source.values,
                actions=actions,
                rewards=rewards,
                dones=np.asarray([row.terminated for row in rows], dtype=np.bool_),
            )
        )
    if not exports:
        raise ContractError("projection contains no transitions to export")
    return tuple(exports)


def write_episode_store(
    exports: Sequence[NumericEpisodeExport], root_dir: str
) -> NumericExportReceipt:
    """Write validated exports and an auditable projection sidecar."""

    exports = tuple(exports)
    if not exports:
        raise ContractError("exports must be non-empty")
    projection_digests = {item.projection_digest for item in exports}
    if len(projection_digests) != 1:
        raise ContractError("all exports must belong to one trace projection")
    obs_dims = {int(item.observations.shape[1]) for item in exports}
    action_dims = {int(item.actions.shape[1]) for item in exports}
    if len(obs_dims) != 1 or len(action_dims) != 1:
        raise ContractError("all exports must share observation and action dimensions")
    root = os.path.abspath(root_dir)
    metadata_path = os.path.join(root, "trace_projection_export.json")
    if os.path.exists(metadata_path):
        raise ContractError(f"refusing to append to existing export: {metadata_path}")
    store = EpisodeStore(
        root,
        DatasetSpec(action_dim=next(iter(action_dims)), obs_vec_dim=next(iter(obs_dims))),
    )
    episode_metadata: list[dict[str, object]] = []
    episode_paths: list[str] = []
    for item in sorted(exports, key=lambda value: (value.split, value.seed, value.branch_digest)):
        path = store.add(item.to_episode(), seed=item.seed)
        relative = os.path.relpath(path, root)
        episode_paths.append(path)
        episode_metadata.append(item.metadata(relative))
    payload: dict[str, object] = {
        "schema_version": NUMERIC_EXPORT_SCHEMA_VERSION,
        "agent_packet_schema_version": AGENT_PACKET_SCHEMA_VERSION,
        "projection_digest": next(iter(projection_digests)),
        "episodes": episode_metadata,
    }
    metadata_digest = content_digest("experiment.numeric-export", payload)
    payload["metadata_digest"] = metadata_digest
    os.makedirs(root, exist_ok=True)
    temporary = f"{metadata_path}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
    os.replace(temporary, metadata_path)
    return NumericExportReceipt(
        root_dir=root,
        metadata_path=metadata_path,
        metadata_digest=metadata_digest,
        episode_paths=tuple(episode_paths),
    )


__all__ = [
    "NUMERIC_EXPORT_SCHEMA_VERSION",
    "AGENT_PACKET_PROVENANCE",
    "AGENT_PACKET_SCHEMA_VERSION",
    "AgentObservationPacket",
    "agent_observation_packet_from_dto",
    "AgentObservationPacketReader",
    "AgentObservationSeries",
    "NumericEpisodeExport",
    "NumericExportReceipt",
    "build_numeric_exports",
    "collect_agent_observation_sources",
    "collect_agent_observation_sources_by_branch_reader",
    "collect_agent_observation_sources_from_packets",
    "read_agent_observation_packet",
    "read_agent_observation_series",
    "read_agent_observation_series_from_packets",
    "write_episode_store",
]
