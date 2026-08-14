# 双语文档规范

语言版本：

- 英文主文：[bilingual_documentation_policy.md](bilingual_documentation_policy.md)
- 中文辅文：`bilingual_documentation_policy.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/bilingual_documentation_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-13`

状态：`2026-08-13`，当前维护中文档语言布局（含英文单语 work/evidence 面与只读的
Tier D 密封证据面）的权威规则。

本文档定义仓库如何拆分英文与中文文档，使主线文档保持可读、可批处理翻译、可审计。

本规范适用于 Git 跟踪的维护中文档。归档、临时稿与仅本地材料默认不进入双语维护判定。

## 目标

- 英文 `.md` 是维护主线中的 canonical 文档。
- 中文 `.zh.md` 是辅文，不再与英文在同一文件中大段混排。
- 维护中的文档应尽量避免段落级中英混写。
- 翻译任务应支持按目录批处理，并允许通过外部 API 自动化。

## 文件配对规则

- 英文主文：`name.md`
- 中文辅文：`name.zh.md`
- 英文主 README：`README.md`
- 中文 README 辅文：`README.zh.md`

示例：

- `docs/engineering/documentation/README.md`
- `docs/engineering/documentation/README.zh.md`
- `docs/domains/air/standards/pilot_action_contract.md`
- `docs/domains/air/standards/pilot_action_contract.zh.md`

Tier B work 文档（如
`docs/systems/physics/work/issues/physics_engine_roadmap.md`）只维护英文主文，
不再保留 `.zh.md` 镜像。

## 权威规则

- 如果英文主文与中文辅文不一致，以英文 `.md` 为准。
- 机器翻译草稿在人工审校并移除草稿标记前，不视为权威文档。
- 在 Tier A 严格双语面上，只有 `.zh.md` 而缺少英文主文属于迁移过渡态，不是目标
  稳态。

迁移期补充规则：

- 如果某份 Tier A 文档当前只有 `.zh.md`，它仍可作为工作输入使用，但应在下一轮
  相关批次中补齐英文主文。

该过渡规则不适用于 Tier D。密封日期证据包内的仅中文页面本身就是被记录下来的
制品，不是待翻译积压项；补一份英文主文也不会让它更权威。参见下文「Tier D」。

## 维护分层

本仓库采用“分层维护”而不是“整棵 `docs/` 树都要强双语持续维护”的模式。

Tier A：严格双语维护面

- 根导航：`docs/README.md`
- `docs/project/`、`docs/architecture/`、`docs/domains/`、`docs/systems/`、
  `docs/learning/`、`docs/operations/`、`docs/engineering/` 和 `docs/research/`
  下的项目级与 owner 根导航
- `docs/engineering/automation/` 下的 Agent 权威、提示词与规则
- 保留参考索引：`docs/reference_artifacts.md`
- 已准入严格维护面的 owner-local standards 与 reference，包括
  `docs/engineering/documentation/standards/` 和
  `docs/engineering/documentation/reference/`
- `docs/domains/air/standards/`、`docs/domains/ground/standards/` 与
  `docs/domains/naval/{standards,reference}/` 下已迁移的 Air、Ground、Naval
  标准/reference
- `docs/domains/joint/` 下已迁移的 Joint common-core 与 service-profile 权威
- `docs/learning/standards/` 下已迁移的 policy/model architecture 标准
- `docs/architecture/standards/`、`docs/systems/standards/` 和
  `docs/research/standards/` 下的跨域 owner standards
- `docs/operations/` 下的面向操作者 reference 与 how-to
- 完成 plan/task 迁移后形成的稳定 owner README、standards 与已准入 reference
  入口，包括 architecture、domain、systems、learning、operations 与
  engineering-testing 路由

Tier A 的成员资格不会随 owner 前缀延伸进其 `work/` 子树：路径中含 `work`
目录组件（例如 `docs/operations/visualization/work/` 或
`docs/domains/joint/work/`）的文档一律属于 Tier B，即使其外层 owner 面属于
Tier A。

Tier B：英文单语 work/evidence 面

- `docs/*/work/issues/` 下归属于 owner 的草拟计划和开放问题
- `docs/*/work/active/` 下仍然当前有效但高频变更的 owner-local active work、
  详细计划、checkpoint、evidence 记录与 analysis 文档
- Tier B 文档只维护英文主文，不保留 `.zh.md` 镜像；`2026-08-12` 的 work 面
  双语收缩已移除既有 work 层镜像
- 仅当 owner 把某文档明确提升进入 Tier A 严格双语面时才增设中文辅文；提升的
  流程是把两个文件路径（`.md` 与 `.zh.md`）登记进
  `tools/maintenance/document_scope.py` 的 `PROMOTED_WORK_DOCUMENTS`
  allowlist，然后用 `clusters --write --pair <pair_id>` 刷新新配对记录
