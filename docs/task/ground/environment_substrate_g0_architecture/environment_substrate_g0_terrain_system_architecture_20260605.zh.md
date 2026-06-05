# Environment Substrate G0 Terrain System Architecture

状态：`2026-06-05`，面向 [README.zh.md](README.zh.md) 的 shared terrain-system
architecture design。本文件细化 G0 environment-substrate 计划中的 terrain 部分；
它不实现 terrain generator、movement model、LOS model、cover model 或 domain runtime。

## 目的

第一个严肃的 ground 场景是当前直接驱动，因为它在诚实进入 mechanized movement 或
village contact 之前，需要 terrain、buildings、roads、vegetation 和 tactical areas。
但这不意味着 terrain system 归 ground 独占。airfields、runways、coastal strips、
islands、littoral clutter、ports、rivers 以及未来 domains 都应迁移到同一套
environment substrate 内的 terrain branch，而不是各自长出私有 map schema。

当前 runtime 只有一个很小的 terrain query/setup surface。本文件定义一个结构化
terrain branch，使它能从当前 primitives 增长，而不是硬编码某个村庄、某个军种或
某个固定 schema。它从属于更大的 environment-substrate manifest；该 manifest 还需要
容纳 atmosphere/weather、wind、illumination、maritime/ocean、hydrology 与 dynamic
environment state branches。

设计目标是：用 deterministic manifests、tile/layer 数据、catalogs、validators、
derived products 和到当前 runtime 的 lossy projections，表达几十到上百平方公里的
terrain substrate。

本设计依据
[environment_substrate_g0_subagent_dispatch_20260605.zh.md](environment_substrate_g0_subagent_dispatch_20260605.zh.md)
中记录的两条只读 diagnostics packet：一条覆盖 C++ environment/query/setup
surfaces，一条覆盖 Python scenario compiler/runtime setup surfaces。

## 当前地形基础

| Current surface | 今天支持什么 | 还不能支持什么 |
| --- | --- | --- |
| `IEnvironmentModel` | elevation lookup、LOS stub、weather attenuation stub、terrain-cell lookup、rectangular zones、wind/maritime state | 没有 terrain manifest、tiled storage contract、road graph、building geometry 或 authoritative ground movement semantics |
| `DefaultEnvironmentModel` | `flat`/legacy elevation mode，20 km by 20 km、100 m raster base，SoftDirt/HardPacked checkerboard，带 surface properties 的 rectangular overlays | 不是 scalable world generation；没有 hydrology、soil/geology stack、feature catalog 或 terrain provenance |
| `WorldTerrainAssignment` | per-world global terrain type，例如 `flat` 或 `legacy` | 除 zones 外，没有 detailed terrain layers 或 regional heterogeneity |
| `WorldZoneDefinition` | name、center、width、length、heading、surface code 组成的 rectangle-like surface override | 没有 polygon/line/multilayer geometry、road width/load/speed semantics、tree density/species、building height/material/interior |
| Scenario compiler/runtime | 编译 `environment.terrain_type` 和 `environment.zones`，随 world yaw 旋转 projected zones，通过 maintained batch/facade paths 应用 setup | 还不理解 manifest/generator，没有 rich terrain provenance 或 derived-product lifecycle |
| Existing tests | 验证 terrain defaults、explicit legacy compatibility、zone setup payloads、batch setup behavior | 不验证 terrain realism、generator determinism 或 ground mobility/LOS behavior |

设计结论：新的 terrain system 必须位于当前 query/setup primitives 之上。当前 primitives
是 compatibility targets，不是 canonical terrain model。

两个直接风险决定了架构边界：

- 扩展 `WorldZoneDefinition` 会把 compatibility projection DTO 误变成假的
  canonical terrain schema。
- 继续依赖 loose `environment.zones` dictionaries，会让 unsupported 或 misspelled
  terrain semantics 静默降级成默认 surface setup，而不是 fail closed。

## Shared Domain 边界

terrain system 是 shared environment infrastructure：

- Air 可用它表达 runways、taxiways、airfield surfaces、approach terrain、
  obstacles 以及 weather/terrain projection boundaries。
- Naval 可用它表达 coastlines、islands、ports、littoral corridors、rivers、
  wetlands 和 shore-side infrastructure。
- Ground 可用它表达 roads、buildings、vegetation、soil、tactical areas，以及后续
  terrain-aware movement/LOS products。
