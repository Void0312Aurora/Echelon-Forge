"""Common-runtime consumer for an admitted scripted joint task graph.

The graph remains a common coordination declaration.  Each active node is
resolved through the registry owned by its domain and is then scheduled by the
neutral ``DecisionRuntimeRoster``.  This module does not project service
payloads into a joint mega-schema and does not import RL, native bindings, or a
simulation backend.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..common.decision_registry import DecisionModelRegistry
from ..common.decision_runtime import (
    DECISION_RUNTIME_ACTION_DECIDED,
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
    DecisionRuntimeRoster,
    DecisionRuntimeStep,
)
from .command_link import JointCommandLinkEnvelope, ScriptedJointCommandLink
from .coordination import ScriptedJointTaskGraph


class ScriptedJointRuntimeConsumer:
    """Resolve graph nodes through domain registries and run one joint roster."""

    def __init__(
        self,
        graph: ScriptedJointTaskGraph,
        *,
        registries: Mapping[str, DecisionModelRegistry],
        factory_kwargs_by_node: Mapping[str, Mapping[str, Any]] | None = None,
        decision_period_s: float = 1.0,
    ) -> None:
        if not isinstance(graph, ScriptedJointTaskGraph):
            raise TypeError("joint runtime consumer requires ScriptedJointTaskGraph")
        if not isinstance(registries, Mapping):
            raise TypeError("joint runtime consumer registries must be domain keyed")
        joint_directors = graph.joint_director_ids()
        if len(joint_directors) != 1:
            raise ValueError(
                "joint runtime graph must contain exactly one active joint director; "
                f"got {len(joint_directors)}"
            )
        kwargs_by_node = factory_kwargs_by_node or {}
        agents: list[DecisionRuntimeAgent] = []
        for node in graph.nodes:
            if not node.active:
                continue
            registry = registries.get(node.domain)
            if not isinstance(registry, DecisionModelRegistry):
                raise KeyError(f"joint runtime has no registry for domain {node.domain!r}")
            kwargs = kwargs_by_node.get(node.node_id, {})
            if not isinstance(kwargs, Mapping):
                raise TypeError(f"joint runtime factory kwargs for {node.node_id!r} must be a mapping")
            model = registry.create_for(
                domain=node.domain,
                role_id=node.role_id,
                model_id=node.payload_ref,
                model_kind="scripted",
                **dict(kwargs),
            )
            spec = DecisionRuntimeAgentSpec(
                agent_id=node.node_id,
                model_id=node.payload_ref,
                domain=node.domain,
                role_id=node.role_id,
                model_kind="scripted",
                decision_period_s=decision_period_s,
                communication_state="available",
                authority_scope=node.authority_scope,
                active=True,
            )
            agents.append(DecisionRuntimeAgent(spec, model))
        if not agents:
            raise ValueError("joint runtime graph has no active executable nodes")
        self.graph = graph
        self._joint_director_id = joint_directors[0]
        self.roster = DecisionRuntimeRoster(tuple(agents))
        self.command_link = ScriptedJointCommandLink(graph)
        self.last_delivered_commands: tuple[JointCommandLinkEnvelope, ...] = ()
        self._pending_command_inboxes: dict[str, list[JointCommandLinkEnvelope]] = {
            node_id: [] for node_id in self.active_node_ids
        }
        self._closed = False

    @property
    def active_node_ids(self) -> tuple[str, ...]:
        return self.graph.active_node_ids()

    def reset(
        self,
        *,
        context_by_node: Mapping[str, Any] | None = None,
        episode_seed: int | None = None,
    ) -> None:
        if self._closed:
            raise RuntimeError("joint runtime consumer is closed")
        supplied = context_by_node or {}
        contexts: dict[str, Any] = {}
        for node_id in self.active_node_ids:
            raw = supplied.get(node_id, {})
            context = dict(raw) if isinstance(raw, Mapping) else {}
            if node_id == self._joint_director_id:
                context.setdefault("task_graph", self.graph)
            contexts[node_id] = context
        self.command_link.reset()
        self.last_delivered_commands = ()
        for inbox in self._pending_command_inboxes.values():
            inbox.clear()
        self.roster.reset(context_by_agent=contexts, episode_seed=episode_seed)

    @property
    def pending_command_inboxes(self) -> Mapping[str, tuple[JointCommandLinkEnvelope, ...]]:
        """Return durable delivered envelopes awaiting target consumption."""

        return {
            node_id: tuple(inbox)
            for node_id, inbox in self._pending_command_inboxes.items()
            if inbox
        }

    def route_intent(
        self,
        intent: Any,
        *,
        clock_s: float,
        delay_s: float = 0.0,
    ) -> tuple[JointCommandLinkEnvelope, ...]:
        """Route one Joint intent to its declared active graph targets."""

        if self._closed:
            raise RuntimeError("joint runtime consumer is closed")
        if getattr(intent, "graph_id", None) != self.graph.graph_id:
            raise ValueError("joint runtime intent graph does not match consumer graph")
        source = str(getattr(intent, "producer_id", "")).strip()
        target_ids = tuple(getattr(intent, "target_node_ids", ()) or ())
        envelopes = []
        for target_id in target_ids:
            if not self.graph.allows_command(source, target_id):
                raise ValueError(
                    f"joint runtime command edge is not declared: {source!r} -> {target_id!r}"
                )
            envelopes.append(
                self.command_link.send(
                    source_node_id=source,
                    target_node_id=target_id,
                    payload=intent,
                    clock_s=clock_s,
                    delay_s=delay_s,
                )
            )
        return tuple(envelopes)

    def step(
        self,
        *,
        observations: Mapping[str, Any],
        clock_s: float,
        observation_versions: Mapping[str, str] | None = None,
        context_by_node: Mapping[str, Any] | None = None,
        force_decide: bool = False,
    ) -> dict[str, DecisionRuntimeStep]:
        if self._closed:
            raise RuntimeError("joint runtime consumer is closed")
        delivered = self.command_link.deliver(clock_s=clock_s)
        self.last_delivered_commands = delivered
        for envelope in delivered:
            self._pending_command_inboxes.setdefault(envelope.target_node_id, []).append(envelope)
        supplied = context_by_node or {}
        routed_contexts: dict[str, Any] = {
            node_id: (dict(value) if isinstance(value, Mapping) else {})
            for node_id, value in supplied.items()
        }
        for node_id, pending in self._pending_command_inboxes.items():
            if not pending:
                continue
            inbox = routed_contexts.setdefault(node_id, {}).setdefault("joint_command_inbox", [])
            if not isinstance(inbox, list):
                raise TypeError(
                    f"joint runtime context joint_command_inbox for {node_id!r} must be a list"
                )
            inbox.extend(pending)
        results = self.roster.step(
            observations=observations,
            clock_s=clock_s,
            observation_versions=observation_versions,
            context_by_agent=routed_contexts,
            force_decide=force_decide,
        )
        for node_id, pending in self._pending_command_inboxes.items():
            result = results.get(node_id)
            if result is not None and result.report.action_source == DECISION_RUNTIME_ACTION_DECIDED:
                pending.clear()
        return results

    def close(self) -> None:
        if not self._closed:
            self.command_link.close()
            self.roster.close()
            self._closed = True

__all__ = ["ScriptedJointRuntimeConsumer"]
