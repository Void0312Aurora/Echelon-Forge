# A2 通用导弹杀伤模型基础任务簇

状态：`2026-06-09` finite task-cluster plan for [README.zh.md](README.zh.md)。

父子项目链接：

- 父级 A2：[../README.zh.md](../README.zh.md)
- 当前子项目：[README.zh.md](README.zh.md)
- MLF-1 合同：[missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- MLF-1A 字段盘点：[missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)

## 边界决策

本任务簇只推进通用导弹杀伤模型基础，不针对 AIM-120C/MQ-9 调参数，也不声明真实弹种杀伤概率。当前第一轮聚焦 `MLF-1 Chain Contract`，目标是把事件和诊断字段标准化，后续才进入几何、引信、破片、连续杆、结构失效和残骸对象。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-1A` | main thread or documentation worker | n/a | 完成现有事件字段盘点，确认哪些字段属于发射、接近、引信、效果、部件、损伤、后果和生命周期 | `missile_lethality_field_inventory_20260609*.md` | 不改运行代码，不新增弹种数值 | `rg -n "[ \\t]$" missile_lethality_field_inventory_20260609*` | 字段表覆盖 `engagement_contracts.h`、event store、diagnostics probe、reward consumer | first, serial | 1 | pass |
| `MLF-1B` | Turing `019eac4f-0cac-7380-bc79-e62db308cda2` | inherited / high | 设计公共事件头和新增事件 DTO 形状 | `src/runtime/contracts/*`、对应 binding/test 草案 | 不实现破片/连续杆/结构解体 | focused contract tests + binding smoke | 每个阶段有链路 id、状态、原因、证据等级 | after `MLF-1A`; serial with 1C on API names | 2 | pass |
| `MLF-1C` | Descartes `019eac5b-0d84-7df3-b7df-26c2949467ef` | inherited / high | 建立统一诊断投影字段，让 probe 能按一枚弹输出多阶段记录 | `tools/diagnostics/**`、必要的 Python helper、诊断测试 | 不让训练奖励生成杀伤事实，不保留旧字段别名 | diagnostics pytest + controlled fake/export sample | 不再依赖 `last_effect_*` 和 `last_damage_*` | after `MLF-1A`; parallel with 1D after API names freeze | 2 | pass |
| `MLF-1D` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | inherited / high | 迁移训练奖励和终局消费端，隔离旧字段依赖 | `gym_envs/scenario_loader/reward_runtime/**`、`tests/runtime/air_combat/**`、相关 diagnostics tests | 不改变奖励含义，不新增击毁规则，不保留长期双轨字段 | reward/runtime pytest + diagnostics pytest | 标准字段优先，旧字段仅短期 fallback 且有删除条件 | after `MLF-1B`; parallel with 1C after shared names | 2 | pass |
| `MLF-1E` | main thread | n/a | 模块边界验收，决定是否正式抽 `lethality_chain_contracts.h` | README、chain contract、task cluster、acceptance note | 不把 event store 变成物理模型 | `git diff --check` + relevant tests from 1B-1D | 合同、诊断、训练消费边界写清楚 | after 1B-1D; serial | 1 | planned |
| `MLF-2A` | future geometry/fuze worker | n/a | 构建受控接近几何和引信 probe | weapon runtime/tests/diagnostics docs | 不调 AIM-120C/MQ-9 杀伤结果 | controlled geometry/fuze tests | 不同距离和方位能解释触发/未触发 | after MLF-1 accepted | 2 | planned |

## 派发规则

- 每个 worker packet 必须只对应一个 cluster。
- `MLF-1B` 和 `MLF-1C` 不能同时改同一份字段命名表。
- 旧字段不是兼容承诺；若需要短暂过渡，必须写清删除点和负责人。
- 运行逻辑修改必须等字段合同冻结后再做。
- 如果一个 cluster 超过 round cap，先回主线程重划范围，不继续追加 wave。
- 不创建新的会话线程；如需 subagent，只允许作为当前工作流内的受控分发。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Round-1 验收记录

- `MLF-1A` 字段盘点已验收通过；交付物为 [missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md) 和英文辅文。
- `MLF-1B` 只读合同探查已返回路线证据：建议先定义公共头和 DTO，再接 packet、binding、facade、manifest；这不是实现完成。
- `MLF-1C` 只读诊断探查已返回路线证据：当前问题集中在 `last_effect_*` / `last_damage_*`；建议改成 `chain_id + event_id + stage` 行；这不是实现完成。
- `MLF-1D` 只读消费端探查已返回路线证据：reward/terminal 迁移必须保持现有奖励语义和 `ground_lifecycle >= 2` 坠毁含义；这不是实现完成。

## Round-2 派发记录

- `MLF-1B` 已派发给 Turing `019eac4f-0cac-7380-bc79-e62db308cda2`，负责公共头、DTO 形状、最小 Python binding 和静态形状测试。
- 本轮暂不派发 `MLF-1C/1D` 实现；诊断和奖励消费迁移要等 `MLF-1B` 字段名稳定后再展开。
- 本轮仍禁止实现破片、连续杆、结构解体、Pk 或具体 AIM-120C/MQ-9 调参。

## Round-2 验收记录

- `MLF-1B` 已验收通过：新增 `LethalityChainHeader` 和十个杀伤链 DTO 形状，接入 `RecentEngagementEvents`、facade packet 和 Python binding。
- 本验收只接受合同/绑定形状，不表示运行时已经写入这些事件；event store、诊断投影和训练消费迁移仍属后续任务。
- 本地复验通过：`cmake --build build-workshop --target ef_py -j2`，`test_engagement_contract_shape.py`，`test_bindings_engagement_surface.py`，`test_bindings_runtime_dto_surface.py`，以及相关 `git diff --check`。

## Round-3 派发记录

- `MLF-1C` 已派发给 Descartes `019eac5b-0d84-7df3-b7df-26c2949467ef`，负责诊断链路投影、`lethality_chain_rows`、可选链路 CSV 和诊断测试。
- `MLF-1D` 继续等待 `MLF-1C` 输出稳定后再展开，避免奖励消费端提前绑定临时字段。
- 本轮仍不改 reward runtime、不实现 event store writer、不新增杀伤行为。

## Round-3 验收记录

- `MLF-1C` 已验收通过：诊断 payload 输出 `lethality_chain_rows`，CLI 支持 `--chain_csv_out`，每行带 `chain_id`、`event_id`、`stage`、来源事件和证据等级。
- 旧 `last_effect_*` / `last_damage_*` 已从诊断工具本体移除；测试中只保留“不得出现”的断言。
- 当前链路行仍是从 `EffectsEvent` / `DamageReport` 生成的过渡投影，真实 DTO event-store writer 仍是后续工作。
- 本地复验通过：`test_air_combat_process_probe.py`、`py_compile`、相关 `git diff --check`。

## Round-4 派发记录

- `MLF-1D` 已派发给 Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24`，负责训练奖励和终局消费端迁移。
- 目标是优先消费标准 `PlatformConsequenceEvent` / `LifecycleTransitionEvent`；旧 `DamageReport` 只能作为过渡 fallback，并必须有删除条件。
- 本轮禁止改变奖励语义、禁止新增击毁规则、禁止把任何触地直接当坠毁。
- CMO-DB 已纳入 `cmo_db_proxy` 代理资料源口径；这只是证据/参数来源规则，不是本轮 runtime 改动。

## Round-4 验收记录

- `MLF-1D` 已验收通过：训练奖励现在优先从 `platform_consequence_events` / `lifecycle_transition_events` 形成消费端事实，旧 `DamageReport` 只留在 `_transitional_damage_report_fact_projection()` 兜底路径。
- 终局判断优先读取标准生命周期事件；触地仍必须达到 `ground_lifecycle >= 2` 或对应坠毁残骸状态才会被当作失去行动能力，安全接地不会被判定为坠毁。
- 旧 `DamageReport.platform_damage_state_delta` 字符串解析没有扩散到新路径；删除条件是 runtime event store 能为 live scenario 写入 `PlatformConsequenceEvent` 和 `LifecycleTransitionEvent`。
- 本地复验通过：`test_air_combat_reward_surface.py`、`test_air_combat_process_probe.py`、`py_compile`、相关 `git diff --check`。

## 验证计划

第一轮文档验证：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_model_foundation
```

进入代码后，至少需要补充：

```bash
python -m pytest tests/diagnostics/test_air_combat_process_probe.py -q
python -m pytest tests/runtime/air_combat/test_air_combat_reward_surface.py -q
```

## 验收标准

MLF-1 被标记为 accepted 前必须满足：

- 事件链可以说明一枚弹从发射到后果的每一步。
- 未触发、未命中、命中无效、非终局损伤、延迟坠毁、结构解体都有记录位置。
- 诊断字段有稳定名称，并有 C++/Python 边界说明。
- 旧字段依赖已经迁移或列入删除清单，没有长期双轨导出。
- 训练奖励只消费事实，不反向制造杀伤结论。
- 文档仍明确拒绝真实 AIM-120C/MQ-9 专项权威。

## 残余地图

| Residual | Owner | Release condition |
| --- | --- | --- |
| 破片模型未实现 | `MLF-3` | `MLF-2` 几何/引信 probe 通过 |
| 连续杆/切割模型未实现 | `MLF-4` | 通用破片模型和部件载荷字段可复用 |
| 结构断裂和空中解体未实现 | `MLF-6` | 部件损伤和目标脆弱性字段稳定 |
| 残骸/碎片对象未实现 | `MLF-8` | 结构失效事件能产生非整机结果 |
| Pk/统计层未实现 | `MLF-9` | 高细节链路可运行，Pk 只做低细节或趋势检查 |
