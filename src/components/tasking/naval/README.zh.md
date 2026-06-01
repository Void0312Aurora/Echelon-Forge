# `src/components/tasking/naval` 边界

`components/tasking/naval` 保存舰艇/海上任务组织的 tasking 扩展。这里承载
station type、海上任务角色、command authority 和舰载航空任务组织这类 naval-specific
语义，而不是共享 tasking core 或执行层 command。

## 允许

- 维护中的 `TaskOrderNaval`、`LeaderIntentNaval`、`PilotReportNaval` 扩展字段。
- screen station、warfare role、officer-in-tactical-command、embarked air ops 相关的纯 DTO 语义。
- 对 `common/` 共享 tasking core 的 naval 侧补充，而不把 air 术语直接平移为 ship。

## 禁止

- `MissionCommand`、`PilotAction`、`CommandLink` 等 command 对象；这些进入 `components/command`。
- 舰艇运动、数据链、传感器、舰载机发收舰等 tick/update 逻辑；这些属于 `systems/`。
- mission transition、scenario loader、reward/termination 或 facade 适配。
- 把本目录当作“海军 runtime 已经完整存在”的替代说法。

## 当前状态

当前目录处于 first-stage maintained DTO 阶段：

- 共享/联合层字段应继续落在 `common/*`。
- 已有 air sortie 语义仍留在 `air/*`。
- `TaskOrder`、`LeaderIntent`、`PilotReport` 已有 naval-specific station 与 command-authority owner slice。
- facade/runtime contract 可以传输 naval tasking slice，但 mission execution 仍受下层 runtime owner 边界约束。

这意味着本目录已经是当前主线的正式边界入口，但还不是完整 naval tasking
runtime 的证明。

## 依赖方向

本目录可以依赖 `components/tasking/common`。它不应依赖 `core/mission`、
`systems/`、`runtime/facade` 或 `interfaces/python`。