- Future domains 应通过 components、catalogs、projection profiles 和 derived
  products 扩展，而不是接管 schema root。

ground task 仍是孵化入口，因为第一批缺口来自 land scenarios。但 implementation
ownership 仍应命名为 shared `environment_substrate`。

## 与其他 Environment Branches 的关系

terrain 不应变成所有环境 concern 的容器。G0 root manifest 应暴露 branch registry，
本 terrain 设计只占据其中的 `terrain` branch。

| Branch | 与 terrain 的关系 | G0 边界 |
| --- | --- | --- |
| `atmosphere_weather` | weather 可影响 visibility、attenuation、mud、snow 或 flight context，但它不是 terrain layer。 | 只保持 manifest-compatible branch；不释放 weather simulation。 |
| `wind_field` | wind 后续可与 terrain、fires、flight、smoke 共享 coordinate frames 和 time windows。 | richer profiles 前只投影到已接受的 global wind setup fields。 |
| `illumination` | sun/time/light context 后续可影响 terrain 上的 visibility 和 shadows。 | visual/sensing gates 前只作为 metadata。 |
| `maritime_ocean` | sea state 与 waves 在 shorelines、ports、islands、littoral strips 与 terrain 相接。 | shared naval/littoral branch；不释放 hydrodynamics。 |
| `hydrology` | inland water 与 wetness 可属于 terrain，并连接 maritime/coastal state。 | runtime mobility/LOS/effects 继续 held。 |
| `dynamic_environment` | smoke、fire、flooding、destruction、contamination 后续可修改 terrain-derived products。 | 当前 G0 static substages 只预留 IDs/hooks。 |

cross-branch objects 应使用 `branch_membership[]` 和 components，而不是 schema
inheritance。例如 flooded coastal road 可组合 `terrain`、`hydrology`、
`maritime_ocean`，以及后续 `dynamic_environment` membership，同时仍是一个经过验证的
environment object。

## Terrain System 边界

terrain system 是一个 static shared environment-substrate package，职责有五项：

- 存储 versioned terrain manifests；
- 验证 layered terrain objects 和 components；
- 运行 deterministic generator plugins；
- 在单独 gates 允许后构建 derived terrain products；
- 将受支持的子集投影到 maintained runtime setup surfaces。

它明确不做：

- 更新 entity positions；
- 在 runtime 决定 passability；
- 在 runtime 阻挡 LOS；
- 授予 cover、concealment、suppression、damage 或 combat effects；
- 在当前 G0 substages 替换 `IEnvironmentModel` 或 `WorldZoneDefinition`；
- 变成任一单独 domain 的 map schema。

## 建议 Package 形状

G1 应从 Python 侧开始，因为第一片是 static contracts、validation、fixture data 和
projection tests。任何 domain 的 C++ terrain ownership 都等后续 runtime release gate。

```text
python/scenario/environment_substrate/
  __init__.py
  manifest.py
  components.py
  validation.py
  projection.py
  terrain/
    __init__.py
    schema.py
    catalog.py
    layers.py
    generators.py
    derived_products.py
    projection_profiles.py
```

聚焦测试放在：

```text
tests/scenario/test_environment_substrate_manifest.py
tests/scenario/test_environment_substrate_projection.py
tests/scenario/test_terrain_system_schema.py
tests/scenario/test_terrain_system_projection.py
```

G1 不应编辑 C++ runtime code。

## 核心数据模型

```text
TerrainManifest
  manifest_id
  schema_version
  coordinate_frame
  extent
  tile_scheme
  generation
  layer_stack[]
  terrain_objects[]
  terrain_relationships[]
  catalogs[]
  projection_profiles[]
  validation_evidence[]
```

```text
TerrainObject
  object_id
  object_kind
  geometry
  tile_refs[]
  layer_membership[]
  components[]
  properties{}
  provenance
```

`object_kind` 只是描述。runtime meaning 来自 components 和 derived products，而不是
hardcoded labels。

## Layer Stack

terrain system 应支持 layered composition。layers 是有序且可组合的，所以 geology/soil、
hydrology、vegetation、buildings、roads 和 tactical overlays 都能在不改变 schema
root 的前提下加入。

