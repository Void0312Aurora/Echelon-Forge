# Environment Substrate G0 Source Inventory

状态：`2026-06-05`，面向 [README.zh.md](README.zh.md) 的 source inventory。
这是 G0 架构计划的证据，不是 runtime release 记录。

## 清点结论

仓库已经有共享的 environment query 和 setup primitives，但还没有维护中的 shared
environment substrate。当前机制足以把简单 `terrain_type`、矩形 zone、wind 与
maritime state 投影进 world setup；它不足以把大面积地形、airfields、coastlines、
ports、建筑、道路、植被、atmosphere/weather cells、wind layers、illumination state、
sea-state areas、cover、LOS 或 terrain-aware movement 表达为跨域一等数据。

| Surface | Evidence | 当前作用 | 边界 |
| --- | --- | --- | --- |
| `IEnvironmentModel` | [../../../../src/core/interfaces/environment_model.h](../../../../src/core/interfaces/environment_model.h) | 共享 atmosphere、elevation、LOS、weather attenuation、sun、terrain-cell、wind、terrain type、maritime state 和矩形 zone API。 | 没有 shared environment manifest、branch registry、component catalog、road/coast/airfield graph、building model、weather branch、hydrology branch、dynamic state branch 或 domain mobility contract。 |
| `DefaultEnvironmentModel` | [../../../../src/models/environment/default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp) | 20 km by 20 km、100 m raster base，SoftDirt/HardPacked checkerboard，legacy gaussian elevation，`flat` terrain switch，矩形 overlay zones，简单 surface properties，简单 atmosphere/wind defaults、fixed sun 与 maritime override storage。 | checkerboard、fixed/no-op query defaults 和 rectangle zones 是兼容 primitives，不是可扩展 environment generator 或 branch substrate。 |
| Environment model boundary docs | [../../../../src/models/environment/README.md](../../../../src/models/environment/README.md)、[../../../../src/README.md](../../../../src/README.md) | 明确把 terrain/environment snapshots 定位为 query models。 | 禁止把这一区域当成 canonical terrain ownership、movement、sensing、fires 或 damage runtime。 |
| Batch setup contracts | [../../../../src/runtime/contracts/world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h) | `WorldTerrainAssignment`、`WorldWindAssignment` 与 `WorldZoneDefinition` 把 global terrain type、global wind 和矩形 surface zones 带入 batch setup。 | contracts 无法保留 branch membership、rich geometry、road class、building height、tree density、wind volume、weather cell、hydrology、dynamic state、provenance 或 per-consumer semantics。 |
| Runtime facade setup | [../../../../src/runtime/facade/runtime_facade_types.h](../../../../src/runtime/facade/runtime_facade_types.h)、[../../../../src/core/engine/world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp) | single-world setup fields 承载 terrain、wind、zones，以及带 `maritime_configured`、sea state、wave heading、wave period 的 global maritime override。 | maritime setup 是 global compatibility override；不是 ocean substrate、wave field、surf model 或 hydrodynamics release。 |
| World setup helper | [../../../../src/core/engine/world_batch_setup_helper.h](../../../../src/core/engine/world_batch_setup_helper.h) | 对 world 应用 terrain assignments、wind、zones、reset seed 和 spawns。 | wind 和 zones 都是 setup fields，不是 branch-aware environment manifest 或 derived-product lifecycle；batch setup 不承载完整 runtime-layout maritime branch surface。 |
| Scenario compiler layout | [../../../../python/scenario/compiler/layout_template.py](../../../../python/scenario/compiler/layout_template.py) | 把 `environment.terrain_type`、`environment.wind`、`environment.maritime` 和 `environment.zones` 编译成 coarse setup fields。 | compiler 只验证自己消费的 shape；还不理解 environment manifest 或 branch registry。 |
| Scenario runtime setup | [../../../../python/scenario/runtime/models.py](../../../../python/scenario/runtime/models.py)、[../../../../python/scenario/runtime/world_setup.py](../../../../python/scenario/runtime/world_setup.py)、[../../../../python/scenario/runtime/kernel_apply.py](../../../../python/scenario/runtime/kernel_apply.py)、[../../../../python/scenario/runtime/batch_apply.py](../../../../python/scenario/runtime/batch_apply.py) | 把编译后的 terrain、wind、zones、spawns、yaw/randomization、maritime fields 和 setup payload 推到 maintained runtime/facade surface。 | runtime setup 能消费 compatibility setup fields，但还不能消费 rich environment manifest；未来没有 fail-closed validators 时，unknown rich branch fields 可能被忽略。 |
| Scenario generation metadata | [../../../../python/scenario/compiler/generation_request.py](../../../../python/scenario/compiler/generation_request.py)、[../../../../python/scenario/compiler/generation_runtime.py](../../../../python/scenario/compiler/generation_runtime.py) | 现有 request/runtime artifacts 已经承载 deterministic seed、generator version、baseline counts、provenance/evidence refs 和 generated scenario data。 | 现有 generation kinds 还不包含 environment-substrate generation，runtime artifact 追踪的是 zone counts，不是 rich manifest provenance。 |
| Terrain query/display consumers | `src/systems/physics/ground_contact_system.h`、`src/systems/visual/visual_system.h`、`src/models/systems/default_sensor_model.cpp`、GPU visual snapshots | 现有系统能消费 terrain elevation、surface/friction hints、runway/off-road cues 和 elevation-only LOS checks。 | 这些是 query primitives 的 consumers；它们不是 shared terrain ownership，也不证明 terrain-aware movement、vegetation/building LOS 或 cover。 |

