# `src/components/tasking/common` 边界

`components/tasking/common` 保存跨军种共享的 tasking/C2 基础结构。这里定义
联合层或通用任务组织语义，不直接携带 air 或 naval 的平台专用字段。

## 允许

- `ServiceProfile`、`TaskFamily`、`CoordinationMode` 等共通枚举。
- `TaskOrderCore`、`LeaderIntentCore`、`PilotReportCore` 这类共享字段壳。
- 可被 `air/`、`naval/` 继续扩展的通用任务/意图/回报字段。

## 禁止

- runway、approach、wingman、element、station pattern 等 air-specific 字段。
- future naval station/warfare commander 这类 naval-specific 字段。
- `MissionCommand`、`PilotAction`、`CommandLink` 等 command 层对象。
- mission transition、JSON codec、reward/termination 逻辑。

## 当前文件

- [core_tasking_enums.h](/home/void0312/Workshop/CMO/src/components/tasking/common/core_tasking_enums.h)
- [task_order_core.h](/home/void0312/Workshop/CMO/src/components/tasking/common/task_order_core.h)
- [leader_intent_core.h](/home/void0312/Workshop/CMO/src/components/tasking/common/leader_intent_core.h)
- [pilot_report_core.h](/home/void0312/Workshop/CMO/src/components/tasking/common/pilot_report_core.h)

## 依赖方向

本目录应保持为数据层。`air/` 与 `naval/` 只能向下复用这里的 core 定义；
这里不应反向依赖具体军种子域。