- 既有 work README 页可保留 `README.zh.md` 导航辅文；中文导航页直接链接英文
  work 文档是预期稳态
- 遗留的仅中文 work 文档（缺英文主文的 `.zh.md`，或中文内容仍是超集的文档）
  在英文主文补齐前保留中文文件，不得仅为满足本层级而删除

Tier C：历史、归档、临时稿与本地保留面

- `docs/Archive/` 下的历史归档材料
- `docs/**/archive/` 下的本地 archive 镜像
- retired `docs/plan/` 与 `docs/task/` 根下的全部剩余材料；其路径必须含
  `archive` 组件
- `docs/**/temp/` 和 `docs/temp/` 下的临时稿、草稿和本地分析记录

Tier D：密封日期证据

- `reviews/` 子树下归属于 owner 的评审与验收证据包，例如
  `docs/systems/effects/reviews/<packet>_<YYYYMMDD>/` 或
  `docs/learning/reviews/<packet>_<YYYYMMDD>/`，含整棵包内子树
  （`evidence/`、`retained_artifacts/`、`data_collection/` 及同级目录）
- Tier D 文档记录的是「在某个明确日期上审阅到的内容」。它是只读的：不因后续
  行为变化而回写；新的结论应进入新的日期包或 `work/active/`
- Tier D 不承担双语 SLA：不翻译、不做镜像，也永远不排队补齐缺失的英文或中文
  对应页
- 密封包内的仅中文页面本身就是被保留的制品，不适用上文「权威规则」中的仅中文
  过渡条款
- Tier D 内容常被 retained-artifact manifest 中的 SHA-256 条目钉死。修改被钉死
  的字节（哪怕只是修正链接层级这类外观改动）都会使 pin 失效，因此必须获得
  owner 的明确授权，并在同一轮中级联重算受影响链路上的全部 pin，且在包内
  README 中留痕。
  [A2 毁伤模型证据包 README](../../../systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md)
  的 `2026-08-13` 条目是已落地的先例：按 owner 指令修正了一条 ledger 链接，
  随后把 `sha256`、`content_hash`、`size_bytes` 沿 manifest 与 gate 制品逐级
  重算，直到链路终止
- 若某条 pin 无法重算，就保持文件原样，把不一致记录为继承状态，而不是去「修」
  字节

由于这些路径规则会相互重叠，分层优先级明确规定如下：

1. 即使位于 `reviews/` 子树下，归档或临时副本仍属 Tier C；
2. 即使位于 `reviews/` 子树下，owner 已明确提升进严格双语面并登记进簇注册表
   的配对仍属 Tier A，因为其双语 SLA 是活的；
3. 其余 `reviews/` 文档属于 Tier D；
4. 其他全部文档属于 Tier B。

[tools/maintenance/document_scope.py](../../../../tools/maintenance/document_scope.py)
中的 `classify_document` 是该判定的唯一真源，`docs/` 下每个受跟踪的 Markdown
文件都恰好落入一层。`tests/architecture/governance/test_document_tier_census.py`
普查测试会把该划分及四层计数与提交进仓库的基线快照对齐。

Tier A 需要双语配对。Tier B 除明确提升外不维护中文辅文。Tier C 默认不纳入
持续维护判定。Tier D 禁止新增双语配对。

## 写作规则

- 在条件允许时，每个文件正文只保留一种自然语言。
- 不要在维护中的主文里按 bullet 或段落交替写中英文。
- 代码、路径、CLI 参数、API 名称、环境变量和标识符保持不翻译。
- 人类可读的标题、正文、说明、链接标签应翻译。
- 只有在搜索或术语对齐明显受益时，才使用少量括号式双语补注，例如
  `mission command (任务指挥)`。
- 指向本仓库内部文件的 Markdown 链接应使用相对路径，而不是绑定到某台机器的绝对工作区路径。

允许保留混合写法的例外：

- 路径，如 `python/rl/runtime/world_batch_vec_env.py`
- 标识符，如 `MissionCommand`、`CommandLink`
- 正式出版物名称、产品名、来源标题
- 简短术语注释

## 顶部语言导航约定

维护中的双语文档对，建议在开头加入简短语言导航：

```md
Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)
```

如果辅文尚未补齐，应明确写明，而不是在正文里继续大段混排。

## 簇注册表约定

维护中的双语配对还应进入机器可读的簇注册表：

- [双语文档簇](../reference/bilingual_document_clusters.zh.md)
- 注册表文件：`../reference/bilingual_document_clusters.json`

