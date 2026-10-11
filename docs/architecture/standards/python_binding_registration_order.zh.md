# Python binding 注册顺序

语言：
- 英文规范页：[python_binding_registration_order.md](python_binding_registration_order.md)
- 中文配套页：`python_binding_registration_order.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/python_binding_registration_order.md`
Owner: `architecture/python-bindings`
Last verified: `2026-10-10`

诊断模块 `ef_py` 与生产 facade-only 模块共用
`bindings_runtime_detail.h` 中的一条有序注册链，nanobind DTO 注册顺序因此只维护一份。

两种模式以相同顺序注册 16 组运行时 DTO 和 facade。诊断模式在 tasking-world DTO 之后、facade
之前插入 `bind_runtime_engine(m)`，保留原始 raw engine 的依赖位置；生产模式省略该调用。

该 helper 是注册顺序契约，而不是通用循环。新增运行时切片必须显式插入，并由架构测试保护，防止
两种构建模式的类型可见性和签名解析发生漂移。
