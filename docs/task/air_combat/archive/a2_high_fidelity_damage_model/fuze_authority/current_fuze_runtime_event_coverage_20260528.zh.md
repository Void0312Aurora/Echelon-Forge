# 当前 fuze runtime/event 覆盖与 deferred 原因

状态：`2026-05-28` 计划/标准文档。本文只记录当前 A2 fuze runtime/event 覆盖和 Phase 4 仍 deferred 的原因，不代表 deterministic fuze 已放行。

## 当前已覆盖的 runtime 面

当前实现已经把 fuze 从隐式 proximity radius 推进到显式 `FuzeProfile` 数据面：

- weapon JSON 可声明 fuze `type`、`trigger_radius_m`、`delay_s`、`reliability` 和 provenance；
- loader 会规范化 `radar_proximity`、`laser_proximity`、`proximity`、`contact` / `impact`、`timed` 等类型；
- `MissileTuning` / runtime `Missile` 携带 fuze profile；
- 缺少显式 fuze profile 的旧 weapon 数据可由兼容层生成 synthetic fuze profile，并在事件中保留 synthetic 标记；
- proximity 类触发半径来自 `FuzeProfile.trigger_radius_m`；
- `FuzeProfile.reliability` 和 target-signature proxy 会调制当前有效引信可靠度，但现阶段仍通过既有随机 gate 结算。

当前实现还具备最小触发语义分支：

- `proximity` / `radar_proximity` / `laser_proximity`：按近炸触发半径工作；
- `radar_proximity`：消费目标 RCS / aspect 代理，形成 `fuze_signature_scale` 和 `fuze_effective_reliability`；
- `laser_proximity`：消费目标 hitbox 投影几何代理，形成 `fuze_signature_scale` 和 `fuze_effective_reliability`；
- `contact` / `impact`：不再把 near-miss radius 当作接触触发，要求进入 authored hitbox 表面接触容差；
- `timed`：按发射后 `delay_s` 独立调度起爆，不依赖近炸门。

## 当前已覆盖的 event 面

`EffectsEvent` 已能审计下列 fuze 和几何字段：

- `fuze_type`
- `fuze_trigger_radius_m`
- `fuze_delay_s`
- `fuze_reliability`
- `fuze_profile_synthetic`
- `fuze_signature_source`
- `fuze_target_signature`
- `fuze_signature_scale`
- `fuze_effective_reliability`
- `fuze_contact_surface_distance_m`
- `fuze_contact_penetration_depth_m`
- `fuze_contact_surface_tolerance_m`
- `fuze_contact_inside_hitbox`
- `nearest_approach_time_s`
- `detonation_time_s`
- `miss_distance_m`
- 目标机体系起爆点、闭合速度、导弹速度轴、引爆姿态和 warhead orientation evidence。

这些字段足以做回放审计和准入诊断，但还不足以放行 deterministic fuze。

## 当前测试覆盖的意图

当前回归大致覆盖以下行为边界：

- live missile proximity fuze 能记录 `EffectsEvent` / `DamageReport`；
- debug runtime 可暴露 proximity minimum distance state；
- PN miss-distance baseline 能区分 head-on、tail-chase、beam、high-off-boresight 等几何；
- fuze delay 能让 `detonation_time_s` 晚于 `nearest_approach_time_s`；
- contact fuze 不由 near-miss radius 误触发；
- contact / impact event 能记录 surface distance、penetration depth、inside-hitbox；
- timed fuze 能在未进入 proximity gate 时按 delay 生成可审计 event；
- vulnerability evidence gate 能阻止 synthetic profile、未授权 descriptor 或 JSON 自声明误提升为 Pk / deterministic-fuze authority。

这些测试是 P4 的输入证据，不是 P4 admission 结果。

## 为什么仍 deferred

P4 仍 deferred，原因不是“没有 fuze 字段”，而是缺少可授权的引信杀伤链证据：

- 当前 proximity fuze 仍在最近点后一帧触发，`closure_mps` 在事件时可合法为 0，不能单独证明触发时序精确；
- radar / laser signature 仍是 RCS、aspect 或投影几何代理，没有校准 seeker / fuze receiver 模型、门限、噪声、遮蔽、目标姿态和反射材料证据；
- contact / impact 只具备 hitbox 表面容差和穿入深度诊断，还没有结构表面材料、入射角、接触持续时间、保险/解除保险、穿入延迟和失效模式模型；
- timed fuze 只按 `delay_s` 起爆，没有战术设定来源、装定误差、漂移、安全窗口和任务约束证据；
- `FuzeProfile.reliability` 还不是经验证的失效率 / 误触发 / 漏触发模型；
- warhead footprint、target vulnerability、component failure probability 与 fuze trigger 的联合校准尚未闭合；
- evasion 影响仍部分通过随机 gate 和命中概率保留，不能在没有替代机制前移除；
- 当前 vulnerability descriptor 明确不是 fuze authority，不得混用其 schema 或 manifest；
- fixed-fire smoke 只能证明发射链路和运行稳定性，不能证明单发必然 `combat_win`。

## 当前 P4 放行结论

结论：`deterministic_fuze_authority` 必须保持 `false` / `not_admitted`。

只有当独立 fuze authority manifest 通过、四类 fuze evidence 覆盖相应适用域、replay/admission matrix 全部满足门槛，并完成残余风险签核后，才允许对一个窄域 weapon / target / aspect / closure / environment scope 申请 deterministic fuze admission。
