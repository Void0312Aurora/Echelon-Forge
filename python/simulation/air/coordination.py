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
    target_key: EntityKey | None = None


class AirScriptedRosterCoordinator:
    """Assign distinct declared contact tracks to an active Air roster."""

    def assign_targets(
        self,
        *,
        observations: Mapping[EntityKey, Any],
        members: Mapping[EntityKey, str],
        candidate_target_ids: Sequence[int | EntityKey],
        authorized_member_keys: Sequence[EntityKey] | None = None,
    ) -> tuple[AirTargetAssignment, ...]:
        if not isinstance(observations, Mapping) or not isinstance(members, Mapping):
            raise TypeError("Air roster coordination requires entity-keyed mappings")
        world_indices = {int(key[0]) for key in members}
        candidate_keys = set()
        for value in candidate_target_ids:
            if isinstance(value, (tuple, list)) and len(value) == 2:
                key = (int(value[0]), int(value[1]))
            else:
                if len(world_indices) > 1:
                    raise ValueError(
                        "Air roster coordination requires world-qualified candidate target keys"
                    )
                key = (next(iter(world_indices), 0), int(value))
            if key[0] >= 0 and key[1] > 0:
                candidate_keys.add(key)
        if not candidate_keys:
            raise ValueError("Air roster coordination requires candidate target IDs")
        reserved: set[EntityKey] = set()
        # Authority is an explicit input to the coordinator.  Omitting it must
        # never silently grant every roster member fire authority.
        authorized = set() if authorized_member_keys is None else set(authorized_member_keys)
        unknown_authorized = authorized.difference(members)
        if unknown_authorized:
            raise KeyError(f"Air roster authority references unknown members: {sorted(unknown_authorized)}")
        results: list[AirTargetAssignment] = []
        for member_key in sorted(members, key=lambda key: (self._role_priority(members[key]), key)):
            observation = observations.get(member_key)
            contacts = list(getattr(observation, "contacts", ()) or ()) if observation is not None else []
            viable = [
                contact
                for contact in contacts
                if (member_key[0], int(getattr(contact, "id", 0))) in candidate_keys
                and (member_key[0], int(getattr(contact, "id", 0))) not in reserved
            ]
            viable.sort(key=lambda contact: (self._float(contact, "range"), int(getattr(contact, "id", 0))))
            contact = viable[0] if viable else None
            target_id = None if contact is None else int(getattr(contact, "id", 0))
            target_key = None if target_id is None else (member_key[0], target_id)
            if target_key is not None:
                reserved.add(target_key)
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
                    authority_holder_id=int(member_key[1]) if member_key in authorized else 0,
                    target_key=target_key,
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
