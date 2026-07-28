from __future__ import annotations

from python.scenario import compiler as _compiler


_SCENARIO_COMPILER_ALL = _compiler.__all__
__all__ = list(_SCENARIO_COMPILER_ALL)

globals().update({name: getattr(_compiler, name) for name in __all__})
