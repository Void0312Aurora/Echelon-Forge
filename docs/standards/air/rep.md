# 飞行员汇报标准 (Pilot Reporting Standard)

> Scope note (2026-03-23): 本文档是 `air specialization`，描述 air profile 下的平台与战术汇报语义。
> 当前标准化主基线请先看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)、
> [docs/standards/joint/command_and_modeling_baseline.md](/home/void0312/Workshop/CMO/docs/standards/joint/command_and_modeling_baseline.md)、
> [docs/standards/services/air_force.md](/home/void0312/Workshop/CMO/docs/standards/services/air_force.md)。

本文档定义了“僚机/数字飞行员”向“长机/指挥层”上报信息的规范。这是双向战术链路的重要组成部分，使指挥层能够根据各机的实时状态、观测发现和任务进度调整战术。

在新的标准体系中：

- joint/common core 负责共通 reporting 骨架
- 本文档只负责 air profile 的具体汇报语义
- 这里的 brevity / wingman / RTB 口径不应直接推广到 sea/land

## 1. 指令确认 (Command Acknowledgment)
对长机指令的基本反馈。

| 报告代码 | 语义说明 | 备注 |
| :--- | :--- | :--- |
| `REP_WILCO` | 收到指令，将执行 (Will Comply) | 指令生效确认 |
| `REP_ROGER` | 收到信息 (Received) | 仅确认收到信息，不代表执行 |
| `REP_UNABLE` | 无法执行指令 | 通常伴随原因（如：燃油不足、过载过大） |
| `REP_CANT_DO` | 虽然收到，但由于机体限制无法达成 | 例如：要求速度 2.0M 但飞机无法达到 |

## 2. 机体状态报告 (Status Report)
定期或应答式的自身情况汇总。

| 变量名 | 说明 | 数据类型 | 备注 |
| :--- | :--- | :--- | :--- |
| `status_fuel` | 状态油量代码 | {Joker, Bingo, State} | Joker: 需撤出; Bingo: 必须返航; State: 具体读数 |
| `status_ammo` | 弹药余量状态 | {Winchester, Remington, State} | Winchester: 弹药耗尽; Remington: 仅剩少量自卫 |
| `status_damage` | 机体受损程度 | 0.0 (完好) - 1.0 (毁伤/不可控) | 基于 Health/System 损毁 |
| `status_pos` | 当前坐标上报 | {x, y, z} | 自动同步或应答同步 |

## 3. 战术动态汇报 (Tactical/Brevity Reports)
模拟空战术语（Brevity Codes）的数据化表达。

| 报告代码 | 说明 | 对应参数 | 备注 |
| :--- | :--- | :--- | :--- |
| `REP_TALLY` | 发现敌方目标 (目视) | `target_id`, `pos` | 目标确认为敌对 |
| `REP_VISUAL` | 发现友方目标 (目视) | `target_id`, `pos` | 确认长机或其他僚机位置 |
| `REP_BLIND` | 丢失目标目视/雷达接触 | `target_id` | 提醒编队注意 |
| `REP_SPIKE` | 受到敌方雷达持续锁定 | `threat_type`, `azimuth` | 来自 RWR 的告警 |
| `REP_ENGAGED` | 正在交战 | `target_id` | 告知长机自己已进入格斗/攻击状态 |
| `REP_SPLASH` | 成功击落目标 | `target_id` | 空对空确认 |
| `REP_DEFENDING` | 正在规避威胁 | `threat_type` | 告知我方正在进行防御机动 |

## 4. 任务进度报告 (Mission Progress)
关于 [aim.md](/home/void0312/Workshop/CMO/docs/standards/air/aim.md) 中宏指令的完成情况。

| 报告代码 | 说明 | 备注 |
| :--- | :--- | :--- |
| `REP_ON_STATION` | 已到达指定区域/阵位 | 编队集合完成或巡航到达 |
| `REP_FENCE_IN` | 准备进入战区 | 所有武器/传感器状态就绪检查完毕 |
| `REP_FENCE_OUT` | 离开战区 | 任务完成，返回基地的阶段性反馈 |
| `REP_RTB` | 正在返航 | 最终确认 |

## 5. 紧急情况报告 (Emergency/Warning)
非计划中的突发状况。

| 变量名 | 说明 | 备注 |
| :--- | :--- | :--- |
| `warn_flameout` | 发动机熄火告警 | 燃油耗尽或损毁 |
| `warn_bingo` | 到达返航油量线 | 强制提醒长机 |
| `warn_missile_launch` | 侦测到敌方导弹发射 | 极高优先级提醒 |

## 6. 标准化意义
1.  **闭环指挥**: 长机下达指令 ([aim.md](/home/void0312/Workshop/CMO/docs/standards/air/aim.md))，僚机反馈结果 ([rep.md](/home/void0312/Workshop/CMO/docs/standards/air/rep.md))，形成闭环。
2.  **多智能体协作 (MARL)**: 在多机训练中，这些报告是 Transformer 学习“协同”的关键输入。长机 Agent 会根据僚机的反馈来调整后续的战术分工。
3.  **日志与分析**: 所有的汇报内容都作为 Time-stamped Log 记录，极大方便了训练后的复盘与可视化。
