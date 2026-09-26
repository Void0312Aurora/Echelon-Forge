"""Compatibility shell for the common leader decision state."""

from __future__ import annotations

from .common import leader_decision_state as _canonical
from .common.leader_decision_state import *

__all__ = _canonical.__all__
