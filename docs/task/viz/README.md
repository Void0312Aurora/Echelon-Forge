# Viz

Status: unified-entry refactor workline remains active; local entry converged on
`2026-05-18`; the tactical-map interface refactor closed on `2026-06-06`.

## Current Status

- The original large design/freeze document is still the primary active record,
  explicitly promoted by this README despite living under `archive/`.
- The plan already records first usable closure for the unified entry workflow,
  especially `WP-V4` asset registry and `WP-V5` in-app loader/session flow.
- The follow-on default is no longer "design the architecture again", but
  extending registry coverage and cleaning up runtime exit/session noise on top
  of the landed structure.
- The tactical-map interface refactor is now a closed first slice: map-first
  shell, tabbed workspaces, grouped tactical layers, profile UI defaults, and
  validation/closure evidence are accepted within their documented boundaries.

## Recommended Reading Order

- Active plan and current implementation boundary:
  [viz_unified_entry_session_profile_plan_20260516.md](./archive/viz_unified_entry_session_profile_plan_20260516.md)
- Tactical map interface refactor:
  [tactical_map_interface_refactor/README.md](./tactical_map_interface_refactor/README.md)

## Current Follow-On Focus

- treat the closed tactical map interface refactor as the current map-first UI
  baseline on top of the unified-entry/profile/session foundation
- extend asset-registry coverage for more verified naval/air assets
- clean up runtime exit and repeated session debug flow noise
- keep visualization convenience separate from realism/world-parameter changes
- open a new task cluster or subproject before adding richer environment
  layers, split-map layout, or symbol-registry extraction
- do not treat other files under `archive/` as active unless this README
  promotes them

The earlier large freeze/design snapshot now lives under
[archive/README.md](./archive/README.md).
