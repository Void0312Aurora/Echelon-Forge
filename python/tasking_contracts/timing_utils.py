"""Compatibility shell for common timing helpers."""

from __future__ import annotations

from .common import timing_utils as _canonical
from .common.timing_utils import *

__all__ = _canonical.__all__
