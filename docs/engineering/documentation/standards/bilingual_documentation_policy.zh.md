# 双语文档规范

语言版本：

- 英文主文：[bilingual_documentation_policy.md](bilingual_documentation_policy.md)
- 中文辅文：`bilingual_documentation_policy.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/bilingual_documentation_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

状态：`2026-08-08`，当前维护中文档语言布局的权威规则。

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
- `docs/systems/physics/work/issues/physics_engine_roadmap.md`
- `docs/systems/physics/work/issues/physics_engine_roadmap.zh.md`

## 权威规则

- 如果英文主文与中文辅文不一致，以英文 `.md` 为准。
- 机器翻译草稿在人工审校并移除草稿标记前，不视为权威文档。
- 只有 `.zh.md` 而缺少英文主文，属于迁移过渡态，不是目标稳态。

迁移期补充规则：

- 如果某份维护文档当前只有 `.zh.md`，它仍可作为工作输入使用，但应在下一轮相关批次中补齐英文主文。

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
- 仍通过迁移期遗留 plan 表面路由的稳定计划权威：
  - `docs/plan/README.md`
  - `docs/plan/architecture/**`
  - `docs/plan/runtime_facade/**`
  - `docs/plan/cooperative/**`
- 仍通过迁移期遗留 task 表面路由的稳定任务导航：
  - `docs/task/README.md`
  - `docs/task/task_archive_convergence_plan_20260518.md`
  - `docs/task/*/README.md` 下的子项目导航页
  - `docs/task/flight_dynamics/*/README.md` 下的更深层导航页

Tier B：英文主文，中文辅文可选或延后

- `docs/*/work/issues/` 下归属于 owner 的草拟计划和开放问题
- `docs/plan/exact_runtime/**` 这类非权威计划分支
- 仍处于高频变更中的 task 计划、checkpoint、freeze、analysis 长文

Tier C：历史、归档、临时稿与本地保留面

- `docs/Archive/` 下的历史归档材料
- `docs/**/archive/` 下的本地 archive 镜像
- `docs/**/temp/`、`docs/temp/`、`docs/plan/results/`
  下的临时稿、草稿和本地分析记录
- `docs/plan/architecture/review/` 下的本地架构审查草稿

Tier A 需要双语配对。Tier B 可以先维护英文主文。Tier C 默认不纳入持续维护判定。

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

对于新文档：

1. 先写英文主文 `.md`。
2. 再生成或撰写 `name.zh.md` 作为中文辅文。
3. 审校术语、链接和代码引用。
4. 当该文档成为真实入口时，再把它加入最近的 README 导航。

对于现有仅中文文档：

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
- Tier B 文档即使中文延后，也已明确采用英文主文维护
- 维护中的英文主文不再有大段中英混排
- 机器翻译草稿已审校或被明确标记
- Tier A 配对文档变更后，双语簇注册表已同步更新
- 迁移后本地链接仍然有效

以下临时/历史/本地目录不纳入上述主验收口径：

- `docs/**/temp/`
- `docs/temp/`
- `docs/Archive/`
- `docs/**/archive/`
- `docs/plan/results/`
- `docs/plan/architecture/review/`

## 相关文档

- [docs/README.md](../../../README.zh.md)
- [已归档的双语迁移记录](../../../plan/archive/documentation_bilingual_migration_plan_20260518.zh.md)
- [document_alignment_map.md](../reference/document_alignment_map.zh.md)
