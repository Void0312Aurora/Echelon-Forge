# `src/components/domains/air/tasking` 边界

`components/domains/air/tasking` 保存当前空中任务组织面的 tasking 扩展。这里承载明显属于空中任务面的字段，例如编队、起降、回收以及 CAP/航路语义，而不是跨军种共享语义。

## 允许

- `TaskOrderAir`、`LeaderIntentAir`、`PilotReportAir` 这类空中扩展字段。
- 空中域专用的 tasking 枚举。
- 与编队、站位、跑道、回收、进近相关的纯 DTO 字段。

## 禁止

- 联合层共享枚举和 core 字段；这些进入 `common/`。
- `MissionCommand`、`PilotAction`、`CommandLink` 等 command 对象。
- episode transition、mission runtime、env glue 或控制律逻辑。
- Python binding 和 facade 适配。

## 当前文件

- [air_tasking_enums.h](air_tasking_enums.h)
- [task_order_air.h](task_order_air.h)
- [leader_intent_air.h](leader_intent_air.h)
- [pilot_report_air.h](pilot_report_air.h)

## 依赖方向

本目录可以依赖 `components/tasking/common`。它不应依赖 `core/mission`、`systems/` 或 `interfaces/python`。
