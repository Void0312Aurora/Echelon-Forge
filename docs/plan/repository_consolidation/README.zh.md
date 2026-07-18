# 仓库精简与整合路线图

语言：
- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/repository_consolidation/README.md`
Owner: `repository consolidation workline`
Last verified: `2026-07-18`

状态：在分支 `codex/redundancy-consolidation` 上执行中的仓库精简路线图。

## 目标

减少全仓冗余代码、重复权威、兼容残留、过大的导航表面和文档漂移。证据充分时允许
调整架构，但必须保留维护中的行为、明确的兼容承诺、测试、provenance 和有界能力
claim。

所有精简迭代都保留在同一分支。每轮迭代产生一个可独立审阅的提交；同一表面只有在
上一轮验收后才能进入下一轮修改。

## 迭代协议

每轮严格按以下顺序执行：

1. **分析**
   - 检查当前工作区和调用者；
   - 找出重复 owner 或过时路径；
   - 明确必须保留的行为和证据；
   - 冻结 write set 和非目标。
2. **实施**
   - 做出能够收敛到单一维护 owner 的最小完整架构变更；
   - 删除兼容表面或历史前先迁移调用者；
   - 不混入无关清理。
3. **验证**
   - 为每个受影响行为运行 focused test；
   - 按风险运行结构、链接、lint、build 或 smoke gate；
   - 审阅前记录命令和结果。
4. **独立审阅**
   - 派发一个没有编写该变更的独立 subagent；
   - 对冻结 diff 检查行为损失、被删除功能、调用者存活、兼容、文档权威、测试充分性，
     以及是否重复已有 owner 或堆砌不必要的平行机制；
   - reviewer 只读，返回 blocking finding、non-blocking finding 和 verdict。
5. **修复与复审**
   - 修复 blocking finding 并重跑受影响验证；
   - 实质修复后必须进行最终独立复核。
6. **提交**
   - 最终 diff 没有未解决 blocking finding 后才能提交；
   - 每轮一个提交，并在下方迭代登记中记录证据；
   - 不通过 amend 旧迭代来隐藏后续修复。

最终审阅后发生的实现改动，未经再次审阅不得进入提交。

## 必需验收证据

每轮验收交接必须包含：

- 精确 write set 和非目标；
- 被删除/移动表面的 caller 或 consumer 清单；
- focused validation 命令和结果；
- 生产行为变更时的更广 maintained smoke/build 结果；
- 文件/行数变化和仍存在的重复 owner；
- 独立 reviewer 身份、被审 revision/diff、findings 和 verdict；
- 对保留行为和残余的明确说明；
- 提交建立后的 commit hash。

纯文档迭代还必须证明受影响入口的本地链接有效、强制双语 companion 一致，并通过
`git diff --check`。

## 候选优先级

下表是路由顺序，不是预先授权。每个候选开始迭代时都必须重新审计源码和调用者。

| 优先级 | 候选 | 预期结果 | 主要风险 |
| --- | --- | --- | --- |
| P0 | 重复表示暴露出的正确性缺陷 | 在机械删除前修复错误行为。 | 保持兼容的补丁仍可能改变默认语义。 |
| P1 | 不可达实现和完全相同的 helper | 删除 dead body，建立唯一 runtime/test helper owner。 | 隐藏构造或 import 方式可能绕过正常调用者。 |
| P2 | 文档生命周期与精简治理 | 建立可执行的分类、审阅、归档和 evidence 规则。 | 只写政策而不索引、不执行，会增加新的闲置权威。 |
| P3 | 维护导航与兼容 shim | 修复入口链接，迁移内部 shim 调用者，保留有界外部兼容 facade。 | 调用者迁移前移动/删除 shim 会破坏测试不可见用户。 |
| P4 | Python taxonomy、geometry、objective、C2/ROE 和 bootstrap helper 重复 | 建立单一语义 owner，并用 scalar/tensor 或 runtime/compiler parity test 约束。 | 表面相似 helper 可能有有意语义差异。 |
| P5 | World-batch、step-evaluation、effects-event 和配置 schema 重复 | 用共享 payload 或显式 adapter 取代字段逐项同步。 | public binding、ABI、序列化和报告 schema 可能改变。 |
| P6 | Python 包循环与 C++ target/layer 边界 | 强制依赖方向和更小的 build/runtime owner。 | 广泛 import、链接、初始化顺序和性能回归。 |
| P7 | 文档压缩、archive 规范化和 evidence manifest | 缩小维护导航；完成 provenance 映射后再折叠重复 archive 层。 | 路径迁移会破坏工具、测试、历史引用和权利证据。 |
| P8 | 最终全仓残余审计 | 把每个剩余重复项分类为有意、held 或收益不足。 | 扫描可能漏掉行为重复，或高估文本相似性。 |

## 迭代登记

| 迭代 | 状态 | Commit / 分支证据 | 范围与结果 | 验证 / 审阅证据 |
| --- | --- | --- | --- | --- |
| I1 Runtime 与测试基础设施整合 | `accepted` | `aaec45882173d57c679e3e7233a81980ee9d8fdc`，分支 `codex/redundancy-consolidation` | 修复 missile tuning 稀疏覆盖语义，删除不可达 `UniversalEnv` body，统一 `ef_py` runtime bootstrap 和 suite-manifest 解析，合并重复测试 helper。净变化为新增 1,413 行、删除 2,390 行。 | Focused regression 与 maintained smoke suite 通过；最终迭代收口记录为 `361 passed`、`41 subtests passed`。独立审阅在提交前未留下 unresolved blocking finding。 |
| I2 文档生命周期与精简治理 | `accepted` | `c844bd900856682f18d6dc72fcb442b95e75c18a`，分支 `codex/redundancy-consolidation` | 建立生命周期与精简权威、唯一维护文档范围规则、严格链接审计、选择性双语登记刷新，并在不使用 baseline allowlist 的前提下完成链接安全修复。严格登记现覆盖 76 对文档。最终 diff 为 57 个文件、新增 1,960 行、删除 427 行。 | 默认审计检查 155 份文档和 2,592 个内部链接，零问题；治理聚焦测试 `15 passed`；maintained smoke 为 `371 passed`、`41 subtests passed`；Ruff 与 `git diff --check` 通过。登记结果为 70 对同步、6 对保留的既有分歧、1 个既有缺失英文 companion。`iteration2_independent_review` 发现两个 archive 权威 blocker，均已修复；最终 `bilingual_registry_audit` 复审没有遗留 blocker。 |
| I3 文档去重与双语残余闭环 | `accepted` | 同一分支；commit 待收口建立 | 否决了为根 README 增建登记特例的方案；把重复的 realism-authority 标准压成复用既有 owner 的兼容路由对；删除 air-combat 上级索引复制的归档实现细节；补回缺失的 review 路由；刷新四个已有证据的旧 baseline。最终 diff 为 17 个文件、新增 184 行、删除 192 行（净删除 8 行）。 | 登记结果为 77/77 同步，无缺失 peer 或漂移；链接审计检查 156 份文档、2,590 个链接，零问题；治理聚焦测试 `25 passed`；maintained smoke 为 `372 passed`、`41 subtests passed`；Ruff 与 `git diff --check` 通过。独立审阅发现 authority 与 registry gate blocker，均已修复；最终复审以零 blocker 批准候选。 |

### I2 残余在 I3 的处置

- 仓库根 README 对继续直接审阅；维护链接审计已经覆盖它，为一个特例新增第二套
  registry 路径模型不具备收益。
- 独立 realism-authority 内容改为路由到既有 gradient realism、source admission 与
  lifecycle owner，不再重复规则。
- 六个旧分歧通过四个有证据的 baseline 刷新、删除 air-combat 复制的归档细节，
  以及补回 review 路由完成闭环。
- 旧 archive 规范化和 evidence 压缩仍属于 P7，没有混入 I3。

## 未满足额外门槛时不得删除的表面

以下内容不能仅因体积大、陈旧或重复就成为删除候选：

- public 或 compatibility API：必须先有内部及合理外部 caller 的迁移路径和弃用边界；
- 测试：必须由同等或更强行为断言替代，并保留相关 bug 历史；
- frozen config、canonical scenario、accepted evidence、source-rights 记录、
  第三方输入和 provenance manifest；
- maintained release 或 validation 路径消费的 generated artifact：必须先证明可在干净
  环境重建；
- 仅因历史陈旧或篇幅过长的 archive 记录；
- 未准入 tracked 范围的 ignored/private/local 工作区；
- 用户拥有的无关工作区变更；
- 没有 characterization test 的行为：必须先测量并决定意图边界。

删除任何 evidence 或 archive 包之前，必须扫描 consumer/reference，审查权利和
provenance，并证明更小的保留集合仍支撑同一有界 claim。

## 提交与审阅纪律

- 除非用户明确改变分支策略，所有迭代都在 `codex/redundancy-consolidation`。
- 一轮迭代对应一个完整提交。
- 独立 reviewer 不得修改被审实现。
- 审阅必须判断功能是否被消除、是否重复已有 owner，不能只看测试是否通过或代码是否缩短。
- 窄测试通过不证明全仓兼容。
- 若本轮发现实质不同的问题，记录为后续候选，不扩大当前 write set。
- 存在未解决 blocking finding、必需验证失败或无法解释的删除时不得提交。

## 停止条件

只有最终审计证明以下条件全部满足，精简计划才能宣告完成：

1. 维护入口均有唯一命名 owner，且没有已知失效内部导航；
2. active tree 中没有已确认的不可达 production body 或无 owner compatibility path；
3. 剩余重复 schema/helper 已有共享 owner，或有明确理由保持独立表示；
4. 剩余 archive/evidence 重复是 provenance、权利、可复现性或有界验收所必需；
5. 剩余候选已被分类为有意、受明确兼容决定 held，或其风险/成本确实高于收益；
6. focused test、maintained smoke/build gate、文档 gate 和最终独立审阅全部通过；
7. 最终残余报告明确记录了有意保留内容及理由。

最后一次实质整合后至少连续运行两轮残余审计。第二轮不得发现新的高置信、可安全
整合候选。没有文本重复不等于完成；还必须审计 caller、行为、文档和 evidence owner。

若进展需要外部兼容决定、不可获得的 source rights，或仓库内无法 characterization
的行为，应把候选标为 `held` 并写明缺失 authority。不得为了减少行数而删除。

## 相关权威

- [文档生命周期规范](../../standards/governance/document_lifecycle_policy.zh.md)
- [Agent 文档权威索引](../../agent/rules/document_authority_map.zh.md)
- [标准维护政策](../../standards/governance/standards_maintenance_policy.zh.md)
- [Subagent 使用规范](../../standards/governance/subagent_usage_policy.zh.md)