## 现有机制细节

### C++ Environment Query

- `IEnvironmentModel::TerrainCell` 暴露 `SurfaceType`、elevation、friction、
  roughness、vegetation density 和 runway heading。
- `IEnvironmentModel` 还暴露 atmospheric data、weather attenuation、sun direction、
  wind setup 与 maritime state。
- `DefaultEnvironmentModel` 计算简单 altitude-based atmosphere，weather attenuation
  返回 no-op，暴露 fixed sun vector，并保存 global wind 与 maritime override values。
- `IEnvironmentModel::add_zone()` 接受 name、center、width、length、heading
  和 surface 组成的 rectangle-like zone。
- `DefaultEnvironmentModel` 只从 Concrete、Asphalt、HardPacked、SoftDirt、
  Water、Obstacle 这一小组 enum 生成默认 surface parameters。
- `check_line_of_sight()` 只采样 elevation 和 maritime special case；它不处理
  buildings、vegetation、smoke、tactical concealment 或 cover。

### Scenario And Runtime Projection

- Scenario JSON 当前使用 `environment.terrain_type` 和 `environment.zones`，并有
  `environment.wind` 与 `environment.maritime` 这类 loose setup fields。
- compiler 把 zone `surface` 字符串映射为整数 surface code。
- runtime 可以随着 world yaw 旋转 projected zones，并通过 `WorldZoneDefinition`
  应用它们；wind 映射到 global wind setup；maritime 只映射到 global runtime-layout
  override fields。
- 现有测试覆盖 terrain-type defaults 和 compatibility behavior，但不验证
  rich terrain-substrate semantics、branch registry semantics、weather cells、wind
  volumes、maritime areas、hydrology 或 dynamic environment state。
- shape validation 当前只检查 compiler 直接消费的 object/list 结构。它不验证
  terrain semantics，也不拒绝 unsupported rich terrain fields。
- 一个具体 loose-schema 风险已经存在：当前 compiler/runtime 路径读取 zone 的
  `surface` 字段，但至少一个 generation-runtime fixture 使用 `surface_type`
  字符串。没有 projection validator 时，这类不匹配可能静默退回默认
  SoftDirt-style setup，而不是 fail closed。

## G0 设计后果

- rich environment state 必须作为 manifest 位于当前 zone surface 之上。
- `WorldZoneDefinition` 只能作为有损 compatibility projection target，而不是
  canonical schema。
- terrain 只是第一条被细化的 branch。substrate root 必须为 atmosphere/weather、
  wind、illumination、maritime/ocean、hydrology 与 dynamic environment state 保留
  branch ownership，而不是让 terrain 吞掉这些 concern。
- inventory claims 必须区分“API hook exists”、“setup field exists”和
  “branch/runtime behavior exists”。当前 wind 与 maritime setup 可能影响现有
  consumers，但仍是 compatibility projections，不是 canonical branch ownership。
- environment substrate 内的 terrain branch 应由 air、naval、ground 和未来 domains
  共享。ground 是第一条压力线，不是 schema owner。
- road、forest、building、trench 或 village block 这类 feature label 应是由
  generic components 组合出来的 catalog entries。
- validators 必须显式拒绝 unsupported、misspelled 或 lossy projection semantics；
  当前 loose `environment.zones` 行为对 rich terrain-substrate data 过于宽松。
- 未来 terrain generator 应产出 deterministic manifest 与 provenance，再由
  validators 和 projection 决定什么能进入现有 runtime。
- weather simulation、hydrodynamics、hydrology effects、dynamic environment
  mutation、movement、LOS、cover、sensing、fires、damage 和 combat 继续等待单独的
  derived-product 与 runtime release gates。
