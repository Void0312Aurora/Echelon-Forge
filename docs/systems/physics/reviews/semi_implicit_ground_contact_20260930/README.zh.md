# 半隐式地面接触

Document kind: `review`
Lifecycle: `retained`
Canonical: `docs/systems/physics/reviews/semi_implicit_ground_contact_20260930/README.md`
Owner: `systems/physics`
Last verified: `2026-09-30`

状态：`2026-09-30` `implemented / validation green at bounded scope`。`GroundContact`
中的起落架接触改为按下游积分器的步末状态求解，而不是按步初状态显式求解。弹簧阻尼、
Coulomb 摩擦和起落架姿态约束不再限制步长。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- 需求方：[航母打击群交战](../../../../domains/naval/work/active/carrier_strike_group_engagement/README.zh.md)，`S0-D` 残差 (2)
- [梯度真实性原则](../../../standards/gradient_realism_principles.zh.md)
- [物理引擎升级路线图](../../work/issues/physics_engine_roadmap.md)（草案），第 3 阶段"地面接触作为单边约束"
- 代码：`src/systems/physics/ground_contact_system.h`、`src/systems/physics/ground_contact_solver.h`、
  `src/systems/physics/leapfrog_system.h`、`src/systems/physics/rotational_system.h`

## 问题

`GroundContact` 用步初状态计算起落架力，再交给 `RotationalIntegrate` 和
`LeapfrogIntegrate` 显式推进。法向弹簧（k = 2.0e6 N/m，c = 3.5e5 N s/m）对 7–25 t
机体的固有周期约 0.3–0.5 s，显式步长只在约 0.12–0.17 s 以下稳定，而海军场景步长是
0.5 s。在改动前的 `bd64bef6` 构建上实测（零油门、无指令、置于起落架高度 10 s）：

| 机型 | dt 0.05 s | dt 0.2 s | dt 0.5 s |
| --- | --- | --- | --- |
| F/A-18E Block III | 静止（z 1.49–1.59 m） | 抛至 149 m | 抛至 320 m |
| F-16C Block 50 | 静止 | 抛至 669 m | 抛至 713 m |
| MH-60R | 静止 | 抛至 163 m | 发散（z ~ 1e44 m） |
| E-2D | 静止 | 抛至 116 m | 抛至 253 m |

摩擦同样是显式的。tanh 平滑的 Coulomb 律（v_ref 0.5 m/s）和侧偏角轮胎律在低速时都很刚，
大步长下刹停会振荡。0.05 s 下靠两个补丁掩盖：有界的停车保持力，以及速度低于 0.25 m/s
时直接把 `Velocity` 写零。

## 决策

Owner 决策（`2026-09-30`）：替换时间离散方式，同时把平滑摩擦换成集值（精确）Coulomb
摩擦，删除两个低速补丁。

## 机制

`GroundContact` 是积分前最后一个力的产生者，此时 `ForceAccumulator` 已包含本步其余全部
力和力矩。求解器复现下游更新 `v1 = v + h a`、`z1 = z + h v + h^2 a / 2`、
`w1 = w + h tau / I`，求出使接触律在步末成立的接触力。阶段顺序、积分器和可执行图都不变。

| 通道 | 力学律（系数不变） | 离散方式 |
| --- | --- | --- |
| 法向 | 单边 `F = max(0, k p - c v)` | 对步末穿透和下沉速度的闭式解；自由运动预计步末穿透即激活；上限保证接触力本身不会在一步内把机体推离地面 |
| 滚动阻力 | 每轮 Coulomb 线段 `|f_x| <= mu_roll N` | 集值；与原来一样不占摩擦椭圆 |
| 刹车与侧向 | 主轮摩擦椭圆 `(f_x/mu_brake N)^2 + (f_y/mu_lat N)^2 <= 1` | 集值 |
| 轮胎侧偏 | 侧偏刚度 `C_alpha = 18 N/rad per N` | 侧向柔度 `v_lat = -(|v_long| / C_alpha) f_y`，静止时退化为精确粘着 |
| 轮组 | 前轮 +4 m（可转向、不刹车），主轮 -2 m，载荷 20/80 | 每轮在其力集合（缩放坐标下为胶囊形）上求凸 QP，两轮在平面刚体（前、左、偏航）上做块 Gauss-Seidel |
| 俯仰/滚转起落架约束 | 俯仰 10 deg、滚转 2 deg 以外为弹簧，0.01 rad/s 死区以外为阻尼 | 按 `RotationalIntegrate` 的欧拉运动学，对步末角度和角速度逐轴做单调标量求解 |

切向求解满足最大耗散：每个轮力在其可行集上最小化
`0.5 f'(h J M^-1 J' + R) f + (J u_free)' f`，即步末滑移速度落在摩擦集的法锥内的离散条件。

## 验证

本地 Windows MSVC Release（`build-independent-win`）与 HEI Linux gcc 13（`build-hei`），均为改动后：

