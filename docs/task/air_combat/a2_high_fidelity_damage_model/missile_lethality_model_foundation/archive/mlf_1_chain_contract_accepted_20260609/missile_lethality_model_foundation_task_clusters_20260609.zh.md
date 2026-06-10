# A2 通用导弹杀伤模型基础任务簇

状态：`2026-06-09` MLF-1A-E 已验收，当前子项目进入 accepted/archived 收口路线。

父子项目链接：

- 父级 A2：[../README.zh.md](../README.zh.md)
- 当前子项目：[README.zh.md](README.zh.md)
- MLF-1 合同：[missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- MLF-1A 字段盘点：[missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)

## 边界决策

本任务簇只推进 `MLF-1 Chain Contract`：把事件、诊断字段和训练消费边界标准化，并完成模块边界验收。它不针对 AIM-120C/MQ-9 调参数，也不声明真实弹种杀伤概率。MLF-1 完成后，本子项目归档；几何、引信、破片、连续杆、结构失效和残骸对象必须作为后续独立子项目展开。

## 有限任务簇列表

本列表只覆盖当前 `missile_lethality_model_foundation/` 子项目内的 MLF-1 收口任务。MLF-2 及以后阶段不在本子项目继续展开；需要时另按 `docs/agent` 子项目标准创建新的 MLF-2 子项目。

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-1A` | main thread or documentation worker | n/a | 完成现有事件字段盘点，确认哪些字段属于发射、接近、引信、效果、部件、损伤、后果和生命周期 | `missile_lethality_field_inventory_20260609*.md` | 不改运行代码，不新增弹种数值 | `rg -n "[ \\t]$" missile_lethality_field_inventory_20260609*` | 字段表覆盖 `engagement_contracts.h`、event store、diagnostics probe、reward consumer | first, serial | 1 | pass |
| `MLF-1B` | Turing `019eac4f-0cac-7380-bc79-e62db308cda2` | inherited / high | 设计公共事件头和新增事件 DTO 形状 | `src/runtime/contracts/*`、对应 binding/test 草案 | 不实现破片/连续杆/结构解体 | focused contract tests + binding smoke | 每个阶段有链路 id、状态、原因、证据等级 | after `MLF-1A`; serial with 1C on API names | 2 | pass |
| `MLF-1C` | Descartes `019eac5b-0d84-7df3-b7df-26c2949467ef` | inherited / high | 建立统一诊断投影字段，让 probe 能按一枚弹输出多阶段记录 | `tools/diagnostics/**`、必要的 Python helper、诊断测试 | 不让训练奖励生成杀伤事实，不保留旧字段别名 | diagnostics pytest + controlled fake/export sample | 不再依赖 `last_effect_*` 和 `last_damage_*` | after `MLF-1A`; parallel with 1D after API names freeze | 2 | pass |
| `MLF-1D` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | inherited / high | 迁移训练奖励和终局消费端，隔离旧字段依赖 | `gym_envs/scenario_loader/reward_runtime/**`、`tests/runtime/air_combat/**`、相关 diagnostics tests | 不改变奖励含义，不新增击毁规则，不保留长期双轨字段 | reward/runtime pytest + diagnostics pytest | 标准字段优先，旧字段仅短期 fallback 且有删除条件 | after `MLF-1B`; parallel with 1C after shared names | 2 | pass |
| `MLF-1E` | main thread | n/a | 模块边界验收，决定是否正式抽 `lethality_chain_contracts.h` | README、chain contract、task cluster、acceptance note | 不把 event store 变成物理模型 | `git diff --check` + relevant tests from 1B-1D | 合同、诊断、训练消费边界写清楚 | after 1B-1D; serial | 1 | pass |

## 派发规则

- 每个 worker packet 必须只对应一个 cluster。
- `MLF-1B` 和 `MLF-1C` 不能同时改同一份字段命名表。
- 旧字段不是兼容承诺；若需要短暂过渡，必须写清删除点和负责人。
- 运行逻辑修改必须等字段合同冻结后再做。
- 如果一个 cluster 超过 round cap，先回主线程重划范围，不继续追加 wave。
- 不创建新的会话线程；如需 subagent，只允许作为当前工作流内的受控分发。
- 本任务簇完成后不得在当前子项目内继续派发 MLF-2；MLF-2 必须单独新建子项目。

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
- 本地复验通过：`test_diagnostics_probe_contracts.py`、`py_compile`、相关 `git diff --check`。

## Round-4 派发记录

- `MLF-1D` 已派发给 Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24`，负责训练奖励和终局消费端迁移。
- 目标是优先消费标准 `PlatformConsequenceEvent` / `LifecycleTransitionEvent`；旧 `DamageReport` 只能作为过渡 fallback，并必须有删除条件。
- 本轮禁止改变奖励语义、禁止新增击毁规则、禁止把任何触地直接当坠毁。
- CMO-DB 已纳入 `cmo_db_proxy` 代理资料源口径；这只是证据/参数来源规则，不是本轮 runtime 改动。

## Round-4 验收记录

- `MLF-1D` 已验收通过：训练奖励现在优先从 `platform_consequence_events` / `lifecycle_transition_events` 形成消费端事实，旧 `DamageReport` 只留在 `_transitional_damage_report_fact_projection()` 兜底路径。
- 终局判断优先读取标准生命周期事件；触地仍必须达到 `ground_lifecycle >= 2` 或对应坠毁残骸状态才会被当作失去行动能力，安全接地不会被判定为坠毁。
- 旧 `DamageReport.platform_damage_state_delta` 字符串解析没有扩散到新路径；删除条件是 runtime event store 能为 live scenario 写入 `PlatformConsequenceEvent` 和 `LifecycleTransitionEvent`。
- 本地复验通过：`test_air_combat_reward_surface.py`、`test_diagnostics_probe_contracts.py`、`py_compile`、相关 `git diff --check`。

## Round-5 验收记录

- `MLF-1E` 已验收通过，`MLF-1 Chain Contract` 可从 planned/active 进入 accepted。
- 当前不正式拆 `src/runtime/contracts/lethality_chain_contracts.h`。杀伤链 DTO 已在 `engagement_contracts.h` 内形成清晰分块，并已由 `RecentEngagementEvents`、facade packet 和 Python binding 暴露；现在拆文件会制造 include/binding churn，收益不足。
- 后续拆分条件：标准 DTO event-store writer 落地，或未来单独 MLF-2/MLF-3 子项目的受控 probe 让几何、引信、战斗部、部件载荷合同形成独立所有权。
- 职责边界验收：合同只放数据结构；event store 只记录、排序、关联和导出；诊断只做阶段投影；reward/terminal 只消费事实；几何/引信、破片、连续杆、结构解体、残骸对象和 AIM-120C/MQ-9 个案调参不在 MLF-1E 内实现。
- 旧字段删除条件保持为：runtime event store 为 live scenario 写入 `PlatformConsequenceEvent` 和 `LifecycleTransitionEvent` 后，删除 `DamageReport` transitional fallback 与 `platform_damage_state_delta` 字符串解析路径。
- 当前子项目完成 MLF-1E 后走 accepted/archived 路线，不继续承载 MLF-2 几何/引信模型；MLF-2 必须稍后按 `docs/agent` 子项目标准新建。
- 本轮只改文档，未修改运行代码。

## 后续 MLF-2 立项保留说明

当前任务簇不派发 MLF-2。归档后如需新建 MLF-2，目标应先写成：用受控几何和引信评估解释触发、未触发、延迟和失败，把起爆状态交给后续战斗部模型，而不是直接给出击毁结果。

未来 MLF-2 的最小子项目内容应包括：

- README：说明目标、范围、非目标、入口门和退出门。
- 有限任务簇：至少分出几何场景、最近接近事件、引信评估事件、诊断导出和验证场景。
- 验收门：不同距离、方位、速度、姿态能产生可解释结果；没有起爆也必须有原因；接触与近炸判定分开记录。
- 残余地图：破片、连续杆、结构断裂、残骸对象、Pk 和具体弹种校准都继续留给后续独立子项目。

## 验证计划

第一轮文档验证：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_model_foundation
```

进入代码后，至少需要补充：

```bash
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
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
| 当前子项目归档指针尚未写入 | main thread / archive workflow | 按任务系统把 MLF-1 accepted 包移动或指向 archive |
| 标准 DTO event-store writer 尚未写入 live scenario | future runtime writer subproject | live runtime 能直接产生 `PlatformConsequenceEvent` / `LifecycleTransitionEvent` 后删除 `DamageReport` fallback |
| 几何/引信 probe 未实现 | future standalone MLF-2 subproject | 另建 MLF-2 子项目后处理 |
| 破片、连续杆、结构断裂、残骸、Pk 未实现 | future standalone MLF subprojects | MLF-2 之后按独立子项目逐步展开 |
