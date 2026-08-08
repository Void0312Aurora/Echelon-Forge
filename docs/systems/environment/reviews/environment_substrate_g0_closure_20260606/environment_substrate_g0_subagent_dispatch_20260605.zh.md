# Environment Substrate G0 Subagent Dispatch

状态：`2026-06-05`，面向 [README.zh.md](README.zh.md) 的只读 diagnostics
dispatch record。

## 权威依据

派发遵循：

- [子项目创建标准](../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- [Subagent 使用规范](../../../../engineering/automation/standards/subagent_usage_policy.zh.md)
- [文档权威索引](../../../../engineering/automation/rules/document_authority_map.zh.md)

主线程拥有 integration 和最终 scope decisions。本轮 G0 中 subagents 只做 diagnostics。

## 已应用派发规则

- 每个 diagnostics worker 映射到一个命名 environment-branch evidence slice。
- workers 只读，不得编辑文件。
- workers 不得创建新的会话线程。
- workers 不得回滚无关编辑或其他 worker 的编辑。
- worker 不得声明 terrain generation、weather simulation、hydrodynamics、
  movement、LOS、cover、fires、damage、combat 或 runtime release。
- subagent 返回必须由主线程整合后，才能成为 package evidence。

## Dispatch Packets

| Packet | Worker | Scope | Files / surfaces | Write set | Required return | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `TERR-DIAG-A` | `Averroes` | C++ terrain/environment foundation | `src/core/interfaces/environment_model.h`、`src/models/environment/default_environment_model.cpp`、`src/runtime/contracts/world_batch_contracts.h`、`src/core/engine/world_batch_setup_helper.h`、相关 README/tests | none，只读 | files inspected；existing mechanisms；limitations；architecture implications；held capabilities | pass |
| `TERR-DIAG-B` | `Descartes` | Python scenario/compiler/runtime terrain setup | `python/scenario/compiler/*`、`python/scenario/runtime/*`、`tests/scenario`、`tests/world_batch`、`tests/runtime/core` | none，只读 | files inspected；existing mechanisms；limitations；architecture implications；held capabilities | pass |
| `ENV-BRANCH-DIAG-A` | `Huygens` | Existing non-terrain environment branches | C++ 与 Python atmosphere/weather、wind、illumination/sun、maritime/ocean、hydrology 与 dynamic-environment hints | none，只读 | files inspected；existing mechanisms；limitations；architecture implications；behavior risks；held capabilities | pass |
| `ENV-BRANCH-DIAG-B` | `Pascal` | Branch ontology and component gap review | G0 architecture docs、terrain-branch docs、source inventory、task clusters | none，只读 | branch/component/catalog gaps；rejected alternatives；integration notes；held capabilities | pass |
| `ENV-BRANCH-DIAG-C` | `Carson` | Projection and validator gate review | world-batch setup、scenario compiler/runtime setup、environment model、relevant tests | none，只读 | accepted/rejected compatibility projections；validator classes；evidence requirements；held gates | pass |

## Returned Diagnostics Summary

`TERR-DIAG-A` 发现 C++ 侧是 query 与 compatibility-consumer surface：

- `IEnvironmentModel` 暴露 atmosphere、elevation、LOS、weather attenuation、
  terrain cells、rectangular zones、wind、terrain profile 与 maritime state。
- `DefaultEnvironmentModel` 使用固定 20 km by 20 km、100 m raster base，
  SoftDirt/HardPacked checkerboard，`flat` 对 legacy Gaussian elevation，以及
  z-ordered rectangular overlays。
- `WorldTerrainAssignment` 与 `WorldZoneDefinition` 只携带 global terrain type
  和 rectangle-like surface overrides。
- ground contact、visual cues、sensor LOS elevation、GPU visual snapshots 这类
  existing consumers 是 query/display/compatibility consumers，不是 canonical
  terrain owners。

`TERR-DIAG-B` 发现 Python 侧是 setup plumbing：

- `terrain_type` 是 global string，默认 `flat`，显式 legacy 会被标记为
  compatibility。
- `environment.zones` 把 rectangle-like `surface` entries 编译到六类 coarse
  surface codes。
- runtime/batch setup 通过 maintained setup contracts 转发 terrain、wind、zones
  和 spawns。
- scenario generation metadata 已有 deterministic seed、generator version 与
  evidence refs，但它不是 terrain generator contract。

综合影响：

- 不要把 loose `environment.zones` 或 `WorldZoneDefinition` 扩成 canonical
  terrain schema。
- terrain system 应走 manifest-first：layer stack、tile scheme、object identity、
  component registry、catalogs、relationships、provenance、validators、projection
  profiles 与 derived-product gates。
- 当前 C++ 与 Python surfaces 应保持 compatibility projection/query targets，
  直到单独 runtime gates 被接受。
- validators 必须捕捉 unsupported 或 misspelled zone/projection semantics，不能让
  rich terrain data 静默降级成默认 SoftDirt-style setup。

继续 held 的能力：terrain generator implementation、大面积 terrain generation、
面向任一 domain 的 C++ terrain-runtime ownership、movement/passability、LOS、
cover/concealment、sensing/contact reports、fires、damage、suppression、dynamic
terrain state，以及完整 village firefight behavior。

`ENV-BRANCH-DIAG-A` 返回 `pass`，并确认当前 non-terrain support 并不均匀：

- atmosphere/weather/sun 是 query hooks：简单 atmosphere、no-op weather
  attenuation 和 fixed sun direction 不证明 weather 或 illumination branches；
- wind 是维护中的 global setup field，包含 speed、direction-from 与 shear，不是
  wind volumes、gusts 或 time evolution；
- maritime 是 global runtime-layout override，包含 sea state、wave heading 与
  wave period，且现有 naval consumers 可能读取它；
- hydrology 与 dynamic environment 今天还不是 maintained substrate branches。

`ENV-BRANCH-DIAG-B` 返回 `pass`，并确认当前 ontology 可以支持 cross-branch
objects，但 G0 需要记录额外 contracts：

- 显式 branch、component、layer、catalog 与 projection registries；
- branch descriptors 应包含 version、ownership、static/dynamic status、geometry、
  temporal support、allowed components、validators、projection targets 与 conflicts；
- branch membership 应有 roles，而不是 bare IDs；
- `properties{}` 只能作为 metadata，不得作为 behavior escape hatch；
- 显式拒绝 terrain-only root、domain-owned schema、feature-label schema roots、
  branch inheritance trees，以及 G0 parser/projection implementation。

`ENV-BRANCH-DIAG-C` 返回 `pass`，并定义 fail-closed projection matrix：

- terrain 只可投影到 global terrain type 或显式简化后的 rectangular surface zones；
- wind 只可投影到当前 global wind setup fields；
- maritime 只可投影到当前 global runtime-layout maritime fields；
- atmosphere/weather、illumination 与 dynamic environment 在 G0-J 保持
  manifest-only；
- hydrology 只有在记录 dropped hydrology attributes 时，才可使用 lossy rectangular
  water/wet/soft surface projection；
- 每个成功 projection 都需要 source object IDs、branch membership、component IDs、
  profile IDs、target setup surface、simplification method、dropped attributes、
  provenance，以及 no-held-capability-release flag。

## Integration Target

返回的 diagnostics 应整合到：

- [environment_substrate_g0_source_inventory_20260605.zh.md](environment_substrate_g0_source_inventory_20260605.zh.md)
- [environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)
- [environment_substrate_g0_terrain_system_architecture_20260605.zh.md](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)
- [environment_substrate_g0_task_clusters_20260605.zh.md](environment_substrate_g0_task_clusters_20260605.zh.md)

## Worker Packet Template

```md
status: pass | partial | blocked | failed
touched files: none expected for diagnostics
files inspected:
commands/outcomes:
existing mechanism summary:
structural limitations:
architecture implications:
behavior risks:
explicit held capability claims:
integration notes:
```

## Acceptance Boundary

diagnostics packet 只有在保持只读、引用当前 repo 文件、并保持 terrain generation、
weather simulation、hydrodynamics、movement、LOS、cover、fires、damage、combat 和完整
environment/domain runtime 全部 held 时，才能支撑 G0 architecture evidence。
