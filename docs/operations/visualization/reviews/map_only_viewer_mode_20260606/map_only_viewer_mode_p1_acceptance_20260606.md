# Map-Only Viewer Mode P1 Acceptance

Status: `2026-06-06` `VIZ-MAPONLY-P1` accepted as a UI-only viewer slice.
The parent follow-on remains active for later profile/object-binding design.

Parent: [Map-Only Viewer Mode And Profile Binding Follow-On](README.md)

Chinese companion:
[map_only_viewer_mode_p1_acceptance_20260606.zh.md](map_only_viewer_mode_p1_acceptance_20260606.zh.md)

## Decision

`VIZ-MAPONLY-P1` is accepted for the tactical map viewer.

The accepted implementation:

- adds an explicit `MAP ONLY` action to the existing viz top bar;
- hides the top bar, setup dock, data dock, and help overlay while preserving
  the tactical canvas;
- keeps a small `EXIT MAP` control visible in map-only mode;
- lets `Escape` exit map-only mode;
- lets profile `ui.map_only` set the initial viewer posture as a UI preference;
- returns from `3D Inspect` to the last tactical map workspace before entering
  map-only mode.

The change is a visualization posture change only. It does not change scenario
content, runtime action semantics, simulation payloads, or profile ownership of
world state.

## Evidence

Code and regression checks:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_tactical_map_only_mode.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

Observed result: module syntax check passed; focused viz tests reported
`12 passed`; diff whitespace check passed.

Browser smoke used the local viz server with
`scenarios/ground/ground_platoon_tasking_smoke_v1.json`:

- Initial page reached `READY`.
- Clicking `MAP ONLY` set `document.documentElement.dataset.mapOnly` to
  `true` and `layoutMode` to `map-only`.
- The menubar, left dock, right dock, and help overlay were hidden; the
  `EXIT MAP` control remained visible.
- The tactical canvas remained visible at about `780x493`.
- Pressing `Space` continued to drive the session and the map rendered
  non-background pixels.
- Clicking `EXIT MAP` restored the normal shell.
- Re-entering map-only mode and pressing `Escape` also restored the normal
  shell.
- Browser console reported `Errors: 0`.
- Screenshot: `output/playwright/tactical_map_only_mode_20260606.png`.

Final re-smoke after doc/test cleanup used `http://127.0.0.1:5066` and
confirmed:

- `mapOnly=true`, `layoutMode=map-only`, `leftDock=closed`, and
  `rightDock=closed` after clicking `MAP ONLY`;
- menubar, left dock, right dock, and help overlay computed `display: none`;
- `EXIT MAP` computed `display: block`;
- tactical canvas measured `1280x720`;
- pressing `Escape` restored `mapOnly=false`, menubar `display: flex`, and
  `EXIT MAP` `display: none`;
- browser console reported `Errors: 0`.

During the smoke run, the scenario continued to use the existing ground
compatibility shell and emitted repeated aircraft-style `failfast_extreme_pitch`
episodes after the session started. That is recorded as existing scenario/runtime
behavior and is not attributed to this UI-only viewer slice.

## Accepted Boundaries

- No scenario schema changes.
- No simulation runtime behavior changes.
- No terrain generation or generated map artifact is accepted here.
- No movement, LOS, cover, sensing, fires, damage, reward, or termination
  behavior is accepted here.
- No profile object-binding semantics are accepted here beyond normalizing and
  applying `ui.map_only` as a boolean UI default.
- No service/domain hardcoding removal is accepted here.

## Residuals

- Design profile/object binding as a later slice before replacing hardcoded
  service/domain assumptions in viz profiles.
- Consider a richer map-only toolbar only after the object-binding and
  multi-map requirements are clearer.
