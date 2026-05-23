# WP12-E Integration And Acceptance Handoff

状态：`2026-05-20` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp12_integration_acceptance_cluster_20260520.md](wp12_integration_acceptance_cluster_20260520.md)
- 中文辅文：`wp12_integration_acceptance_cluster_20260520.zh.md`

输入：

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.zh.md)
- [WP12-A Law 14 read-side enforcement](wp12_law14_read_side_enforcement_cluster_20260520.zh.md)
- [WP12-B agency role authority boundary](wp12_agency_role_authority_cluster_20260520.zh.md)
- [WP12-C information transformation surface](wp12_information_transformation_surface_cluster_20260520.zh.md)
- [WP12-D intent injection authority guard](wp12_intent_injection_authority_guard_cluster_20260520.zh.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

`WP12-E` 是串行 integration and acceptance handoff lane。它整合 A-D 的实现证据，
诚实记录 residuals，准备 acceptance review，并在 implementation streams
mergeable 后同步 task/review indexes。

它不得让 documentation closure 阻塞 implementation mergeability。

## 2. 范围

范围内：

- 收集 A-D touched files、tests、commands 与 residuals；
- 整理 shared validator naming 与重复 fixtures；
- 运行最终 focused validation set，或记录精确 blockers；
- 只有在 implementation evidence 存在后，才起草
  `wp12_information_agency_enforcement_acceptance_review_20260520.md` 及中文辅文；
- 把 route、README、review index 与 bilingual references 作为 closure-lane
  work 更新；
- 只有实际 acceptance 后才 archive 或 index。

范围外：

- 用 prose-only evidence 接受 gate；
- 把 WP12 扩大到 backend/fidelity 或 capability work；
- 隐藏 failed 或 blocked validation commands；
- 未先检查 worker handoff notes 就重写 worker-owned code。

## 3. 集成检查清单

必需检查：

- `WP12-A` 证据证明 focused Law 14 read-side enforcement 与显式
  diagnostics-only truth access。
- `WP12-B` 证据证明 role authority validation 与 rejected invalid-role
  fixtures。
- `WP12-C` 证据证明 selected slice 的 transformation vocabulary/evidence
  可机器检查。
- `WP12-D` 证据证明 authorized belief-to-intent 或 coordination injection
  通过 facade-compatible seam。
- Acceptance text 不声明完整 Agency Graph runtime、repository-wide Law 14
  coverage、backend/fidelity expansion 或完整 producer migration。

## 4. 验证命令

预期最终命令：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_policy_belief_boundaries.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP12
```

如果某个命令对 integration pass 过宽，记录实际运行的更窄命令和原因。

## 5. 验收评审形态

最终 review 应包含：

- verdict；
- `WP12-A` 到 `WP12-E` 的 gate verdict table；
- 精确 validation commands 与 observed outcomes；
- implementation notes；
- residuals and next plan；
- scope caveats。

planning 阶段不要求 review。缺少 acceptance review 表示 `WP12` open，而不是 failed。

## 6. 交付契约

返回：

- A-D stream status table；
- final validation commands 与 outcomes；
- acceptance review files created 或 blocked；
- README/route/review index touched files；
- residual register；
- next-WP recommendation，但不得在 WP12 evidence accepted 前打开 backend/fidelity。