| Layer | 作用 | runtime 使用前必需 attributes |
| --- | --- | --- |
| `base_elevation` | height field、contour source、terrain relief | elevation source、resolution、vertical datum、uncertainty |
| `terrain_morphology` | slope、embankment、ditch、berm、cut/fill | slope range、height/depth、geometry、confidence |
| `soil_surface` | soil、compaction、mud、snow、roughness | material class、wetness、roughness、seasonal state |
| `hydrology` | streams、ponds、drainage、flooded areas | water depth、bank geometry、flow/current、fordability metadata |
| `vegetation` | forest、tree line、orchard、shrub、grass | species group、canopy height、trunk spacing、density、undergrowth |
| `built_structure` | buildings、walls、bridges、bunkers | footprint、height、floors、material、entrance/window hints |
| `infrastructure` | roads、tracks、alleys、bridges、paths | network nodes、width、surface、load class、speed metadata、connectivity |
| `tactical_overlay` | contact line、objective、village block、assembly area | semantic type、side/control、confidence、time window |
| `hazard_overlay` | minefield、obstacle belt、contaminated area | hazard type、marking、activation、confidence |
| `dynamic_overlay` | 未来 mutable state，例如 destruction、smoke、fire、flood | G0-J 只预留 IDs |

这直接回应“地质叠加植被”的问题：base/surface layers 可以独立于 vegetation 存在，
validators 检查它们的兼容性，不需要把所有内容塞进单一 feature schema。

## Catalog And Components

catalog entries 是 reusable recipes。road、forest 或 building 是 catalog composition，
不是 schema root。

| Catalog example | Geometry | Required components | Projection rule |
| --- | --- | --- | --- |
| `rural_gravel_road` | line 加 corridor width 或 polygon | `surface_material`、`network`、`mobility_modifier` | 只有显式 rectangle-simplified 时才可投影到 Asphalt/HardPacked rectangle |
| `field_track` | line corridor | `surface_material`、`network`、optional `seasonal_state` | 只能作为低保真 surface zone 投影；不声明 movement speed |
| `shelterbelt_tree_line` | polygon strip | `vegetation`、optional `occlusion`、optional `cover_concealment` | G0-J 不做 LOS/cover projection |
| `village_house_light` | footprint polygon 加 height | `structure`、`surface_material`、optional `occlusion`、optional `damageable` | building projection accepted 前可保持 manifest-only |
| `farm_field` | polygon | `soil_surface`、optional `vegetation`、optional `hydrology` | 若 lossy profile 允许 dropped attributes，可投影为 SoftDirt |
| `runway_paved_surface` | polygon 或 rectangle | `surface_material`、`terrain_morphology`、optional `tactical_semantic` | 可投影到 Concrete，但不创建 air-only schema |
| `littoral_shoreline_strip` | polygon 或 polyline corridor | `hydrology`、`terrain_morphology`、`surface_material`、optional `tactical_semantic` | 可支持 naval/littoral context，runtime effects 仍 held |
| `port_hardstand` | polygon | `surface_material`、`infrastructure`、optional `ownership_control` | 可被 naval logistics 与 ground tasking 共用，不拆成私有 schema |
| `assembly_area` | polygon | `tactical_semantic`、optional `ownership_control` | 可被 tasking/status 引用，不声明 physics claims |

道路尺寸、通行能力、树木密度、树种、建筑高度、墙体材料、入口、surface condition
都是 component attributes。它们不能被压成单一 road/forest/building schema。

## Generator Architecture

未来 terrain generator 应是 plugin-based 且 deterministic。

```text
TerrainGenerationRequest
  request_id
  generator_id
  generator_version
  deterministic_seed
  extent
  tile_scheme
  realism_target
  catalog_refs[]
  constraints[]
  evidence_refs[]
```

generator stages 应可组合：

1. Frame and tile setup：extent、coordinate frame、tile grid、deterministic seed
   partitioning。
2. Base terrain：elevation、slope、roughness、major landforms。
3. Hydrology：drainage、streams、wet areas、crossings。
4. Surface and soil：material class、compaction、seasonal mud/snow/wetness。
5. Infrastructure：先生成 road/path graph，再生成 corridor geometry 和 bridges。
6. Built environment：settlement blocks、parcels、building footprints、walls。
7. Vegetation：biomes、field edges、tree lines、forests、density/species mix。
8. Tactical overlays：bases、contact line、objective areas、assembly areas。
9. Validators and projection profiles。

算法上应优先采用 hybrid approach：

- broad background layers 使用 deterministic procedural generation；
- roads、paths 和 infrastructure connectivity 使用 graph-based generation；
- settlement layout、bridge/crossing placement 和 tactical relationships 使用
  constraint solving；
