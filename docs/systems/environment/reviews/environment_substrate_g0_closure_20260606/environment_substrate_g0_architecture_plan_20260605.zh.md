# Environment Substrate G0 Architecture Implementation Plan

状态：`2026-06-05`，面向 [README.zh.md](README.zh.md) 的 G0 架构实现计划。
本计划定义未来 environment substrate package 的形状；它不实现该 package。

## 边界决策

第一版 environment substrate 必须是 component-based，并且跨 domains 共享。
ground 是第一个压力入口，因为 land 场景会比当前 air/naval MVP 更早需要 terrain、
buildings、vegetation、infrastructure 和 tactical overlays；但 schema root 必须是
shared environment manifest 和 generic environment objects。它不能是 road、forest、
building、village、weather cell、wind field、sea-state area 或其他 feature label，
也不能由 ground domain 独占 ownership。

terrain 是第一条被细化的 branch，不是整个 substrate。现有 `IEnvironmentModel`
已经包含 atmosphere、weather attenuation、sun direction、wind 与 maritime state，
所以 G0 必须保留一个 branch registry，用来把 terrain 与其他 environment branches
合并，而不是创建 terrain-only root。

G0 之后的第一版 implementation 现在已作为 shared environment-substrate namespace 下的
Python 侧 manifest contract 与 validator 切片接受。C++ runtime terrain ownership、
movement、LOS、cover、fires、effects 和 damage 继续留在单独 release vote 之后。

## 目标流水线

```text
Scenario Intent
  -> Environment Generator Plugins
  -> Component-Based Environment Manifest
  -> Validators
  -> Derived Product Builders
  -> Runtime Projection
  -> Query / Simulation Consumers
```

manifest 是 rich static environment state 的权威来源。runtime projection 是从
manifest 到当前 maintained setup surfaces 的受控、有损操作，例如
`WorldTerrainAssignment` 和 `WorldZoneDefinition`。

## Manifest Shape

manifest 应该 versioned、deterministic，并显式记录 coordinate frame 与 provenance。

```text
EnvironmentManifest
  manifest_id
  schema_version
  coordinate_frame
  region_extent
  branch_registry[]
  component_registry[]
  layer_registry[]
  generation
    generator_id
    generator_version
    deterministic_seed
    source_inputs[]
  catalogs[]
  layer_stack[]
  objects[]
  relationships[]
  projection_profiles[]
  validation_evidence[]
```

每个对象保持通用：

```text
EnvironmentObject
  object_id
  catalog_ref
  branch_membership[]
  geometry
  layer_membership[]
  components[]
  properties{}
  provenance
```

`catalog_ref` 只是描述性入口。仿真含义必须来自 components 和经过验证的 projection，
而不是来自 label 本身。`properties{}` 只允许 metadata；任何只出现在 untyped
property 中的 simulation behavior 都必须被 validators 拒绝。

## Registry Locations

G1 应把 registries 显式且 versioned，而不是藏在 loose objects 中：

- `branch_registry[]`：branch descriptors、branch ownership、allowed components、
  validators、legal dependencies/conflicts 与 projection targets。
- `component_registry[]`：typed component descriptors、units、required
  attributes、consumer tags 与最低 realism grades。
- `layer_registry[]`：layer ordering、compatibility rules 与 branch/layer
  relationship rules。
- `catalogs[]`：可复用 feature recipes，引用 branches、layers、components 与
  projection profiles，但不成为 schema roots。
- `projection_profiles[]`：到当前 setup targets 的命名 lossy mappings，包括所需
  evidence 和 dropped-attribute policy。

## Branch Registry

manifest root 拥有 environment branches。branch 是 environment state、components、
validators、projection profiles 与未来 derived products 的 typed namespace。
branches 可以覆盖同一区域或同一个 object。

