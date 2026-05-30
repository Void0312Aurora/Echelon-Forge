# Local Game Workspace

This folder is a local-only sandbox for gameplay/frontend experiments.

It is intentionally ignored by git. Keep branch-local launchers, scratch notes,
temporary exports, and integration glue here unless and until they are ready to
be promoted into tracked repo documentation or reusable code.

Current local entrypoints:

- `mod/@EchelonProxy/`: first-pass local Arma mod shell
- `bridge/`: Windows DLL extension project
- `scripts/build_bridge.ps1`: local build helper
- `scripts/launch_arma_proxy.ps1`: local launcher helper
- `docs/echelon_proxy_backend_sync_v1.md`: first-pass state-sync protocol

## Current Bring-Up Order

Recommended local order:

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
- `-BackendKind EchelonEnv`
  - swap the synthetic stub for a real Echelon `UniversalEnv`-backed state source

Notes:

- The local mod is still unpacked, so the launcher enables `-filePatching`.
- The backend metadata is written to `game/runtime/last_backend.json`.
- Stub logs are written under `game/logs/`.
- `-BackendKind EchelonEnv` currently defaults to
  `scenarios/stable_flight/stable_flight.json` and keeps the Arma world position
  as a rigid anchor while the backend owns the stepped flight truth.
