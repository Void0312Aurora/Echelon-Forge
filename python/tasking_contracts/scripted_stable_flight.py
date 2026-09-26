"""Compatibility shell for the canonical Air stable-flight controller."""

from __future__ import annotations

from .air.execution import stable_flight as _canonical
from .air.execution.stable_flight import *

__all__ = _canonical.__all__
