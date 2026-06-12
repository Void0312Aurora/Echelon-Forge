# Arma Game Workspace Docs

This folder now documents the active Arma proxy integration under `game/`.

Current tracked entrypoints:

- `../mod/@EchelonProxy/`: Arma mod shell
- `../bridge/`: DLL bridge project
- `../scripts/build_bridge.ps1`: local bridge build helper
- `../scripts/launch_arma_proxy.ps1`: Arma bring-up helper
- `echelon_proxy_backend_sync_v1.md`: backend sync contract

On `2026-05-30`, the locally mixed Godot/WebSocket playable-shell materials were
archived to the local-only ignored path
`archive/20260530_game_godot_local_archive/` so `game/` stays aligned with the
active Arma workflow.

## Bring-Up Order

1. Build the DLL bridge:
   - `powershell -File game/scripts/build_bridge.ps1`
2. Start the local stub and launch Arma:
   - `powershell -File game/scripts/launch_arma_proxy.ps1 -Mode StubAndArma -ShowScriptErrors`
3. In Arma, enter a local single-player mission or Eden session so the mod
   postInit hook can start the session pump.

Useful launcher modes:

- `-Mode StubOnly`
  - start only the local backend stub and wait for Arma-side manual bring-up
- `-Mode ArmaOnly -ReuseExistingBackend`
  - launch Arma against an already-running stub

Notes:

- The local mod is still unpacked, so the launcher enables `-filePatching`.
- The backend metadata is written to `game/runtime/last_backend.json`.
- Stub logs are written under `game/logs/`.
- The launcher no longer starts a repo-side `UniversalEnv` backend. Use
  `ArmaOnly` plus `-ReuseExistingBackend` when connecting Arma to an external
  authoritative backend.
