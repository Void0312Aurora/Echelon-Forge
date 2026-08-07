# WP Closure Lane Policy

语言版本：

- 英文主文：[wp_closure_lane_policy.md](wp_closure_lane_policy.md)
- 中文辅文：`wp_closure_lane_policy.zh.md`

状态：`2026-05-20`，用于降低主实现路径上的 WP 文档同步工作量。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/standards/wp_closure_lane_policy.md`
Owner: `engineering/automation`
Last verified: `2026-08-07`

本规范把实现进展和发布闭合分开。目标是在保持 WP 记录可追踪的同时，
避免 README、review、双语和归档同步拖慢架构/代码工作。

## 状态模型

- `Mergeable`：代码、focused tests、英文 canonical 任务记录和命名残余项已足够完整，
  实现流可以继续推进。
- `Blocked`：该流已经达到声明的轮次或风险预算，且在缺少 replacement、owner decision
  或 public API change 的情况下，无法安全删除、迁移或完成某个 surface。`Blocked`
  必须包含 owner、reason、replacement condition、validation gap 与 forced review
  trigger。
- `Closed`：在 `Mergeable` 基础上，已完成验收审查、README/index 同步、
  必需双语伴生文档、归档判断和残余项 owner 追踪。

文档 closure 不应重新打开实现范围。若 closure 发现技术缺口，应记录 blocked residual，
或把它送回新的实现流，而不是靠改写 verdict 抹平问题。

`Blocked` 是有效 close-out record，但不是 acceptance result。当剩余工作不安全或定义不清时，
它应优先于反复追加 partial waves。

## 主实现流

主实现流负责：

- WP 范围和非目标。
- 代码与 focused tests。
- 当前实现所需的英文 canonical 任务或 cluster 记录。
- 精确验证命令和结果。
- 带 owner、原因和下一步的 residual ID。

主实现流应避免在活跃实现期间编辑 README 索引、review 索引、archive tree
和大范围双语表面，除非这些改动确实阻塞当前代码或测试变更。

主实现流还应保持明确的文档预算。创建更多 planning files 不是中性的；如果超出预算，
该流应停止并 re-baseline，而不是继续产出 queue 或 ledger。

## Closure Lane

closure lane 负责：

- 发布 acceptance review。
- 同步 simulation architecture README 与 review README。
- 补齐 Tier A 或 WP acceptance surface 所需双语伴生文件。
- 处理 archive 或 superseded review 归位。
- 清理交叉引用和坏链接。
- 更新最终 `Closed` 状态。

closure lane 应在并行 cluster 返回 handoff packet 后，以串行 integration pass
方式运行。它适合分配给 subagent，因为工作边界清楚、主要是机械同步，
并且可通过审计工具验证。

## Worker Handoff Packet

每个实现 worker 应返回：

```md
Stream: WPx-A / WPx-B / ...
Scope: 一句话范围
Status: pass | fail | blocked
Touched files:
Commands run:
- <exact command> -> passed | failed | blocked
Evidence:
- implementation/test/doc evidence
Residuals:
- ID / owner / reason / next WP or stream
Integration notes:
- shared files left for closure lane
Closure impact:
- README/index update needed?
- required zh companion?
- archive or superseded-review action?
```

## 自动化

分配或验收 closure lane 前，先运行只读 closure audit：

```bash
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9
```

当某个 WP 预期没有 error-level closure gap 时使用 `--strict`；需要把清单传给
worker 时使用 `--json`。

该审计只覆盖 WP task/review closure，不替代语义审查、测试执行或人工双语审阅。
