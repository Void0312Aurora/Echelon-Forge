# 当前 Runtime Gap Audit

状态：`2026-06-16` PF-R2 pass / 只读审计，用于
[README.zh.md](README.zh.md)。

英文辅文：[current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md)。

## 审计边界

本审计只读取当前实现和测试。不修改代码、测试、配置、训练 reward 或生成制品。

主要实现面：

- `src/systems/combat/damage_system_common.h`

主要观察测试：

- `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`
- `tests/runtime/air_combat/test_continuous_rod_surface.py`
- `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py`

## 当前 Runtime 已经做得较好的部分

| Runtime 表面 | 证据 | 为什么有用 |
| --- | --- | --- |
| 引信类型路由 | `damage_resolved_fuze_type` 区分 contact、radar/RF proximity、laser proximity、timed 和 generic proximity。 | 后续 contract 可以按传感器族拆 evidence。 |
| 目标签名 proxy | `damage_fuze_signature_evidence` 记录 `target_rcs_aspect`、`target_projected_geometry` 或 `generic_proximity`。 | 已有位置可承接目标签名证据。 |
| 最近接近事件 | `damage_record_nearest_approach_event` 记录 local point、miss distance、closure 和 aspect bucket。 | 这是很好的诊断事实，应保留。 |
| 引信评估事件 | `damage_record_fuze_evaluation_event` 记录 armed/triggered/failure reason/delay/reliability/sample/trigger radius。 | 事件边界可用，后续可以扩展。 |
| 未起爆不产生活载荷 | 现有测试断言 fuze 未起爆时没有正的 fragment/rod facts。 | 这是任何后续 surrogate 都必须保住的不变量。 |
| contact 与 timed fuze 已拆开 | 现有测试区分 proximity、contact、impact 和 timed 行为。 | 避免所有引信类型都退化为半径门。 |
| 战斗部机制诊断 | 连续杆测试检查 range、local aspect、orientation，以及 non-rod case 不产生 rod facts。 | 下游机制差异已经存在。 |

## 核心 Proxy 缺口

| 缺口 | 当前行为 | 为什么不够 | 后续 surrogate 方向 |
| --- | --- | --- | --- |
| 最近点支配起爆几何 | `damage_effective_detonation_world_point` 在非 contact、非 timed 的 proximity 事件中优先使用 `proximity_min_local_*`。 | 公开机制说明 closest approach 是诊断点，不一定是优选 burst point。 | 保留 nearest approach 作为观察事实，但用 sensor window、closing state、delay 和 mechanism coverage 计算起爆点。 |
| trigger radius 是主门 | runtime 用 `detonation_metric_m` 或 `min_dist` 对比 `trigger_radius_m` / `fuse_distance`。 | 更真实的近炸取决于目标探测和 lethal burst opportunity，不只是中心距离。 | 新增 sensor-opportunity gate，包含目标表面/投影、传感器族、range window、crossing state 和 terminal-track evidence。 |
| quality 基本是线性距离余量 | proximity case 用 `quality = 1 - distance / trigger_radius`。 | 这会让很多 case 差异较弱，也容易遮蔽方位/高度/机制效应。 | 把它降级为多因素 opportunity score 的一个输入。 |
| 概率底座是硬编码 | proximity `base_hit = 0.35 + 0.65 * quality`。 | 这解释了近炸概率底座，也会让近距离结果低或平坦，但原因不可解释。 | 将概率拆到 detection/trigger/reliability 阶段；不保留无解释 floor。 |
| 签名影响 reliability，而不是 detection state | radar/laser signature 在 range gate 后缩放 effective reliability。 | 目标探测 surrogate 应该能在 trigger 前失败，而不是只降低最终概率。 | 输出 `fuze_detection_event` 或等价字段：detected、source、signature、threshold proxy、reason。 |
| terminal guidance support 是偏晚的二值 veto | `proximity_fuze_has_terminal_guidance_support` 可在 range-quality 之后拦截。 | track validity 应作为 sensor/target opportunity 的可见部分，不应是隐藏后置否决。 | 在 trigger 前记录 terminal-track state 和 reasoned no-detonation outcomes。 |
| delay 被记录，但不独立选择 burst opportunity | 当前 delay 在 trigger 后应用；proximity 起爆点仍倾向来自最近 local point。 | 公开机制把 delay 描述为从首次目标探测走向更有用起爆点的一部分。 | proximity fuze 的 delay 应关联沿导弹轨迹或局部传感器几何预测的起爆点。 |
| Blast-fragmentation 与 continuous rod 共用 fuze gate | fuze trigger path 不随战斗部机制变化，机制差异主要在起爆后出现。 | useful burst interval 依赖机制几何；连续杆和方向性破片带不应共享完全相同 opportunity test。 | 在 detection 后、最终 detonation 前加入机制覆盖检查，或至少记录 coverage confidence。 |
| 目标中心/命中盒距离可能主导几何 | proximity range 使用当前距离路径；contact 有 surface evidence，但 proximity 默认还未消费 retained fine geometry。 | 对大飞机，中心距离会误读机翼、机鼻或上下掠过。 | 以 opt-in 输入使用目标表面/投影几何，默认路径替换单独验收。 |

## 需要保留的当前测试覆盖

| 测试行为 | 保留 | 扩展 |
| --- | --- | --- |
| Radar proximity delay 记录 fuze 和 effects events | yes | 增加 detection/trigger 子 reason 和 detonation-point source。 |
| Reliability failure 记录 no-detonation 且没有正载荷 | yes | 区分 detection failure 和 trigger/reliability failure。 |
| Contact fuze 不因 near-miss radius 触发 | yes | 确保 proximity-specific surface logic 不破坏 contact 语义。 |
| Timed fuze 独立于 proximity gate 起爆 | yes | timed path 保持在 sensor window logic 之外。 |
| 连续杆 margin 随 range/aspect/orientation 变化 | yes | 增加尊重 rod cutting band 的 fuze opportunity 检查。 |
| Non-rod 和 no-detonation 不带 rod facts | yes | 新 fuze failure mode 后仍保留 no-load invariant。 |

## 审计结论

当前 runtime 有不错的解释性骨架，但触发逻辑仍是最近距离 proxy。下一步设计不应丢掉事件链，
而应在 nearest approach 和 effects 之间插入明确的 sensor-opportunity / detection / trigger /
burst-timing 层。

PF-R2 已作为只读 gap audit 完成。Implementation 仍 held。