| Branch family | 作用 | 当前源码线索 | G0 规则 |
| --- | --- | --- | --- |
| `terrain` | surface、elevation、built features、vegetation、roads 和 tactical areas。 | `terrain_type`、`WorldZoneDefinition`、terrain-cell queries。 | 第一条细化 architecture branch；不释放 runtime terrain behavior。 |
| `atmosphere_weather` | air density、pressure、temperature、humidity、weather attenuation、clouds、precipitation、visibility。 | `get_atmosphere_at()`、`get_weather_attenuation()`。 | 保持 manifest-compatible branch；不释放 weather simulation。 |
| `wind_field` | wind vectors、direction、speed、shear、gust models、altitude bands。 | `set_wind()`、atmosphere wind velocity。 | richer profiles 出现前，只能投影到当前 global wind setup。 |
| `illumination` | sun direction、time-of-day、light、shadow/visibility context。 | `get_sun_direction()`。 | sensing/visual gates 前只作为 metadata。 |
| `maritime_ocean` | sea state、waves、wave heading/period、littoral water state。 | `set_maritime_state()`、`get_maritime_state()`。 | 与 naval 和 littoral terrain 共享；不释放 hydrodynamics/effects。 |
| `hydrology` | inland water、wetness、drainage、flooded areas、crossings。 | terrain branch 需要；当前 runtime 没有 rich hydrology。 | 可连接 terrain 与 maritime；runtime effects held。 |
| `dynamic_environment` | mutable smoke、fire、flooding、destruction、contamination、time windows。 | 还没有 maintained static manifest。 | 当前 G0 static substages 只预留 IDs 和 component hooks。 |

每个 branch descriptor 至少应包含：

- branch ID 与 schema version；
- shared owner、static/dynamic status、supported geometry dimensions 与
  temporal-support model；
- allowed component families 与 required validators；
- accepted projection targets 与 explicit non-targets；
- legal branch dependencies/conflicts；
- 本 branch 自身不能解锁的 held capability claims。

branch membership 避免把 weather 或 ocean semantics 硬塞进 terrain layers。例如 coastal
storm 可组合 `terrain`、`atmosphere_weather`、`wind_field` 与 `maritime_ocean`
objects；muddy village road 后续可组合 `terrain`、`hydrology` 与
`dynamic_environment` objects，但需要单独 gates。

`branch_membership[]` entries 应带 roles，而不只是 branch IDs：

- `primary`：拥有 object 主身份和 validation path 的 branch；
- `supporting`：贡献 components，但不接管 identity 的 branch；
- `context`：只提供 environmental context 的 branch；
- `projectable`：可进入命名 compatibility projection profile 的 branch membership；
- `metadata_only`：保留在 manifest 中但不投影的 branch data；
- `reserved_dynamic`：stable future mutable-state hook，不具备已接受的 G0 runtime
  behavior。

Branch membership 可以引用 branch-scoped component IDs 和 projection profile IDs。
只有 branch descriptors 允许的组合才是合法 cross-branch object。

## Layer Semantics

默认 layer stack 是开放的，并按依赖关系排序；它不是固定封闭 enum。

branches 与 layers 是不同概念。branch 是 ownership、validation 与 projection
namespace；layer 是 branch 内部或跨 branch 的 ordering/composition slot。
`hydrology` 这类名称可以同时出现在两层，但 docs 和 validators 必须保留这一区分。

