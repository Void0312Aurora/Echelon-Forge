<!-- Machine-translated draft generated on 2026-05-18 from examples/README.md. Review before treating this file as authoritative. -->

# 示例

`examples/` 现在主要作为维护的输入/配置表面，加上一小套轻量级固定装置和可视化资源。

此目录不再是演示、遗留实验或替代训练入口点的综合性集合。

## 结构

- `config/`
  - 维护的 JSON 配置输入，用于训练、诊断、预制件和单位数据库。
- `scenarios/`
  - 仅用于示例的场景固定装置。规范的维护场景位于仓库级别的 [scenarios/README.md](../scenarios/README.md)。
- `viz/`
  - 可视化资源以及（如果存在）示例可视化入口点。

## 当前入口表面

- [config/training/README.md](config/training/README.md)
  - 维护的训练配置入口点和状态分类。
- `config/database/`
  - 由运行时/内容加载器使用的单位、飞机和模块数据库输入。
- `config/diagnostics/`
  - 维护的基准测试和诊断配置输入。
- `config/prefabs/`
  - 由场景和内容输入使用的共享预制件/配置片段。
- [scenarios/README.md](scenarios/README.md)
  - 仅用于示例的场景固定装置的范围说明。

## 使用说明

- 对于维护的配置、测试和工具，优先使用仓库相对路径 `scenarios/...`。
- 将 `examples/scenarios/` 视为固定装置或兼容性示例，而不是维护的训练/评估场景的规范来源。
