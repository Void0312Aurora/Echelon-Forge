# 长机/指挥指令标准 (Mission Command Standard)

> Scope note (2026-03-23): 本文档是 `air specialization`，描述 air profile 下
> `Tactical Intent / Execution Command` 的专用语义，不再作为全项目通用核心标准。
> 当前标准化主基线请先看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)、
> [docs/standards/joint/command_and_modeling_baseline.md](/home/void0312/CMO/docs/standards/joint/command_and_modeling_baseline.md)、
> [docs/standards/services/air_force.md](/home/void0312/CMO/docs/standards/services/air_force.md)。

本文档定义了“长机” (Lead Aircraft) 或“指挥层”下达给“僚机/数字飞行员”的指令规范。这些指令是高度抽象的战术目标，数字飞行员（RL Agent）的任务是将这些抽象目标通过 [act.md](./act.md) 中的操作转化为飞机的物理运动。

在新的标准体系中：

- joint/common core 只定义 `intent / order / report` 的共通骨架
- 本文档只定义 air profile 下这些对象如何具体化
- `CAP`、`runway approach`、`wingman formation` 都属于 air-specific 语义

## 1. 基础引导指令 (Core Vectoring)
最直接的参数化指令，用于定义期望的飞行状态。

| 变量名 | 说明 | 物理单位 | 备注 |
| :--- | :--- | :--- | :--- |
| `cmd_heading` | 目标航向 | 度 (deg) | 0-360, 磁航向或真航向 |
| `cmd_alt` | 目标高度 | 米 (m) | 通常为 MSL (海平面高度) |
| `cmd_speed` | 目标速度 | 当前实现为米每秒 (m/s) | 现实抽象上可对应 IAS / TAS / Mach，但仓内 flight-task 训练目前统一使用 m/s |
| `cmd_vvi` | 目标升降率 | m/s | 可选，用于精确控制爬升/下降曲线 |

## 2. 任务状态/宏指令 (Procedural/Macro Commands)
定义当前的任务阶段，暗示了综合性的行为模式。

| 指令代码 | 语义说明 | 典型参数配置 |
| :--- | :--- | :--- |
| `CODE_IDLE` | 地面静态/等待指令 | Speed=0, Alt=Ground |
| `CODE_TAKEOFF` | 起飞指令 | Heading=Rwy, Speed=V2, Alt=Initial |
| `CODE_CRUISE` | 航向-高度-速度矢量引导 | Heading/Alt/Speed |
| `CODE_ROUTE_NAV` | 航路/航点导航 | Steerpoint Sequence, LNAV |
| `CODE_LAND` | 着陆指令 | Heading=Rwy, Alt=GlideSlope, Speed=Vref |
| `CODE_ORBIT` | 盘旋等待 | ReferenceCoord, Radius |
| `CODE_RTB` | 返回基地 | HomeBaseID |

> 当前仓内实现说明：现阶段单机飞行训练实际采用的数值约定为
> `0=Idle`、`1=Takeoff`、`2=Vector/Cruise`、`3=Waypoint/LNAV Route Navigation`、`4=Landing/Final`。
> 其中，`command_code=3` 代表“按 steerpoint 序列执行航路导航”，
> `command_code=4` 代表“跑道对正的进近/着陆任务”。
> 着陆任务的纵向路径不是通过 privileged 跑道几何直接下发，而是通过观测中的
> `ILS` 风格产品（`loc_dev / gs_dev / dme`）提供。

## 3. 编队控制指令 (Formation Controls)
在多机协同中，定义与长机的相对空间关系。

| 变量名 | 说明 | 物理单位 | 备注 |
| :--- | :--- | :--- | :--- |
| `form_pos_id` | 编队阵位 ID | 整数 | 线阵、梯队、楔形等 |
| `form_offset_x` | 相对长机的前后偏移 | 米 (m) | |
| `form_offset_y` | 相对长机的左右偏移 | 米 (m) | |
| `form_offset_z` | 相对长机的高低偏移 | 米 (m) | |

## 4. 战术意图指令 (Tactical Intent)
定义空战行为的优先级。

| 变量名 | 说明 | 取值范围 | 备注 |
| :--- | :--- | :--- | :--- |
| `tac_target_id` | 指定分配目标 ID | 实体 ID | 告诉 AI “那是你的目标” |
| `tac_engagement` | 交战授权 | {HOLD, COVER, ENGAGE} | 是否允许发射武器 |
| `tac_jettison` | 强制抛单指令 | 触发式 | 应对高过载或燃油紧急情况 |

## 5. 典型任务翻译方案 (Case Studies)

### 场景 A：起飞 (Takeoff)
当指挥层下达 `CODE_TAKEOFF` 时，指令流将由以下数据组成：
*   `cmd_heading`: 当前跑道航向 (例: 090)。
*   `cmd_alt`: 初始离地高度 (例: 1000m)。
*   `cmd_speed`: 预定爬升速度 (例: 250kts)。
*   **AI 任务**: 在观察到这些指令后，通过操作杆和油门，在滑跑中保持 090 航向，达到抬头速度后拉杆，并收起落架，直到达成目标。

### 场景 B：战术巡航 (Cruise)
当指挥层下达 `CODE_CRUISE` 时：
*   `cmd_heading`: 巡航航线方位。
*   `cmd_alt`: 巡航层高度 (例: 8000m)。
*   `cmd_speed`: 巡航经济马赫数 (例: 0.7M)。
*   **AI 任务**: 平滑爬升至指定高度，调整油门以维持马赫数。

### 场景 C：航路导航 (Route Navigation)
当指挥层下达 `CODE_ROUTE_NAV` 时：
*   `cmd_heading`: 当前主动航段的期望地面航迹 bug，而不是“直飞某个点的瞬时方位”。
*   `cmd_alt`: 当前主动航点或航段的目标高度。
*   `cmd_speed`: 当前主动航点或航段的目标速度。
*   `附加导航产品`: steerpoint 序号、到主动航点距离、相对方位、CDI/XTK、下一个转弯角/转弯距离。
*   **AI 任务**: 依据 LNAV/EGI 风格导航产品完成航路跟踪、转弯提前量控制和分段高度/速度约束。

### 场景 D：着陆 (Landing / Final)
当指挥层下达 `CODE_LAND` 时：
*   `cmd_heading`: 跑道最后进近航向。
*   `cmd_alt`: 跑道参考高度/着陆参考高度。
*   `cmd_speed`: 进近参考速度。
*   `附加仪表产品`: `ILS` 局道偏差、下滑道偏差、DME。
*   **AI 任务**: 截获局道和下滑道，稳定速度与姿态，在跑道内完成接地与减速。

## 6. 标准化意义
1.  **解耦决策与执行**: 长机层只管“去哪/干什么”，飞行员层（RL）只管“怎么飞”。
2.  **Transformer 训练优势**: AI 将 `cmd_*` 序列与自身的 `alt/speed` 序列进行 Cross-Attention，能更快地学会“追踪”和“达成”指令目标的隐含物理逻辑。