| Layer family | 目的 | 示例 | G0 规则 |
| --- | --- | --- | --- |
| `physical_base` | surface 之下的长期底层。 | geology、soil class、compaction、rock | G1 可作为 metadata；暂不产生 movement effect。 |
| `terrain_surface` | 表面几何与材料。 | slope class、surface roughness、mud、snow | 只有显式 projection 时才能映射到当前 surface codes。 |
| `hydrology` | 水体与湿度状态。 | stream、drainage ditch、flooded field、water table | runtime effects held。 |
| `atmosphere_weather` | 区域上的局部 atmosphere/weather cells。 | fog area、rain band、temperature layer、cloud ceiling | 只做 metadata/projection；不释放 weather dynamics。 |
| `wind_field` | 区域或高度上的 wind state。 | surface wind、shear layer、gust cell | 只能投影到已接受的 wind setup fields。 |
| `illumination` | 后续影响 visibility 的 light 与 sun/time state。 | sun vector、time window、shadow context | sensing/visual effects held。 |
| `maritime_ocean` | sea/wave state 与 littoral water context。 | sea-state area、wave corridor、surf zone | release gates 前只做 naval/littoral context。 |
| `vegetation` | 植被覆盖与生物杂波。 | forest patch、tree line、orchard、shrub density | 声明 cover 或 LOS 前必须有 density/species attributes。 |
| `built_structure` | 人工结构。 | house、wall、barn、bridge、bunker | 声明 occlusion 前必须有 footprint 与 vertical attributes。 |
| `infrastructure_network` | 可通行或连接基础设施。 | road、track、alley、bridge、culvert | 声明 movement 前必须有 width/load/surface/connectivity metadata。 |
| `tactical_semantic` | 分析员或任务意义。 | village block、contact line、assembly area、objective area | 语义 label 本身不暗示物理效果。 |
| `hazard_control_overlay` | 危险、控制、归属和拒止。 | minefield、obstacle belt、controlled sector | effects 继续 held。 |
| `dynamic_state_overlay` | runtime 可变状态。 | destroyed bridge、fire、smoke、flooded road | G0-J static manifest 只能预留 ID。 |

对象可以属于多个 layers。validators 负责检查兼容性，而不是强迫一个对象只能位于
一个 layer。

## Component Registry

component 是带稳定 family、schema version、attributes、consumer tags 和最低
realism grade 的 typed record。扩展 registry 时添加新的 component descriptor 与
validator，不改变 object root。

| Component family | 必需含义 | 示例 attributes | 被阻塞的 consumer |
| --- | --- | --- | --- |
| `surface_material` | 对象表面材料。 | material class、roughness、wetness、snow depth | 可投影到当前 surface codes；movement 需要 future mobility gates。 |
| `terrain_morphology` | 形状或坡度特征。 | elevation source、slope range、embankment height、cut/fill | terrain-aware movement 与 LOS gates。 |
| `mobility_modifier` | 机动可能如何受影响。 | allowed actor classes、speed multiplier、load class、seasonal closure、obstacle severity | movement release vote。 |
| `vegetation` | 植被覆盖细节。 | species group、canopy height、trunk spacing、density、undergrowth、seasonal leaf state | cover、LOS、sensing gates。 |
| `structure` | 建筑结构属性。 | footprint、height、floors、wall material、entrances、windows、interior passability | building LOS、cover、damage gates。 |
| `occlusion` | 潜在遮挡。 | height、opacity by sensor family、permeability、confidence | LOS/sensing gate。 |
| `cover_concealment` | 战术保护或隐蔽语义。 | cover arc、protection class、concealment factor、stance dependency | cover/firefight gate。 |
| `network` | 图连接关系。 | from/to nodes、width、lane count、shoulder、turn radius、grade、bridge/tunnel refs | route graph 与 movement gates。 |
| `hydrology` | 水、湿度和排水语义。 | depth、current、bank slope、fordability、flooding recurrence | mobility 与 sensing gates。 |
| `atmospheric_profile` | 局部 atmosphere state。 | temperature、pressure、density、humidity、altitude band、confidence | flight/weather consumers；不释放 dynamics。 |
| `weather_effect` | 天气现象与 attenuation hints。 | precipitation、fog、cloud ceiling、visibility、attenuation by sensor family | sensing/weather gate。 |
| `wind_field` | 风场状态。 | speed、direction、shear、gust、altitude band、time window | richer gates 前只允许 current global wind projection。 |
| `illumination` | 光照与太阳状态 hints。 | sun vector、time of day、shadow confidence、light level | visual/sensing gate。 |
| `maritime_state` | 海况与波浪状态。 | sea state、wave heading、wave period、surf severity | naval/littoral gates。 |
| `hazard` | 危险或拒止区域。 | hazard kind、activation state、confidence、marking、neutralization state | effects/damage gate。 |
| `tactical_semantic` | 人类作战意义。 | objective ID、control side、phase line、contact line、named area | tasking/status 可引用；不声明 physics。 |
| `ownership_control` | 控制与通行元数据。 | side、confidence、time window、access rule | tasking 与 information-state gates。 |
| `damageable` | 未来可变退化。 | health class、repairability、failure modes、kill criteria | damage/runtime state gate。 |

