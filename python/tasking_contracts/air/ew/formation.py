"""Air-owned, finite EW role leases over the shared opaque command link.

Member availability is an explicit command-communication input, not inferred
from world truth. Roles grant jammer permission; local chaff/flare requests
remain owned by each aircraft's self-protection policy and native resources.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable

import numpy as np

from ...common.command_link import CommandLinkEnvelope, ScriptedCommandLink


AIR_FORMATION_EW_ROLES = ("emission_hold", "self_protect")


@dataclass(frozen=True)
class AirFormationEWRoleOrder:
    role_id: str
    authority_epoch: int


@dataclass(frozen=True)
class AirFormationEWRoleReceipt:
    sequence: int
    source_member_id: str
    target_member_id: str
    role_id: str
    clock_s: float
    outcome: str


class AirFormationEWRuntime:
    """Accept only finite leases issued by the current declared commander."""

    def __init__(
        self, *, member_ids: Iterable[str], commander_ids: Iterable[str], seed: int = 0
    ) -> None:
        self.member_ids = tuple(str(value).strip() for value in member_ids)
        self.commander_ids = tuple(str(value).strip() for value in commander_ids)
        if (
            not self.commander_ids
            or len(set(self.commander_ids)) != len(self.commander_ids)
            or any(node not in self.member_ids for node in self.commander_ids)
        ):
            raise ValueError("Air EW requires unique commanders from the controlled member roster")
        self.link = ScriptedCommandLink(
            active_node_ids=self.member_ids,
            command_edges=(
                (source, target) for source in self.commander_ids for target in self.member_ids
            ),
            seed=seed,
        )
        self._available = set(self.member_ids)
        self._leader_id: str | None = self.commander_ids[0]
        self._authority_epoch = 0
        self._leases: dict[str, CommandLinkEnvelope] = {}
        self._last_accepted: dict[str, int] = {}
        self._receipts: deque[AirFormationEWRoleReceipt] = deque(maxlen=256)
        self._clock_s = 0.0

    @property
    def leader_id(self) -> str | None:
        return self._leader_id

    @property
    def receipts(self) -> tuple[AirFormationEWRoleReceipt, ...]:
        return tuple(self._receipts)

    def _record(self, envelope: CommandLinkEnvelope, outcome: str) -> None:
        self._receipts.append(
            AirFormationEWRoleReceipt(
                envelope.sequence,
                envelope.source_node_id,
                envelope.target_node_id,
                envelope.payload.role_id,
                self._clock_s,
                outcome,
            )
        )

    def issue(
        self,
        *,
        source_member_id: str,
        target_member_id: str,
        role_id: str,
        clock_s: float,
        delay_s: float = 0.0,
        ttl_s: float = 1.0,
        drop_prob: float = 0.0,
    ) -> CommandLinkEnvelope:
        source_member_id = str(source_member_id).strip()
        target_member_id = str(target_member_id).strip()
        if role_id not in AIR_FORMATION_EW_ROLES:
            raise ValueError(f"unknown Air EW role: {role_id!r}")
        if source_member_id != self.leader_id:
            raise ValueError("Air EW role order must originate from the current commander")
        if ttl_s is None or not isfinite(float(ttl_s)) or float(ttl_s) <= 0.0:
            raise ValueError("Air EW role orders require a positive finite ttl_s")
        return self.link.send(
            source_node_id=source_member_id,
            target_node_id=target_member_id,
            payload=AirFormationEWRoleOrder(role_id, self._authority_epoch),
            clock_s=clock_s,
            delay_s=delay_s,
            ttl_s=ttl_s,
            drop_prob=drop_prob,
        )

    def advance(self, *, clock_s: float) -> None:
        delivered = self.link.deliver(clock_s=clock_s)
        self._clock_s = float(clock_s)
        for member, envelope in tuple(self._leases.items()):
            if self._clock_s >= envelope.expires_at_s:
                self._record(envelope, "expired_lease")
                del self._leases[member]
        for envelope in delivered:
            order = envelope.payload
            if (
                not isinstance(order, AirFormationEWRoleOrder)
                or order.role_id not in AIR_FORMATION_EW_ROLES
            ):
                raise TypeError("Air EW transport payload must be an AirFormationEWRoleOrder")
            if (
                envelope.source_node_id != self.leader_id
                or order.authority_epoch != self._authority_epoch
                or envelope.expires_at_s is None
            ):
                self._record(envelope, "rejected_authority")
            elif envelope.sequence <= self._last_accepted.get(envelope.target_node_id, 0):
                self._record(envelope, "rejected_older_order")
            else:
                self._leases[envelope.target_node_id] = envelope
                self._last_accepted[envelope.target_node_id] = envelope.sequence
                self._record(envelope, "accepted")

    def set_member_available(self, member_id: str, *, available: bool, clock_s: float) -> None:
        member_id = str(member_id).strip()
        # Validate/update transport first; a bad node or backwards clock must
        # leave Air authority and accepted leases unchanged.
        self.link.set_node_available(member_id, available=available, clock_s=clock_s)
        self._clock_s = float(clock_s)
        if available:
            self._available.add(member_id)
        else:
            self._available.discard(member_id)
        leader = next((node for node in self.commander_ids if node in self._available), None)
        if leader != self._leader_id:
            self._leader_id = leader
            self._authority_epoch += 1
            for envelope in self._leases.values():
                self._record(envelope, "revoked_authority")
            self._leases.clear()
            self._last_accepted.clear()
        elif not available and member_id in self._leases:
            self._record(self._leases.pop(member_id), "revoked_member")

    def filter_action(self, member_id: str, action: np.ndarray) -> np.ndarray:
        if member_id not in self.member_ids:
            raise KeyError(f"unknown Air EW member: {member_id!r}")
        values = np.asarray(action, dtype=np.float32)
        if values.shape != (16,):
            raise ValueError("Air formation EW requires the 16-element air_ew_hybrid_v2 action")
        result = values.copy()
        lease = self._leases.get(member_id)
        if lease is None or lease.payload.role_id != "self_protect":
            result[14:16] = 0.0
        return result

    def snapshot(self, member_id: str) -> dict:
        member_id = str(member_id).strip()
        if member_id not in self.member_ids:
            raise KeyError(f"unknown Air EW member: {member_id!r}")
        lease = self._leases.get(member_id)
        member_receipts = tuple(
            item for item in self.receipts if item.target_member_id == member_id
        )
        return {
            "member_id": member_id,
            "leader_id": self.leader_id,
            "communication_available": member_id in self._available,
            "role_id": "emission_hold" if lease is None else lease.payload.role_id,
            "role_source": None if lease is None else lease.source_node_id,
            "role_sequence": None if lease is None else lease.sequence,
            "expires_at_s": None if lease is None else lease.expires_at_s,
            "authority_epoch": self._authority_epoch,
            "clock_s": self._clock_s,
            "link_counts": self.link.counts,
            "recent_role_receipt_count": len(member_receipts),
            "latest_role_receipt": None if not member_receipts else asdict(member_receipts[-1]),
        }

    def close(self) -> None:
        self.link.close()
        self._leases.clear()


__all__ = [
    "AIR_FORMATION_EW_ROLES",
    "AirFormationEWRoleOrder",
    "AirFormationEWRoleReceipt",
    "AirFormationEWRuntime",
]
