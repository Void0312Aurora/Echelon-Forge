"""Compatibility shell for common scripted capability metadata."""

from __future__ import annotations

from .common import scripted_capability as _canonical
from .common.scripted_capability import *

__all__ = _canonical.__all__
