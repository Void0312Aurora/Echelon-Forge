from __future__ import annotations

import subprocess
from pathlib import Path

from tools.environment.arnis import bootstrap


def test_install_binary_accepts_windows_release_suffix(monkeypatch, tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    build_dir = tmp_path / "build"
    install_dir = tmp_path / "install"
    source_dir.mkdir()

    def fake_run(command, *, cwd=None, env=None, check=True):
        assert list(command[1:3]) == ["build", "--locked"]
        release = build_dir / "release"
        release.mkdir(parents=True)
        (release / "arnis.exe").write_bytes(b"windows-binary")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(bootstrap, "_run", fake_run)
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "cargo.exe")

    lock = bootstrap._load_lock()
    installed = bootstrap._install_binary(
        lock,
        source_dir=source_dir,
        build_dir=build_dir,
        install_dir=install_dir,
    )

    assert installed.name == "arnis-cmo"
    assert installed.read_bytes() == b"windows-binary"
    assert (install_dir / "installation.json").is_file()
