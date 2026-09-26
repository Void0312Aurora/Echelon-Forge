"""Compatibility shell for common runtime bridge views."""

from __future__ import annotations

from .common import bridge_views as _canonical
from .common.bridge_views import *

__all__ = _canonical.__all__
