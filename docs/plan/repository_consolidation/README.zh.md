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
| I8 标量辅助与模式字面量 owner 整合 | `accepted` | `codex/redundancy-consolidation` 上的 `aa5b537c` | 确立零依赖 owner：`python.angles`（有符号/罗盘 wrap、保号 heading error、方位角、平面距离）与 `python.coercion`（`coerce_nonnegative_int`），约十九处维护中的角度辅助调用点与全部五处 coercion 副本经薄别名迁移到 owner，所有公开名保持可导入。刻意变体留在调用侧并有测试钉住：1e-9 归零 wrap、退化方位 fallback、以及与 owner 形式实测有约 1e-13 度位级差异的纯 `%360` 方位公式。运行时模式字面量残留（ScenarioLoader backend 校验、world-batch 与 cooperative vec-env 校验、scenario-loader 两个 normalize、诊断 benchmark CLI）现从 `python.env_config` 中语义匹配的元组派生；batch observation 与 visual backend 即使当前取值相同，也与 flight shaping 保持不同 owner。此前报告的 `universal_env.py` 残留在当前基线上不存在。`ModeChoiceSurfaceParityTests` 补充 `ACTION_MODES` 内容 pin 与不分引号风格的负向守卫。最终 diff 为 33 个文件、新增 560 行、删除 119 行（代码与测试面为 27 个修改文件 +117/−115 加三个新文件；其余为本登记更新与 registry 刷新）。 | 新增 25 用例 parity 套件把 owner 与被删公式的内嵌副本逐位对拍（覆盖 ±180/360/负角/非有限值）并纳入 CI smoke 清单。naval/world-batch/multi-agent/leader/场景编译器/导航/评估聚焦回归 `325 passed`、`3 skipped`、`51 subtests passed`。maintained smoke 为 `406 passed`、`45 subtests passed`（基线 380 加 26 个新守卫）。Ruff 与 `git diff --check` 通过。独立评审用独立的 1.4 万点位级网格复现数值 parity 零失败，以零 blocker 批准候选。 |
| I9 训练/评估入口整合 | `accepted` | `codex/redundancy-consolidation` 上的 `c20d2366` | 把根目录 `train.py` 的实现主体（1,008 行降至 331 行）下沉到 `python/training/`：延迟 SB3/torch 依赖加载（`deps.py`）、安全动作偏置初始化（`action_bias.py`）、vec-env 选型与构造（`vec_env_factory.py`）。`train.py` 保留薄 `main()`、兼容 re-export（含修复的 `apply_global_seed`——`tools/diagnostics/trace_training_nonfinite_source.py` 依赖此导入）与 WP24 UniversalEnv 退役门禁字符串。Checkpoint 加载现由无 bootstrap 副作用的 `python.rl.policy_checkpoint.load_sb3_policy` 负责；`tools/eval/sb3_eval_base` 在其诊断工具本地 fail-closed bootstrap 之后保留兼容 re-export。如实记录一处有意的行为增强：此前在 `evaluate.py` 加载失败的历史 HMoE/Squashed checkpoint 现经共享的历史 policy-class 探测成功加载。两个端到端入口 smoke 测试钉住 evaluate CLI 与 `train.py --test_only` 路径，后续守卫另行验证导入共享 loader 不会检查本地构建配置。最终 diff 为 14 个文件、新增 1251 行、删除 762 行（代码与测试面为 6 个修改文件 +121/−758 加五个新文件；其余为本登记更新与 registry 刷新）。 | 独立评审以 AST 归一化逐函数对比核实行为保持（动作偏置数值、全部 vec-env kwargs、`main()` 编排与日志文案），实测 `import train` 不加载 torch，并将四份 `--help` 输出与基线逐字节对比。training/policy/eval/architecture 聚焦回归 `251 passed`、`2 skipped`（一个基线即红的 GBK 控制台用例已在未打补丁基线复现）。落地树 maintained smoke 为 `406 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。独立评审以零 blocker 批准候选，并裁决保留两个新入口 smoke 测试。 |
| I10 飞行塑形字段税消除 | `accepted` | `codex/redundancy-consolidation` 上的 `c1a8b2f4` | 把 `FlightShapingRuntimeInputs` 与 `StepEvaluationBatchConfig` 共享的 89 个 config-static 塑形字段提为单一 X-macro 清单（`src/core/mission/runtime/detail/flight_shaping_shared_fields.inc`）；两个结构体字段块、batch-prepare 逐字段拷贝与 FlightShaping `def_rw` 绑定改由该唯一 owner 宏展开。字段类型、名称、默认值、顺序与含 118 个属性的 Python input 表面保持不变；两个任务动态 `target_*` 字段保持手写以保成员顺序。最终 diff 为 8 个文件、新增 136 行、删除 373 行（代码面 5 个文件 +128/−367、净删除 239 行；其余为本登记更新与 registry 刷新）。 | 在隔离 worktree 重建 `ef_core`、`ef_py`、`ef_test`，`ef_test_all` 通过。字段审计 118/118 与 112/112 逐项一致（类型/名称/默认值/顺序）；新旧构建 parity 探针输出 546 行逐字节相同。execution/facade/world-batch/architecture 聚焦回归 `282 passed`、`1 skipped`（window-loop 字符串风格断言与本机 winsock 链接两类既有失败已在未打补丁基线上原样复现）。maintained smoke 为 `380 passed`、`45 subtests passed`。`git diff --check` 通过。独立评审发现一项登记口径 blocker；登记修复后，最终复核以零 blocker 批准候选。 |
| I11 EffectsEvent 字段面 owner 整合 | `accepted` | `codex/redundancy-consolidation` 上的 `cc3bdf1a` | 把 135 字段的 `EffectsEvent` 清单提为 X-macro 列表 `src/runtime/contracts/detail/effects_event_fields.inc`（48 个事件独有 + 87 个与 `EffectsResult` 重叠条目），契约结构体、`apply_effects_result_fields` 投影与 Python `def_rw` 绑定改由该唯一 owner 展开。重叠计数修正了此前 88 字段的估计：`destroy_missile` 是 result 侧控制标志，从未被拷贝。`weapon_launch_adapter.h`（`EffectsEventSnapshot`、`make_effects_event`）确认编译不可达（仅文本形状测试引用），登记为待删候选、本轮未动。契约形状测试改为文本展开 include，使字段从清单移除时断言仍会失败。最终 diff 为 8 个文件、新增 197 行、删除 433 行（代码与测试面为 4 个修改文件 +39/−429 加 150 行清单；其余为本登记更新与 registry 刷新）。 | 独立评审对照改前源码逐项核实全部 135 字段（类型/名称/默认值/顺序）与 87/48 划分，复跑 204 项 engagement/bindings/air-combat/architecture 定向测试与 `ef_test`（113 用例、18,753 断言）全绿，并复现跨构建 parity 探针（dir() 序列与逐字段默认值与主线全等）；结论 approve、零 blocker。在合并落地树（I8+I9+I10+I11）上增量重建通过 `ef_test_all`，engagement/execution 回归 `87 passed`、`226 subtests passed`，maintained smoke 为 `406 passed`、`45 subtests passed`。`git diff --check` 通过。 |
| I12 运行时引导 import 面迁移 | `accepted` | `codex/redundancy-consolidation` 上的 `a1c33d43` | 把 167 个维护面调用者（tests 116、tools 42、python 8、examples 1；共 174 处 direct import，为该基线上唯一存在的 import 形式）从兼容壳 `python.testing.runtime` 迁移到 canonical owner `python.runtime_bootstrap`。兼容壳保留为 archive 专用 re-export facade 并更新 docstring；`tools/archive/` 的十一个调用者按 I4 先例留在兼容路径。新增 AST 治理门禁（`tests/architecture/governance/test_runtime_bootstrap_owner.py`，已入 smoke 清单）禁止维护面再 import 兼容壳。经三方合并落到 I13 头上（相邻 import 块编辑）；字节码缓存噪声已从移植中剔除。最终 diff 为 173 个文件、新增 253 行、删除 183 行（代码与测试面为 169 个修改文件 +181/−179 加门禁测试；其余为本登记更新与 registry 刷新）。 | `compileall` 通过；两个新治理门禁在落地树上通过。落地树 maintained smoke 为 `410 passed`、`45 subtests passed`（基线 409 加新门禁）。流 worktree 全量回归 `2095 passed`、`3 skipped`，十三项已知基线红名单全部复现；其余失败均非 import 路由回归——`ef_py` 导入错误是与并发 worktree 重建的瞬时竞争，artifact 路径与 worktree 路径参数化失败属 worktree 环境效应，`weapon_guidance_realism` 套件在迁移前基线树（匹配构建）上以完全相同的 45 例失败复现，判定为维护 smoke 门禁之外的本机基线红。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方核验移植并复跑落地门禁。 |
| I13 world-batch vec-env 兼容壳调用面收口 | `accepted` | `codex/redundancy-consolidation` 上的 `86bd0fcd` | 把维护中的调用面（生产 `python/` 3 个模块、`tools/diagnostics` 5 个脚本、8 个普通 import 测试文件、3 个 monkeypatch 型 `tests/world_batch` 文件）从 `python.rl.runtime.world_batch_vec_env` 迁移到 canonical 的 `python.rl.runtime.world_batch.vec_env` 与 `_observation_mixin` owner，每个 monkeypatch 点按符号真实 owner 重新定向。`examples/viz/runtime/viz_session.py`（被架构测试钉住）、`tests/gpu` 中的 subprocess 字符串与归档面刻意留在兼容壳上。维护调用者归零后，兼容壳从带七项可变转发表的 `types.ModuleType` 子类收缩为纯 re-export 薄壳；新增三用例 AST 门禁（`tests/architecture/runtime_facade/test_world_batch_owner_imports.py`，已入 smoke 清单）禁止维护面再 import 兼容壳并钉住其 `__all__` 与实际 re-export 一致。配置键字符串 `runtime.world_batch_vec_env=true` 未触碰。最终 diff 为 25 个文件、新增 165 行、删除 63 行（代码与测试面为 21 个修改文件 +50/−59 加 89 行门禁测试；其余为本登记更新与 registry 刷新）。 | world-batch/multi-agent/facade/training/policy 聚焦回归 `291 passed`、`1 skipped`、`104 subtests passed`；全部 world-batch monkeypatch 测试（含三个重定向文件）通过。其余六个失败为该 worktree 本机既有的 flecs 链接/构建产物缺口，已按基线问题复现归因。落地树 maintained smoke 为 `409 passed`、`45 subtests passed`（基线 406 加三个新门禁测试）。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方核验逐字节移植并复跑落地门禁。 |
| I14 编译不可达死接口面删除 | `accepted` | `codex/redundancy-consolidation` 上的 `c04da9a8` | 删除编译不可达的 `src/core/engine/weapon_launch_adapter.h`（503 行，`EffectsEventSnapshot` 与 `make_effects_event`）及其 5 项、332 行的文本/迁移形状测试，并移除 CI smoke 清单中的对应条目。全树引用与符号审计确认无生产 include、CMake、工具、Python 或契约 spec 消费者，仅存文本级测试读取。另两个孤儿候选以具体证据保持 `held`：`information_transform_contracts.h` 被九个架构片段探针编译且被活跃 review 文档点名；`same_window_edge_validation.h` 被六个片段探针编译。最终 diff 为 6 个文件、新增 6 行、删除 840 行（代码与测试面为 3 个文件 −836；其余为本登记更新与 registry 刷新）。 | 在流 worktree 重建 `ef_core`、`ef_py`、`ef_test`，`ef_test_all` 通过。落地树 maintained smoke 为 `405 passed`、`45 subtests passed`（基线 410 精确减去被删的五项形状测试）。流侧大范围回归（`663 passed`、`12 failed`、`5 errors`）复现的全部是未触碰表面的本机既有基线项（路径分隔符匹配、GBK/PDF 探针、fragility 数值基线、陈旧 allowlist 与 facade 文本形状断言），与 I12/I13 已记录的本机基线清单一致；均与被删表面无关。`git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方核验移植、suite 清单合并与落地门禁。 |
| I15 测试归档退役与测试墙裁决 | `accepted` | `codex/redundancy-consolidation` 上的 `3342c435` | 逐文件引用扫描确认零功能消费者后，退役整个 `tests/archive` 树（52 个文件：历史 raw-`UniversalEnv` 回归规范、scripted-bridge 规范与遗留 leader 契约）——套件清单、conftest 与 runner 无引用，三个提及该路径的测试仅将其用作排除模式或合成 tmp fixture；按域核对了维护面的覆盖替代。双语 `tests/` 与 `tests/contracts/unit/training/` README 改为记录退役并指向 git 历史，不再携带断链。两项裁决以证据记为 `held`：weapon-guidance 权威表模块含实质测试逻辑（内核调用、fixture、断言链）而非纯数据表；契约 spec 参数化不被维护 runner 支持，均未强行纳入本轮。最终 diff 为 59 个文件、新增 10 行、删除 4,210 行。 | 提及归档路径的三个门禁/审计测试在落地树上通过（`11 passed`）。maintained smoke 为 `405 passed`、`45 subtests passed`，与基线持平，证实归档对 smoke 无贡献。`git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方复跑引用扫描与落地门禁。 |
| I16 tools 脚手架收敛 | `accepted` | `codex/redundancy-consolidation` 上的 `aa1ec513` | 把 diagnostics、geometry 与 maintenance 七个证据包（约 78 个脚本）中手写的 `REPO_ROOT`/`sys.path` 引导块收敛到 `python.runtime_bootstrap`（`ensure_repo_imports`/`repo_root`/`resolve_repo_path`），保留直接以文件路径运行所需的两行 path hint 与依赖 chdir 的脚本语义。同构标量/IO helper 提升到 `tools/diagnostics/common.py`（`finite_float`、`finite_float_or_none`、`mean_finite`、`native_stdout_to_stderr`、参数化 `write_json_output`），分块文件/文本哈希复用 `tools/maintenance/retained_artifacts/manifest_integrity` owner；全部诊断能力、CLI 面与输出格式保持不变。语义不等价的变体保留本地并注释（三种 `_mean` 空输入约定、非 resolve 的路径展示 helper、weapon-probe schema 的 `_finite_float`），未触碰任何 `write_retained_*` 输出路径。最终 diff 为 87 个文件、新增 991 行、删除 1,923 行（代码面 84 个文件 +985/−1919；其余为本登记更新与 registry 刷新）。 | 聚焦回归与改前失败集逐项一致（`tests/tools` 7 failed/94 passed；fire-timing 契约 19 passed；process-probe 41 passed；damage_model 4 failed/247 passed/5 errors 含已知 GBK 项）。maintained smoke 为 `405 passed`、`45 subtests passed`。三个区域八处 CLI `--help` 冒烟通过。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方核验移植（剔除流侧误触的跟踪态字节码噪声）并复跑落地门禁。 |
| I17 I8-I11 复审修复 | `accepted` | `codex/redundancy-consolidation` 上的 `1cfca742` | 修复 I8-I11 验收后复审发现的三项可执行问题。SB3 checkpoint 加载迁到无 bootstrap 副作用的 `python.rl.policy_checkpoint` owner，使根入口 `evaluate.py` 保留 installed-wheel 回退；`tools/eval/sb3_eval_base.py` 则继续保留诊断工具本地 fail-closed bootstrap 与兼容 re-export。Batch observation 和 visual backend 现在分别拥有语义独立的 owner，并同时驱动 runtime normalizer 与 world-batch benchmark CLI，不再借用 `FLIGHT_SHAPING_BACKENDS`。I9 的 `train.py` 基线从误记的 927 行修正为 1,008 行，I10 错误的 `118/15` 属性表述修正为 118 属性的 input 表面。最终 diff 为 11 个文件、新增 143 行、删除 60 行。 | env-config、evaluate、历史 checkpoint 与训练入口聚焦回归为 `27 passed`、`1 skipped`。八个变更 Python 文件通过内存语法编译与禁用缓存的 Ruff 检查。维护双语审计为 77/77 文档对同步，`git diff --check` 通过。 |
| I18 diagnostics episode/env 构造收敛 | `accepted` | `codex/redundancy-consolidation` 上的 `abed924c` | 将三个 diagnostics 采集器（`event_credit_head` offline/online、fire-timing `real_update`）共有的 reset/step/终止/缓冲调度/close 壳收敛到 `tools/diagnostics/common.py`，域缓冲留在调用方，online value bootstrap 以 episode-end 钩子表达。weapon-employment process probe 与 post-launch assessment benchmark 的标准单世界构造路径改由 `build_single_world_batch_execution_runtime` 承担，全部非默认参数与注入式 VecEnv 兼容缝保持不变。多世界/依赖 VecEnv 私有面的 benchmark、语义不同的 rollout 循环与 kernel 直构探针按设计保留本地。本轮以如实记录的净增行数换取采集壳的单一 owner：含登记与 registry 刷新共 9 个文件、新增 426 行、删除 200 行（代码面 6 个文件 +420/−196）；后续新增采集器复用壳而非复制循环。 | 改前改后聚焦回归逐项一致（fire-timing 19；process-probe 41；event-timing 7；world-batch 113 passed、1 skipped、20 subtests）。offline/real 两步真实采集报告改前改后逐字节相等。七个 CLI `--help` 冒烟、Ruff 与 `git diff --check` 通过。落地树 maintained smoke 为 `407 passed`、`45 subtests passed`（I17 基线向 smoke 内文件新增了两个 env-config 守卫）。按所有者指示未派发独立评审代理；由编排方核验逐字节移植并复跑落地门禁。 |
| I19 retained 写出单一 owner 收敛 | `accepted` | `codex/redundancy-consolidation` 上的 `33501818` | 在 `tools/maintenance/retained_artifacts/manifest_integrity.py` 新增 `write_and_hash_json()`，把七个证据包中 24 处 `write_retained_*` 的 23 处收敛为委托共享 owner 做 JSON 序列化与 SHA-256 哈希的薄壳，函数名、签名、返回值与字节级输出约定全部保持（含 Windows `\r\n` 写出行为与 `candidate_artifacts` 的 `_sha256_text` manifest 哈希路径）。唯一残余 `release_governance/source_release_signoff` 因其三遍 manifest 稳定化语义独立而保留本地实现。新增 260 行对拍套件（`tests/tools/test_retained_write_parity.py`）内嵌被删实现作参照，逐函数逐 payload 证明字节相等。最终 diff 为 28 个文件、新增 487 行、删除 164 行（代码与测试面为 24 个修改文件 +205/−160 加对拍套件；其余为本登记更新与 registry 刷新）。 | 对拍套件 `69 passed`、`4 skipped`（skip 为被删实现自身在 GBK locale 下即崩溃的 Unicode 用例；共享 owner 显式 UTF-8 属严格改进）。`tests/tools` 失败集不变（7 failed，含对拍新增后 163 passed）。`tests/architecture/damage_model` 的 retained/manifest/sha256 子集不变（2 failed、38 passed、1 error，均为既有本机项）。落地树 maintained smoke 为 `407 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方核验逐字节移植并复跑落地门禁。 |
| I21 契约 spec extends 继承与近重复对收敛 | `accepted` | `codex/redundancy-consolidation` 上的 `3c86574a` | 解除 I15 中「契约 spec 参数化缺乏 runner 支持」的 `held`：`python/testing/contracts/common.py` 现支持 `extends`——本文件目录优先、仓库根回退的路径解析，递归复用既有 `_deep_merge`，循环检测与四层链深限制；`extends` 键不进入有效 spec。naval threat-ROE 对收敛至 `tests/contracts/_base/naval_screen_threat_roe_base.json`，scripted-takeoff 对收敛至 `_base/scripted_takeoff_base.json`；四份有效 spec 经内嵌金测证明与收敛前基线逐键相等；base spec 位于 runner 收集 glob 之外（`collected_base_specs=0`）。wrappers 簇因叶级相似度仅 0.79–0.96 保持本地。最终 diff 为 11 个文件、新增 409 行、删除 104 行（代码与测试面为 5 个修改文件 +63/−100 加两份 base spec 与 extends 测试；其余为本登记更新与 registry 刷新）。 | 有效 spec 对拍 4/4 逐键相等。四个收敛契约与 10 项 CI contract suite 全部通过；runners/scenario 回归 `73 passed`。落地树 maintained smoke 为 `408 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方以暂存 blob 一致性核验移植，并复跑契约套件、extends 测试与落地 smoke。 |
| I20 探针 CLI 共享参数组 | `accepted` | `codex/redundancy-consolidation` 上的 `2ca09145` | 在 `tools/diagnostics/common.py` 落地 `add_probe_run_args`/`add_model_load_args`/`add_json_out_arg` 构造器：canonical dest 固定 underscore，underscore/hyphen 双注册（别名用 `help=SUPPRESS`，保证每个 `--help` 面逐字节不变）。迁移七个满配探针 CLI（weapon-employment 过程探针、event-credit offline/online、fire-timing real_update/chain_breakpoint/learnability_audit/window_position_sweep），删除 57 处手写 `add_argument`；部分匹配脚本列入后续批次。与 I18 同理，本轮以净增行数投资共享 owner，使后续探针不再复制脚手架。最终 diff 为 11 个文件、新增 314 行、删除 68 行（代码面 8 个文件 +308/−64；其余为本登记更新与 registry 刷新）。 | 七个迁移脚本改前改后 `--help` 输出逐字节相等；三处双别名解析 dest 一致。聚焦回归 `60 passed`（fire-timing 契约 19、process-probe 41）。落地树 maintained smoke 为 `408 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方以暂存 blob 一致性核验移植并复跑落地门禁。 |
| I22 DTO 单源生成器骨架 | `accepted` | `codex/redundancy-consolidation` 上的 `db97d478` | 新增纯标准库的声明式 DTO schema 包（`tools/maintenance/dto_schema/`）：带扩展位（预留 `python_name`/`readonly`/`hidden`/`json_key`）的 schema 模型、X-macro 解析器、`--check`/`--write` 生成器 CLI 与机器可读 manifest，以及描述新 DTO 家族三步接入流程的 README。以既有两个 X-macro 清单为试点（89 字段 flight-shaping、135 字段 EffectsEvent 含 48/87 分组）：再生成逐字节一致、`--write` 幂等、注入默认值漂移会被非零退出与 unified diff 捕获。新鲜度架构门禁已入 maintained smoke 清单。此为 DTO 单源化分期方案（episode、world-batch、engagement、command、GPU 家族）的地基。最终 diff 为 13 个文件、新增 958 行、删除 4 行（代码与测试面为 10 个新文件 +952；其余为本登记更新与 registry 刷新）。 | 生成器 `--check` 在落地树上报告两个试点 up-to-date，新鲜度门禁通过（`1 passed`）。maintained smoke 为 `408 passed`、`45 subtests passed`（基线 407 加新鲜度门禁）。流 worktree 的 execution/engagement 聚焦回归 `82 passed`、`226 subtests passed`。Ruff 与 `git diff --check` 通过。按所有者指示未派发独立评审代理；由编排方以暂存 blob 一致性核验移植，并复跑生成器检查、门禁与落地 smoke。 |
| I23 episode evaluation DTO 单源化 | `accepted` | `codex/redundancy-consolidation` 上的 `9d23b947` | 统一体系蓝图 W2 关键期迭代。十二个新 schema（233 字段）把 safety/termination、conditional-objective、mission-nav/observation/step-info 与 reward 余量家族纳入单源治理：四个 mission-runtime 头文件的字段块与 `bindings_episode.cpp` 对应段改由生成的 X-macro 清单展开，十四个生成 Python builder（加包 init）并入统一新鲜度命令（`generate.py --check`，29 个产物，含污染检测）。`safety.py` 的十六处机械配置赋值迁移到生成 builder；派生/条件赋值刻意保留手写。只读 products DTO 不生成赋值器，混合类赋值器跳过只读字段。登记残余：execution 组合家族的三个连续块（8 字段 outcome、8 字段输入前缀、9 字段产品前缀）留待后续。最终 diff 为 54 个文件、新增 2,393 行、删除 560 行（代码面 10 个修改文件 +315/−554 加 41 个生成/schema/测试文件；其余为本登记更新与 registry 刷新）。 | 独立评审（本关键期专门派发）逐项核实 233 个宏化字段与改前头文件精确一致（类型/名称/默认值/成员顺序）、687 属性绑定面经静态与运行时双重比对精确一致、safety 迁移映射正确；其两项 blocking（builder 新鲜度未入主门禁、只读 products 生成必崩赋值器）修复后，最终复核以零 blocker 批准。execution/mission 聚焦回归 `136 passed`、`234 subtests passed`；`ef_test_all` 通过；落地树 maintained smoke 为 `408 passed`、`45 subtests passed`。Ruff 与 `git diff --check` 通过。 |
| I24 tasking-contracts 中立层抽取 | `accepted` | `codex/redundancy-consolidation` 上的 `70e75454` | W2 关键期迭代（运行时基座 B-1 步）。把 `gym_envs` 对 `python.rl` 任务派发纠缠中与 profile 无关的切面抽到零依赖新包 `python/tasking_contracts/`（任务指令/阶段词表、bridge 视图与命令链同步 seam、`LeaderDecisionState`、计时归一、脚本化控制器）。全部迁移符号经 `assertIs` 套件证明旧路径 re-export 壳与新定义同一对象。十一个原纠缠 `gym_envs` 文件已零 `python.rl` 引用，`gym_envs.leader_env` 导入期不再拉入 `python.rl.runtime.leader_window_runtime`；十四个文件保留治理台账残余（必须触达 `python.rl` 内部 air/ground/naval 适配器的 profile 派发函数），由「精确允许清单」AST 门禁锁定——新增引用与清单过期均判红。两处既有 bridge 治理断言改指向搬迁后的规范位置且未弱化。登记后续项：残余派发的依赖倒置或包 init 懒化（B-2）、评审指出的 AST 门禁盲区（相对/动态导入形式）。最终 diff 为 44 个文件、新增 1,986 行、删除 1,285 行（代码面 30 个修改文件 +257/−1,281 加 11 个新文件共 1,723 行；其余为本登记更新与 registry 刷新）。 | 独立评审（本关键期专门派发）核实迁移定义与改前源码逐行一致、十四文件残余台账与独立 AST 扫描精确一致、认可「不强拆派发」的裁决（依赖倒置注册表并非更低风险的替代）、确认治理断言改写保持原意且 raw-write 检查更强；结论 approve、零 blocker、三条非阻塞（门禁盲区、私有符号口径、统计修正）。聚焦回归：leader+scenario `120 passed`，world-batch `113 passed, 1 skipped`，runtime 失败集与基线逐字节一致。落地树 maintained smoke 为 `426 passed`、`45 subtests passed`（基线 408 加 18 个新门禁/兼容测试）。Ruff 与 `git diff --check` 通过。 |
| I25 统一架构计划立项 | `accepted` | 同一分支；哈希在下一轮登记刷新时补入 | 文档迭代。确立[统一架构计划](../unified_architecture_program/README.zh.md)为剩余架构级统一工作的冻结路线图（轨道 T1-T7：DTO 单源化收尾、运行时基座统一、C++ 结构边界、exact-runtime 对齐、声明式配置、测试基建理性化、终局残余审计），本登记表保留为单一迭代台账。把该计划对纳入严格双语面（`STRICT_PLAN_SUBTREES`）与 `docs/plan` 索引，并补上索引中此前缺失的整合计划条目。最终 diff 为 8 个文件、新增 183 行、删除 7 行，含登记与 registry 刷新。 | 双语 registry 现覆盖 78 对，全部同步；维护链接审计：158 份文档、2,608 个链接、零问题。maintained smoke 不变。Ruff 与 `git diff --check` 通过。纯文档迭代；落地门禁由编排方执行。 |

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
