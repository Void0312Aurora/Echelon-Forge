# WP16-E Generated Documentation And Closure Automation

状态：`2026-05-21` complete / generated documentation automation accepted。

语言版本：

- 英文主文：[wp16_generated_documentation_automation_cluster_20260521.md](wp16_generated_documentation_automation_cluster_20260521.md)
- 中文辅文：`wp16_generated_documentation_automation_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)
- `tools/maintenance/wp_doc_closure_audit.py`

## 1. 目标

`WP16-E` 处理 post-WP9 过程中暴露出的文档瓶颈。它不应替代 canonical design docs
或人工 acceptance reviews，而是通过 machine-readable status 与 generated summaries
减少 closure 的手工同步，让 closure workers 可以核对结果，而不是在实现期间手工改每个 README 行。

## 2. 范围

范围内：

- 扩展或包裹 closure-audit tooling，输出 WP status、task-doc inventory、
  review readiness、missing peers 与 generated summary hints；
- 定义 WP16 stream states 的 machine-readable status source；
- 添加稳定的 generated-output fixtures 或 tests；
- 文档化哪些 summary 是 generated hints，哪些才是 canonical authority；
- 让主实现 worker 不被 README/review chores 阻塞。

范围外：

- 自动接受一个 WP；
- 从 generated output 重写 canonical scope docs；
- 未经审阅翻译规范性文档；
- 编辑与文档自动化无关的实现代码。

## 3. 交付物

- Maintenance tool update、generated-status fixture 或独立 closure summary command。
- 测试证明输出稳定且不会意外修改 docs。
- 说明 generated 与 canonical authority 边界的文档。
- 给 WP16-F closure 的 handoff notes。

## 4. Gate 规则

| Gate item | Pass condition |
|-----------|----------------|
| Machine-readable status | closure tooling 能消费 stream status source。 |
| Non-mutating default | audit/summary commands 默认只读，除非显式 generation mode。 |
| Stable output | tests 或 fixtures 证明 WP16 输出确定。 |
| Authority boundary | generated summaries 是 hints；acceptance 仍是 reviewed document。 |

## 5. 建议验证

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16
python -m pytest -q tests/tools/test_wp_doc_closure_audit.py -k "wp16 or status or summary"
```

如果现有 tool-test 文件不存在，worker 可以添加 focused tooling test 或 fixture，并报告所选命令。

## 6. 交接契约

返回：

- touched files；
- generated status 或 summary command；
- 精确验证命令和结果；
- generated/canonical authority boundary；
- 给 WP16-F 的 notes。
