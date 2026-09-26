"""Compatibility shell for the canonical Naval adapter layer."""

from __future__ import annotations

from .naval import execution as _canonical
from .naval.execution import *

__all__ = _canonical.__all__
