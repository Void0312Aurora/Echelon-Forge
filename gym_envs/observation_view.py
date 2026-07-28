"""Declared observation view over the TL13 read seam (Unified Architecture Program T8).

This module is the single, layer-tagged *owner* of the raw World-Truth /
Track-State / Shared-Tactical-Picture / engagement-evidence reads that the
maintained observation and reward consumers used to perform inline. It realizes
the T8 second slice ("declaration-view convergence") from the
[G4 truth-leak inventory](../docs/plan/unified_architecture_program/t8_g4_truth_leak_inventory.md):
the consumers declared their information-state layer in the first slice; this
slice materializes a declarative view on the TL13 seam
(``scenario_loader/core.py::get_policy_agent_observation`` /
``get_policy_instrument_state`` -- the one maintained read chokepoint) and moves
the scattered ``truth.*`` / ``sim.*`` leaf reads behind it so the reads flow
through one declared, layer-labelled surface.

Design (G4 / G2):

* **Layer-labelled read faces.** Each function below is grouped and documented by
  the G4 information-state layer it exposes (architecture design doc §3): own-ship
  ``World Truth`` fields, ``Track State`` derived from ``truth.contacts``,
  ``Shared Tactical Picture`` support-unit reads, engagement-evidence reads, and
  explicit ``diagnostic`` reads (``debug_*`` APIs, which are *not* a maintained
  information layer and are labelled as such).
* **Zero behavior change.** Every function performs *exactly* the same underlying
  read (same function/attribute, same argument, same order) the consumer did
  before migration. It is a pure mechanical relocation of the leaf read into a
  layer-tagged owner: no defaults, no coercions, no control flow are added or
  removed here, so numeric results stay bit-for-bit identical. Where two
  consumers' original reads differed even in a guard's coercion, the view keeps
  both variants instead of unifying them: :func:`target_track` preserves the
  mission-observation guard (``int(target_id) <= 0``) and
  :func:`naval_target_track` preserves the naval reward surface's guard
  (``target_id <= 0``, no coercion), which diverge on non-int inputs (conversion
  count, exception propagation, boundary results). The consumers keep their own
  ``None`` guards, ``try``/``except`` and ``int()``/``float()`` coercions at the
  call site.
* **No import-time binding (monkeypatch-safe).** The view never captures a bound
  method or a ``truth``/``sim`` object at import time. It operates on the live
  objects the consumer already holds (obtained through the TL13 seam or
  ``loader.sim`` at call time) and resolves every attribute/method by dynamic
  lookup when called, so test seams that monkeypatch ``get_policy_agent_observation``,
  loader methods, or ``sim`` object methods keep working unchanged.
* **G2 placement.** The module is dependency-terminal (stdlib-only; it imports no
  ``gym_envs`` / ``python.rl`` / ``ef_py`` / ``numpy``), so it is a neutral leaf
  in the one-way layer ring. It sits at the ``gym_envs`` parent-package layer --
  the common lower layer shared by its two consumer subpackages
  (``gym_envs.scenario_loader.*`` and ``gym_envs.universal_env_parts``) -- per
  G2's rule that shared needs sink downward, never sideways: hosting it inside
  ``scenario_loader`` would force ``universal_env_parts`` into a lateral sibling
  import (the baseline has none), so the shared read owner sinks to the common
  parent layer instead. The reads it owns are derived from the TL13 seam's
  ``truth``/``inst`` output and from ``loader.sim``.

Deliberate non-goals for this slice: the view is a read face over the *output* of
the TL13 seam, not a replacement for the seam's ``get_policy_agent_observation``
call itself -- the consumers still fetch ``truth`` through the seam and pass it
in, so no double-fetch or truth-object identity change is introduced. Whole-object
transfers into compiled kernels (e.g. ``ef_py.compute_execution_observation_runtime_numpy(inst, truth, ...)``)
are not leaf field reads and stay in place.
"""

from __future__ import annotations

from typing import Any


# G4 information-state declaration (architecture design doc §3/§15; facility in
# python/architecture/information_layer.py). This module is the declared read
# owner: it consumes World Truth (own-ship + tracks), Track State and the Shared
# Tactical Picture on behalf of migrated consumers and exposes them as the policy
# observation read faces (Agent Observation). Pure metadata; no runtime cost.
INFORMATION_LAYER_CONSUMED = ("World Truth", "Track State", "Shared Tactical Picture")
INFORMATION_LAYER_PRODUCED = ("Agent Observation",)
SEMANTIC_STAGE = ("P10 ObservationExport",)


# --- World Truth: own-ship authoritative fields (own truth read) --------------
def own_ship_field(truth: Any, field: str, default: Any) -> Any:
    """World Truth (own-ship): ``getattr(truth, field, default)`` -- defaulted own-ship field read."""
    return getattr(truth, field, default)


def own_ship_attr(truth: Any, field: str) -> Any:
    """World Truth (own-ship): ``getattr(truth, field)`` -- exact ``truth.<field>`` (no default)."""
    return getattr(truth, field)


