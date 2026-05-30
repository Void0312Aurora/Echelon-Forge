# Game Frontend Integration

Status: exploratory workline opened on `2026-05-29`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

## Goal

This workline explores whether Echelon Forge can drive a playable external game
frontend while keeping the simulation backend authoritative.

The initial target is not a player-flown aircraft. The intended direction is:

- a trained Echelon policy drives the aircraft;
- Echelon owns flight, task, weapon, and damage truth;
- the external game shell provides terrain, visual assets, camera, HUD, audio,
  and immersion;
- mainline repo code remains simulation-first rather than drifting into
  frontend-first shortcuts.

## Local Workspace Boundary

The repo-root `game/` folder is a local-only sandbox and is intentionally
ignored by git.

Use it for workstation-local material such as:

- external-game integration scripts;
- temporary assets, exports, and launcher glue;
- prototype notes that are not yet ready for repo review;
- local test harnesses that should not become mainline dependencies.

Tracked, reviewable documentation belongs under `docs/task/game/`, not under
the ignored `game/` workspace.

The current maintained repo-side companions for this line are:

- [arma_proxy_backend_stub.py](../../../tools/diagnostics/arma_proxy_backend_stub.py)
  - a minimal TCP stub for the first-pass DLL bridge protocol, useful for
    bring-up before a real backend adapter is promoted.
- [arma_proxy_backend_echelon_env.py](../../../tools/diagnostics/arma_proxy_backend_echelon_env.py)
  - an env-backed TCP backend that steps authoritative flight state inside
    Echelon Forge and only uses Arma host frames as a rigid world anchor.

## Authority Model

The working assumption for this line is:

- backend authority stays in Echelon;
- external-game entities act as proxy/presentation shells;
- AI behavior comes from trained repo policies rather than external-game AI;
- any world-state mutation that matters semantically should be computed or
  admitted by the backend, not by the frontend shell.

This is a stronger requirement than a simple visualization bridge. It implies
that external-game flight logic, damage truth, mission truth, or AI truth may
need to be bypassed, replaced, or reduced to presentation-only behavior.

## First MVP

The first maintained exploration target is:

- single-player only;
- one known aircraft asset, initially an F-16;
- one known map with an available airport;
- backend-driven AI flight;
- external-game proxy aircraft synchronized from backend state;
- air-start closure first, runway-start closure second.

The first MVP should prove the following:

- a trained Echelon policy can drive the authoritative aircraft state;
- the external frontend can render that state as a stable proxy aircraft;
- the integration loop can support a useful simulation cadence locally;
- mainline simulation semantics do not need to be weakened just to satisfy the
  frontend shell.

## Current Operator Path

For the current single-aircraft MVP, the practical operator flow is:

- run the authoritative inference backend on HEI inside `~/Workshop/CMO`;
- load the trained policy plus its paired `train_config_backup.json` and
  `scenario_backup.json`;
- expose `127.0.0.1:8765` from HEI to the local workstation over SSH;
- launch Arma locally against the forwarded endpoint so the frontend stays a
  proxy shell while HEI remains the source of truth.

This keeps training and inference close to the heavier runtime environment
while leaving the local workstation responsible for the game client only.

## Non-Goals

- Do not treat the external game shell as the source of truth.
- Do not merge local-only assets or launcher glue into `main` by default.
- Do not open with multiplayer, netcode, or distributed authority.
- Do not contort backend semantics around frontend convenience shortcuts.
- Do not assume runway, ground-roll, taxi, or landing semantics are "free"
  just because the frontend map already contains an airport.

## Promotion Rules

The default policy is:

- local gameplay/frontend glue, temporary assets, build output, and launcher
  scripts live in the ignored `game/` workspace;
- tracked backend, runtime, contract, or documentation changes may be committed
  on the mainline when the integration reveals real coupling that should not be
  duplicated or hidden behind a long-lived side branch;
- only the local-only shell stays quarantined in `game/`;
- any promoted backend changes should remain useful even if the external-game
  experiment is later abandoned.

A dedicated game branch is optional, not required. The priority is to keep
local-only frontend scaffolding out of the maintained repo surface while still
allowing legitimate cross-cutting simulation changes to land normally.
