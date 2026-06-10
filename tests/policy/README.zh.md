# Policy 测试

`tests/policy/` 存放策略侧行为的维护态回归测试：

- policy routing 与 route statistics
- execution-policy head surface 与 hybrid action distribution
- auxiliary training update path
- first-event timing label 与 event-head update contract
- grouped stopping loss contract
- policy bootstrap 与 control-config parity

文件名应描述被测试的能力。`A6`、`A7`、`M3S1`、`M3S2` 等历史机制标签
可以在需要追溯时保留在具体测试名中，但不应继续定义新的测试文件或目录名。