每条簇记录跟踪：

- `pair_id`
- `source_of_truth`
- `last_verified`
- 当前 `english_hash` / `chinese_hash` 基线值

注册表用于判断是否存在“只改了一侧、另一侧还没跟上”的情况。翻译批次完成后，应刷新受影响的 pair 记录，让基线保持最新。

运行说明：

- 簇哈希会刻意忽略文件开头的机器翻译草稿标记，并对行尾做归一化，因此仅仅是
  工作区检出格式（如 `LF`/`CRLF`）不同，不会触发全树双语漂移噪声

审计解释规则：

- `audit` 的结果只表示“相对当前基线”的状态，不是语义真相本身。
- `docs/Archive/` 与 `docs/**/archive/` 默认不属于维护中的漂移判定面，即使其中保留了双语镜像，也只用于追溯。
- 审阅变更文档对后，使用可重复的
  `clusters --write --pair <pair_id>` 参数只刷新这些记录，再运行 `audit`。
- 完成整个维护面的双语审阅后，可以运行全量 `clusters --write`。canonical 路径或
  registry 路径迁移也可以执行全量重建，但前提是迁移前的基线 audit 为 clean，且
  registry diff 能证明无关记录的路径、hash 与核验日期保持不变。不得用全量重建
  掩盖无关的历史分歧。
- `needs-en-update` / `needs-zh-update` 通常表示单侧后续维护未跟上。
- `diverged` 表示两侧都相对记录基线发生了变化，应先人工核对最新意图，再把它定性为真实漂移。

## 翻译工作流

对于新的 Tier A 维护文档：

1. 先写英文主文 `.md`。
2. 再生成或撰写 `name.zh.md` 作为中文辅文。
3. 审校术语、链接和代码引用。
4. 当该文档成为真实入口时，再把它加入最近的 README 导航。

对于新的 Tier B work 文档，只写英文主文 `.md`；除非该文档被提升到 Tier A，
不要创建 `.zh.md` 镜像。

对于 Tier D 密封证据，完全没有翻译环节：不要把这些目录纳入翻译批次，也不要用
`--include-local-only` 把它们喂给翻译工具。

对于 Tier A 现有的仅中文文档：

1. 保留当前 `.zh.md` 文件。
2. 在同目录生成英文 `name.md` 主文。
3. 在人工审校前，为生成结果保留机器翻译草稿标记。
4. 审校完成后，把 README 导航改为优先链接英文主文。

## 批处理规则

翻译批次应按同级目录组织，而不是全仓库随意抽文件混跑。

建议批次规模：

- 一次只处理一个目录
- 每批 `4-8` 个文件
- 每批保持单一主题，例如
  `docs/engineering/documentation/standards/` 或 `docs/domains/joint/`
- 每批结束后做一次链接和路径检查

这样更容易保持术语一致，也便于人工复核。

## 工具规则

本仓库维护中的批量翻译工具是：

- [tools/maintenance/translate_docs_batch.py](../../../../tools/maintenance/translate_docs_batch.py)

工具要求：

- 通过兼容 OpenAI 风格的外部 API 调用翻译模型
- 保留 Markdown 结构、代码块和相对链接
- 自动把仓库内部文件链接规范化为相对路径
- 翻译前支持 audit
- 支持 `--only-missing`，便于增量重跑

## 验收标准

当一个目录或维护切片满足以下条件时，可视为达到双语维护目标：

- Tier A 入口 README 优先链接英文主文
- 该切片下 Tier A 权威文档已配齐中文辅文
- Tier B 文档只保留英文主文；例外仅限明确提升的配对与等待补齐英文主文的
  遗留中文来源
- 维护中的英文主文不再有大段中英混排
- 机器翻译草稿已审校或被明确标记
- Tier A 配对文档变更后，双语簇注册表已同步更新
- 迁移后本地链接仍然有效

以下密封/临时/历史/本地目录不纳入上述主验收口径：

- `docs/**/reviews/` 密封证据包（已登记的 Tier A 配对除外）
- `docs/**/temp/`
- `docs/temp/`
- `docs/Archive/`
- `docs/**/archive/`

已退役的 `docs/plan/results/` 与 `docs/plan/architecture/review/` 两条于
`2026-08-13` 从本清单移除：这两个路径在仓库中已不存在，而 `docs/plan/` 下留存的
材料本就被 `archive` 规则覆盖。

## 相关文档

- [docs/README.md](../../../README.zh.md)
- 已归档的双语迁移记录 (`git show 3dc34673:docs/plan/archive/documentation_bilingual_migration_plan_20260518.zh.md`)
- [document_alignment_map.md](../reference/document_alignment_map.zh.md)
