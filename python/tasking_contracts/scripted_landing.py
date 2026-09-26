"""Compatibility shell for the canonical Air landing controller."""

from __future__ import annotations

from .air.execution import landing as _canonical
from .air.execution.landing import *

__all__ = _canonical.__all__
