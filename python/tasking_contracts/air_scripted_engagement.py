"""Compatibility shell for the canonical Air engagement layer."""

from __future__ import annotations

from .air.engagement import model as _canonical
from .air.engagement.model import *

__all__ = _canonical.__all__
