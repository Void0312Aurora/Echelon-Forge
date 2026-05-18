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
- `docs/task/` 下大量 dated snapshot 仍没有英文 peer
- `docs/plan/archive/`、`docs/plan/results/` 这类本地保留目录可能在某个工作区存在，但不会同步到共享远端，因此维护导航不应把它们当成 canonical 入口

## 目标状态

- 英文 `name.md` 成为维护主文。
- 中文 `name.zh.md` 成为辅文。
- 维护中的入口页不再大段中英混排。
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
- 之后按需要为 `docs/standards/` 长文补中文辅文

目标：

- 让 repo 级计划与架构主线可以从英文主路径直接阅读

### 阶段三：活跃任务线

按目录批处理当前活跃工作线：

- `docs/task/flight_dynamics/`
- `docs/task/naval/`
- `docs/task/air_combat/`
- `docs/task/review/`
- `docs/task/python_rl/`

目标：

- 让 live engineering taskboard、checkpoint、unresolved issues 可以从英文导航进入

### 阶段四：长尾

补齐剩余 dated snapshot 和较低优先级文档：

- `docs/task/common_air_naval/`
- `docs/task/diagnostics_eval/`
- `docs/task/code_redundancy/`
- `docs/task/viz/`
- `docs/manual/`、`docs/forward/` 中仍在使用的遗留说明

目标：

- 清掉 active tree 中残留的中文孤岛

## 批处理执行规则

翻译任务应使用便于复核的批次：

- 每批只处理一个同级目录
- 每批 `4-8` 个文件
- 控制源文总量，便于术语检查
- 不把 architecture、task、standards 的文档混在同一批

目录内推荐顺序：

1. README / 索引
2. current status / progress checkpoint
3. taskboard / plan / unresolved issues
4. 更深层 analysis 和 implementation package

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

为一个活跃目录回填缺失的英文 peer：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/task/flight_dynamics \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

从审校过的英文主文生成中文辅文：

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --files docs/task/flight_dynamics/README.md \
          docs/plan/architecture/README.md \
  --source-lang en \
  --target-lang zh
```

## 维护说明

- 后续维护应默认改英文主文。
- 中文辅文应跟随同一 scope，但不应阻塞英文主线的快速更新。
- 如果某个方向变化很快，可以先落英文 peer，再在下一批补齐中文辅文。

## 整体迁移完成标准

当以下条件满足时，可视为 active tree 的双语迁移基本完成：

- `docs/plan/`、`docs/task/`、`docs/standards/` 的维护入口已是英文主导
- 活跃目录中的 `.zh.md` 文件都已有英文 peer
- 入口 README 不再大段中英混排
- 翻译工具和 audit 流程进入日常文档维护

## 相关文档

- [docs/standards/bilingual_documentation_policy.md](../standards/bilingual_documentation_policy.md)
- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/plan/architecture/README.md](architecture/README.md)
