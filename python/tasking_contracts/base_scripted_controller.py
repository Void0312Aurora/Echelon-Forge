"""Compatibility shell for the canonical Air execution base controller."""

from __future__ import annotations

from .air.execution import base_controller as _canonical
from .air.execution.base_controller import *

__all__ = _canonical.__all__
