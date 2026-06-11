# Archived F-16 Visualization Asset

Status: archived on 2026-06-11.

This directory retains the previous root-level `f16.glb` visualization asset for
provenance comparison only. It is no longer the active F-16 visualization asset
used by the registry.

## File

- `f16.glb`
- SHA256: `7c432edcaec14bc52a262d2ef311b19c525452e2614400c3c10f8e93da1b7ee0`
- Previous path: `examples/viz/web_viz/static/assets/f16.glb`

## Provenance Review

The local GLB metadata does not embed source, author, license, or a Sketchfab
UID. The closest confirmed provenance lead is FlightGear:

- FlightGear archive: https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip
- GitHub source lead: https://github.com/NikolaiVChr/f16
- Pinned commit observed in A2 source records: `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`
- License for the FlightGear package: GPL v2

Object-name comparison found all 117 local node/mesh names in FlightGear
`f16/Models/f16.ac`, making FlightGear a strong candidate source. Because GPLv2
is not a suitable mainline geometry-derived path for this repository, the asset
is archived and replaced by the CC-BY-4.0 Sketchfab `F16-C Falcon` candidate.

Do not generate mainline hitboxes, outer proxies, or component-region facts from
this archived asset.
