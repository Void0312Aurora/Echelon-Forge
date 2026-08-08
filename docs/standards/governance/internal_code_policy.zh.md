# 内部代号命名规范

语言版本：

- 英文主文：[internal_code_policy.md](internal_code_policy.md)
- 中文辅文：`governance/internal_code_policy.zh.md`

状态：`2026-08-07`，项目内部任务代号与实现阶段别名的权威治理规范。

## 目的

本规范用于阻止规划简写演变为缺少解释的运行时或公共合同。仓库会使用工作包、审阅批次、
迭代号和实现阶段标签组织开发；这些标签在所属计划中有用，但其含义不够稳定，不应主导
源码接口、运行时诊断、schema 或入口文档。

本规范不禁止技术缩写。`C2`、`GPU`、`CUDA`、`ECS`、`SoA` 等领域术语需要明确的
标准归口，并应在适当位置就地解释；但它们不会仅因较短就自动成为任务代号。

## 分类

| 类别 | 示例 | 稳定性 | 允许作为主名称的范围 |
| --- | --- | --- | --- |
| 语义名称 | `flight_dynamics`、`control_preparation`、`observation_projection` | 能力语义稳定时保持稳定 | 源码、运行时诊断、schema、维护中文档 |
| 任务追踪代号 | `RB7`、`CR2-5a`、`WP15-C`、`I94` | 仅在所属计划、审阅批次或迭代内成立 | 所属任务计划、历史证据、提交或审阅说明 |
| 实现阶段别名 | `Phase B`、`phase_b`、`kPhaseD...` | 仅在某次执行拆分中成立 | 定义该拆分的计划，或明确标记的兼容接缝 |
| 领域缩写 | `C2`、`EW`、`LOS` | 由领域或联合标准归口 | 就地展开且无歧义时可用于稳定接口 |

短标签只能通过明确的标准决策改变类别。重复使用不会自动把任务追踪代号变成稳定语义。

## 源码与运行时规则

`src/`、`python/`、`gym_envs/` 下维护中的生产源码遵循以下规则：

1. 公共和内部接口都以语义能力名称为主。
2. 异常、日志、计数器、trace 标签和校验消息不暴露工作包、审阅批次或迭代编号。
3. 文件、类型、函数、状态字段和 kernel 不以字母阶段作为主名称。
4. 测试可以在验证迁移行为时保留历史编号；新断言应优先使用语义消息或接口。
5. 只有在修改会破坏稳定序列化或外部合同时，才允许保留兼容别名。同一行或前一行必须带有
   `internal-code: compatibility`，所属标准或任务记录必须说明语义替代项和移除条件。

例如，固定翼动力学错误应指出不受支持的能力，而不是首次实现它的审阅批次；kernel 应按
动力学积分或观测投影命名，而不是只有阶段字母。

## 文档规则

维护中的入口与 README 必须在不查阅另一份代号表的情况下可理解：

1. 任务代号首次在本地出现时必须展开，并链接其所属计划。
2. 标题和导航以语义名称为主；只有在定位历史证据确有需要时，才在括号中保留代号。
3. 同一维护导航面不得用同一短码表达无关概念；应增加归属前缀或改用语义名称。
4. 历史计划和验收证据可以保留原编号，但最近的维护中 README 必须用语义语言概括最终能力。
5. 中央术语表只能作为辅助，不能替代首次使用处的就地展开。

## Schema 与兼容迁移

不得批量直接重命名序列化键、trace schema 名称、产物字段或外部协议值。迁移必须：

- 定义语义替代项
- 识别所有读写方
- 选择带版本的双读、双写或明确的破坏性迁移
- 测试新旧两种表示
- 说明兼容别名的移除条件

若某个内部代号只存在于未发布测试 fixture 中，并且全部读取方能够在同一轮更新，且有证据
表明它不是外部合同，则可以在一个迭代内直接改名。

## 增量执行

维护中的扫描入口为：

```bash
python -m tools.maintenance.internal_code_governance \
  --changed-from <base-revision>
```

扫描器只检查相对指定基线新增的行，从而阻止新增的高置信债务，而不会让无关修改因已有历史
积压而失败。

当前严重程度：

- 错误：生产标识符或运行时字符串包含任务追踪代号
- 错误：新增字母阶段生产标识符且没有兼容标记
- 告警：源码注释包含任务追踪代号
- 告警：维护中文档包含未就地展开的内部代号

源码匹配会拆解 snake case 与 CamelCase/PascalCase 标识符，并检查生产路径的每个组成部分。
仅在语义词内部包含 `phase` 字母的名称（例如 `broadphase_batch`）不会被当作实现阶段别名。
C/C++ 行注释和块注释都保持为注释告警；即使被选中的变更行位于从未变更行开始的块注释中，
分类也不会升级为源码错误。

历史文档和长尾文档积压中的告警继续保持非阻断。维护入口基线采用更严格规则：根 README
中英文对、`docs/README`、`docs/plan/README`、`docs/task/README`、
`docs/standards/README` 中英文对，以及 `tools/README.md` 必须保持零 finding。
`test_maintained_entry_points_have_no_bare_internal_codes` 对该受限集合执行阻断。只有在完成某个
新增入口的整改，并确认扫描器对完整文件的精度后，才可把它加入该集合。

## 实现大小与归属

扫描器由 `tools/maintenance/internal_code_governance/` 负责，测试由
`tests/architecture/governance/` 负责。该包内每个模块必须少于 1000 个物理行。检测逻辑增长时，
应拆分匹配策略、diff 收集、报告和格式解析，不能继续扩大单个通用脚本。

## 验证

```bash
python -m pytest -q \
  tests/architecture/governance/test_internal_code_governance.py
python tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json
python -m tools.maintenance.internal_code_governance \
  --changed-from <base-revision>
git diff --check
```

清理运行时的迭代还必须执行受影响的原生、facade、合同或架构测试。

## 相关文档

- [标准维护政策](standards_maintenance_policy.zh.md)
- [文档生命周期规范](document_lifecycle_policy.zh.md)
- [双语文档政策](bilingual_documentation_policy.zh.md)
- [仓库精简与整合路线图](../../plan/repository_consolidation/README.zh.md)
