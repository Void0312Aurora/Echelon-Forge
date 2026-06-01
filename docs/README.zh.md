<!-- Machine-translated draft generated on 2026-05-18 from docs/README.md. Review before treating this file as authoritative. -->

# 文档索引

`docs/` 汇集了当前仓库维护的架构笔记、规划材料、任务记录、标准及参考手册。

将此目录用作导航表面，而非证明每一条历史笔记仍是活跃的实现权威。

## 从这里开始

- [plan/README.md](plan/README.md)
  - 架构/程序规划、冻结的执行范围以及规划治理说明。
- [plan/documentation_bilingual_migration_plan_20260518.md](plan/documentation_bilingual_migration_plan_20260518.md)
  - 以英文为主的当前文档树双语推广计划。
- [task/README.md](task/README.md)
  - 聚焦的任务文档、实现包和进度检查点。
- [standards/README.md](standards/README.md)
  - 联合/服务/平台建模基线及专业说明。
- [standards/bilingual_documentation_policy.md](standards/governance/bilingual_documentation_policy.md)
  - 规范语言、文件配对及批量翻译策略。
- [manual/](manual)
  - 代码层映射、引擎能力说明、物理清单及面向操作员的手册。
- [forward/README.md](forward/README.md)
  - 尚未冻结为实施任务的前瞻性想法。
- [reference_artifacts.md](reference_artifacts.md)
  - 为仍然重要的线路保留的配置/场景/制品来源说明。

## 权威说明

- `plan/`、`task/`、`standards/` 和 `manual/` 是维护的入口界面。
- 维护文档默认受仓库级 Apache-2.0 许可覆盖，除非具体文件或保留的第三方
  artifact 另有说明。第三方资产、数据集、来源摘录和保留输入 artifact 保留
  其自身的权利和许可证状态；见 [../LICENSE](../LICENSE) 和
  [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。
- 严格双语维护面并不覆盖整棵文档树，而是聚焦在入口导航、标准/治理、操作手册和稳定计划权威面。
- 高频变更的 task 历史、dated checkpoint 以及 forward 想法文档，默认应按英文主文维护；只有被明确提升的较小切片才需要持续双语对等。
- 维护中的文档正逐步转为英文规范的 `.md` 文件，可选配中文 `.zh.md` 配套文件；避免将混合语言页面作为目标稳态。
- `Archive/` 保留了历史设计材料和已废弃的路径。它可用于追溯来源，但不是当前工作的默认权威来源。
- `temp/` 为临时空间，不应视为维护中的真实来源。

## 使用规则

- 如果某个任务需要修改代码，建议先阅读相关的 `plan/` 或 `task/` 条目，再对照当前代码树进行验证。
- 如果某个文档链接到历史制品，请在将其视为可操作的入口点之前，确认目标仍在工作空间中存在。
