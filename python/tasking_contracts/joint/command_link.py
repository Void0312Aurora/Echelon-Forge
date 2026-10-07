"""Graph-scoped compatibility adapter for the shared opaque command link."""

from __future__ import annotations

from ..common.command_link import CommandLinkEnvelope, ScriptedCommandLink
from .coordination import ScriptedJointTaskGraph


JointCommandLinkEnvelope = CommandLinkEnvelope


class ScriptedJointCommandLink(ScriptedCommandLink):
    def __init__(self, graph: ScriptedJointTaskGraph, *, seed: int = 0) -> None:
        if not isinstance(graph, ScriptedJointTaskGraph):
            raise TypeError("joint command link requires ScriptedJointTaskGraph")
        self.graph = graph
        super().__init__(
            active_node_ids=graph.active_node_ids(),
            command_edges=(
                (source, target)
                for source in graph.active_node_ids()
                for target in graph.command_target_ids(source)
            ),
            seed=seed,
        )


__all__ = ["JointCommandLinkEnvelope", "ScriptedJointCommandLink"]
