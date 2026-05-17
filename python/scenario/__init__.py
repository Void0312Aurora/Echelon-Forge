from __future__ import annotations

__all__ = [
    "CompiledScenario",
    "ScenarioCompiler",
]


def __getattr__(name: str):
    if name in __all__:
        from .compiler import CompiledScenario, ScenarioCompiler

        exports = {
            "CompiledScenario": CompiledScenario,
            "ScenarioCompiler": ScenarioCompiler,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
