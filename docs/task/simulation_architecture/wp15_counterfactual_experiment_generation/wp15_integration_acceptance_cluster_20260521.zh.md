# WP15-F Integration And Acceptance Handoff

状态：`2026-05-21` accepted / serial closure lane complete。

语言版本：

- 英文主文：[wp15_integration_acceptance_cluster_20260521.md](wp15_integration_acceptance_cluster_20260521.md)
- 中文辅文：`wp15_integration_acceptance_cluster_20260521.zh.md`

输入：

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.zh.md)
- WP15-A 到 WP15-E worker handoffs
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.zh.md)
- `tools/maintenance/wp_doc_closure_audit.py`

## 1. 目的

`WP15-F` 是串行发布与验收 lane。它在 implementation streams 变为 mergeable 之后运行。
它记录精确 validation outcomes、residuals、acceptance status、README/route sync、
bilingual closure 与剩余 blockers，同时不重写其他 worker 的代码流。

## 2. 范围

范围内：

- 收集 A-E touched files、tests、blockers、residuals 与 integration notes；
- 运行 focused WP15 validation commands；
- 在实现状态明确后更新 README 与 route status；
- gates 通过时创建最终 acceptance review 与中文辅文；
- 保持 residuals 显式。

范围外：

- 在 worker handoff 后继续实现 A-E 代码，除非是小型 integration fixes；
- 隐藏 failed 或 blocked validation；
- 声明 full snapshot/restore、broad generator runtime、maintained counterfactual rollout
  或 score-to-support promotion。

## 3. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Implementation first | A-E 必须 mergeable，closure 才能把 WP15 标为 accepted。 |
| Exact commands | Acceptance 记录精确 command strings 与 outcomes。 |
| Residual honesty | Unsupported restore、generator runtime、facade 或 binding gaps 必须保持可见。 |
| Bilingual/index sync | 英文与中文 task/review/index docs 保持对齐。 |

## 4. 验证命令

预期 closure validation：

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_*.py
python -m pytest -q tests/scenario/test_wp15_*.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
python tools/maintenance/wp_doc_closure_audit.py --wp WP15
```

如果添加 public facade 或 binding surfaces，则纳入 worker handoffs 中给出的相关 focused
runtime/binding commands。

## 5. Handoff Contract

返回：

- final A-E status table；
- exact validation command outcomes；
- residual register；
- 如创建 acceptance review，返回其路径；
- touched README/route/index files；
- 若验收尚无正当依据，列出必须保持 open 的 blockers。
