"""Scene geometry cache is keyed by a backend-computed identity.

Switching profiles (bundle A -> B) must refetch instead of keeping A's
terrain forever, stale in-flight responses must never install after a clear
or a newer request (generation guard), and the cache key comes from the
backend (load generation + digest), never from the bundle's self-declared
id, which is unvalidated and could be empty or collide.
"""

from __future__ import annotations

from pathlib import Path

from frontend_sources import js_text

REPO_ROOT = Path(__file__).resolve().parents[2]
SESSION_MANAGER_SRC = (
    REPO_ROOT / "examples" / "viz" / "app" / "session_manager.py"
).read_text(encoding="utf-8")


def test_frontend_keys_scene_geometry_by_backend_cache_key() -> None:
    scene_geometry = js_text("scene-geometry")
    assert "loadedBundleKey" in scene_geometry
    assert "fetchGeneration" in scene_geometry
    # The old any-payload-blocks-refetch guard must be gone.
    assert "loadingPromise" not in scene_geometry
    # Generation guard applies after every await point.
    assert scene_geometry.count("generation !== fetchGeneration") >= 3


def test_terrain_bitmap_commits_only_after_generation_check() -> None:
    # buildTerrainBitmap builds into locals; global bitmap/rect state is
    # committed via commitTerrainBitmap only after re-checking the fetch
    # generation, so a clear during createImageBitmap cannot resurrect
    # stale terrain.
    scene_geometry = js_text("scene-geometry")
    assert "function commitTerrainBitmap" in scene_geometry
    build_body = scene_geometry.split("async function buildTerrainBitmap()")[1].split(
        "function commitTerrainBitmap"
    )[0]
    assert "terrainBitmap =" not in build_body, "builder must not write globals"
    assert "terrainRect =" not in build_body, "builder must not write globals"
    # Every commit call site is preceded by a generation check.
    assert scene_geometry.count("commitTerrainBitmap(built);") == 2
    for segment in scene_geometry.split("commitTerrainBitmap(built);")[:-1]:
        assert "generation !== fetchGeneration" in segment


def test_clear_invalidates_inflight_fetches() -> None:
    scene_geometry = js_text("scene-geometry")
    clear_body = scene_geometry.split("export function clearSceneGeometry()")[1].split(
        "export function"
    )[0]
    assert "fetchGeneration += 1" in clear_body
    assert "loadedBundleKey = null" in clear_body


def test_session_uses_backend_cache_key_not_declared_id() -> None:
    session = js_text("session")
    assert "sceneGeo.cache_key" in session
    assert "ensureSceneGeometry(!!" not in session
    assert "'unidentified-bundle'" not in session


def test_backend_cache_key_is_generation_scoped() -> None:
    assert "_scene_geometry_generation" in SESSION_MANAGER_SRC
    assert '"cache_key"' in SESSION_MANAGER_SRC
    # Generation bumps on every profile (re)load so even identical declared
    # ids produce distinct keys.
    assert "self._scene_geometry_generation += 1" in SESSION_MANAGER_SRC
