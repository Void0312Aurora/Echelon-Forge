"""Compatibility shell for the common scripted runtime."""

from __future__ import annotations

from .common import scripted_runtime as _canonical
from .common.scripted_runtime import *

__all__ = _canonical.__all__
