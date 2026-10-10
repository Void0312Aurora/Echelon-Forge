# 内部 Backend SPI 的 Setup 与 Export 契约

内部 `IWorldBatchBackend` 接收封闭的 `SetupOperation` 类型和。调用方必须构造
`std::variant<BatchSetup, LayoutSetup, WorldSpawnSetup, TypedPlatformSpawnSetup>` 中的
一种操作。公共 `RuntimeFacade` 仍负责请求校验和公共证据；本契约只描述后端无关的
翻译层。

## Setup 操作

| 操作 | 合法载荷 | CPU 参考后端 | CUDA 常驻候选后端 |
| --- | --- | --- | --- |
| `BatchSetup` | 每个 world 的种子、生成请求、时间步，以及可选环境赋值 | 接受 | 仅接受固定空战能力：每个 world 一个种子/生成请求/时间步，且不能带动态环境赋值 |
| `LayoutSetup` | 一个 world 索引、地形、天气、区域、生成请求、时间步、太阳和大地测量锚点 | 接受 | 确定性拒绝 |
| `WorldSpawnSetup` | 一个非空的同步 `WorldSpawnRequest` | 接受 | 确定性拒绝 |
| `TypedPlatformSpawnSetup` | 一个非空的同步 `TypedPlatformSpawnRequest` | 接受 | 确定性拒绝 |

`VectorBatchView` 是同步的非拥有视图。调用方必须保证源 vector 存活到虚调用结束；
后端如果要在调用边界之后排队处理，必须显式复制数据，不能保存该视图。指针载荷也
只在调用边界内有效，空指针会被封闭式拒绝。

## Export 请求

`ExportRequest` 保持有界聚合结构，因为其标志对应 facade 已使用的独立查询族。CPU
接受受支持的查询族；world 级时间步和交战事件需要 `world_index`，运动学查询需要
`kinematics_ref`。CUDA 常驻候选仅支持固定空战的运动学、时间步、仪器和观测投影；
任务、队长意图、飞行员报告、单元消息和交战事件标志会被拒绝。观测投影必须在窗口
提交后导出，并校验常驻实体身份引用。

不支持的变体和载荷会在修改后端状态前抛出错误。本次迁移不改变公共 facade、Python、
authority 或可序列化证据契约。
