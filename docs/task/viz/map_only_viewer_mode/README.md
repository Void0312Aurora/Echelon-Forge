# Map-Only Viewer Mode And Profile Binding Follow-On

Status: `2026-06-06` active viz follow-on. `P1` implements a UI-only map-only
viewer mode; profile/object binding remains held for a later design slice.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent viz entry: [../README.md](../README.md)
- Archived tactical-map interface baseline:
  [../archive/tactical_map_interface_refactor/README.md](../archive/tactical_map_interface_refactor/README.md)
- Current frontend shell:
  [index.html](../../../../examples/viz/web_viz/templates/index.html)
- Current profile loader:
  [profile_loader.py](../../../../examples/viz/app/profile_loader.py)
- Accepted P1 evidence:
  [map_only_viewer_mode_p1_acceptance_20260606.md](map_only_viewer_mode_p1_acceptance_20260606.md)

## Purpose

This follow-on adds a direct "map only" viewing mode for `examples/viz` so a
user can inspect the tactical map without the setup dock, data dock, top
workspace/action bar, or bottom help overlay competing for attention.

The change is deliberately UI-only. It does not change scenario schema,
profile/session ownership, environment data, tactical payload semantics, or
runtime behavior.

## Current Slice

Accepted implementation for `P1`:

- Add an explicit `MAP ONLY` entry point in the existing top action bar.
- Hide all chrome in map-only mode while preserving the tactical canvas,
  map scale, and a small `EXIT MAP` control.
- Let `Escape` exit map-only mode.
- Let profile `ui.map_only` choose the default viewer posture as a UI
  preference only.
- If map-only is requested while the `3D Inspect` workspace is active, return
  to the last map workspace instead of presenting a blank map-only state.

Acceptance evidence is retained in
[map_only_viewer_mode_p1_acceptance_20260606.md](map_only_viewer_mode_p1_acceptance_20260606.md).

## Held Follow-On

Profile/object binding is not implemented here. A later slice should replace
hardcoded service/domain assumptions in visualization profiles with object
binding rules, for example:

- bind focus and layer defaults to scenario object IDs, object tags, or asset
  registry capabilities;
- keep service labels such as air/naval/ground as metadata, not control-flow
  branches inside profiles;
- preserve the `profile` versus `scenario` boundary: profiles choose viewing
  posture and object bindings, while scenarios own world/content semantics.

## Validation

Accepted validation for `P1`:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_tactical_map_only_mode.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

Browser smoke verified that `MAP ONLY` hides chrome, keeps the map canvas
interactive, and exits through both `EXIT MAP` and `Escape`; see
[map_only_viewer_mode_p1_acceptance_20260606.md](map_only_viewer_mode_p1_acceptance_20260606.md).

## Non-Claims

This follow-on does not release:

- terrain generation or generated scenario artifacts;
- runtime setup application;
- movement, LOS, cover, sensing, fires, damage, combat, reward, or termination
  behavior;
- profile object-binding semantics beyond the explicit held design note above.
