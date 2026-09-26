"""Compatibility shell for the canonical Air EW layer."""

from __future__ import annotations

from .air.ew import model as _canonical
from .air.ew.model import *

__all__ = _canonical.__all__
