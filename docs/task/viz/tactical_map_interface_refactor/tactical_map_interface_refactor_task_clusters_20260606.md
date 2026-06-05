# Tactical Map Interface Refactor Task Clusters

Status: `2026-06-06` finite task-cluster plan for
[Tactical Map Interface Refactor](README.md). `P0` is pass; implementation
clusters remain planned.

## Boundary Decision

This subproject may change `examples/viz` interface structure, tactical-map
layer presentation, map-workspace defaults, focused profile UI defaults, and
the documentation needed to validate those changes. It must not change scenario
truth, environment-runtime behavior, terrain movement, sensing, fires, damage,
reward, termination, or claim compliance with military symbology standards.

The tactical map may become a workspace with multiple surfaces. Those surfaces
are UI views over accepted payloads; they are not new simulation semantics.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `VIZ-TMAP-P0` | main thread | n/a | Install durable subproject authority, task clusters, current status, and style baseline. | `docs/task/viz/tactical_map_interface_refactor/**`, `docs/task/viz/README*.md` | Runtime UI implementation; scenario/profile schema changes. | `git diff --check -- docs/task/viz`; local link/path inspection. | Parent README links the subproject and docs-only validation is clean. | First, serial. | 1 | pass |
| `VIZ-TMAP-P1` | main thread or implementation worker | n/a | Rework the current tactical UI into a map-first shell with docked/collapsible controls. | `examples/viz/web_viz/templates/index.html`; optional screenshots under a dated evidence path | Multi-map semantics; profile schema changes; terrain or combat behavior. | Embedded module syntax check; browser smoke at narrow and desktop viewports; console error check. | Tactical map is visible as the primary first-viewport surface and controls no longer push it below useful view. | Depends on `P0`; serial with `P2` if touching the same template sections. | 2 | planned |
| `VIZ-TMAP-P2` | main thread or implementation worker | n/a | Add a maintained map-workspace model with named surfaces such as `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect`. | `examples/viz/web_viz/templates/index.html`; optional profile fixture only if needed for defaults | Scenario editor; runtime terrain generation; new simulation payload requirements. | Browser smoke proves map surface switching or split behavior; existing profile loading still works. | Each accepted surface has a clear role, default layer set, and no overlap that hides the map. | Depends on `P1`; can share read-only design review with `P3`. | 2 | planned |
| `VIZ-TMAP-P3` | implementation worker or integration worker | n/a | Centralize tactical layer groups, draw order, and first-pass symbology styling. | `examples/viz/web_viz/templates/index.html`; optional small JS/CSS extraction if locally justified | Full MIL-STD-2525/APP-6 compliance; changing tactical payload semantics. | Module syntax check; browser screenshot checks for unit, route, track, sensor, weapon, and ENV layers. | Existing overlays render through grouped layer controls with readable affiliation, uncertainty, and environment styling. | Depends on `P1`; can follow `P2` or land after it if write areas overlap. | 2 | planned |
| `VIZ-TMAP-P4` | integration worker | n/a | Extend profile UI defaults only as needed for default workspace/layer/view selection. | `examples/viz/app/profile_loader.py`, `examples/viz/profiles/*.json`, focused tests under `tests/viz` | Scenario schema changes; training config changes; world/realism parameters. | Focused profile-loader tests plus existing viz smoke load. | Profiles can select default UI workspace/layers while scenarios remain unchanged. | Depends on accepted `P2` or `P3` defaults. | 2 | planned |
| `VIZ-TMAP-P5` | main thread | n/a | Record validation evidence, screenshots, residuals, and capability boundaries. | New dated acceptance/evidence docs under this subproject; optional screenshot artifacts if the repo keeps them | New feature work; archive moves before acceptance. | Commands from `P1`-`P4`; Playwright or browser smoke evidence; `git diff --check` on touched docs/code. | Evidence is sufficient to decide accepted, partial, or held without relying on chat history. | Depends on implementation clusters. Serial. | 1 | planned |
| `VIZ-TMAP-P6` | main thread | n/a | Sync parent README, current status, and archive pointers after acceptance decision. | `docs/task/viz/README*.md`, this subproject README/status/archive files | Reopening accepted implementation without a new cluster; deleting historical records. | Link/path inspection; `git diff --check -- docs/task/viz`. | Current authority and archive boundaries agree after the acceptance decision. | Depends on `P5`. Serial. | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not create new conversation threads or sessions for this subproject.
- Subagents are optional; if used, they must follow
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
  and return the worker packet format below.
- Do not allow two workers to edit the same `index.html` layout block, profile
  loader contract, public status line, or acceptance table concurrently.
- Keep `P5` and `P6` serial in the main thread.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  wave.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Docs-only `P0`:

```bash
git diff --check -- docs/task/viz
```

Implementation clusters:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py
```

Browser smoke must cover at least:

- narrow viewport near `780x493`;
- desktop viewport near `1440x900`;
- one naval or air profile that exercises tracks/sensors/weapons;
- one ground scenario/profile path that exercises `ENV` overlay visibility.

## Acceptance Criteria

- The first accepted implementation keeps the map as the primary view and fixes
  the "map pushed below controls" failure mode.
- The map-workspace model is explicit even if only a first subset lands.
- Layer controls are grouped by purpose and remain usable on narrow and desktop
  viewports.
- Profile defaults, if added, are UI/runtime preferences and do not mutate
  scenario world semantics.
- No new simulation behavior is claimed without code and tests outside this
  visualization subproject.

## Residual Map

Immediate:

- `P1` shell layout implementation.
- Decision between tabbed map surfaces and split-map layout for the first
  runtime slice.

Follow-on:

- Richer environment layers once roads, buildings, vegetation, weather, or other
  derived products are accepted by their owning substrate worklines.
- Optional tactical symbol registry if grouped layer drawing proves too large
  for the current template.

Deferred:

- Standard-compliant military symbology.
- Scenario editor, terrain generator UI, and runtime environment behavior.
