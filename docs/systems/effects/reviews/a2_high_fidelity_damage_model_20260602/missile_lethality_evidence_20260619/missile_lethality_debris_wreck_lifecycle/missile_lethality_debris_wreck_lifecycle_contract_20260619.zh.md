# MLF-8 生命周期契约

状态：`2026-06-19`，基础 MLF-8 生命周期切片的 P2 contract-pass。本页验收下一步
实现所需契约，但尚未验收 runtime 行为。

英文规范页：
[missile_lethality_debris_wreck_lifecycle_contract_20260619.md](missile_lethality_debris_wreck_lifecycle_contract_20260619.md)。

## 契约边界

MLF-8 可以把已验收的结构断裂和终端生命周期事实转成诊断生命周期记录。默认情况下，
不得把这些记录升级为校准碎片物理、Pk 或 reward 权威。

基础切片刻意保持很薄：使用 `LifecycleTransitionEvent`，不写一等 wreck/debris ECS
实体，所有 MLF-8 行在后续 authority-promotion 明确改变 consumer visibility 前都保持
`diagnostics_only`。

## P2 决策

| 决策 | 已接受答案 | 原因 |
| --- | --- | --- |
| 事件载体 | 基础切片使用现有 `LifecycleTransitionEvent`。 | DTO、Python 绑定、facade packet 和 recent-event packet storage 都已经存在。 |
| 新 ECS debris/wreck component | 基础切片不新增。 | MLF-8 先做生命周期账本，不做一等碎片物理。 |
| 脱落部件表达 | 每个新的 `StructuralBreakupEvent` 写一条聚合 lifecycle 行。 | MLF-6 每个新脱落结构组会发一条 structural event；父事件已经携带 `detached_part_ref`。 |
| 脱落部件标签位置 | lifecycle 字段不重复写 `detached_part_ref`，通过 `parent_event_id` 回查 structural event。 | 避免把 lifecycle 字符串滥用成伪物理字段。 |
| 终端残骸范围 | 基础 MLF-8 只在目标已有链路关联的导弹结构/后果证据时，写 terminal wreck lifecycle 行。普通落地/坠毁仍属于现有 ground lifecycle 行为。 | 保持 MLF-8 在导弹杀伤链范围内，不接管通用地面接触权威。 |
| writer ownership | 在维护中的 engagement event recorder/store 增加 lifecycle 写入支持，再从已验收 structural / ground transition 点调用。 | 复用现有 chain-header 和 recent-event infrastructure。 |
| Reward visibility | 所有基础 MLF-8 行使用 `diagnostics_only`；启用任何 writer 前，reward 必须忽略 diagnostics-only lifecycle 行。 | P1 发现 reward 目前会消费 lifecycle events，除非补 guard。 |
| 一等 wreck entity | 基础切片禁止；`wreck_entity` 保持 zero ref。 | 当前没有维护中的非战斗残骸实体身份。 |
| 碎片物理 | 基础切片禁止。 | selected debris-output 证据尚未准入。 |

## 已接受生命周期行

| 行 | Producer input | Lifecycle output | Header / visibility | 验收说明 |
| --- | --- | --- | --- | --- |
| 脱落部件碎片事实 | 新 `StructuralBreakupEvent`，且 `detached_part_ref` 非空或 `detached_part_count > 0` | `lifecycle_from=attached_airframe_part`、`lifecycle_to=detached_part_debris_fact`、`ground_lifecycle=unknown`、`debris_count=detached_part_count`、`terminal=false`、`terminal_projection_id=<structural_event_id>` | `stage=lifecycle`、`parent_event_id=<structural_event_id>`、`consumer_visibility=diagnostics_only` | 父 structural event 仍是脱落部件标签和原因链的来源。 |
| 机体解体碎片摘要 | `StructuralBreakupEvent.airframe_breakup == true` | 与脱落部件碎片事实相同的 lifecycle 行形状，`debris_count` 使用 structural event 的累计值 | `diagnostics_only` | 这里只做解体账本摘要，不是直接坠毁/删除规则。 |
| 终端原机体残骸事实 | 链路关联的 `PlatformConsequenceEvent` / structural evidence，加上 `GroundImpactLifecycle::CrashedWreck` 或 `DebrisFragmentResidue` 转移 | `lifecycle_from=lost_airframe_observable`、`lifecycle_to=ground_crashed_wreck`、`ground_lifecycle=crashed_wreck`、`debris_count=0`、`terminal=true`、`terminal_projection_id=<parent consequence or structural event id>` | `stage=lifecycle`、`consumer_visibility=diagnostics_only` | 原实体 liveness 仍由 `is_alive()` / `is_unit_active()` 决定；lifecycle 行只是诊断事实，不是替代实体。 |

## 明确保留的行

| 保留行 | 去向 | 原因 |
| --- | --- | --- |
| 逐碎片记录 | 未来 MLF-8 extension | 基础证据只有结构组标签和累计数量，没有 fragment inventory。 |
| 一等 wreck entity | 未来 MLF-8 extension，等待实体契约 | 尚无非战斗残骸身份、targeting 限制或 lifecycle owner。 |
| 碎片对其他目标的二次损伤 | 未来 MLF-8 extension 或后续校准门 | 会暗示本切片没有的物理和损伤权威。 |
| 通用非导弹地面坠毁 lifecycle | 单独 ground-contact lifecycle work | 不是所有坠毁都是 MLF 导弹杀伤事实。 |
| Pk / 统计投影 | MLF-9 | 需要独立趋势/概率契约。 |
| 校准碎片抛散或 selected debris-output 权威 | MLF-10 或后续证据门 | TP-21 selected outputs 仍 fail-closed。 |

## P3 Runtime 要求

- 增加 `LifecycleTransitionEvent` 的 recorder/store path。
- 补全 header：`stage=lifecycle`、chain id、parent event id、target ref、producer id、
  observation mode 和 `diagnostics_only` visibility。
- recent-event export 需要 cap 和 sort lifecycle rows。
- 对每个已接受 structural breakup event，恰好写一次脱落部件 lifecycle fact。
- 对有链路证据的原飞机，ground lifecycle 第一次进入 crashed-wreck/residue 时，恰好写一次
  diagnostics-only terminal row。
- `wreck_entity` 保持 zero，不 spawn entity。
- 启用任何 MLF-8 writer 前，reward 必须忽略 diagnostics-only lifecycle 行。

## 必需测试

P3/P5 必须证明：

- no-breakup 输入不产生 lifecycle row；
- 单个 wing/tail/engine/fuselage 脱落产生一条 diagnostics-only detached-part lifecycle row，
  且链接到 structural event；
- multi-axis / airframe breakup 产生有边界聚合 lifecycle row；
- 有链路 structural/consequence 证据后的 terminal ground wreck 产生一条 diagnostics-only
  terminal row；
- diagnostics-only lifecycle rows 不会触发 reward terminal state，也不会新增 reward term；
- 若未来显式测试 promoted non-diagnostics lifecycle row，则保留现有 reward 行为；
- `is_unit_active()` 仍是原实体 liveness 权威。

## 禁止输出

- 来自 MLF-8 诊断的 reward term。
- Pk、伤亡或真实世界损伤概率。
- 证据准入前的 selected TP-21 debris output 权威。
- 武器或飞机专用碎片校准。
- 在没有事实 bug 的情况下重开已归档 MLF-6/7 实现。
