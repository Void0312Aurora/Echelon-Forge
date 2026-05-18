<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/README.md. Review before treating this file as authoritative. -->

# Service Profile 总览

本目录定义以美军公开资料为基线的军种 profile。

当前纳入：

- [US Air Force](air_force.md)
- [US Army](army.md)
- [US Navy](navy.md)
- [US Marine Corps](marine_corps.md)

配套的平台专用补充标准当前仅有：

- [Air 平台专用标准](../air/README.md)

## 1. 使用原则

这些文档不是要把项目锁死成“军种百科”，而是为了回答三个问题：

1. 各军种真实的战术组织与控制口径是什么？
2. 哪些层级适合进入 tight-loop runtime？
3. 哪些层级应只作为 scenario / campaign / operation 元数据？

## 2. 统一结论

四个军种都不支持把“行政编制树”直接塞进 tight-loop RL。

更合理的做法是：

- 把高层军种/联合层保持为任务发布与资源分配层
- 把 tight-loop runtime 放在真实的 tactical unit 上
- tactical unit 的具体形态由各军种 profile 决定
