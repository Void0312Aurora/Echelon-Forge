from __future__ import annotations

from python.runtime_bootstrap import ensure_repo_imports


def pytest_configure() -> None:
  ensure_repo_imports()
