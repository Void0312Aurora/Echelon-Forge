# `src/components/tasking` 边界

`components/tasking` 是编队、任务分配、leader intent、pilot report 和 C2 状态 DTO 的归属目录。它描述“意图与任务状态”，不描述底层动作如何被物理系统执行。

当前目录边界已经把 tasking 和 command 分开。维护中的形态是 common C2/tasking
foundation 加 air/naval/ground extensions：`common` 承载共享语义，`air`
承载成熟的空中任务组织面，`naval` 承载第一阶段海上 tasking slice，`ground`
承载第一版正式 G0/G1 tasking/status 边界。

## 允许

- 跨域共享的 tasking/C2 基础枚举与 DTO，例如 authority、relationship、service、task family、coordination 这类语义。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 这类任务状态对象，以及它们的 `common` / `air` / `naval` 分层版本。
- 可被 mission runtime、facade、Python binding 读写的轻量任务状态。

## 禁止

- `PilotAction`、`MissionCommand`、`CommandLink` 和 legacy movement/action command；这些进入 `components/command`。
- waypoint transition、landing transition 或任务 JSON 解释逻辑；这些属于 `core/mission`。
- 物理控制、传感器、武器、数据链 tick 逻辑。
- Python binding 代码。

## 拆分方向

- `common tasking` 放跨域共享语义：例如 C2/authority/relationship、task family、通用 assignee 或 coordination 元数据。
- `air tasking` 放当前明显航空化的语义：例如 CAP、起降、跑道、编队、wingman、approach/recovery。
- `naval tasking` 保存当前舰艇/海上 tasking slice：naval station type、warfare role、officer-in-tactical-command owner 字段。不应直接复用 air 的 runway/formation/recovery 命名。
- `ground tasking` 现在是窄 C++ component owner slice，只覆盖 G0/G1
  status/schema 证据。不要为了绕开未来 ground schema，把 land movement、
  sensing、fires、damage 或 terrain-control 语义塞进泛化 `common` 字段。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 比 `MissionCommand` 更适合先做文档和类型层拆分，因为它们当前更多是 DTO/API 面，而不是高耦合飞控执行面。

## 依赖方向

tasking DTO 位于数据层。`core/mission` 可以解释它，`systems/` 可以消费它，`runtime/facade` 可以批量设置和导出它，但它不能依赖这些上层。

## 迁移备注

已落地：

- `air/air_tasking_enums.h`
- `naval/naval_tasking_enums.h`
- `tasking_enums.h`
- `task_order.h`
- `leader_intent.h`
- `pilot_report.h`
- task order、leader intent、pilot report 的 `common/*`、`air/*`、`naval/*` owner slice。
- `ground/*` owner slice 只覆盖 G0/G1 static status 与 native schema boundary
  evidence。

WP0 文档口径：

- 先识别哪些字段/枚举应下沉到 `common`。
- 再把 air 特有语义从共享 DTO 中分离出来。
- naval 侧单独建模，并已有有限的维护中 tasking slice；不沿用 “ship = air but on water” 的拆分方式。
- ground-aware setup 通过 unit type/capability evidence 与 `ground/*`
  tasking/status owner slice 表达；维护中的 ground movement、observation/action
  packet 与 combat runtime 仍保持 held。
- `tasking_enums.h` 作为兼容 umbrella 保留，新代码应优先显式依赖 `common/core_tasking_enums.h`、`air/air_tasking_enums.h` 或 `naval/naval_tasking_enums.h`。

`MissionCommand` 虽然和 tasking 强相关，但它属于 command 侧，而且是后续高风险拆分项：它已经连到执行 episode、mission runtime、控制律和观测链路，WP0 先明确方向，不在 tasking 文档里把它描述成可立即安全拆出的对象。

旧 `components/physics/action.h` 已降级为 compatibility umbrella include。新代码应 include 具体头文件。
