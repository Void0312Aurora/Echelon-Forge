from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.environment.arnis.cli import (
    ArnisCliError,
    _phase1_export_command,
    _verify_bundle,
    _verify_checksums,
)
from tools.environment.arnis.bootstrap import ArnisBootstrapError, _ensure_command_link


_FIXTURE_ROOT = (
    Path(__file__).parents[1]
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "chicago_river_phase1"
)


def test_phase1_request_builds_frozen_export_command(tmp_path: Path) -> None:
    command = _phase1_export_command(
        _FIXTURE_ROOT / "request.json",
        tmp_path / "output",
        Path("/opt/arnis-cmo"),
    )

    assert command[0] == "/opt/arnis-cmo"
    assert "--file" in command
    assert "--terrain" in command
    assert "--projection" in command
    assert "web_mercator" in command
    assert "--overture=false" in command
    assert command[command.index("--cmo-require-elevation-provider") + 1] == "usgs_3dep"
    patch_sha = command[command.index("--cmo-exporter-patch-sha256") + 1]
    assert patch_sha == "26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee"


def test_verify_bundle_reports_retained_continuous_identity() -> None:
    result = _verify_bundle(_FIXTURE_ROOT / "expected")

    assert result["valid"] is True
    assert result["object_count"] == 511
    assert result["bundle_digest_sha256"] == (
        "524064a993f83bd1c25c6b5b039ba2ee5c11fd5fae3a9a3cb9a8d617a609571d"
    )


def test_phase1_request_rejects_changed_osm_input(tmp_path: Path) -> None:
    request = json.loads((_FIXTURE_ROOT / "request.json").read_text(encoding="utf-8"))
    changed_input = tmp_path / "changed.json"
    changed_input.write_text("{}\n", encoding="utf-8")
    request["source_input"]["path"] = changed_input.name
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    with pytest.raises(ArnisCliError, match="frozen OSM input"):
        _phase1_export_command(
            request_path,
            tmp_path / "output",
            Path("/opt/arnis-cmo"),
        )


def test_checksum_verifier_rejects_path_escape(tmp_path: Path) -> None:
    (tmp_path / "checksums.sha256").write_text(
        f"{'0' * 64}  ../escape\n",
        encoding="utf-8",
    )

    with pytest.raises(ArnisCliError, match="unsafe checksum path"):
        _verify_checksums(tmp_path)


def test_prepare_safely_migrates_managed_arnis_command_link(tmp_path: Path) -> None:
    managed_root = tmp_path / "opt" / "arnis-cmo"
    old_install = managed_root / "v3.0.0-cmo1"
    new_install = managed_root / "v3.0.0-cmo5"
    old_install.mkdir(parents=True)
    new_install.mkdir(parents=True)
    old_binary = old_install / "arnis-cmo"
    new_binary = new_install / "arnis-cmo"
    old_binary.write_bytes(b"old")
    new_binary.write_bytes(b"new")
    (old_install / "installation.json").write_text(
        json.dumps(
            {
                "install_id": "v3.0.0-cmo1",
                "patch_sha256": "1" * 64,
                "source_revision": "2" * 40,
            }
        ),
        encoding="utf-8",
    )
    command_link = tmp_path / "bin" / "arnis-cmo"
    command_link.parent.mkdir()
    command_link.symlink_to(old_binary)

    _ensure_command_link(new_binary, command_link)

    assert command_link.resolve() == new_binary.resolve()


def test_prepare_refuses_unmanaged_arnis_command_link(tmp_path: Path) -> None:
    managed_root = tmp_path / "opt" / "arnis-cmo"
    new_install = managed_root / "v3.0.0-cmo5"
    new_install.mkdir(parents=True)
    new_binary = new_install / "arnis-cmo"
    new_binary.write_bytes(b"new")
    unrelated = tmp_path / "other" / "arnis-cmo"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"other")
    command_link = tmp_path / "bin" / "arnis-cmo"
    command_link.parent.mkdir()
    command_link.symlink_to(unrelated)

    with pytest.raises(ArnisBootstrapError, match="unrelated symlink"):
        _ensure_command_link(new_binary, command_link)
