# 测试工程

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/testing/README.md`
Owner: `engineering/testing`
Last verified: `2026-08-08`

本 owner 覆盖全仓测试组织、收集与覆盖率治理、测试基础设施，以及跨 owner
验证约定。它不拥有领域行为 contract；带日期 review 也不能覆盖当前测试或相关
技术标准。

## 当前权威

- [测试索引](../../../tests/README.zh.md)
- [已知测试基础设施残差](reference/known_test_infrastructure_residuals.zh.md)
- [测试系统残差治理 issue](work/issues/test_system_residual_governance/README.zh.md)
- [测试系统治理验收包](reviews/test_system_governance_20260621/README.zh.md)

`reviews/` 下其他文件是带日期的支撑记录。其计数与实现观察在重新核验前只应视为
快照。

## 路由边界

- 领域与 runtime owner 定义必须满足的行为。
- 测试工程定义全仓 gate、收集、分类和基础设施残差的表达方式。
- 覆盖率数据只证明 evidence packet 记录的测量源码集与命令。
- 旧归档路径下已完成的 task/plan 包只是 provenance，不是当前测试权威。

## 重新核验触发条件

测试根、CI lane、覆盖率所有权、strict-xfail 策略或 owner-local issue/review
路由变化时，更新本索引。
