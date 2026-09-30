"""Route opaque Joint command envelopes into maintained facade assignments."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from python.tasking_contracts.joint.command_link import JointCommandLinkEnvelope
from python.tasking_contracts.joint.coordination import ScriptedJointTaskGraph


CommandBuilder = Callable[[JointCommandLinkEnvelope], Any]
ReportBuilder = Callable[[JointCommandLinkEnvelope], Any]


class JointFacadeCommandRouter:
    """Bind explicit Joint node builders to controlled facade entities.

    The router owns only endpoint validation and batch submission.  A builder
    is the domain owner for the native ``MissionCommand`` payload; the Joint
    layer never interprets Air or Naval fields.
    """

    def __init__(
        self,
        backend: Any,
        *,
        entity_key_by_node: Mapping[str, tuple[int, int]],
        command_builder_by_node: Mapping[str, CommandBuilder],
        task_graph: ScriptedJointTaskGraph,
        ignored_node_ids: Sequence[str] = (),
    ) -> None:
        submit = getattr(backend, "submit_mission_commands", None)
        if not callable(submit):
            raise TypeError("joint facade router backend must expose submit_mission_commands")
        if not isinstance(entity_key_by_node, Mapping) or not isinstance(command_builder_by_node, Mapping):
            raise TypeError("joint facade router endpoints and builders must be mappings")
        if not isinstance(task_graph, ScriptedJointTaskGraph):
            raise TypeError("joint facade router requires the authoritative ScriptedJointTaskGraph")
        self.backend = backend
        self.task_graph = task_graph
        self.entity_key_by_node = {
            str(node_id): (int(key[0]), int(key[1]))
            for node_id, key in entity_key_by_node.items()
        }
        self.command_builder_by_node = dict(command_builder_by_node)
        self.ignored_node_ids = frozenset(str(node_id) for node_id in ignored_node_ids)
        for node_id, builder in self.command_builder_by_node.items():
            if not str(node_id).strip() or not callable(builder):
                raise TypeError("joint facade router builders must be callable and node keyed")

    def route(self, envelopes: Sequence[JointCommandLinkEnvelope]) -> tuple[str, ...]:
        if not isinstance(envelopes, Sequence) or isinstance(envelopes, (str, bytes)):
            raise TypeError("joint facade router requires a sequence of command envelopes")
        assignments: dict[tuple[int, int], Any] = {}
        routed: list[str] = []
        for envelope in envelopes:
            if not isinstance(envelope, JointCommandLinkEnvelope):
                raise TypeError("joint facade router received a non-envelope payload")
            node_id = str(envelope.target_node_id)
            if node_id in self.ignored_node_ids:
                continue
            if node_id not in self.entity_key_by_node:
                raise KeyError(f"joint facade router has no entity endpoint for {node_id!r}")
            if not self.task_graph.allows_command(envelope.source_node_id, node_id):
                raise ValueError(
                    f"joint facade router rejects undeclared command edge: "
                    f"{envelope.source_node_id!r} -> {node_id!r}"
                )
            builder = self.command_builder_by_node.get(node_id)
            if builder is None:
                raise KeyError(f"joint facade router has no command builder for {node_id!r}")
            key = self.entity_key_by_node[node_id]
            if key in assignments:
                raise ValueError(f"joint facade router received duplicate command for {node_id!r}")
            assignments[key] = builder(envelope)
            routed.append(node_id)
        if assignments:
            self.backend.submit_mission_commands(assignments)
            # Submission acknowledges enqueue.  CommandLink may deliver later;
            # an immediate readback would incorrectly reject valid delayed state.
        return tuple(routed)


class JointFacadeReportRouter:
    """Submit domain-owned pilot reports and verify common report identity.

    The Joint layer routes opaque envelopes only.  Report builders remain
    domain-owned and may populate Air, Naval, or Ground slices without a
    cross-domain report schema.
    """

    def __init__(
        self,
        backend: Any,
        *,
        entity_key_by_node: Mapping[str, tuple[int, int]],
        report_builder_by_node: Mapping[str, ReportBuilder],
        ignored_node_ids: Sequence[str] = (),
    ) -> None:
        submit = getattr(backend, "submit_pilot_reports", None)
        if not callable(submit):
            raise TypeError("joint facade report router backend must expose submit_pilot_reports")
        if not isinstance(entity_key_by_node, Mapping) or not isinstance(report_builder_by_node, Mapping):
            raise TypeError("joint facade report router endpoints and builders must be mappings")
        self.backend = backend
        self.entity_key_by_node = {
            str(node_id): (int(key[0]), int(key[1]))
            for node_id, key in entity_key_by_node.items()
        }
        self.report_builder_by_node = dict(report_builder_by_node)
        self.ignored_node_ids = frozenset(str(node_id) for node_id in ignored_node_ids)
        for node_id, builder in self.report_builder_by_node.items():
            if not str(node_id).strip() or not callable(builder):
                raise TypeError("joint facade report builders must be callable and node keyed")

    def route(self, envelopes: Sequence[JointCommandLinkEnvelope]) -> tuple[str, ...]:
        if not isinstance(envelopes, Sequence) or isinstance(envelopes, (str, bytes)):
            raise TypeError("joint facade report router requires a sequence of command envelopes")
        assignments: dict[tuple[int, int], Any] = {}
        routed: list[str] = []
        for envelope in envelopes:
            if not isinstance(envelope, JointCommandLinkEnvelope):
                raise TypeError("joint facade report router received a non-envelope payload")
            node_id = str(envelope.target_node_id)
            if node_id in self.ignored_node_ids:
                continue
            if node_id not in self.entity_key_by_node:
                raise KeyError(f"joint facade report router has no entity endpoint for {node_id!r}")
            builder = self.report_builder_by_node.get(node_id)
            if builder is None:
                raise KeyError(f"joint facade report router has no report builder for {node_id!r}")
            key = self.entity_key_by_node[node_id]
            if key in assignments:
                raise ValueError(f"joint facade report router received duplicate report for {node_id!r}")
            assignments[key] = builder(envelope)
            routed.append(node_id)
        if assignments:
            self.backend.submit_pilot_reports(assignments)
            self._verify_common_report_readback(assignments)
        return tuple(routed)

    def _verify_common_report_readback(self, assignments: Mapping[tuple[int, int], Any]) -> None:
        """Verify common report identity, timing, authority, and provenance."""
        read_chain = getattr(self.backend, "read_command_chain", None)
        roster = getattr(self.backend, "entity_keys", None)
        if not callable(read_chain) or roster is None:
            raise RuntimeError(
                "joint facade report router requires maintained pilot-report readback "
                "to acknowledge delivery"
            )
        chain = read_chain()
        reports = tuple(chain.get("pilot_reports", ())) if isinstance(chain, Mapping) else ()
        keys = tuple(roster)
        for key, expected in assignments.items():
            try:
                index = keys.index(key)
            except ValueError as exc:
                raise KeyError(f"joint facade report router readback has no roster entry for {key!r}") from exc
            if index >= len(reports):
                raise RuntimeError(f"joint facade report router readback omitted report for {key!r}")
            actual = reports[index]
            for name in (
                "active",
                "sender_id",
                "task_id",
                "phase_id",
                "timestamp_s",
                "task_group_id",
                "roe_state",
                "authorization_to_fire",
                "assigned_target_id",
                "engagement_authority_holder_id",
                "engagement_authority_grantor_id",
            ):
                expected_value = _field(expected, name)
                actual_value = _field(actual, name)
                if expected_value != actual_value:
                    raise RuntimeError(
                        f"joint facade report router readback mismatch for {key!r}: "
                        f"{name} expected {expected_value!r}, got {actual_value!r}"
                    )


def _field(value: Any, name: str) -> Any:
    # Maintained native reports keep common provenance in shared_core while
    # domain fields such as phase_id live in the corresponding slice.
    for candidate in (
        value,
        getattr(value, "shared_core", None),
        getattr(value, "air", None),
        getattr(value, "naval_command_authority", None),
        getattr(value, "naval", None),
        getattr(value, "ground", None),
    ):
        if candidate is not None and hasattr(candidate, name):
            return getattr(candidate, name)
    return None


__all__ = ["JointFacadeCommandRouter", "JointFacadeReportRouter"]
