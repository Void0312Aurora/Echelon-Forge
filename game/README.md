# CMO Game Workspace

`game/` now follows the active Arma authoritative-backend integration line.

The maintained contents in this tree are:

- `mod/@EchelonProxy/`: local Arma mod shell
- `bridge/`: Windows DLL extension project
- `docs/echelon_proxy_backend_sync_v1.md`: Arma/backend sync contract
- `scripts/build_bridge.ps1`: local bridge build helper
- `scripts/launch_arma_proxy.ps1`: local Arma bring-up helper

On `2026-05-30`, the locally mixed Godot/WebSocket playable-shell experiment was
removed from `game/` and archived under the local-only ignored path
`archive/20260530_game_godot_local_archive/` so this workspace matches the
active Arma project again.

## Current Layout

```text
game/
  bridge/
  docs/
  mod/
  scripts/
```

## Local Usage

Build the DLL bridge:

```powershell
powershell -File game/scripts/build_bridge.ps1
```

Launch the Arma-side workflow:

```powershell
powershell -File game/scripts/launch_arma_proxy.ps1 -Mode StubAndArma -ShowScriptErrors
```

See also:

- [docs/README.md](docs/README.md)
- [docs/echelon_proxy_backend_sync_v1.md](docs/echelon_proxy_backend_sync_v1.md)
- [bridge/README.md](bridge/README.md)
- [mod/@EchelonProxy/README.md](mod/@EchelonProxy/README.md)