道路宽度、道路等级、树种、树木密度、建筑高度、入口布局这类细节都是 component
attributes，不是特殊 schema root。

## Catalog Composition Examples

| Catalog entry | Geometry | Components | Notes |
| --- | --- | --- | --- |
| `rural_paved_road` | LineString 或 polygon corridor | `surface_material`、`network`、`mobility_modifier`、optional `damageable` | movement 使用前必须有 width、lane count、surface class、load class 和 speed metadata。 |
| `shelterbelt_tree_line` | Polygon strip | `vegetation`、optional `occlusion`、optional `cover_concealment` | LOS 或 cover 使用前必须有 species、density、canopy attributes。 |
| `village_house_light` | footprint polygon 加 height/extrusion | `structure`、`surface_material`、optional `occlusion`、optional `cover_concealment`、optional `damageable` | static tasking 可引用；building combat held。 |
| `field_boundary_ditch` | LineString 或 narrow polygon | `terrain_morphology`、`hydrology`、optional `mobility_modifier` | mobility impact 继续等待 route/movement gates。 |
| `airfield_surface` | Polygon 或 rectangular zone | `surface_material`、optional `terrain_morphology`、optional `tactical_semantic` | 可支持 airfield/runway setup projection，但不变成 air-only schema。 |
| `coastal_littoral_strip` | Polygon 或 polyline corridor | `terrain_morphology`、`hydrology`、optional `surface_material`、optional `tactical_semantic` | 可支持 naval/littoral context，但不变成 naval-only schema。 |
| `fog_bank` | Polygon 或 volume | `weather_effect`、optional `atmospheric_profile`、optional `time_window` | sensing/weather projection 接受前保持 manifest-only。 |
| `wind_shear_layer` | Volume 或 altitude band | `wind_field`、optional `atmospheric_profile` | 只有显式 simplified 时才可投影到 current global wind。 |
| `sea_state_patch` | Polygon 或 area | `maritime_state`、optional `weather_effect`、optional `time_window` | 可支持 naval/littoral setup，不声明 runtime hydrodynamics。 |
| `assembly_area` | Polygon | `tactical_semantic`、optional `ownership_control` | 可支持 early ground task references，不声明 terrain physics。 |

Catalog entries 应声明：

- catalog ID 与 schema version；
- allowed branches、branch roles 与 layers；
- accepted geometry kinds 和 dimensions；
- required 与 optional components；
- minimum realism grade 和 consumer tags；
- accepted projection profile refs；
- lossy projection 的 dropped-attribute policy；
- forbidden capability claims。

## Validator Plan

G1 validators 应 fail closed，并返回 machine-readable rejection reasons。

- Structural validator：manifest ID、schema version、coordinate frame、extents、
  object IDs、component family IDs 和 required fields。
- Geometry validator：允许的 geometry types、有限坐标、extents、area/length
  sanity bounds，以及必要时的 ring orientation。
- Reference validator：catalog refs、layer refs、object relationships、
  projection profile refs 和 provenance refs。
- Component validator：按 component family 检查 required attributes、units、
  value ranges、consumer tags 和最低 realism grade。
