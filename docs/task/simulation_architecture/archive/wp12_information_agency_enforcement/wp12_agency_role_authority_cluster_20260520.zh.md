# WP12-B Agency Role Authority Boundary

状态：`2026-05-20` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp12_agency_role_authority_cluster_20260520.md](wp12_agency_role_authority_cluster_20260520.md)
- 中文辅文：`wp12_agency_role_authority_cluster_20260520.zh.md`

输入：

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)

## 1. 目的

`WP12-B` 让 `AgentRole` five-part schema 在第一个 maintained authority slice
中变成可执行边界。它验证 maintained action 或 coordination output 在被视为
authorized 前，具有 role、authority scope、information-state source、
decision-model reference 与 action interface。

这是 Agency Graph boundary，而不是完整 Agency Graph runtime。

## 2. 范围

范围内：

- 为 maintained paths 添加或扩展 `AgentRole` validation helpers；
- 拒绝缺失、未知或不兼容的 authority scopes；
- 拒绝与 consumer maintained/diagnostics 状态不兼容的 information-state sources；
- 拒绝与产出的 action 或 coordination packet family 不匹配的 action interfaces；
- 增加 binding/runtime/architecture tests，证明 accepted 与 rejected roles。

范围外：

- scripted、learned、human、LLM 或 MCTS agents 的完整 decision-model dispatcher；
- 覆盖每个 information producer 的完整 role-based access control；
- orchestration UI 或 mission editor work；
- capability-bundle migration；
- backend/fidelity promotion。

## 3. 候选实现接缝

编辑前检查：

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/mission/test_policy_contract_shape.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`

优先方式：

- 在 contract/facade boundary 引入可复用 validation，而不是把 role table
  硬编码到单个测试；
- 第一个 slice 的 authority vocabulary 保持窄且显式；
- 尽量保留既有 DTO compatibility，但 maintained authorization 要 fail closed。

## 4. Gate 规则

| Boundary | 必需行为 |
|----------|----------|
| Valid maintained role | 声明 role、authority scope、information-state source、decision-model reference 与 action interface。 |
| Missing role field | maintained authorization 中被拒绝。 |
| Incompatible information source | 除非路径被显式标为 diagnostics-only，否则拒绝。 |
| Incompatible action interface | 在 intent injection 前拒绝。 |
| Unknown authority scope | 除非显式加入 accepted vocabulary，否则 fail closed。 |

## 5. 验收测试

最低测试：

- valid role 授权 focused maintained action 或 coordination path；
- 缺少 authority scope 时失败；
- maintained role 使用 diagnostics-only/truth source 时失败；
- role action interface mismatch 时失败；
- binding 或 Python-visible shape 保留 role fields；
- tests 明确说明这不是完整 Agency Graph runtime dispatch。

## 6. 交付契约

返回：

- touched contract/facade/binding files；
- accepted authority vocabulary 与 rejected cases；
- 新增或更新的 tests；
- 精确 commands run 与 outcomes；
- 完整 Agency Graph runtime 的 blockers 和 residuals；
- 给 `WP12-D` 与 `WP12-E` 的 integration notes。
