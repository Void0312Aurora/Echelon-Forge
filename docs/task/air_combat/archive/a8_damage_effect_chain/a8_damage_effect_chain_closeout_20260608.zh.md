# A8 损伤效果链收口 2026-06-08

状态：`已按 accepted with deferred residuals 归档`。

## 决定

将 A8 作为有边界损伤效果链切片的 sealed evidence package 归档。

accepted claim 有意保持窄口径：

- 公开射击行暴露具体 synthetic failure modes；
- 固定 MQ-9/AIM-120C-like 样例能解释从起爆到受损部位再到维护中系统响应的路径；
- 动力、翼面/操纵气动、燃油/泄漏/质量、更完整火灾、数据链任务/传感器下降，以及原实体
  地面接触生命周期可观察性都有聚焦证据覆盖；
- 本包不声明校准武器真值、真实世界 Pk、确定性引信真值、stock AIM-120C/MQ-9 杀伤结论，
  也不接受一等碎片/残留对象。

## 保留证据

- 当前状态与验证记录：
  [a8_damage_effect_chain_current_status_20260607.zh.md](a8_damage_effect_chain_current_status_20260607.zh.md)
- dispatch 与 P6 验收记录：
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- 任务簇：
  [a8_damage_effect_chain_task_clusters_20260607.zh.md](a8_damage_effect_chain_task_clusters_20260607.zh.md)

## 继续 held 的残余

- 校准级战斗部、火灾和目标脆弱性真值未验收。
- 飞机专用飞控律保真未验收。
- 平台族扩展未验收。
- 真实世界 Pk、引信与 stock 杀伤权威继续拒绝。
- 一等碎片/残留对象后置；本切片只接受原实体 `landed_airframe` / `crashed_wreck`
  可观察性。

## 归档动作

将本包移动到 `docs/task/air_combat/archive/` 下，并在原
`docs/task/air_combat/a8_damage_effect_chain/` 路径留下 pointer README。
