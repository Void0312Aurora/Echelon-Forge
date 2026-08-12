"""Process-level memo behind ``configure_repo_imports``.

The bootstrap used to reglob the build tree and walk ``PATH`` for the MinGW
runtime on every call (~0.25s each), and a single pytest process calls it dozens
of times: ``tests/conftest.py`` once, plus a module-level ``ensure_repo_imports()``
in most runtime test modules. The scan is memoized now, so these tests pin the
parts that must not be memoized with it: the fail-closed checks, a changed
``CMO_BUILD_DIR``, and the ``sys.path`` ordering every caller relies on.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from python import runtime_bootstrap


@pytest.fixture(autouse=True)
def _isolated_bootstrap_state():
    """Keep the memo and ``sys.path`` edits from leaking into the session."""
    saved_path = list(sys.path)
    runtime_bootstrap._reset_import_plan_cache()
    try:
        yield
    finally:
        runtime_bootstrap._reset_import_plan_cache()
        sys.path[:] = saved_path


def _fake_build(tmp_path: Path, name: str) -> Path:
    build = tmp_path / name
    build.mkdir()
    (build / "ef_py.so").write_bytes(b"")
    return build


def _count_scans(monkeypatch: pytest.MonkeyPatch) -> list[str | None]:
    """Record every build-tree scan and neutralize the Windows DLL PATH walk."""
    scans: list[str | None] = []
    original = runtime_bootstrap.build_dirs

    def counted(root: str | None = None) -> list[str]:
        scans.append(root)
        return original(root)

    monkeypatch.setattr(runtime_bootstrap, "build_dirs", counted)
    monkeypatch.setattr(runtime_bootstrap, "_iter_windows_dll_dirs", lambda build: ())
    return scans


def test_repeated_calls_with_the_same_inputs_scan_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build = _fake_build(tmp_path, "build-memo")
    monkeypatch.setenv("CMO_BUILD_DIR", str(build))
    scans = _count_scans(monkeypatch)

    first = runtime_bootstrap.configure_repo_imports()
    second = runtime_bootstrap.configure_repo_imports()
    third = runtime_bootstrap.ensure_repo_imports()

    assert first == second == third == runtime_bootstrap.repo_root()
    assert len(scans) == 1, f"expected one scan, got {len(scans)}"


def test_the_pin_written_back_by_the_first_call_does_not_force_a_second_scan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The first call rewrites CMO_BUILD_DIR to the normalized build it selected;
    # keying on the raw string would make every second call miss.
    build = _fake_build(tmp_path, "build-pin")
    monkeypatch.setenv("CMO_BUILD_DIR", str(build).replace(os.sep, "/"))
    scans = _count_scans(monkeypatch)

    runtime_bootstrap.configure_repo_imports()
    assert os.environ["CMO_BUILD_DIR"] == str(build)
    runtime_bootstrap.configure_repo_imports()

    assert len(scans) == 1, f"expected one scan, got {len(scans)}"


def test_a_changed_build_dir_is_never_served_from_the_memo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first_build = _fake_build(tmp_path, "build-one")
    second_build = _fake_build(tmp_path, "build-two")
    scans = _count_scans(monkeypatch)

    monkeypatch.setenv("CMO_BUILD_DIR", str(first_build))
    runtime_bootstrap.configure_repo_imports()
    assert sys.path[0] == str(first_build)

    monkeypatch.setenv("CMO_BUILD_DIR", str(second_build))
    runtime_bootstrap.configure_repo_imports()

    assert sys.path[0] == str(second_build)
    assert len(scans) == 2, f"expected a rescan per build dir, got {len(scans)}"


def test_explicit_build_dir_without_an_artifact_fails_closed_on_every_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    good_build = _fake_build(tmp_path, "build-good")
    empty_build = tmp_path / "build-empty"
    empty_build.mkdir()
    _count_scans(monkeypatch)

    monkeypatch.setenv("CMO_BUILD_DIR", str(good_build))
    runtime_bootstrap.configure_repo_imports()

    monkeypatch.setenv("CMO_BUILD_DIR", str(empty_build))
    for _ in range(2):
        with pytest.raises(RuntimeError, match="does not contain an ef_py artifact"):
            runtime_bootstrap.configure_repo_imports()


def test_require_local_fails_closed_on_every_call_without_a_local_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CMO_BUILD_DIR", raising=False)
    monkeypatch.setattr(runtime_bootstrap, "build_dirs", lambda root=None: [])

    for _ in range(2):
        with pytest.raises(RuntimeError, match="refusing to fall back"):
            runtime_bootstrap.ensure_repo_imports()

    # The same empty result stays valid for installed-wheel callers.
    assert runtime_bootstrap.configure_repo_imports() == runtime_bootstrap.repo_root()


def test_a_memoized_call_still_reapplies_the_sys_path_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build = _fake_build(tmp_path, "build-syspath")
    monkeypatch.setenv("CMO_BUILD_DIR", str(build))
    _count_scans(monkeypatch)
    root = runtime_bootstrap.configure_repo_imports()

    sys.path.remove(str(build))
    sys.path.remove(root)
    sys.path.append(root)

    runtime_bootstrap.configure_repo_imports()

    assert sys.path[:2] == [str(build), root]


def test_the_reset_hook_forces_a_fresh_scan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build = _fake_build(tmp_path, "build-reset")
    monkeypatch.setenv("CMO_BUILD_DIR", str(build))
    scans = _count_scans(monkeypatch)

    runtime_bootstrap.configure_repo_imports()
    runtime_bootstrap._reset_import_plan_cache()
    runtime_bootstrap.configure_repo_imports()

    assert len(scans) == 2, f"expected the reset hook to drop the memo, got {len(scans)}"
