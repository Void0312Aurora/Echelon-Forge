"""Compatibility shell for the common scripted model registry."""

from __future__ import annotations

from .common import scripted_registry as _canonical
from .common.scripted_registry import *

__all__ = _canonical.__all__
