# Training 测试

`tests/training/` 存放训练编排面的维护态契约：

- bootstrap 与 CLI acceptance
- active training entry gate
- diagnostics callback 日志契约
- 确定性的 fault-localization probe

文件名应描述被保护的训练能力。air-combat、naval、A6、A7、M3S1、M3S2、
N4 等领域、阶段或机制标签可以在需要追溯时保留在具体测试名中，但不应继续
定义新的测试文件名。

临时学习探针和一次性调试脚本应先放在 `tools/diagnostics/`；稳定后再提升到
上面的维护态测试面。