- Branch validator：known branch IDs、branch-specific component allowance，以及
  合法 cross-branch combinations。
- Layer validator：layer membership compatibility 与 illegal combinations。
- Projection validator：显式 lossy projection permission、geometry simplification
  method、surface-code mapping 和 unsupported feature rejection。
- Target-contract validator：当前 setup targets 只能接受它们实际维护的字段，例如
  global terrain type、rectangular zones、global wind 与 global maritime layout fields。
- Evidence-completeness validator：成功 projection 必须记录 source object IDs、
  branch memberships、component IDs、projection profile IDs、target setup surfaces、
  simplification method、dropped attributes、provenance refs，以及显式
  no-held-capability-release flag。
- Realism gate validator：若没有对应 derived product 和 runtime gate，拒绝
  manifest 启用 movement、LOS、cover、fires、damage、combat、weather simulation、
  hydrodynamics、hydrology effects 或 dynamic environment mutation 的声明。

validators 应返回 stable、machine-readable rejection reasons。必需 reason-code
families 包括 unsupported geometry、unknown branch/component、illegal branch
combination、missing required component attribute、invalid units or ranges、
unsupported target field、ambiguous mapping、dropped attribute without permission、
unknown `surface`、把 `surface_type` 写到只消费 `surface` 的 zone path 这类 misspelled
fields，以及 held capability claim。

## Projection Plan

从 manifest 到当前 setup surface 的 projection 必须显式：

- `terrain_type`：只用于 `flat` 或 `legacy` 这类 global compatibility modes。
- `WorldZoneDefinition`：只用于存在 accepted rectangular 或 rectangle-simplified
  projection profile，并且能映射到当前 surface code 的 objects。
- Wind setup：只用于存在 accepted global 或 altitude-band simplification profile
  的 `wind_field` objects。
- Maritime setup：只用于存在 accepted global sea-state simplification profile 的
  `maritime_ocean` objects。
- Atmosphere/weather/illumination：除非未来 accepted projection profile 映射到
  maintained runtime fields，否则保持 manifest-only。
- projection evidence 必须记录 source object IDs、component IDs、projection
  profile ID、simplification method 和 dropped attributes。
- unsupported objects 保留在 manifest 中；除非 profile 显式允许 omission，否则
  从 runtime projection fail closed。

当前 G0 static/projection-contract substages 的 compatibility targets 如下：

| Branch | Accepted compatibility projection | Rejected or held |
| --- | --- | --- |
| `terrain` | `terrain_type` 仅用于 global `flat` 或 explicit legacy compatibility；`WorldZoneDefinition` 只用于 rectangle 或 rectangle-simplified 的 surface-only objects，并映射到当前 surface codes。 | 未简化的非矩形 geometry、route graphs、building/vegetation LOS 或 cover、slope/elevation grids、movement/passability/fires/damage claims、unknown surface fields。 |
| `wind_field` | `WorldWindAssignment` 或 runtime layout wind fields：speed、direction-from、shear，且必须通过显式 simplification profile。 | wind volumes、gust cells、time evolution、smoke/drift、fire behavior 或 flight-dynamics claims。 |
| `maritime_ocean` | runtime layout maritime fields：configured flag、sea state、wave heading、wave period；explicit calm sea 仍是有效 override。 | area sea-state patches、surf/littoral hydrodynamics、wave fields 或 naval runtime release claims。 |
| `atmosphere_weather` | G0-J 保持 manifest-only。 | fog/rain/cloud cells 投影进 runtime、weather simulation、sensing attenuation release。 |
| `illumination` | G0-J 保持 manifest-only。 | time-of-day、shadow、visual/sensing effects，除非已有 maintained projection target。 |
| `hydrology` | 只有 profile 记录所有 dropped hydrology attributes 时，才可选择 lossy terrain-surface projection 到 rectangular `Water` 或 wet/soft surface code。 | depth、current、fordability、drainage、flood effects、mobility 或 sensing effects。 |
| `dynamic_environment` | G0-J 不做 runtime projection；只保留 stable IDs/hooks 作为 static manifest data。 | smoke、fire、flooding、destruction、contamination、mutable runtime state、damage 或 combat effects。 |

