"""Compatibility shell for the canonical Joint projection layer."""

from __future__ import annotations

from .joint import projection as _canonical
from .joint.projection import *

__all__ = _canonical.__all__
