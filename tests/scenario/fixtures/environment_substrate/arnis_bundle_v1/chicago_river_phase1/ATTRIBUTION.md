# Attribution and License Boundary

This fixture contains code-generated metadata together with retained or
derived third-party geospatial data. Those data files are not relicensed under
the repository-level Apache-2.0 license.

## OpenStreetMap

Applies to:

- `input/osm_extract_20260715.json`;
- the OpenStreetMap-derived portions of `expected/vectors/roads.cmo.json`;
- the OpenStreetMap-derived portions of
  `expected/vectors/buildings.cmo.json`; and
- the OpenStreetMap-derived portions of
  `expected/vectors/hydrology.cmo.json`.

Attribution: `© OpenStreetMap contributors`

OpenStreetMap data is available under the Open Data Commons Open Database
License 1.0 (`ODbL-1.0`):

- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/

The frozen extract was acquired through the Overpass API. The Overpass endpoint
is a delivery service and is not represented as the owner or licensor of the
OpenStreetMap data.

## ESA WorldCover

Applies to:

- `expected/rasters/landcover.u8` and its descriptive metadata; and
- land-cover-aware processing effects retained in
  `expected/rasters/elevation.f32le`.

Source: ESA WorldCover 2021 v200, licensed under Creative Commons Attribution
4.0 International (`CC-BY-4.0`). The retained raster is a resampled and
postprocessed derivative, not an unmodified upstream tile.

Required acknowledgement:

> © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data
> (2021) processed by ESA WorldCover consortium

License and data information:

- https://esa-worldcover.org/en/data-access
- https://creativecommons.org/licenses/by/4.0/

## USGS 3DEP

Applies to:

- `expected/rasters/elevation.f32le` and its descriptive metadata.

The actual Arnis elevation provider for this fixture was `usgs_3dep`. USGS 3DEP
products are public-domain United States government data and are available
without use restrictions. The retained raster contains Arnis postprocessing and
ESA land-cover-aware repair, and is not represented as an original USGS
product. It is exported directly from the postprocessed metre grid before any
Minecraft Y transform. Its source-native vertical datum was not preserved by
the exporter and is therefore recorded as unspecified.

Source information:

- https://www.usgs.gov/3d-elevation-program

## Arnis

The bundle was produced with Arnis `3.0.0`, upstream commit
`af521c99124b5e07ecba018ea54f2ac47b6441d5`, plus exporter version
`cmo.phase1.v1` and continuous patch
`0001-cmo-continuous-bundle-export-v1` (SHA-256
`26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`).
Arnis is licensed under Apache License 2.0:

- https://github.com/louis-e/arnis
- https://github.com/louis-e/arnis/blob/v3.0.0/LICENSE

The software license does not replace or alter the licenses of the geospatial
source data. No source provider endorses this fixture or the CMO project.
