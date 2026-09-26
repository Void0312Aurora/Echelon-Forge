"""Compatibility shell for the canonical Air execution layer."""

from __future__ import annotations

from .air.execution import model as _canonical
from .air.execution.model import *

__all__ = _canonical.__all__
