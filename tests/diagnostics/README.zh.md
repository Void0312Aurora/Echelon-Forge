# 诊断工具 README

`tests/diagnostics/` 包含探索性和调试导向型脚本。

这些脚本不被视为契约回归测试。它们之所以独立存放，通常是因为：

- 运行较长的探索循环
- 输出丰富的人类可读跟踪信息
- 依赖于可选的训练/运行时包
- 用于调查失败原因，而非断言某个单一稳定的不变量

当某个诊断行为稳定为确定性回归时，优先将其迁移至：

- `tests/contracts/` 并配以精简的执行器，或
- `tests/` 中一个小型、聚焦的测试（如果 contracts 不适合）

此文件夹本身并非通用单元/运行时测试的归宿。如果某个文件开始在 `pytest` 下断言稳定的不变量，它应当移回主 `tests/` 目录树，而不是留在此处。

目前，此文件夹中的活跃探索脚本已被清理。当前唯一留下的维护文件是
`test_diagnostics_import_order.py`，它是 diagnostics/runtime import-order 行为的
pytest 回归，不是探索性脚本；等 import-order ownership 明确后，应迁移到主测试域。

如果在此添加新的诊断脚本，它们应是临时的，并明确走向以下两条路径之一：

- 提升至 `tools/diagnostics/` 作为维护人员使用的常备工具，或
- 在行为稳定后迁移至 `tests/contracts/` / 聚焦的 `tests/` 目录。
