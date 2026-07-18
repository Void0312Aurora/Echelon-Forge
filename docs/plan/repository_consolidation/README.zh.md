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
| I3 文档去重与双语残余闭环 | `accepted` | `d0dbf0d7ee68643baa30d41e66e3955407d3a3ba`，分支 `codex/redundancy-consolidation` | 否决了为根 README 增建登记特例的方案；把重复的 realism-authority 标准压成复用既有 owner 的兼容路由对；删除 air-combat 上级索引复制的归档实现细节；补回缺失的 review 路由；刷新四个已有证据的旧 baseline。最终 diff 为 17 个文件、新增 184 行、删除 192 行（净删除 8 行）。 | 登记结果为 77/77 同步，无缺失 peer 或漂移；链接审计检查 156 份文档、2,590 个链接，零问题；治理聚焦测试 `25 passed`；maintained smoke 为 `372 passed`、`41 subtests passed`；Ruff 与 `git diff --check` 通过。独立审阅发现 authority 与 registry gate blocker，均已修复；最终复审以零 blocker 批准候选。 |
| I4 Scenario compiler 兼容 owner 整合 | `accepted` | `afe03257e26f9355013293fb0bace77cfeb4091b`，分支 `codex/redundancy-consolidation` | 把只绑定 64 个名称的不完整手工 facade 改为由 canonical `__all__` 驱动的 86 项完整转发；15 个维护中调用方迁到 `python.scenario.compiler`；测试与 archive 保留兼容入口。结构门禁阻止维护代码重新依赖 facade。最终 diff 为 22 个文件、新增 77 行、删除 86 行（净删除 9 行）。 | 直接 star-import 校验 86/86 导出且对象身份一致；scenario、world-batch、多 agent 与架构聚焦测试 `81 passed`；maintained smoke 为 `374 passed`、`41 subtests passed`；Ruff 与 `git diff --check` 通过。独立审阅发现一个平行扫描 blocker；复用既有全仓扫描器并采用 AST import 检查后，最终复审以零 blocker 批准候选。 |
| I5 MissionCommand shared-core owner 整合 | `accepted` | `9c999b81`，分支 `codex/redundancy-consolidation` | 让 `MissionCommandCore` 成为可直接判等的 shared owner；重复 directive struct 改为 alias；projection 与 maintained-contract 回填折叠为值复制；episode-state 等价判断直接消费 owner equality。该变更修复手写比较漏掉的四个已序列化字段，同时保留 Python 类型名称；完整 umbrella 以及 umbrella/core 两个方向的混合 equality 均被显式删除，避免静默忽略领域 slice。最终 diff 为 9 个文件、新增 65 行、删除 74 行（净删除 9 行）。 | 已重建 `ef_core`、`ef_py`、`ef_test`，`ef_test_all` 通过；架构、binding、episode、world-batch 与领域聚焦回归 `119 passed`、`1 skipped`、`6 subtests passed`；maintained smoke 为 `375 passed`、`45 subtests passed`；Ruff 与 `git diff --check` 通过。独立审阅先发现继承产生的不完整 umbrella equality 和测试缺少正向 baseline，复审又发现两个 umbrella/core 混合比较方向；全部 finding 均已用编译与运行时门禁修复，最终复审以零 blocker 批准候选。 |
| I6 Execution runtime 行为 owner 整合 | `accepted` | `codex/redundancy-consolidation` 上的 `143ee4e9` | 删除重复的 `execution_frame_runtime.cpp`，把保留的 Frame 兼容符号迁入 Episode 所属实现，并让两个 API 共享唯一内部公共产品路径与批处理调度器。公开 Frame/Episode DTO、Python 名称、名义类型分离、64 项并行阈值、顺序与异常传播均保持不变。最终 diff 为 13 个文件、新增 147 行、删除 151 行（净删除 4 行）。 | 已重建 `ef_core`、`ef_py`、`ef_test`，`ef_test_all` 通过；scalar/batch/fallback/architecture 聚焦回归 `46 passed`、`226 subtests passed`；维护中的 multi-agent/world-batch 调用者 `71 passed`、`1 skipped`、`5 subtests passed`；maintained smoke 为 `375 passed`、`45 subtests passed`。Registry 为 77/77 synced；链接审计检查 156 份文档、2,592 个链接，零问题；Ruff 与 `git diff --check` 通过。独立复审以零 blocker 批准候选。 |
| I7 模式选项面 owner 整合 | `accepted` | `codex/redundancy-consolidation` 上的 `587df736` | 把 `python.mission_obs_taxonomy`（任务观测模式）与 `python.env_config`（action、execution-step-runtime、step-info、flight-shaping 模式）确立为模式面的唯一有序 owner。训练/评估 CLI 的选项清单与校验集合改为从 owner 元组派生，移除 `python/training/cli.py`、`python/env_config.py`、`tools/eval/eval_utils.py`、`tools/eval/sb3_eval_base.py` 中五处手写字面量副本。导出名、选项内容与顺序保持不变；新增 parity 测试把每个派生面钉在其 owner 上。最终 diff 为 9 个文件、新增 111 行、删除 27 行。 | env-config/taxonomy、training-bootstrap 与评估 CLI 聚焦回归 `48 passed`、`2 skipped`、`20 subtests passed`；maintained smoke 为 `380 passed`、`45 subtests passed`（基线 375 加五个新 parity 守卫）。Ruff、`git diff --check`、双语 registry 审计（77 对）与维护链接审计通过。独立评审以零 blocker 批准候选。 |
| I8 标量辅助与模式字面量 owner 整合 | `accepted` | `codex/redundancy-consolidation` 上的 `aa5b537c` | 确立零依赖 owner：`python.angles`（有符号/罗盘 wrap、保号 heading error、方位角、平面距离）与 `python.coercion`（`coerce_nonnegative_int`），约十九处维护中的角度辅助调用点与全部五处 coercion 副本经薄别名迁移到 owner，所有公开名保持可导入。刻意变体留在调用侧并有测试钉住：1e-9 归零 wrap、退化方位 fallback、以及与 owner 形式实测有约 1e-13 度位级差异的纯 `%360` 方位公式。运行时模式字面量残留（ScenarioLoader backend 校验、world-batch 与 cooperative vec-env 校验、scenario-loader 两个 normalize、诊断 benchmark CLI）改为从 `python.env_config` 派生；此前报告的 `universal_env.py` 残留在当前基线上不存在。`ModeChoiceSurfaceParityTests` 补充 `ACTION_MODES` 内容 pin 与不分引号风格的负向守卫。最终 diff 为 33 个文件、新增 560 行、删除 119 行（代码与测试面为 27 个修改文件 +117/−115 加三个新文件；其余为本登记更新与 registry 刷新）。 | 新增 25 用例 parity 套件把 owner 与被删公式的内嵌副本逐位对拍（覆盖 ±180/360/负角/非有限值）并纳入 CI smoke 清单。naval/world-batch/multi-agent/leader/场景编译器/导航/评估聚焦回归 `325 passed`、`3 skipped`、`51 subtests passed`。maintained smoke 为 `406 passed`、`45 subtests passed`（基线 380 加 26 个新守卫）。Ruff 与 `git diff --check` 通过。独立评审用独立的 1.4 万点位级网格复现数值 parity 零失败，以零 blocker 批准候选。 |
| I9 训练/评估入口整合 | `accepted` | 同一分支；哈希在下一轮登记刷新时补入 | 把根目录 `train.py` 的实现主体（927 行降至 331 行）下沉到 `python/training/`：延迟 SB3/torch 依赖加载（`deps.py`）、安全动作偏置初始化（`action_bias.py`）、vec-env 选型与构造（`vec_env_factory.py`）。`train.py` 保留薄 `main()`、兼容 re-export（含修复的 `apply_global_seed`——`tools/diagnostics/trace_training_nonfinite_source.py` 依赖此导入）与 WP24 UniversalEnv 退役门禁字符串。`evaluate.py` 的模型加载统一到单一 owner `tools/eval/sb3_eval_base.load_sb3_policy`（新增可选 `env=` 参数；既有十五处调用方不受影响）。如实记录一处有意的行为增强：此前在 `evaluate.py` 加载失败的历史 HMoE/Squashed checkpoint 现经共享的历史 policy-class 探测成功加载。两个新的端到端入口 smoke 测试钉住 evaluate CLI 与 `train.py --test_only` 路径。最终 diff 为 14 个文件、新增 1251 行、删除 762 行（代码与测试面为 6 个修改文件 +121/−758 加五个新文件；其余为本登记更新与 registry 刷新）。 | 独立评审以 AST 归一化逐函数对比核实行为保持（动作偏置数值、全部 vec-env kwargs、`main()` 编排与日志文案），实测 `import train` 不加载 torch，并将四份 `--help` 输出与基线逐字节对比。training/policy/eval/architecture 聚焦回归 `251 passed`、`2 skipped`（一个基线即红的 GBK 控制台用例已在未打补丁基线复现）。落地树 maintained smoke 为 `406 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。独立评审以零 blocker 批准候选，并裁决保留两个新入口 smoke 测试。 |
| I10 飞行塑形字段税消除 | `accepted` | `codex/redundancy-consolidation` 上的 `c1a8b2f4` | 把 `FlightShapingRuntimeInputs` 与 `StepEvaluationBatchConfig` 共享的 89 个 config-static 塑形字段提为单一 X-macro 清单（`src/core/mission/runtime/detail/flight_shaping_shared_fields.inc`）；两个结构体字段块、batch-prepare 逐字段拷贝与 FlightShaping `def_rw` 绑定改由该唯一 owner 宏展开。字段类型、名称、默认值、顺序与 Python 属性面（118/15 个属性）保持不变；两个任务动态 `target_*` 字段保持手写以保成员顺序。最终 diff 为 8 个文件、新增 136 行、删除 373 行（代码面 5 个文件 +128/−367、净删除 239 行；其余为本登记更新与 registry 刷新）。 | 在隔离 worktree 重建 `ef_core`、`ef_py`、`ef_test`，`ef_test_all` 通过。字段审计 118/118 与 112/112 逐项一致（类型/名称/默认值/顺序）；新旧构建 parity 探针输出 546 行逐字节相同。execution/facade/world-batch/architecture 聚焦回归 `282 passed`、`1 skipped`（window-loop 字符串风格断言与本机 winsock 链接两类既有失败已在未打补丁基线上原样复现）。maintained smoke 为 `380 passed`、`45 subtests passed`。`git diff --check` 通过。独立评审发现一项登记口径 blocker；登记修复后，最终复核以零 blocker 批准候选。 |

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
