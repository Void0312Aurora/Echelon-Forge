<!-- Machine-translated draft generated on 2026-05-18 from src/components/tasking/air/README.md. Review before treating this file as authoritative. -->

# `src/components/tasking/air` 边界

`components/tasking/air` 保存当前空中任务组织的 tasking 扩展。这里承载编队、
起降、回收、CAP/航路等明显属于 air 任务面的字段，而不是跨军种共享语义。

## 允许

- `TaskOrderAir`、`LeaderIntentAir`、`PilotReportAir` 这类 air 扩展字段。
- air-specific tasking enum。
- 编队、站位、跑道、回收、approach 相关的纯 DTO 字段。

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

本目录可以依赖 `components/tasking/common`。它不应依赖 `core/mission`、
`systems/` 或 `interfaces/python`。