- vegetation/buildings/obstacles 使用 catalog-driven feature instancing；
- 后续可加入 GIS 或 analyst-authored authoritative data import adapters。

这避免手写巨大地图，同时保持每个 generated object 可检查、可复现。

## Tiling And Scale

大面积 land areas 从第一版 schema 起就应 tile-aware：

- tile IDs 必须 deterministic 且 stable；
- objects 可以跨 tile，但必须声明 owning tile 和 covered tiles；
- validators 检查 extent bounds 与 cross-tile references；
- derived products 可按 tile 加 border halos 构建；
- projection 只发出当前 scenario/world 需要的子集。

G0-J contract 可以只存小 fixture，但 schema 应预留 tile fields，避免后续 generator
工作需要破坏性改写。

## Projection Boundary

当前 runtime projection 只支持：

- `WorldTerrainAssignment.terrain_type`；
- `WorldZoneDefinition` rectangle-like surface zones。

因此 projection profiles 必须显式：

```text
TerrainProjectionProfile
  profile_id
  target_surface
  allowed_object_kinds[]
  required_components[]
  geometry_simplification
  surface_code_mapping
  dropped_attribute_policy
  fail_closed_reasons[]
```

projection rules：

- unsupported geometry fail closed，除非 profile 显式允许 omission；
- unsupported field names 或 ambiguous surface mappings fail closed；
- dropped attributes 必须记录到 projection evidence；
- projection 不能声明 movement speed、LOS blockage、cover 或 damage；
- rich manifest provenance 在 lossy projection 后仍是权威来源。

## Derived Product Gates

derived products 是 static terrain data 到未来 runtime behavior 的桥。它们必须有独立
contracts 和 release gates。

| Product | Requires | Future use | Current status |
| --- | --- | --- | --- |
| `terrain_surface_map` | base elevation、soil/surface layers | query/debug 与 projection sanity | held |
| `road_graph` | infrastructure/network components | route planning 与 convoy movement | held |
| `movement_cost_grid` | soil、slope、hydrology、vegetation、mobility components | terrain-aware movement | held |
| `passability_mask` | obstacles、hydrology、buildings、actor class rules | stuck/off-route checks | held |
| `los_occlusion_index` | elevation、vegetation、structures、occlusion components | contact/report 与 sensing | held |
| `cover_concealment_index` | vegetation、structure、terrain morphology | firefight/cover behavior | held |
| `tactical_area_graph` | tactical overlay、ownership、infrastructure | tasking/report semantics | held |

## Implementation Roadmap

| Step | Goal | Write set | Release boundary |
| --- | --- | --- | --- |
| `T0` | Terrain system architecture and diagnostics evidence. | task package docs only | accepted G0 documentation |
| `T1 / G0-J-A-B` | Static shared environment manifest schema and validators. | `python/scenario/environment_substrate/**`、focused `tests/scenario/**` | accepted G0-J static contract；no runtime behavior |
| `T2 / G0-J-C` | Tiny deterministic fixture and projection tests. | fixture/test files plus projection contract | accepted G0-J contract tests；no generator release |
| `T3 / G0-K` | Generator plugin skeleton and request contract. | Python generator package and tests | no runtime projection unless separately accepted |
| `T4 / G0-L` | Projection integration into scenario compiler/runtime setup. | scenario compiler/runtime setup plus tests | only lossy zone projection |
| `T5 / G0-M` | First derived product contract. | derived-product package and tests | no movement/LOS effect without runtime gate |
| `T6 / G0-N` | C++ shared terrain query adapter. | new C++ package, bindings, tests | separate runtime release vote |

第一 implementation slice 现在是已接受的 G0-J shared static contract：schema、
registries、validators、deterministic fixture 与 projection contract tests。它证明
rich features 可以作为 static manifest data 存在，且 unsupported runtime claims 会
fail closed。

## Acceptance Boundary

本 terrain system design 只有在以下条件成立时才能支撑 G0 acceptance：

- 当前 terrain foundation 被描述为 compatibility primitives；
- terrain schema 是 layered、tiled、catalog-driven、component-based；
- terrain system 被明确为 air、naval、ground 和未来 domains 共享；
- road/building/vegetation details 是 attributes 和 components，不是 schema roots；
- generator、projection、derived products 和 runtime query ownership 被拆成后续 gates；
- movement、LOS、cover、fires、damage 和 combat 全部继续 held。
