"""Compatibility shell for common runtime contracts."""

from __future__ import annotations

from .common import runtime_contract as _canonical
from .common.runtime_contract import *

__all__ = _canonical.__all__
