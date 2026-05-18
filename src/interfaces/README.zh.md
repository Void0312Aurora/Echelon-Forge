# `src/interfaces` 边界

`interfaces/` 保存外部语言、工具或集成边界。它负责把维护中的 C++ API 暴露出去，不拥有 simulation、mission 或 model 领域逻辑。

## 允许

- 语言绑定。
- 外部 ABI/API 适配。
- 轻量类型转换和错误映射。
- 只为绑定服务的小型 helper。

## 禁止

- mission-command JSON 业务解释。
- reward、termination、episode transition 或 physics 行为。
- 直接实现 runtime capability。
- 把训练配置或场景语义塞入绑定层。

## 子目录约定

- `python/`：nanobind Python module 和 Python 相关适配。

## 迁移备注

后续可评估把 `interfaces/python` 重命名为 `bindings/python`。在重命名前，新增绑定仍放在 `interfaces/python`，但必须保持“只绑定、不拥有领域逻辑”。
