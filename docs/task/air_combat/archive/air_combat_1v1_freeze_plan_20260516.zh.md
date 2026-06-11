# 空战 1v1 冻结计划

状态：`2026-05-16` 冻结执行版。

关联文档：

- [空战 1v1 切入分析](air_combat_1v1_entry_analysis_20260516.zh.md)
- [P8 协同执行管线发现与计划](../../../plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
- [多 Agent 协同训练底座与性能计划](../../../plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
- [HMoE Strict Terminal Eval (2026-05-15)](../../../plan/results/hmoe_strict_terminal_eval_20260515.md)

文档定位：

- 本文档把“进入空战 `1v1`”收敛为一份可执行的任务单。
- 本轮只冻结 `1v1` 第一阶段，不把 `2v2`、自博弈和多 policy 对抗一并打包。
- 本文档不授权“顺手重写” cooperative 主线，也不授权直接发散到完整对抗训练平台。

验证口径：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_summary
```

若本轮触及 Python / 训练 / 运行时 / eval 主线，默认至少补：

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q
```

若本轮触及 `ef_py`、ScenarioLoader 或空战终止/奖励底座，至少补：

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j4
```

## 一、目标

本轮的目标不是“立刻做出完整自博弈体系”，而是把空战 `1v1` 的最小维护主线建立起来。

本轮要解决的核心问题：

1. 为 `1v1` 建立一条明确的训练主线入口。
2. 为 `1v1` 建立可维护的场景、奖励、终止与评估合同。
3. 让 `1v1` 的最小基线能够跑通“单学习机 vs 单脚本/冻结对手”。
4. 为后续 `2v2` 与 self-play 留干净接口，但不在本轮同时实现。

## 二、冻结范围

本文档只冻结五个工作包：

1. `WP1`：`1v1` 任务合同与场景基线
2. `WP2`：`execution` 主线的 `1v1` 训练入口接入
3. `WP3`：`1v1` 评估与结果口径
4. `WP4`：脚本/冻结对手基线
5. `WP5`：为后续 `2v2` / self-play 预留但不实现的接口

本文档明确不覆盖：

1. `2v2` cooperative-vs-cooperative 对抗训练
2. 真正双边同时更新的 self-play PPO 闭环
3. 历史策略池、Elo、league training
4. HMoE 在对抗线上的直接实验
5. 多 policy route 对抗训练闭环

## 三、总体策略

执行顺序固定为：

1. 先建立 `1v1` 任务合同。
2. 再让 `execution` 主线能跑通该任务。
3. 再补 `1v1` 评估与结果口径。
4. 再接脚本/冻结对手。
5. 最后只预留 `2v2` / self-play 的扩展缝，不在本轮进入。

原因：

1. 当前最大的缺口不是“推理框架不够复杂”，而是对抗任务合同还没有维护型定义。
2. 没有清晰的 reward / termination / eval，直接上 self-play 会把问题混在一起。
3. `execution` 主线已经成熟，最适合作为第一阶段承载体。

## 四、工作包

### WP1：`1v1` 任务合同与场景基线

目标：

- 为空战 `1v1` 建立最小维护型任务合同。
- 明确第一阶段的场景边界、敌我双方、成功/失败条件与奖励目标。

冻结范围：

- `scenarios/` 下新增或整理 `1v1` 空战场景
- 必要的 `ScenarioLoader` / reward / termination 合同配置
- 相关文档与最小 contract tests

本阶段必须明确的问题：

1. 蓝方学习机是谁。
2. 红方对手是谁。
3. 胜负条件如何定义。
4. 脱战 / 超时 / 弹药耗尽 / 双方存活的终局如何定义。
5. 第一阶段是否允许使用导航式 mission block，还是需要新增 combat mission block。

推荐冻结方向：

1. 第一阶段以“单学习机 vs 单脚本/冻结对手”为唯一支持形态。
2. 第一阶段不要求 mission observation 一次性引入复杂对抗专用大向量。
3. 优先复用现有 `instruments / contacts / rwr / mission` 结构，只对 mission task 语义做最小必要扩展。
4. 第一阶段不要把旧文档中的 `capture_zone` 当成现成主线能力；若需要空间占领式胜负判定，必须先补明确实现或改走 `conditional` / 显式评估路径。
5. 第一阶段不要假设 `fire_weapon` 动作已经直连武器发射；发射主链需要单独设计并验证。

验收标准：

1. 仓库内存在可重复加载的 `1v1` 场景输入。
2. `1v1` 胜负 / 超时 / 脱战 / 资源耗尽口径有明确定义。
3. 至少有一条聚焦测试验证终止理由与奖励主项可工作。

### WP2：`execution` 主线的 `1v1` 训练入口接入

目标：

- 不新增新的大平面训练入口文件。
- 在当前维护中的 `execution` 主线上接入 `1v1` 任务。

冻结范围：

- [train.py](../../../../train.py)
- [python/env_config.py](../../../../python/env_config.py)
- [gym_envs/universal_env.py](../../../../gym_envs/universal_env.py)
- 必要的训练 config

推荐冻结方向：

1. 第一阶段不新增 `agent_layer = "combat_execution"`。
2. 第一阶段优先把 `1v1` 作为 `execution` 任务族下的一条新任务线接入。
3. 若确实需要新的 mode，也应优先新增窄配置分支，而不是复制一套完整 vec env。

不建议本轮采用：

1. 直接把 `cooperative_execution` 改造成敌我双边对抗入口。
2. 直接引入“双 policy 同时训练”的新 agent layer。
3. 新建专用 `TwoShipCombatEnv` 孤岛。

验收标准：

1. 现有 `train.py` 入口仍保持兼容。
2. `1v1` 配置能通过维护主线训练入口启动。
3. 不要求本轮就完成自博弈，但必须能完成最小 rollout 与 checkpoint 落盘。

### WP3：`1v1` 评估与结果口径

目标：

- 为 `1v1` 建立独立于 `single` / `cooperative` 的评估口径。
- 让后续冻结对手、自博弈、`2v2` 都能复用同一套对抗结果统计字段。

冻结范围：

- [tools/eval/policy_execution_eval.py](../../../../tools/eval/policy_execution_eval.py) 或同域评估入口
- 必要的 JSON 输出 schema
- 必要的评估文档与回归测试

最低结果字段建议包括：

1. 蓝方胜率
2. 红方胜率
3. 平局 / 超时率
4. 平均交战步数
5. 终止原因计数
6. 蓝方资源消耗或存活状态
7. 红方资源消耗或存活状态

验收标准：

1. `1v1` 评估脚本可以独立运行。
2. 输出不再只使用 waypoint-success 口径解释结果。
3. 至少补一条 focused test 证明 `1v1` 评估 JSON 可产出且字段稳定。

### WP4：脚本 / 冻结对手基线

目标：

- 为第一阶段 `1v1` 提供稳定可复现的对手。
- 避免一开始把训练不稳归因到 self-play。

冻结范围：

- 脚本对手或冻结 checkpoint 对手接入
- 对手配置与切换方式
- 必要的 smoke / eval 测试

推荐顺序：

1. 先脚本对手
2. 再冻结 checkpoint 对手
3. 最后才考虑 policy pool

原因：

1. 脚本对手最容易调 reward / termination / scene contract。
2. 冻结对手更适合在第一版合同稳定后做强基线。
3. 直接从 policy pool 起步会让调试维度过多。

验收标准：

1. 至少有一种稳定对手可以重复加载。
2. 同一配置下多次评估结果分布可解释。
3. 文档中明确写清“当前基线对手是什么，不是什么”。

### WP5：为 `2v2` / self-play 预留接口，但不实现

目标：

- 确保第一阶段 `1v1` 不把后续 `2v2` 路径堵死。
- 但不让“为了将来”破坏本轮收敛。

本阶段只允许预留的接口方向：

1. 评估 schema 中允许扩展双方多实体统计。
2. 场景/配置层允许未来表达蓝红双方 roster。
3. 对手加载接口允许后续切换到 frozen pool。

本阶段明确不做：

1. `cooperative_execution` 与对抗线的正式并轨。
2. 敌我双方多 controllable roster 的统一 world runtime。
3. 双边同时学习的 optimizer / replay / league 机制。

## 五、推荐切口

本轮推荐按下面顺序推进：

1. 先补一份 `1v1` 场景与合同草案。
2. 再为 `execution` 线补最小训练 config。
3. 再为 `eval` 补 `1v1` 结果口径。
4. 最后接脚本对手并跑一轮 smoke。

优先观察的风险点：

1. 当前 reward / termination 是否仍过度绑定 waypoint-success 语义。
2. 当前 mission observation 是否不足以承载最小空战任务阶段。
3. 当前单 `agent_id` 路径下，对手控制面应放在脚本链、scenario 行为链，还是冻结执行策略链。

## 六、停止条件

一旦出现下列情况，应停止继续扩范围并另起任务单：

1. 需要把 `1v1` 与 `2v2` 同时做完。
2. 需要同步重写 `cooperative_execution` 为敌我对抗主入口。
3. 需要直接接入完整 self-play league。
4. 需要为了 `1v1` 先大改现有 HMoE / cooperative 主线。

## 七、预期产出

本轮完成后，仓库应至少具备：

1. 一份维护中的 `1v1` 场景与任务合同。
2. 一组可启动训练的 `1v1` config。
3. 一条可输出胜负与终局口径的 `1v1` eval 路径。
4. 一种稳定脚本/冻结对手基线。
5. 一组最小 smoke / focused tests。

## 八、结论

进入空战 `1v1` 是合理的下一步，但第一阶段必须控制变量。

当前最合适的推进方式是：

1. 站在已经稳定的 `execution` 主线上进入。
2. 把目标冻结为“单学习机 vs 单脚本/冻结对手”。
3. 先把场景、奖励、终止和评估四件套做稳。
4. 把 `2v2` 与 self-play 明确留到下一阶段。

这条路径既承接了刚刚稳定下来的 cooperative/HMoE 设施，又不会因为过早把问题做成“多边协同 + 对抗 + 自博弈”而失控。
