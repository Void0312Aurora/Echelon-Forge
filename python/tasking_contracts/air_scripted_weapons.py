"""Compatibility shell for the canonical Air strategy weapon layer."""

from __future__ import annotations

from .air.strategy.weapons import AirWeaponEnvelope, load_air_weapon_envelope

__all__ = ["AirWeaponEnvelope", "load_air_weapon_envelope"]