| 检查 | 改动前（`bd64bef6`） | 改动后 |
| --- | --- | --- |
| `ef_test` | 191 个用例 | 202 / 202，新增 11 个（`ground_contact_solver`、`ground_contact_system`） |
| `ef_composition_evidence_test` | 通过 | 通过（图哈希不变） |
| 停放探针（上表），dt 0.05/0.2/0.5 | 0.2 与 0.5 被抛飞或发散 | 所有机型所有步长均静止；z 距起落架高度 0.1 m 以内；零漂移 |
| HEI `tests/runtime tests/content tests/scenario tests/world_batch tests/architecture/composition` | 1361 通过，1 失败 | 1361 通过，1 失败（同一个仅与环境有关的 `runtime_bootstrap_import_plan_cache` 红） |
| 本地架构守卫、海军、内容、场景 | — | 356 通过，2 失败（WP22 绑定计数红，`bd64bef6` 上相同） |

新增原生测试（期望值来自闭式解或连续律）：

- 7、15、25 t 在 dt 0.05、0.2、0.5 s 下达到静平衡 `m g / k`；
- 以 3 m/s 下落的机体在到达的那一步被接住，不反弹；
- 慢车推力对抗停车刹车，30 s 内零蠕动；
- 全刹以 `(0.8 * 0.8 + 0.02) g` 减速并精确停住，不做速度清零；
- 推力超过滚动阻力时以 `(T - mu_roll N) / m` 加速；
- 持续抬头力矩稳定在 `10 deg + tau / K`，峰值不超过连续律自身的超调（16.8 deg，RK4 参考；俯仰弹簧阻尼很轻，zeta 0.18）；
- 每轮最小化器用可行集上的密网格校核。

Kernel 合约（`tests/contracts/unit/kernel/`，逐文件运行）：

| 合约 | 改动前 | 改动后 |
| --- | --- | --- |
| `action_midpoint_ground_roll` | 通过（IAS 7.48） | 通过（IAS 6.63） |
| `crosswind_track_vs_heading`、`free_fall_idle`、`pilot_pitch_sign_response` | 通过 | 通过 |
| `manual_takeoff` | **失败**（到不了 300 m / 150 m/s） | **通过**（660 步） |
| `pitch_hold_speed_scan`、`pitch_hold_throttle_scan`、`stable_level_flight` | 失败 | 失败，数值相同（纯空中） |
| `takeoff_then_stable_flight`、`repeatability_takeoff_then_stable_flight` | 失败（稳定段 708 步） | 失败（稳定段滚转 29.4 deg） |

两个 takeoff-then-stable 合约改动前后都失败，原因不在地面接触。控制器发送中立杆且
`PilotAction.active` 为真，`pilot_action_requests_manual_takeover` 把 0.05 死区内的杆量视为
不接管，于是由任务自动驾驶飞行。场景指令航向 0 deg，出生航向 90 deg，自动驾驶在整个滑跑中
保持满副翼（追踪确认，从第一步起副翼指令即饱和）。起落架滚转恢复力矩把机翼压在 2 deg 直到
离地，然后飞机滚入指令转弯。只是失败信息变了：隐式滚转约束把机翼稳定在带边，而显式约束会
振荡。这属于 Air owner 的控制源仲裁，见残差。

## 行为变化

- 低速地面动力学由平滑律改为精确 Coulomb。刹车或停放的机体会粘着，外力离开摩擦集时才滑动。
  中点滑跑 IAS 由 7.48 变为 6.63 m/s，因为平滑律在 1 m/s 以下少施加了滚动阻力。
- 首次触地步按预测穿透而非当前穿透激活，不会出现一步结束时已压入起落架却未施力的情况。
- 隐式阻尼为一阶精度。dt 0.05 s 触地的起落架峰值载荷低于连续律（15 t、3 m/s 下沉：4.3 g，
  参考 9.2 g）。`GroundState` 的坠毁分类读取下沉率和速度而非载荷，生命周期结果不变。
- `GroundContact` 不再写 `Velocity`。精确阶段清单的读集新增 `Inertia` 和 `ControlLawState`，
  写集去掉 `Velocity`/`truth.vz`。

## 残差

| 残差 | Owner | 进入条件 |
| --- | --- | --- |
| 甲板接触面：接触只读地形高程，飞机无法停在飞行甲板上 | `systems/physics`，海军提供甲板几何 | `CSG-S2` 甲板循环 |
| takeoff-then-stable 合约：中立杆 `PilotAction` 不从任务自动驾驶接管；场景航向 0 deg 对出生 90 deg 使滑跑中副翼饱和 | Air owner（控制源仲裁） | Air 控制源评审；与接触无关 |
| 起落架系数（k、c、俯仰/滚转 K 与 D、`C_alpha`、20/80 分配、接触点）是固定代理值，未按机型区分 | Air owner，配合平台内容 | unit schema 中的逐机型起落架内容 |
| 未建纵向轮胎滑移（按滑移率的刹车力、防抱死）；刹车为 `0.8 * brake` 的 Coulomb | `systems/physics` | 着陆滑跑真实性工作包 |
| 每个起落架腿只有一个等效接触点且载荷分配固定；无逐腿法向力和俯仰载荷转移 | `systems/physics` | 多点接触工作包（路线图第 3/4 阶段） |
