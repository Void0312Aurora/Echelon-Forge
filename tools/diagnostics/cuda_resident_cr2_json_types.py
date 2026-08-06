from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


Require = Callable[[bool, str], None]


class StrictJson:
    """Bind exact JSON scalar/container checks to an evidence error type."""

    def __init__(self, require: Require) -> None:
        self._require = require

    def object(self, value: Any, keys: set[str], label: str) -> dict[str, Any]:
        self._require(type(value) is dict, f"{label} must be an object")
        assert isinstance(value, dict)
        self._require(set(value) == keys, f"{label} keys drifted")
        return value

    def list(self, value: Any, label: str) -> list[Any]:
        self._require(type(value) is list, f"{label} must be a list")
        assert isinstance(value, list)
        return value

    def boolean(self, value: Any, label: str, expected: bool | None = None) -> bool:
        self._require(type(value) is bool, f"{label} must be a boolean")
        assert isinstance(value, bool)
        if expected is not None:
            self._require(value is expected, f"{label} must be {str(expected).lower()}")
        return value

    def integer(self, value: Any, label: str) -> int:
        self._require(type(value) is int, f"{label} must be an integer")
        assert isinstance(value, int)
        return value

    def nonnegative_integer(self, value: Any, label: str) -> int:
        result = self.integer(value, label)
        self._require(result >= 0, f"{label} must be non-negative")
        return result

    def positive_integer(self, value: Any, label: str) -> int:
        result = self.integer(value, label)
        self._require(result > 0, f"{label} must be positive")
        return result

    def exact_integer(self, value: Any, expected: int, label: str) -> int:
        result = self.integer(value, label)
        self._require(result == expected, f"{label} must equal {expected}")
        return result

    def exact_integer_list(self, value: Any, expected: Sequence[int], label: str) -> list[Any]:
        result = self.list(value, label)
        self._require(len(result) == len(expected), f"{label} shape drifted")
        for index, (actual, wanted) in enumerate(zip(result, expected, strict=True)):
            self.exact_integer(actual, wanted, f"{label}[{index}]")
        return result

    def exact_integer_map(
        self, value: Any, expected: Mapping[str, int], label: str
    ) -> dict[str, Any]:
        result = self.object(value, set(expected), label)
        for key, wanted in expected.items():
            self.exact_integer(result[key], wanted, f"{label}.{key}")
        return result

    def exact_scalar(self, value: Any, expected: Any, label: str) -> Any:
        if expected is None:
            self._require(value is None, f"{label} must be null")
        elif type(expected) is bool:
            self.boolean(value, label, expected)
        elif type(expected) is int:
            self.exact_integer(value, expected, label)
        elif type(expected) is float:
            self._require(
                type(value) is float and value == expected,
                f"{label} must be exactly float {expected}",
            )
        elif type(expected) is str:
            self._require(type(value) is str and value == expected, f"{label} drifted")
        else:
            self._require(
                type(value) is type(expected) and value == expected,
                f"{label} type or value drifted",
            )
        return value

    def exact_members(self, value: dict[str, Any], expected: Mapping[str, Any], label: str) -> None:
        for key, wanted in expected.items():
            self.exact_scalar(value[key], wanted, f"{label}.{key}")

    def exact_list(self, value: Any, expected: Sequence[Any], label: str) -> list[Any]:
        result = self.list(value, label)
        self._require(len(result) == len(expected), f"{label} shape drifted")
        for index, (actual, wanted) in enumerate(zip(result, expected, strict=True)):
            self.exact_scalar(actual, wanted, f"{label}[{index}]")
        return result
