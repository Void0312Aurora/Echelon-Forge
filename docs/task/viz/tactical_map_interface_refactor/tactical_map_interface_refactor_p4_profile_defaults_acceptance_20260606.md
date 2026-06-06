# Tactical Map Interface Refactor P4 Profile Defaults Acceptance

Status: `2026-06-06` `VIZ-TMAP-P4` accepted slice. Historical slice note: the
overall tactical-map interface refactor remained active at this checkpoint;
`P5` validation roll-up and `P6` closure/archive sync were not accepted by this
note. Current overall status is superseded by
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).

Parent: [Tactical Map Interface Refactor](README.md)

Chinese companion:
[tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md)

## Decision

`VIZ-TMAP-P4` is accepted as a profile UI-defaults slice.

The accepted implementation extends profile `ui` defaults with:

- `tactical_workspace`: normalized to `cop`, `environment`, `tracks`, or
  `inspect3d`.
- `tactical_layers`: a partial or full layer map normalized to the front-end
  layer keys `environment`, `route`, `trails`, `tracks`, `sensorRings`,
  `datalinks`, and `weapons`.

The loader filters unknown workspaces, unknown layers, and non-boolean layer
values. The browser applies profile layer defaults as UI state over the selected
workspace defaults; it does not mutate scenario JSON, simulation payload
semantics, or environment runtime state.

## Evidence

Code, JSON, and regression checks:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py
python -m json.tool examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_contact_report_debug.json >/dev/null
```

Observed result: module syntax check passed; focused viz tests reported
`12 passed`; edited profile JSON files parsed cleanly.

Browser smoke used the local viz server on `http://127.0.0.1:5064`:

- Loaded `examples/viz/profiles/naval_ddg51_contact_report_debug.json` from the
  profile selector.
- The profile loaded
  `scenarios/naval/ddg51_take1_screen_contact_report_v1.json` and reached
  `READY`.
- The session initialized with `action_mode=naval_station3`, matching the
  current maintained naval action surface.
- The profile applied `tactical_workspace=tracks`; the top bar and right-dock
  workspace read `TRACKS`.
- The profile layer defaults pressed `TRAIL`, `TRACK`, `RING`, and `LINK`,
  while `ENV`, `ROUTE`, and `WEPN` remained off.
- Browser console reported `Errors: 0`; warnings were WebGL `ReadPixels`
  performance messages only.
- Screenshot: `output/playwright/tactical_map_p4_profile_defaults_20260606.png`.

Server shutdown after the smoke run emitted existing nanobind leak warnings.
Those warnings occur after browser evidence is collected and are not attributed
to the profile UI-defaults contract.

## Accepted Boundaries

- No scenario schema changes.
- No simulation payload semantic changes.
- No terrain-aware movement, passability, LOS, cover, concealment, sensing,
  fires, damage, reward, termination, scenario editor, terrain generator UI, or
  environment-runtime mutation is accepted here.
- No MIL-STD-2525, APP-6, or other military-symbol standard compliance is
  claimed.
- Updating naval viz profiles to `action_mode=naval_station3` only aligns them
  with the already-maintained naval tasking action surface; it does not claim a
  new naval behavior release.

## Residuals

- `VIZ-TMAP-P5` should roll up validation evidence and residuals across `P1`
  through `P4`.
- `VIZ-TMAP-P6` should sync closure/archive pointers after the acceptance
  decision.
- Future profile defaults may include more environment layer entries only after
  those environment products are accepted by their owning substrate worklines.
