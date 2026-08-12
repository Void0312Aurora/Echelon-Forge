# C++ 依赖与 DTO 残差

语言：
- 英文规范版：[cpp_dependency_and_dto_residuals.md](cpp_dependency_and_dto_residuals.md)
- 中文伴随版：`cpp_dependency_and_dto_residuals.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/cpp_dependency_and_dto_residuals.md`
Owner: `architecture/cpp-boundaries`
Last verified: `2026-08-08`
Content status: 从已完成 T6 账本抽取的所有者本地页面；保留的边是设计问题，
不授权修改 include direction。

## 范围

本文负责需要经过实测架构或 schema 迁移的 C++ 依赖边与 DTO 所有权决策，
不负责校准行为和测试环境缺陷。

## 保留的依赖边

T6 矩阵已收敛 missile-seeker 边，仍保留以下五条：

1. `core/engine/world_batch_runtime.cpp` → GPU interaction-broadphase 类型；
2. `core/engine/world_batch_runtime.h` → execution-episode controller；
3. `core/engine/world_batch_runtime.h` → GPU visual runtime；
4. world-batch visual compatibility helper → GPU visual runtime；
5. `runtime/contracts/world_batch_contracts.h` → mission episode-batch preparation 类型。

前四条需要 GPU/engine 或 facade/mission 接缝；第五条嵌入大型 mission 所有的
嵌套 DTO 图，是 T1 级 schema 所有权问题；只移动一个头文件会反转依赖或复制整张图。

## 相关 DTO 残差

`ExecutionBatchStepResult` 因 `std::vector<std::array<double, 4>>` 字段对当前
X-macro 预处理器不具备 token 安全性，仍保持手写。`RecentEngagementEvents` 仍是
未来候选，且不在已完成账本的写集内。两者都不是实施任务。

## 证据边界与晋级门槛

来源矩阵保留在
[已完成的 T6 账本](../../../plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.zh.md)。
只有在完成消费者普查、依赖方向门禁、必要的 ABI/绑定 parity 证据，并通过独立评审的
架构或 DTO-family 决策后，才能关闭某条边。仅反转依赖或制造第二份手工维护形状的移动
不能通过门槛。

## 非目标

- 不得通过修改 include-direction allowlist 隐藏仍开放的边。
- 不得仅凭名称相似把 mission 所有的聚合类型移入中立 contracts。
- 不修改已归档的计划记录。
