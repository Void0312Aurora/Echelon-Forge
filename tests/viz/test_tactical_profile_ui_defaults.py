from __future__ import annotations

import json
from pathlib import Path

from examples.viz.app.profile_loader import _normalize_ui_defaults, load_viz_profile


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_viz_profile_loader_accepts_tactical_workspace_and_layer_defaults(tmp_path: Path) -> None:
    profile_path = tmp_path / "tracks_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "name": "Tracks Profile",
                "scenario": "scenarios/ground/ground_platoon_tasking_smoke_v1.json",
                "ui": {
                    "presentation_mode": "map",
                    "camera_mode": "free",
                    "focus_unit": "Blue_Lead",
                    "tactical_zoom": 1.4,
                    "tactical_workspace": "tracks",
                    "map_only": "true",
                    "tactical_layers": {
                        "environment": False,
                        "route": False,
                        "trails": True,
                        "tracks": True,
                        "sensor_rings": True,
                        "datalinks": True,
                        "weapons": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    profile = load_viz_profile(str(profile_path), roots=[str(tmp_path)])

    assert profile["ui_defaults"] == {
        "presentation_mode": "MAP",
        "camera_mode": "FREE",
        "focus_unit": "Blue_Lead",
        "tactical_workspace": "tracks",
        "map_only": True,
        "tactical_layers": {
            "environment": False,
            "route": False,
            "trails": True,
            "tracks": True,
            "sensorRings": True,
            "datalinks": True,
            "weapons": False,
        },
        "tactical_zoom": 1.4,
    }
    assert profile["summary"]["ui_defaults"] == profile["ui_defaults"]


def test_viz_profile_loader_filters_unknown_tactical_ui_defaults() -> None:
    defaults = _normalize_ui_defaults(
        {
            "presentation_mode": "dashboard",
            "camera_mode": "orbit",
            "tactical_workspace": "not-a-workspace",
            "map_only": "disabled",
            "tactical_layers": {
                "sensor-rings": "on",
                "links": "0",
                "unknown_layer": True,
                "weapons": "definitely",
            },
        }
    )

    assert defaults == {
        "map_only": False,
        "tactical_layers": {
            "sensorRings": True,
            "datalinks": False,
        }
    }


def test_viz_profile_fixtures_expose_p4_defaults_and_current_naval_action_mode() -> None:
    air_profile = load_viz_profile(
        "examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json"
    )
    naval_profile = load_viz_profile(
        "examples/viz/profiles/naval_ddg51_contact_report_debug.json"
    )
    closing_profile = load_viz_profile(
        "examples/viz/profiles/naval_ddg51_closing_contact_debug.json"
    )

    assert air_profile["ui_defaults"]["tactical_workspace"] == "cop"
    assert air_profile["ui_defaults"]["tactical_layers"]["sensorRings"] is True
    assert air_profile["ui_defaults"]["tactical_layers"]["weapons"] is True

    assert naval_profile["session_overrides"]["action_mode"] == "naval_station3"
    assert naval_profile["ui_defaults"]["tactical_workspace"] == "tracks"
    assert naval_profile["ui_defaults"]["tactical_layers"] == {
        "environment": False,
        "route": False,
        "trails": True,
        "tracks": True,
        "sensorRings": True,
        "datalinks": True,
        "weapons": False,
    }
    assert closing_profile["session_overrides"]["action_mode"] == "naval_station3"


def test_tactical_profile_ui_defaults_are_applied_without_scenario_mutation() -> None:
    text = _index_text()

    assert "const nextWorkspace = String(ui.tactical_workspace || '').trim();" in text
    assert "const hasProfileLayerDefaults = ui.tactical_layers && typeof ui.tactical_layers === 'object';" in text
    assert "const nextMapOnly = typeof ui.map_only === 'boolean' ? ui.map_only : null;" in text
    assert "mergeTacticalLayerSnapshot(workspaceLayerDefaults(baseWorkspace), ui.tactical_layers)" in text
    assert "window.setTacticalWorkspace(targetWorkspace, { skipCapture: true, layers: profileLayers });" in text
    assert "window.toggleMapOnlyMode(nextMapOnly)" in text
    assert "captureActiveWorkspaceLayers();" in text

    assert "socket.emit('viz_load_profile'" in text
    assert "socket.emit('viz_load_session'" in text
    assert "scenario.environment =" not in text
    assert "profile.ui_defaults =" not in text
