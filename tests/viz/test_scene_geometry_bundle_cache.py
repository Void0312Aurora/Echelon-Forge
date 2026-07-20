"""Scene geometry cache is keyed by bundle identity.

Switching profiles (bundle A -> B) must refetch instead of keeping A's
terrain forever, and stale in-flight responses must never install after a
clear or a newer request (generation guard).
"""

from __future__ import annotations

from frontend_sources import js_text


def test_frontend_keys_scene_geometry_by_bundle() -> None:
    scene_geometry = js_text("scene-geometry")
    assert "loadedBundleKey" in scene_geometry
    assert "fetchGeneration" in scene_geometry
    # The old any-payload-blocks-refetch guard must be gone.
    assert "loadingPromise" not in scene_geometry
    # Generation guard applies after every await point.
    assert scene_geometry.count("generation !== fetchGeneration") >= 3


def test_clear_invalidates_inflight_fetches() -> None:
    scene_geometry = js_text("scene-geometry")
    clear_body = scene_geometry.split("export function clearSceneGeometry()")[1].split(
        "export function"
    )[0]
    assert "fetchGeneration += 1" in clear_body
    assert "loadedBundleKey = null" in clear_body


def test_session_passes_bundle_identity_not_boolean() -> None:
    session = js_text("session")
    assert "bundle_id" in session
    assert "ensureSceneGeometry(!!" not in session
