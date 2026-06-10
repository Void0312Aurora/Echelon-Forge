# 标准化文档治理派发表

状态：`2026-06-10`，第一批 standards governance remediation 的派发表。

父子项目：[标准化文档治理](README.zh.md)

语言：

- 英文主文：[standards_documentation_governance_dispatch_queue_20260610.md](standards_documentation_governance_dispatch_queue_20260610.md)
- 中文辅文：`standards_documentation_governance_dispatch_queue_20260610.zh.md`

## 派发边界

本队列把 P1 triage 账本展开为有边界的工作包。它不授权新会话线程、生产路径 demo
domain、大范围源码重构，或把未接受任务工作提前提升为标准。

每个 packet 必须返回标准 worker packet：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 队列

| Packet | Gap | Owner | 目标 | 写集 | 非目标 | 必需验证 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SDG-A1` | GAP-001 | main thread | 解决 ground `TASK_MOVE` 与此前 static-hold 命名错配，但不释放动态地面机动。 | `src/components/domains/ground/tasking/**`、`docs/standards/ground/minimal_task_structure*`、受影响 tests/docs | 完整 ground movement、terrain、fires、sensing、runtime owner release | Ground tasking architecture tests；若 header 改动则聚焦 C++ build/test；双语 audit；`git diff --check` | P1 账本已接受 | 代码和标准命名一致，G0 静态限制仍明确 | pass |
| `SDG-A2` | GAP-003 | main thread | 在 joint command 标准中登记活跃 `MissionCommandCore` threat/target 字段。 | `docs/standards/joint/command_link_and_reporting_baseline*`；若证据要求则含受影响 command docs/tests | 新 command 字段；除非发现错配，否则不改 codec | Mission command roundtrip tests 或现有聚焦 command tests；双语 audit；Markdown inspection | P1 账本已接受 | 四个字段有 ownership classification，且不扩写 sensor/track 声明 | pass |
| `SDG-B1` | GAP-002 | documentation worker | 将活跃 mission observation modes 登记到 air/naval specialization owner。 | `docs/standards/air/obs*`、naval observation 标准或 naval README 小节、受影响 standards 索引 | Observation redesign、training/model 改动 | 聚焦 mission observation import/test；双语 audit；standards link check | SDG-A2 可并行；避免与 SDG-B2 同文件编辑 | Air/naval observation mode ownership 明确 | pass |
| `SDG-B2` | GAP-004 | documentation worker | 在同文件内容更新落地后刷新陈旧 status/date header。 | 陈旧 air、bridge、joint、naval standards header 和最近索引 | 字段合同编辑已分配给其他 packet | Markdown inspection；双语 audit | SDG-B1 和 SDG-A2 在重叠文件上完成 | 读者能判断每页是 current contract、planning 还是 held | pass |
| `SDG-C1` | GAP-005 | integration worker | 让 modularization planning 与当前 `src/*/domains` roots 对齐。 | `docs/standards/planning/modularization_plan*`、`docs/standards/README*`、`docs/standards/overview/document_alignment_map*` | 新源码模块树、大范围重构 | Structural boundary tests、Markdown inspection、双语 audit | 当前 split 后 domains roots 保持稳定 | Planning 页面有 current-layout 小节，或归档并带前向指针 | pass |
| `SDG-D1` | GAP-006 | held future worker | 仅在 MLF-3 任务验收后准入 weapon-effects standards。 | 未来 `docs/standards/air/*weapon*` 或 `docs/standards/weapons/**`；已接受 MLF-3 evidence docs | 仅凭未接受或 untracked 测试创建 standards entry | MLF-3 acceptance evidence、source admission gates、standards link check | MLF-3 acceptance 存在 | Standards owner 存在，或 held 状态仍明确 | held |
| `SDG-V1` | all | main thread | 在 remediation 批次后整合状态、验证证据和残余。 | 子项目 README/status/queue、父 review 索引、受影响 standards 索引 | 隐藏 partial；在 held 项解决前声明总体 accepted | 聚焦 pytest、双语 audit、`git diff --check` | 一个或多个 remediation packet 返回 | 已接受切片和 residual map 与证据一致 | planned |

## 分批提交建议

- 如果 `SDG-A1` 改 C++ identifier，应单独提交。
- `SDG-A2` 和 `SDG-B1` 若触及不同 standards owner，应分别提交。
- `SDG-B2` 只在重叠内容更新落地后提交。
- `SDG-C1` 会改变 planning authority 与读者预期，应独立提交。
- `SDG-D1` 在 acceptance trigger 出现前不得提交。

## 强制复审触发器

任一 packet 发现以下情况时，停止并重新划界：

- standards contract 与活跃 runtime test 冲突
- 必需代码 rename 跨越 public Python bindings 或序列化 scenario/config 字段
- Tier-A touched standards file 缺少双语 peer
- 需要创建新的 standards 顶层目录
- MLF-3 evidence 尚未 accepted，却被用作 current authority

## 集成说明

- 更宽的 governance pytest suite 当前因缺少 simulation-architecture WP 历史路径存在无关失败。
  除非同批修复那些旧测试，本子项目以 focused standards governance test 作为本地 gate。
- 默认双语 audit 当前报告一个本子项目外的既有英文 peer 缺口：
  `docs/standards/foundation/realism_authority_boundary.zh.md`。
