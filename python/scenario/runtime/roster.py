from __future__ import annotations

from typing import Any

import ef_py

from python.scenario_compiler import _clone_runtime_mission_command

from .models import AppliedScenarioRosterMember, AppliedScenarioWorld, ScenarioRosterMemberLayout


def _coerce_optional_positive_int(value: Any) -> int | None:
    try:
        out = int(value)
    except Exception:
        return None
    return out if out > 0 else None


def _cooperative_roster_config(scenario_data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(scenario_data, dict):
        return None
    roster = scenario_data.get("cooperative_roster", None)
    if isinstance(roster, dict):
        return roster
    roster = scenario_data.get("active_controllable_roster", None)
    if isinstance(roster, dict):
        return roster
    return None


def _normalized_cooperative_roster_members(scenario_data: dict[str, Any] | None) -> list[ScenarioRosterMemberLayout]:
    roster_cfg = _cooperative_roster_config(scenario_data)
    members: list[ScenarioRosterMemberLayout] = []
    if not isinstance(roster_cfg, dict):
        return members

    raw_members = roster_cfg.get("members", None)
    if not isinstance(raw_members, list) or not raw_members:
        return members

    default_team_id = _coerce_optional_positive_int(roster_cfg.get("team_id", None))
    default_policy_route = roster_cfg.get("policy_route", None)
    default_element_id = _coerce_optional_positive_int(roster_cfg.get("element_id", None))
    for raw_member in raw_members:
        if not isinstance(raw_member, dict):
            continue
        entity_name = str(raw_member.get("entity", raw_member.get("entity_name", ""))).strip()
        if not entity_name:
            continue
        is_agent = bool(raw_member.get("is_agent", True))
        team_id = _coerce_optional_positive_int(raw_member.get("team_id", default_team_id))
        element_id = _coerce_optional_positive_int(raw_member.get("element_id", default_element_id))
        role_code = _coerce_optional_positive_int(raw_member.get("role_code", None))
        formation_role_id = str(raw_member.get("formation_role_id", "")).strip() or None
        relative_slot_code = _coerce_optional_positive_int(raw_member.get("relative_slot_code", None))
        policy_route = str(raw_member.get("policy_route", default_policy_route or "")).strip() or None
        reference_entity_name = str(
            raw_member.get("reference_entity", raw_member.get("reference_entity_name", ""))
        ).strip() or None
        reference_entity_id = _coerce_optional_positive_int(
            raw_member.get("reference_entity_id", raw_member.get("reference_entity_id", None))
        )
        mission_command_overrides = raw_member.get("mission_command_overrides", None)
        if not isinstance(mission_command_overrides, dict):
            mission_command_overrides = None
        task_order_overrides = raw_member.get("task_order_overrides", None)
        if not isinstance(task_order_overrides, dict):
            task_order_overrides = None
        members.append(
            ScenarioRosterMemberLayout(
                entity_name=entity_name,
                is_agent=is_agent,
                team_id=team_id,
                element_id=element_id,
                role_code=role_code,
                formation_role_id=formation_role_id,
                relative_slot_code=relative_slot_code,
                policy_route=policy_route,
                reference_entity_name=reference_entity_name,
                reference_entity_id=reference_entity_id,
                mission_command_overrides=(
                    None if mission_command_overrides is None else _clone_runtime_mission_command(mission_command_overrides)
                ),
                task_order_overrides=None if task_order_overrides is None else dict(task_order_overrides),
            )
        )

    return members


def resolve_active_controllable_roster(
    scenario_data: dict[str, Any] | None,
    entities: dict[str, int] | None = None,
    *,
    world_index: int | None = None,
) -> list[AppliedScenarioRosterMember]:
    scenario_data = scenario_data if isinstance(scenario_data, dict) else {}
    entities = entities if isinstance(entities, dict) else {}

    members = _normalized_cooperative_roster_members(scenario_data)
    if not members:
        entities_cfg = scenario_data.get("entities", [])
        if isinstance(entities_cfg, list):
            for ent_cfg in entities_cfg:
                if not isinstance(ent_cfg, dict) or not bool(ent_cfg.get("is_agent", False)):
                    continue
                entity_name = str(ent_cfg.get("name", "")).strip()
                if not entity_name:
                    continue
                members.append(
                    ScenarioRosterMemberLayout(
                        entity_name=entity_name,
                        is_agent=True,
                    )
                )

    roster: list[AppliedScenarioRosterMember] = []
    for member in members:
        entity_id = entities.get(member.entity_name)
        if entity_id is None:
            continue
        reference_entity_id = member.reference_entity_id
        if reference_entity_id is None and member.reference_entity_name:
            reference_entity_id = entities.get(member.reference_entity_name)
        roster.append(
            AppliedScenarioRosterMember(
                world_index=None if world_index is None else int(world_index),
                entity_name=str(member.entity_name),
                entity_id=int(entity_id),
                is_agent=bool(member.is_agent),
                team_id=member.team_id,
                element_id=member.element_id,
                role_code=member.role_code,
                formation_role_id=member.formation_role_id,
                relative_slot_code=member.relative_slot_code,
                policy_route=member.policy_route,
                reference_entity_name=member.reference_entity_name,
                reference_entity_id=None if reference_entity_id is None else int(reference_entity_id),
                mission_command_overrides=(
                    None if member.mission_command_overrides is None else _clone_runtime_mission_command(member.mission_command_overrides)
                ),
                task_order_overrides=None if member.task_order_overrides is None else dict(member.task_order_overrides),
            )
        )
    return roster


def find_active_roster_member(
    roster: list[AppliedScenarioRosterMember] | None,
    *,
    entity_id: int | None = None,
    entity_name: str | None = None,
    role_code: int | None = None,
    formation_role_id: str | None = None,
) -> AppliedScenarioRosterMember | None:
    if not isinstance(roster, list) or not roster:
        return None

    normalized_name = str(entity_name).strip() if entity_name is not None else None
    normalized_formation_role = str(formation_role_id).strip() if formation_role_id is not None else None

    for member in roster:
        if entity_id is not None and int(member.entity_id) != int(entity_id):
            continue
        if normalized_name is not None and str(member.entity_name) != normalized_name:
            continue
        if role_code is not None and int(member.role_code or 0) != int(role_code):
            continue
        if normalized_formation_role is not None and str(member.formation_role_id or "") != normalized_formation_role:
            continue
        return member
    return None


def active_roster_world_entity_refs(
    roster: list[AppliedScenarioRosterMember] | None,
    *,
    world_index: int | None = None,
) -> list[Any]:
    if not isinstance(roster, list) or not roster:
        return []

    refs: list[Any] = []
    for member in roster:
        ref_world_index = member.world_index if world_index is None else int(world_index)
        if ref_world_index is None:
            continue
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(ref_world_index)
        ref.entity_id = int(member.entity_id)
        refs.append(ref)
    return refs


def _attach_active_roster_to_applied_world(
    applied_world: AppliedScenarioWorld,
    *,
    world_index: int | None = None,
) -> AppliedScenarioWorld:
    layout = getattr(applied_world, "layout", None)
    scenario_data = getattr(layout, "scenario_data", None) if layout is not None else None
    active_roster = resolve_active_controllable_roster(
        scenario_data if isinstance(scenario_data, dict) else {},
        getattr(applied_world, "entities", None),
        world_index=world_index,
    )
    applied_world.active_roster = active_roster
    return applied_world
