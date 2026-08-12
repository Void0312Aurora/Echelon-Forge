# 工作区工程

语言：
- 英文规范页：[README.md](README.md)
- 中文配套：`README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/workspace/README.md`
Owner: `engineering`
Last verified: `2026-08-13`

本 owner 管的是检出（checkout）的形状而非其内容：链接 worktree 放在哪里、其文件
归哪个账户所有、以及路径长到什么程度会让宿主工具打不开文件。构建配置、CI 流水线
与测试组织属于其他工程 owner。

## 当前权威

- [Worktree 与路径策略](worktree_and_path_policy.zh.md)：worktree 放置与生命周期、
  提权 shell 的属主陷阱、200 字符仓库相对路径预算，以及两者的修复手册。

## 执行面

| 执行面 | 约束内容 |
| --- | --- |
| [`tools/maintenance/audit_worktrees.py`](../../../tools/maintenance/audit_worktrees.py) | 只读审计：worktree 位置、`git status` 可达性、未跟踪残留。有任何 finding 即返回非零。 |
| [`tests/architecture/governance/test_path_length_budget.py`](../../../tests/architecture/governance/test_path_length_budget.py) | 相对路径预算的棘轮门禁，基线存于 `path_length_baseline.json`。 |
| [`tests/architecture/governance/test_worktree_audit_contract.py`](../../../tests/architecture/governance/test_worktree_audit_contract.py) | 审计脚本的分类契约，只针对合成清单运行。 |

审计脚本刻意不接入测试。仓库当前的 worktree 清单属于开发者本地状态，任何提交都
修不好它；若用门禁断言它必须干净，反而会在检出本来正常的机器上失败。请在 worktree
行为异常时、以及把机器交给他人之前运行该审计。

## 边界

- 本 owner 定义检出可以放在哪里、路径可以多长。
- 内容 owner 仍然决定存在哪些文件；路径预算只约束嵌套深度。
- 宿主级配置（注册表长路径开关、账户属主）在此仅作为诊断材料记录，不由本 owner 拥有。

## 复核触发条件

worktree 布局策略变化、路径长度预算或其基线重新生成、或上表任一执行面迁移/退役时，
更新本索引。
