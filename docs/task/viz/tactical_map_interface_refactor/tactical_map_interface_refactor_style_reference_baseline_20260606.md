# Tactical Map Interface Style Reference Baseline

Status: `2026-06-06` `P0` reference baseline for the tactical map interface
refactor. This is a visual-design baseline, not an authority for operational
standard compliance.

Parent: [Tactical Map Interface Refactor](README.md)

## Decision

The `examples/viz` tactical interface should become a restrained map-first
situational display. It may borrow visual ideas from military symbology,
professional GIS, nautical/chart portrayal, common operational picture tools,
and public OSINT situation maps, but it must not claim that the implementation
is doctrinally correct or standard-compliant.

## Reference Families

| Family | Useful lesson | Local use | Boundary |
| --- | --- | --- | --- |
| Military symbology standards | Affiliation, unit identity, tactical graphics, and draw-order discipline. | Use blue/red/neutral/unknown language, simple unit frames, routes, contact/uncertainty marks. | No MIL-STD-2525 or APP-6 compliance claim. |
| GIS and chart portrayal | Layer hierarchy, scale, subdued basemaps, and legibility under dense overlays. | Separate base map, operational overlays, mission graphics, environment layers, and debug aids. | No geodetic/chart certification claim. |
| Common operational picture tools | Map-first workflow, collapsible side panels, contact lists, and quick focus controls. | Use docked panels and map surface switching without hiding the map. | No interoperability claim with TAK or other COP systems. |
| Public OSINT situation maps | Area/control/front-line uncertainty and readable public-facing annotations. | Use dashed uncertainty, muted control fills, and compact labels for areas. | OSINT map conventions are presentation references, not simulation truth. |

Reference links to inspect before implementation:

- DLA QuickSearch MIL-STD-2525 entry:
  <https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=114934>
- Army FM 1-02.2 military symbols public PDF mirror:
  <https://rdl.train.army.mil/catalog-ws/view/100.ATSC/CD4DFE54-1C0B-43D9-B8BA-B869F10E6561-1739243205786/FM1_02x2.pdf>
- ArcGIS Pro Military Symbology Editor:
  <https://pro.arcgis.com/en/pro-app/latest/help/production/military-symbology-editor/military-symbology-editor-intro.htm>
- IHO ENC portrayal:
  <https://iho.int/en/enc-portrayal>
- TAK.gov:
  <https://tak.gov/>
- ISW/CTP cartographical methodology:
  <https://www.understandingwar.org/sites/default/files/Cartographical%20Methodology%20Explanation%20ISW%20CTP%202022.pdf>
- War Mapper public map archive:
  <https://www.warmapper.org/>

## Interface Principles

- The map is the primary object. The first viewport should show the operational
  picture, not a stack of controls.
- Controls should be docked, collapsible, grouped, and predictable. A permanent
  top row full of layer buttons is not the long-term shape.
- Multiple maps are allowed. A single "tactical map" can become a workspace with
  named surfaces instead of one overloaded canvas.
- Text should be compact and tied to map objects. Avoid long explanatory blocks
  inside the application UI.
- The palette should be functional rather than one-note: dark neutral map base,
  blue/red affiliation, amber warnings, muted green/brown/gray environment
  overlays, and dashed uncertainty.
- Debug information belongs in a debug layer or inspector, not in the default
  presentation.

## Proposed Map Surfaces

| Surface | Primary question | Default layers | Notes |
| --- | --- | --- | --- |
| `COP` | What is happening and where are friendly/enemy units? | Base grid, units, routes, tracks, sensor rings, weapons as needed. | Main default for naval/air and mixed-domain tactical views. |
| `Environment` | What terrain, zone, road, building, vegetation, or weather context matters? | Base grid, environment overlays, area labels, optional mission zones. | Starts with accepted G0 overlay payloads only. |
| `Tracks/Sensors` | What is detected, linked, uncertain, or targeted? | Tracks, sensor rings, datalinks, weapons, uncertainty marks. | Useful for air/naval and later ground sensing work. |
| `3D Inspect` | What does the focused unit or local geometry look like? | Existing 3D view plus focus controls. | This is a workspace surface, not a replacement for the map. |

## Layer Grouping

| Group | Examples | Default |
| --- | --- | --- |
| Base | grid, scale, extent, optional basemap tint | on |
| Units | friendly, enemy, neutral, unknown units | on |
| Mission | routes, objectives, patrol areas, contact lines | on when present |
| Sensors/Tracks | sensor rings, datalinks, tracks, target cues | on for air/naval; profile-selectable |
| Effects | weapons, explosions, warnings, terminal states | on when present |
| Environment | G0 zones, terrain areas, buildings, roads, vegetation, weather overlays | on for ground/environment profiles |
| Debug | raw ids, payload diagnostics, evidence flags | off by default |

## Profile And Scenario Boundary

| Concern | Belongs in profile/UI | Belongs in scenario |
| --- | --- | --- |
| Default map surface | yes | no |
| Default visible layer groups | yes | no |
| Tactical zoom/camera/focus | yes | no |
| Unit starting location | no | yes |
| Terrain/building/road semantics | no | yes, once owned by environment/scenario contracts |
| Movement/passability/LOS/combat truth | no | yes, only after owning runtime worklines accept it |

## First Implementation Shape

The preferred first implementation is:

1. Map-first shell: central map/workspace area, slim top status strip, collapsible
   left session/profile panel, collapsible right inspector/layer panel.
2. Workspace selector: small tab or segmented control for `COP`, `Environment`,
   `Tracks/Sensors`, and `3D Inspect`.
3. Layer tray: grouped toggles with clear active state and compact labels.
4. Responsive rule: at narrow widths, panels collapse over the map only when
   explicitly opened; they do not permanently consume the first viewport.
5. Browser evidence: screenshots at narrow and desktop sizes before acceptance.

## Held Items

- Standard-compliant military symbology.
- Real geospatial projection and map-tile handling.
- Scenario editor and terrain generator UI.
- Runtime environment behavior, terrain-aware movement, LOS, cover, sensing, or
  combat behavior.
