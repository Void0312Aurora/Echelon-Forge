"""Compatibility shell for the canonical Joint coordination layer."""

from __future__ import annotations

from .joint import coordination as _canonical
from .joint.coordination import *

__all__ = _canonical.__all__
