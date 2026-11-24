from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


PATCH = Path(__file__).resolve().parents[3] / "cmake/patches/flecs_exact_json_precision.cmake"
ORIGINAL = """flecs_strbuf_ftoa(b, flt, 10, nan_delim);
const char *result = flecs_parse_digit(json, token);
if (!strchr(token, '.')) {
}
void ecs_reset_clock(
    ecs_world_t *world)
{
    world->info.world_time_total = 0;
    world->info.world_time_total_raw = 0;
}
"""


def _apply(source: Path) -> subprocess.CompletedProcess[str]:
    cmake = shutil.which("cmake")
    if cmake is None:
        pytest.skip("CMake is required to exercise the dependency patch")
    return subprocess.run(
        [cmake, f"-DFLECS_SOURCE_FILE={source.as_posix()}", "-P", str(PATCH)],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_precision_patch_can_be_applied_repeatedly(tmp_path: Path) -> None:
    source = tmp_path / "flecs.c"
    source.write_text(ORIGINAL, encoding="utf-8")
    first = _apply(source)
    assert first.returncode == 0, first.stderr
    patched = source.read_bytes()
    assert patched.count(b"void ef_flecs_restore_clock(") == 1
    second = _apply(source)
    assert second.returncode == 0, second.stderr
    assert source.read_bytes() == patched


@pytest.mark.parametrize("mode", ["missing", "duplicate_original", "duplicate_patched"])
def test_precision_patch_rejects_drift_without_writing(tmp_path: Path, mode: str) -> None:
    source = tmp_path / "flecs.c"
    contents = ORIGINAL
    if mode == "missing":
        contents = contents.replace("void ecs_reset_clock(", "void renamed_reset_clock(")
    elif mode == "duplicate_original":
        contents += ORIGINAL
    else:
        source.write_text(contents, encoding="utf-8")
        assert _apply(source).returncode == 0
        contents = source.read_text(encoding="utf-8") * 2
    source.write_text(contents, encoding="utf-8")
    before = source.read_bytes()
    result = _apply(source)
    assert result.returncode != 0
    assert "requires exactly one pinned" in result.stderr
    assert source.read_bytes() == before
