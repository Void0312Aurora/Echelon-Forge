# 文档双语化迁移计划

语言版本：

- 英文主文：`documentation_bilingual_migration_plan_20260518.md`
- 中文辅文：[documentation_bilingual_migration_plan_20260518.zh.md](documentation_bilingual_migration_plan_20260518.zh.md)

状态：`2026-05-18`，当前执行中的迁移计划。

本文档把仓库文档迁移为“英文主文、中文辅文”的双语体系，同时保证迁移过程可批处理、可持续推进。

## 基线盘点

本地在 `2026-05-18` 的盘点结果：

- `docs/` 下 Markdown 总数：`195`
- `*.zh.md` 中文辅文或仅中文文档：`57`
- 缺失英文 peer 的 `.zh.md` 文件：`56`

当前主要问题：

- 一些维护入口页仍然在同一文件中中英混排
- 一些目录仍默认把中文长文当作主阅读路径
- 之前的迁移范围把过多 `docs/task/**` 内容当成了稳定双语维护面
- 某些入口 README 仍直接深链到 dated 的 status、taskboard、freeze
  快照，而不是稳定的本地 README 导航
- `docs/plan/archive/`、`docs/plan/results/` 这类本地保留目录可能在某个工作区存在，但不会同步到共享远端，因此维护导航不应把它们当成 canonical 入口

## 目标状态

- 英文 `name.md` 成为维护主文。
- 中文 `name.zh.md` 成为辅文。
- 维护中的入口页不再大段中英混排。
- 默认双语维护面应当有意保持小而稳定，并集中在权威层。
- 高频变更的 task/history 长文可以先保持英文主文，而不要求即时双语对等。
- 翻译按目录批处理，并配套统一工具和审校流程。

## 迁移优先级

### 阶段一：入口面

先处理决定导航体验的入口文件：

- `docs/README.md`
- `docs/plan/README.md`
- `docs/task/README.md`
- `docs/standards/README.md`
- 活跃方向的 README，如 `docs/task/flight_dynamics/README.md`
- 权威索引页，如 `docs/plan/architecture/README.md`

目标：

- 先消除最显眼、最容易制造冲突预期的中英混排入口页

### 阶段二：权威主文

为维护中的权威计划文档补齐英文主文：

- `docs/plan/architecture/*.zh.md`
- `docs/plan/runtime_facade/*.zh.md`
- `docs/plan/cooperative/*.zh.md`
- `docs/manual/*.md`
- 之后按需要为 `docs/standards/` 长文补中文辅文

目标：

- 让 repo 级计划与架构主线可以从英文主路径直接阅读

### 阶段三：稳定任务导航面

保持 task 树可导航，但不把每一份 dated 工作记录都纳入严格双语 SLA：

- `docs/task/README.md`
- `docs/task/task_archive_convergence_plan_20260518.md`
- `docs/task/*/README.md` 下的子项目入口
- `docs/task/flight_dynamics/*/README.md` 下更深一层的导航页

目标：

- 让贡献者从稳定 README 表面进入 task 区域，而不是从 dated 的
  status/taskboard/freeze 文档进入

### 阶段四：按需补齐活跃任务长文

只有在下列条件满足时，才补齐详细 task 长文：

- 该 task 文档仍是当前活跃执行权威
- 不能由本地 README 或更新的 current-status 文档替代为稳定入口
- 该工作线的维护者明确需要该切片的中文对等版本

目标：

- 保持英文主线可读，同时避免把整棵 task/history 树变成永久翻译跑步机

## 批处理执行规则

翻译任务应使用便于复核的批次：

- 每批只处理一个同级目录
- 每批 `4-8` 个文件
- 控制源文总量，便于术语检查
- 不把 architecture、task、standards 的文档混在同一批

目录内推荐顺序：

1. README / 索引
2. authority 或 contract 主文
3. 仍真实活跃的 current status / progress checkpoint
4. 只有在仍然活跃时才继续下探 analysis 与 implementation package

## 每批验收门槛

- 英文 peer 已生成到正确的 `name.md` 路径
- 入口文档中的 `.md` / `.zh.md` 互链已补齐
- 相对链接仍可解析
- 代码标识符、路径、CLI 参数、条令名称未被误翻
- 机器翻译草稿标记已经人工确认、保留或移除

## 工具

当前维护工具：

- [tools/maintenance/translate_docs_batch.py](../../tools/maintenance/translate_docs_batch.py)

它支持：

- audit
- 按目录扫描
- `--only-missing`
- 分块 Markdown 翻译
- 为生成文件自动写入 draft note

## 示例命令

盘点当前文档树：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs
```

为一个维护中的权威目录回填缺失的英文 peer：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/plan/architecture \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

从审校过的英文主文生成中文辅文：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --files docs/plan/architecture/README.md \
          docs/standards/joint/README.md \
  --source-lang en \
  --target-lang zh
```

## 维护说明

- 后续维护应默认改英文主文。
- 中文辅文应优先跟随 Tier A 权威/导航面，但不应阻塞英文主线的快速更新。
- 如果某个方向变化很快，可以先落英文 peer；对于 Tier B task/history 长文，可以在下一批补齐中文，或不把它纳入强双语维护面。

## 整体迁移完成标准

当以下条件满足时，可视为维护中的文档表面已基本完成迁移：

- `docs/`、`docs/plan/`、`docs/task/`、`docs/standards/` 的维护入口已是英文主导
- Tier A 权威表面已具备双语配对
- 入口 README 不再大段中英混排
- task 树默认通过稳定 README 导航，而不是通过 stale dated 深链进入
- 翻译工具和 audit 流程进入日常文档维护

## 相关文档

- [docs/standards/governance/bilingual_documentation_policy.md](../standards/governance/bilingual_documentation_policy.md)
- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/plan/architecture/README.md](architecture/README.md)
