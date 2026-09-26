"""Compatibility shell for the common agency vocabulary."""

from __future__ import annotations

from .common import agency_registry as _canonical
from .common.agency_registry import *

__all__ = _canonical.__all__
