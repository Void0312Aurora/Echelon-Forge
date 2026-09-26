"""Compatibility shell for the canonical Air takeoff controller."""

from __future__ import annotations

from .air.execution import takeoff as _canonical
from .air.execution.takeoff import *

__all__ = _canonical.__all__
