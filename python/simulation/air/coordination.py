"""Declared-sensor Air roster coordination for the scripted line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


EntityKey = tuple[int, int]


@dataclass(frozen=True)
class AirTargetAssignment:
    """One deterministic member-to-track assignment."""

    member_key: EntityKey
    role_id: str
    target_id: int | None
    target_range_m: float
    target_bearing_deg: float
    target_elevation_deg: float
    closing_speed_mps: float
    track_age_s: float
    authorization_to_fire: bool
    authority_holder_id: int


class AirScriptedRosterCoordinator:
    """Assign distinct declared contact tracks to an active Air roster."""

    def assign_targets(
        self,
        *,
        observations: Mapping[EntityKey, Any],
        members: Mapping[EntityKey, str],
        candidate_target_ids: Sequence[int],
        authorized_member_keys: Sequence[EntityKey] | None = None,
    ) -> tuple[AirTargetAssignment, ...]:
        if not isinstance(observations, Mapping) or not isinstance(members, Mapping):
            raise TypeError("Air roster coordination requires entity-keyed mappings")
        candidates = {int(value) for value in candidate_target_ids if int(value) > 0}
        if not candidates:
            raise ValueError("Air roster coordination requires candidate target IDs")
        reserved: set[int] = set()
        authorized = set(members) if authorized_member_keys is None else set(authorized_member_keys)
        unknown_authorized = authorized.difference(members)
        if unknown_authorized:
            raise KeyError(f"Air roster authority references unknown members: {sorted(unknown_authorized)}")
        authority_holder_id = next(
            (int(key[1]) for key in sorted(authorized) if key in members),
            0,
        )
        results: list[AirTargetAssignment] = []
        for member_key in sorted(members, key=lambda key: (self._role_priority(members[key]), key)):
            observation = observations.get(member_key)
            contacts = list(getattr(observation, "contacts", ()) or ()) if observation is not None else []
            viable = [
                contact
                for contact in contacts
                if int(getattr(contact, "id", 0)) in candidates
                and int(getattr(contact, "id", 0)) not in reserved
            ]
            viable.sort(key=lambda contact: (self._float(contact, "range"), int(getattr(contact, "id", 0))))
            contact = viable[0] if viable else None
            target_id = None if contact is None else int(getattr(contact, "id", 0))
            if target_id is not None:
                reserved.add(target_id)
            results.append(
                AirTargetAssignment(
                    member_key=member_key,
                    role_id=str(members[member_key]),
                    target_id=target_id,
                    target_range_m=0.0 if contact is None else self._float(contact, "range"),
                    target_bearing_deg=0.0 if contact is None else self._float(contact, "azimuth"),
                    target_elevation_deg=0.0 if contact is None else self._float(contact, "elevation"),
                    closing_speed_mps=0.0 if contact is None else self._float(contact, "closing_speed"),
                    track_age_s=0.0 if contact is None else self._float(contact, "time_since_update"),
                    authorization_to_fire=member_key in authorized,
                    authority_holder_id=authority_holder_id,
                )
            )
        return tuple(results)

    @staticmethod
    def _role_priority(role_id: Any) -> int:
        role = str(role_id).strip().lower()
        return 0 if role in {"lead", "element_lead", "flight_lead"} else 1

    @staticmethod
    def _float(value: Any, name: str) -> float:
        try:
            return float(getattr(value, name))
        except (AttributeError, TypeError, ValueError):
            return 0.0


__all__ = ["AirScriptedRosterCoordinator", "AirTargetAssignment", "EntityKey"]
