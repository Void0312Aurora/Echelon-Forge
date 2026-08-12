# radar / laser / contact / timed 放行证据清单

状态：`2026-05-28` 计划/标准文档。本文列出 future P4 admission 所需证据清单；它不是已完成证据，不代表 deterministic fuze 已放行。

## 通用证据

所有 fuze type 都必须先满足通用证据：

- 独立 `a2.fuze_authority.v1` manifest 已通过；
- weapon / fuze / warhead profile 版本固定且可追溯；
- target geometry、target signature 和 aircraft component geometry 版本固定；
- time-step policy、backend profile、event ordering 和 delayed detonation scheduling 已固定；
- `nearest_approach_time_s`、`detonation_time_s`、`miss_distance_m`、起爆点、导弹速度轴、引爆姿态、target local coordinates 可回放；
- false trigger、missed trigger、delay error、detonation point error 有量化验收门槛；
- deterministic replay 能在固定 seed、固定 backend、固定 dt 下复现 fuze event 序列；
- admission 明确 scope，不覆盖未验证 weapon / target / aspect / closure / environment。

## radar proximity fuze

当前状态：已有 target-signature proxy 和 event 字段，未校准，不能放行。

放行前必须补齐：

- 目标 RCS / aspect / range / closure 的可追溯数据或验证 surrogate；
- 雷达近炸触发门限、接收链路、SNR 或等价信号尺度；
- 目标姿态、机体系局部几何、遮蔽和多路径敏感性说明；
- 搜索 / 解除保险 / 近炸触发窗口的时间逻辑；
- false trigger 与 missed trigger 门槛；
- delay distribution 或 deterministic delay policy；
- clutter / ground / chaff / multi-target 不在 scope 时的显式排除；
- event 中必须记录 `fuze_signature_source=radar_rcs_*` 或等价校准来源、`fuze_target_signature`、`fuze_signature_scale`、`fuze_effective_reliability`、trigger threshold ref 和 evidence ref；
- replay cases 必须覆盖 head-on、tail-chase、beam、high-off-boresight、low-RCS aspect、high-closure near miss、out-of-scope target。

最小 admission 不得使用 `engineering_rcs_proxy` 或 synthetic RCS fixture 授权。

## laser proximity fuze

当前状态：已有 hitbox 投影几何 proxy 和 event 字段，未校准，不能放行。

放行前必须补齐：

- 目标反射率 / 投影面积 / aspect 的可追溯数据或验证 surrogate；
- laser / optical proximity gate 的触发门限、束形、距离窗口和采样频率；
- 姿态、表面材料、遮蔽、太阳角或环境可见性对触发的 scope 声明；
- false trigger、missed trigger、delay error 门槛；
- event 中必须记录 `fuze_signature_source=laser_reflectance_*` 或等价校准来源、目标投影尺度、trigger threshold ref 和 evidence ref；
- replay cases 必须覆盖大投影侧向、小投影首尾向、高角速度穿越、边缘擦过、低反射目标、远离 hitbox 的 no-trigger。

最小 admission 不能只用 hitbox projected area 授权，除非该几何 proxy 已在 manifest 中被验证并限定 scope。

## contact / impact fuze

当前状态：已防止 near-miss radius 误触发，并记录 surface distance / penetration depth / inside-hitbox；未建模接触物理和失效模式，不能放行。

放行前必须补齐：

- authored hitbox surface 与 component surface 的几何精度标准；
- impact point、surface normal、入射角、相对速度和穿入深度的稳定计算；
- fuze arming / safe separation / graze angle / dud 条件；
- 接触持续时间、穿入后延迟或 instant detonation policy；
- 目标材料 / 结构层级 / 外壳厚度对触发的 scope 声明；
- false contact、tunneling、time-step overshoot 的检测和补偿；
- event 中必须记录 surface distance、penetration depth、surface tolerance、inside-hitbox、impact normal、impact angle、arming state、contact evidence ref；
- replay cases 必须覆盖 direct nose hit、wing graze、component hit、near miss within old radius but no contact、high-speed pass-through、delayed impact detonation。

contact / impact admission 不能借用 proximity miss-distance bucket 授权。

## timed fuze

当前状态：可按 `delay_s` 独立起爆，未校准战术装定、漂移和安全约束，不能放行。

放行前必须补齐：

- timed setting 来源：预设、发射前装定、任务策略或 fire-control 解算；
- delay accuracy、clock drift、arming delay、safe separation 和 self-destruct policy；
- delay 与 expected intercept time / range gate 的关系；
- 未命中、越过目标、远离目标起爆时的 no-effect / limited-effect policy；
- event 中必须记录 setting source、commanded delay、actual delay、drift model ref、arming state、detonation reason、evidence ref；
- replay cases 必须覆盖 on-time intercept、early detonation、late detonation、no target in footprint、safe separation not met、multi-step replay exactness。

timed fuze admission 不能只凭 `delay_s` 字段存在授权。

## 证据最小集判定

P4 admission 的最小证据集必须包括：

- 一份 admitted fuze authority manifest；
- 每个目标 fuze type 的触发门限证据；
- 每个目标 fuze type 的 false / missed trigger 验收；
- delay / scheduling 验收；
- deterministic replay 验收；
- scope 外回退策略；
- revocation policy；
- residual risk 签核。

任何一项缺失，结论保持 `deferred`。