def own_missiles_remaining(truth: Any) -> int | None:
    """World Truth (own-ship weapon count): ``int(truth.missiles_remaining)``, or None if <0/unreadable."""
    try:
        value = int(getattr(truth, "missiles_remaining", -1))
    except Exception:
        return None
    return value if value >= 0 else None


# --- Track State: contacts and target track (derived from truth.contacts) -----
def contacts(truth: Any) -> Any:
    """Track State source: ``getattr(truth, "contacts", [])`` -- the own-ship contact list, for iteration."""
    return getattr(truth, "contacts", [])


def rwr_warnings(truth: Any) -> Any:
    """Sensed/Track (threat warnings): ``getattr(truth, "rwr_warnings", [])`` -- the RWR warning list, for iteration."""
    return getattr(truth, "rwr_warnings", [])


def target_track(truth: Any, target_id: int) -> Any | None:
    """Track State (mission-observation guard variant): the ``truth.contacts`` track with ``id == target_id``, else None.

    Token-for-token replica of ``mission_observation.py``'s original
    ``_target_track`` (baseline 1d25c4d1); its guard coerces first
    (``int(target_id) <= 0``). The naval reward surface uses
    :func:`naval_target_track`, whose guard does not coerce -- the two variants
    differ on non-int inputs and must not be unified.
    """
    if truth is None or int(target_id) <= 0:
        return None
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


def naval_target_track(truth: Any, target_id: int) -> Any | None:
    """Track State (naval guard variant): the ``truth.contacts`` track with ``id == target_id``, else None.

    Token-for-token replica of ``reward_runtime/naval.py``'s original
    ``_target_track`` (baseline 1d25c4d1); its guard compares uncoerced
    (``target_id <= 0``), unlike :func:`target_track` (the mission-observation
    variant, ``int(target_id) <= 0``). The variants diverge on non-int inputs
    (conversion count, exception propagation, boundary results -- e.g.
    ``target_id=0.5`` with an ``id=0`` track, or a string id), so each consumer
    keeps its own.
    """
    if truth is None or target_id <= 0:
        return None
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


# --- Shared Tactical Picture: support-unit reads ------------------------------
def support_agent_observation(reader: Any, entity_id: Any) -> Any:
    """Shared Tactical Picture: ``reader.get_agent_observation(entity_id)`` (a support unit's picture).

    ``reader`` is whatever the consumer already holds -- the loader-owned runtime
    view or the raw ``sim`` -- resolved dynamically so the seam is not bound early.
    """
    return reader.get_agent_observation(entity_id)


def support_unit_position(reader: Any, entity_id: Any) -> Any:
    """Shared Tactical Picture: ``reader.get_unit_position(entity_id)`` (a support unit's position)."""
    return reader.get_unit_position(entity_id)


def support_unit_messages(sim: Any, entity_id: Any) -> Any:
    """Shared Tactical Picture: ``sim.get_unit_messages(entity_id)`` (report chain, direct sim read)."""
    return sim.get_unit_messages(entity_id)


def support_unit_messages_optional(runtime_view: Any, entity_id: Any) -> Any:
    """Shared Tactical Picture: ``runtime_view.call_optional("get_unit_messages", entity_id, default=[])`` (report chain via the loader-owned runtime view)."""
    return runtime_view.call_optional("get_unit_messages", entity_id, default=[])


# --- Engagement evidence: kernel engagement / liveness / health reads ---------
def recent_engagement_events(sim: Any) -> Any:
    """Engagement evidence: ``sim.export_recent_engagement_events()`` (damage/lifecycle/consequence events)."""
    return sim.export_recent_engagement_events()


def unit_active(sim: Any, entity_id: Any) -> Any:
    """Engagement evidence (other-entity liveness): ``sim.is_unit_active(entity_id)``."""
    return sim.is_unit_active(entity_id)


def unit_health(sim: Any, entity_id: Any) -> Any:
    """Engagement evidence (other-entity health): ``sim.get_unit_health(entity_id)``."""
    return sim.get_unit_health(entity_id)


# --- Diagnostic reads: explicit debug_* APIs (NOT a maintained layer) ---------
def debug_aircraft_damage_state(sim: Any, entity_id: Any) -> Any:
    """Diagnostic: ``sim.debug_get_aircraft_damage_state(entity_id)`` (damage-consequence shaping)."""
    return sim.debug_get_aircraft_damage_state(entity_id)


def debug_ground_contact_state(sim: Any, entity_id: Any) -> Any:
    """Diagnostic: ``sim.debug_get_ground_contact_state(entity_id)`` (ground-contact terminal state)."""
    return sim.debug_get_ground_contact_state(entity_id)


__all__ = [
    "INFORMATION_LAYER_CONSUMED",
    "INFORMATION_LAYER_PRODUCED",
    "SEMANTIC_STAGE",
    "contacts",
    "debug_aircraft_damage_state",
    "debug_ground_contact_state",
    "naval_target_track",
    "own_missiles_remaining",
    "own_ship_attr",
    "own_ship_field",
    "recent_engagement_events",
    "rwr_warnings",
    "support_agent_observation",
    "support_unit_messages",
    "support_unit_messages_optional",
    "support_unit_position",
    "target_track",
    "unit_active",
    "unit_health",
]