Wind 与 maritime projection 一旦应用就不是中性 metadata：现有 flight/naval consumers
可能读取它们。因此 projection evidence 必须区分“setup value accepted”和
“domain behavior released”。

这样 rich environment information 可以保留给后续 G0-K+ gates，同时当前 scenario
setup 仍能兼容当前 runtime。

## Derived Product Roadmap

derived products 不是 G0-J runtime features。它们是未来带独立 release gate 的
contracts。

| Derived product | Inputs | Future consumer | Held capability |
| --- | --- | --- | --- |
| `road_graph` | `network`、`surface_material`、`mobility_modifier` | route planning 与 convoy movement | movement。 |
| `movement_cost_grid` | terrain、hydrology、vegetation、mobility components | terrain-aware movement | future mobility gate。 |
| `passability_mask` | obstacles、hydrology、structures、actor class rules | stuck/off-route checks | movement/runtime behavior。 |
| `los_occlusion_index` | terrain morphology、vegetation、structures、occlusion | sensing 与 contact reports | LOS/sensing。 |
| `cover_concealment_index` | cover、vegetation、structures、tactical state | firefight behavior | cover/fires。 |
| `tactical_area_graph` | tactical semantics、ownership、infrastructure | tasking 与 reports | higher-grade command behavior。 |
| `weather_attenuation_field` | atmosphere/weather、visibility、precipitation、sensor family hints | sensing 与 flight/ship/ground observation | weather/sensing。 |
| `wind_field_volume` | wind components、altitude bands、time windows | flight dynamics、fires、smoke/drift | weather/dynamics。 |
| `maritime_state_field` | sea state、wave heading/period、weather、littoral geometry | naval movement 与 sensor context | maritime runtime behavior。 |

## G0-J Implementation Package Map

本 G0 package 内已接受的 G0-J write set 如下。该 namespace 刻意保持 shared；
没有放到按军种或 domain 特化的 Python package 下：

- `python/scenario/environment_substrate/__init__.py`
- `python/scenario/environment_substrate/manifest.py`
- `python/scenario/environment_substrate/components.py`
- `python/scenario/environment_substrate/validation.py`
- `python/scenario/environment_substrate/projection.py`
- `tests/scenario/test_environment_substrate_contracts.py`
- `tests/scenario/test_environment_projection_contracts.py`
- [G0-J static manifest contract](environment_substrate_g0_static_manifest_contract_20260605.zh.md)

G0-J 没有编辑 C++ runtime code。它只引入 static manifest data structures、
registries、validators、一个极小 deterministic fixture，以及 projection contract tests，用来证明
unsupported rich features 会 fail closed，而不是被静默当成 runtime behavior。

G0-K 后续可以在同一 package 下增加 generator plugins 和 catalogs。G0-L 后续再接入
scenario compiler/runtime setup projection。G0-M+ 只有在显式 release vote 之后才能
增加 derived products。

## Rejected Alternatives

- terrain-only environment root。
- ground-owned、air-owned 或 naval-owned environment schema。
- road、house、fog bank、wind layer、sea-state patch 等 feature-label schema roots。
- 让某一 branch 通过 inheritance tree 拥有另一个 branch 语义。
- 把 `WorldZoneDefinition` 或 loose `environment.zones` dictionaries 当作 canonical
  schema。
- 把 `properties{}` 当作 simulation-behavior escape hatch。
- 在 G0 实现 parser、generator、projection runtime、weather simulation、
  hydrodynamics、movement、LOS、cover、fires、damage、combat 或 dynamic environment
  mutation。
