<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g2_content_test_seed/g2_content_fixture_test_cluster_20260521.md. Review before treating this file as authoritative. -->

# G2 内容夹具与测试集群

状态：`2026-05-21` 已由主线程 G2-C 集成验收。

输入：

- [G2 自述文件](README.md)
- [G1 配置文件和 DTO 合约集群](../g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [子代理使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

创建首个版本控制的地面夹具和测试。目标是合约可用性，而非模拟真实感。

## 任务项

| ID | 项目 | 验收标准 |
|----|------|------------|
| `G2-A1` | 夹具放置 | 在 `examples/config/database/` 下选择首个内容根目录，不与空中/海军布局冲突。 |
| `G2-A2` | 起始单位夹具 | 添加一个以排为中心的地面夹具，不涉及运行时移动、地形、感知、射击或战斗声明。 |
| `G2-A3` | 能力说明 | 记录夹具如何映射到能力包构建，即使公共 `spawn_platform` 不可用。 |
| `G2-B1` | 任务规范合约 | 添加涵盖 `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 配置文件默认值的合约规范。 |
| `G2-B2` | 合约测试 | 测试证明合约规范通过地面配置文件和通用核心字段进行归一化。 |
| `G2-C1` | 集成 | 在工作器返回后同步 G2 文档、调度队列、验证证据和 G3 剩余项。 |

已验收结果：

- `G2-A1/G2-A2/G2-A3`：通过，产出
  `examples/config/database/ground/units/ground_platoon_starter.seed` 和
  `examples/config/database/ground/units/CAPABILITY_NOTE.md`。
- `G2-B1/G2-B2`：通过，在 `tests/contracts/unit/ground/` 下新增三个可运行
  `unit_regression` 合同。
- `G2-C1`：通过，主线程完成验证与状态同步。

## 工作器调度

| 流 | 代理类型 | 模型/推理 | 任务 | 写入范围 |
|--------|------------|-------------------|------|-------------|
| `G2-A` | 工作器 | `gpt-5.4`, 高 | 添加首个地面夹具根目录和能力说明。 | 仅限 `examples/config/database/ground/**`。不进行测试、文档/任务编辑、运行时编辑或加载器编辑。 |
| `G2-B` | 工作器 | `gpt-5.4`, 高 | 添加地面单位合约和专注的合约运行器覆盖。 | 仅限 `tests/contracts/unit/ground/**` 和一个专注的 `tests/leader` 或 `tests/runners` 测试。不进行夹具编辑、文档/任务编辑、运行时编辑或加载器编辑。 |
| `G2-C` | 主线程集成 | 当前主线程 | 接受或拒绝工作器结果并发布最终同步状态。 | `docs/task/ground/g2_content_test_seed/**`、`docs/task/ground/ground_subagent_dispatch_queue_20260521.md`，仅验证。 |

## 写入范围

允许已发布的 G2 工作器：

- `G2-A`：`examples/config/database/ground/**`
- `G2-B`：`tests/contracts/unit/ground/**` 和一个专注的测试框架文件
- `G2-C`：此 G2 集群文档、G2 自述文件和地面调度队列

不要编辑：

- 运行时移动/物理系统
- 武器/效果运行时
- 公共外观设置架构，除非 G1 明确要求
- C++ DTO 外壳、绑定或场景加载器行为

## 建议验证

```bash
git diff --check
python -m pytest -q tests/leader
```

一旦夹具路径存在，添加专注的地面合约测试。

推荐的专注命令：

```bash
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json
python -m pytest -q tests/leader/test_ground_profile_semantics.py
```

## 交接

返回：

- 夹具路径
- 添加的任务规范
- 运行的测试
- 能力构建剩余项
- G3 执行面设计的阻塞项

工作器返回数据包必须包括：

```md
Stream:
Status: pass | fail | blocked | preflight-only
Model / reasoning:
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

## G2-C 集成记录

worker 返回：

- `G2-A`：`pass`，`gpt-5.4 / high`；在
  `examples/config/database/ground/units/` 下添加第一批 ground 内容根和能力说明。
- `G2-B`：`pass`，`gpt-5.4 / high`；在 `tests/contracts/unit/ground/`
  下添加 ground 起步合同。

主线程集成调整：

- 将 starter fixture 从 `ground_platoon_starter.json` 改为
  `ground_platoon_starter.seed`。内容仍保持 JSON 形状并通过
  `python -m json.tool` 验证，但非 `.json` 后缀可防止当前 runtime database
  loader 把规划 seed 当作具体 unit definition，并产生 unknown-type warning。

已验收验证：

```bash
python -m json.tool examples/config/database/ground/units/ground_platoon_starter.seed > /tmp/ground_platoon_starter.seed.pretty.json
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
python -m pytest -q tests/leader/test_ground_profile_semantics.py
```

额外集成证据：

```bash
python - <<'PY'
from python.testing.runtime import ensure_repo_imports
ensure_repo_imports()
import ef_py
sim = ef_py.SimulationKernel()
print(sim.load_database('examples/config/database'))
PY
```

结果：database load 成功，且不会因 G2 seed 产生 ground unknown-type warning，
因为该 seed 不会作为受维护的 runtime unit definition 自动加载。

G3 剩余项：

- 精确选择一个 G4 候选；不要扩展到 runtime movement、terrain、sensing、
  fires、weapon、damage 或 combat 行为。
- 决定第一执行面继续保持 tasking-only，还是添加最小 command/status/report 壳。
- 如果后续需要可由 runtime 加载的 ground unit schema，必须通过已验收的
  capability-bundle/public-platform seam 引入，而不是把这个规划 seed 变成
  私有 ground runtime 路径。
