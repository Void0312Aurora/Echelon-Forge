# ADR：类型化机制端口与递归组合

语言：
- 英文规范页：[typed_mechanism_ports_adr.md](typed_mechanism_ports_adr.md)
- 中文配套页：`typed_mechanism_ports_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/typed_mechanism_ports_adr.md`
Owner: `architecture/mechanism-contracts`
Last verified: `2026-10-12`

**状态：** 待评审的资格验证设计；不启用生产路径。

## 决策

采用独立的机制图描述层，并将其编译到现有 composition 与 stage 契约。不新增第二套运行时
执行引擎，也不引入无类型的 `execute(anything)` ABI。机制适配器声明带版本的输入/输出端口、
单位、坐标系、时钟语义、可见性、所需能力、状态所有权和效果义务。

编译器必须在 provider 或 world 发布前完成图验证，生成仅用于资格验证的规范化图产物，再通过
现有 composition requested/resolved 产物和 native execution graph 接纳。native runtime 仍是
唯一执行权威。

## 约束

连接必须检查 schema 版本、单位、坐标系、新鲜度和可见性；需要转换或估计时必须显式插入节点，
不得凭空制造信息。禁止同一窗口内的瞬时环；延迟或有状态反馈必须声明延迟和状态所有者。组合
节点导出类型化公共端口及状态/效果契约后，才能作为父图中的节点重新验证。

首个证明应放在资格验证路径，包含兼容连接、单位/坐标系或 schema 冲突、禁止环、子机制故障和
递归组合；不得改变 `builtin.default_compatibility` 或 facade/Cordis 的既有行为。

最小语义表为：端口边检查物理单位和坐标系；每秒值由有状态 owner 模型积分，每 tick 值必须显式
标记；采样/新鲜度属于端口契约；状态写入只在 owner 的 publication/commit barrier 后可见；延迟
反馈必须声明延迟窗口和状态 owner。这些检查不证明数值标定或 timestep 不变性。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

原型已补齐递归输入闭包、能力与时钟继承、信息层和多生产者校验，并对显式 native system
映射检查已实现顺序。不可变参数、backend 引用与 clock policy 参与图和组合身份。

这仍是静态机制图契约试点。qualification/shadow 编译和生产接纳是分开的 gate；通过现有
manifest machinery 产出的 artifact 不会自动变成可执行机制。

受限 Air seeker 证明复用现有 native 视线转换、距离/世界坐标投影和有状态 CV 跟踪器，区分
窗口发布与每秒数值语义。固定测量时刻下，四种步长到达同一 4 秒终点，结果满足记录的容差。
测试路径在 tracker 更新后、外部 packet 发布前注入异常，并复用 #251 投影为未知状态；
该证据不证明回滚，也未把用户编写的图安装进 native 调度。未知 schema 准入、状态分片权属
和 freshness 强制约束仍待验收。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
