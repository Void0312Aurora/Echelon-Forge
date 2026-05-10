# `src/tools` 边界

`tools/` 保存开发期工具、诊断工具和实验验证入口。这里的代码可以调用 runtime API 做探测，但不构成维护中的库 API 或训练主线。

## 允许

- 一次性诊断工具。
- 性能或 parity 探针入口。
- 辅助开发的命令行程序。

## 禁止

- 被 `runtime/facade`、`core/` 或 `interfaces/python` 反向依赖。
- 定义主线 component、system、model 或 facade contract。
- 作为默认训练或 simulation 路径的一部分。

## 子目录约定

- `experimental/`：未进入维护主线的实验工具。

## 迁移备注

工具代码若要进入主线，应先迁移到对应层级并补充冻结计划、测试和 README 边界说明。
