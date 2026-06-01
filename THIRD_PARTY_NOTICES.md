# Third-Party Notices

This repository is licensed under the Apache License, Version 2.0, except where
noted otherwise.

The notices below cover third-party files that are currently stored in the
repository or used as local visualization assets. They do not replace the
upstream license terms for those files.

## Bundled JavaScript

### Socket.IO client

- File: `examples/viz/web_viz/static/socket.io.min.js`
- Version: 4.7.2
- Copyright: 2014-2023 Guillermo Rauch
- License: MIT License, as stated in the file header.

## Visualization Assets

The GLB assets under `examples/viz/web_viz/static/assets/` are visualization
assets. They are not relicensed by the repository-level Apache-2.0 license.

### Missile assets

Source attribution is maintained in
`examples/viz/web_viz/static/assets/missiles/ATTRIBUTION.md`.

- `examples/viz/web_viz/static/assets/missiles/aim120_amraam_rickslash.glb`
  - Title: AIM-120 AMRAAM missile
  - Author: RickSlash
  - Source: https://sketchfab.com/3d-models/aim-120-amraam-missile-e52d37a110004e1480465bc6b0943ebc
  - License: CC-BY-4.0
- `examples/viz/web_viz/static/assets/missiles/r77_mustafa_garip.glb`
  - Title: Game Ready Low Poly R-77
  - Author: Mustafa.Garip
  - Source: https://sketchfab.com/3d-models/game-ready-low-poly-r-77-0da27c5b53f24542843a4a423c59b96a
  - License: CC-BY-4.0

### UAV assets

Source attribution is maintained in
`examples/viz/web_viz/static/assets/uav/ATTRIBUTION.md`.

- `examples/viz/web_viz/static/assets/uav/mq9_reaper_game_ready_aesthetic_modeler.glb`
  - Title: MQ-9 Reaper Drone - Game Ready Military Asset
  - Author: The Aesthetic Modeler
  - Source: https://sketchfab.com/3d-models/mq-9-reaper-drone-game-ready-military-asset-a02057e7401a4f4ea130cb75cc73d8cb
  - License: Creative Commons Attribution (CC BY), as recorded in the local attribution file.
- `examples/viz/web_viz/static/assets/uav/shahed_136_faintastic18.glb`
  - Title: Shahed 136
  - Author: faintastic18
  - Source: https://sketchfab.com/3d-models/shahed-136-bc8754128c9d48c48baadeff1db8f0c7
  - License: Creative Commons Attribution (CC BY), as recorded in the local attribution file.

### Assets requiring attribution cleanup

The following local GLB files are tracked in the repository but do not currently
have a local attribution record next to the asset. Treat them as visualization
assets with unresolved local license metadata until a source, author, license,
retrieval date, and checksum are recorded.

- `examples/viz/web_viz/static/assets/f16.glb`
- `examples/viz/web_viz/static/assets/ddg51.glb`
- `examples/viz/web_viz/static/assets/naval/usns_patuxent_tao_201.glb`

## Fetched Build Dependencies

The CMake build fetches external dependencies such as `flecs` and `nanobind`
from their upstream repositories. Those dependencies retain their upstream
licenses and are not relicensed by this repository.

Python packages declared in `pyproject.toml` also retain their upstream
licenses.
