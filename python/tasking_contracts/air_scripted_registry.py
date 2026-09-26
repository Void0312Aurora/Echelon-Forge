"""Compatibility shell for the canonical Air model registry."""

from __future__ import annotations

from .air import registry as _canonical
from .air.registry import *

__all__ = _canonical.__all__
