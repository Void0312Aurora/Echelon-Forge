"""Compatibility shell for common mission vocabulary."""

from __future__ import annotations

from .common import mission_defs as _canonical
from .common.mission_defs import *

__all__ = _canonical.__all__
