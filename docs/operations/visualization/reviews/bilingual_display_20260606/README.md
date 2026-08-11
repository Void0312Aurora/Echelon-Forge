# Bilingual Display

Status: `2026-06-06`, accepted P1 viz follow-on. P1 implements a display-only
English/Chinese language switch for the tactical-map UI.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/operations/visualization/reviews/bilingual_display_20260606/README.md`
Owner: `operations/visualization`
Last verified: `2026-08-08`

Parent owner: [Operations](../../../README.md)

P1 acceptance:
[bilingual_display_p1_acceptance_20260606.md](bilingual_display_p1_acceptance_20260606.md)

## Purpose

Add an explicit EN/ZH display layer to `examples/viz` so the same tactical map
can be inspected in either language without changing scenario, profile, terrain,
or runtime semantics.

P1 covers:

- a language toggle in the top action bar;
- static UI labels, buttons, dock titles, control help, and ARIA labels;
- dynamic workspace tabs, layer controls, run/session controls, map-only labels,
  speed text, view/camera mode text, and tactical scale text;
- environment overlay callouts for generated terrain constructs;
- C2 task/phase/history labels where the runtime emits known task tokens.

## Boundaries

This follow-on is display-only. It does not add or release:

- scenario schema changes;
- profile or object-binding semantics;
- terrain generation, terrain artifacts, or runtime setup application;
- passability, movement cost, LOS, cover, concealment, combat, reward, or
  termination behavior;
- translation of scenario file names, profile names, unit IDs, or asset IDs.

Scenario/profile/object identifiers remain stable data labels and are displayed
as emitted by the runtime.

## Validation

P1 accepted with:

- JS module syntax check;
- focused viz pytest covering the bilingual UI contract;
- browser smoke confirming the language button switches `documentElement.lang`
  and key visible controls to Chinese, then back to English;
- browser console `Errors: 0`.

See the P1 acceptance page for command output and observed browser state.
