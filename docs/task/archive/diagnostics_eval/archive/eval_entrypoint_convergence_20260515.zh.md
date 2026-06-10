# Eval 与 Diagnostic 入口收敛主计划

状态：阶段 1、阶段 2、阶段 3、阶段 4 已完成。

日期：`2026-05-15`

## 1. 背景

近期围绕 HMoE、协同执行、terminal eval 与轨迹诊断做了较多探索。核心运行时与训练主线已经逐步稳定，但评估与诊断脚本层出现了明显的入口膨胀：

- 同一任务往往同时存在 `world-model` 与 `scripted` 两个独立脚本。
- 不同脚本大量重复 episode loop、指标采样、环境构造与输出格式。
- 若继续沿现状迭代，后续每补一个评估维度都需要复制更多脚本。

这类膨胀会带来三个直接问题：

- 维护成本高：一个指标语义修正需要同步改多个入口。
- 行为漂移风险高：不同入口容易在阈值、默认值、输出字段上悄悄分叉。
- 协作成本高：使用者很难判断“应该复用哪个脚本”而不是继续新建一个。

## 2. 已确认发现

### 2.1 明确存在的重复簇

`tools/eval` 在收敛前存在 4 组最明显的成对入口：

- `eval_stable_flight.py`
- `eval_stable_flight_scripted.py`
- `eval_takeoff_roll.py`
- `eval_takeoff_roll_scripted.py`
- `eval_centerline.py`
- `eval_centerline_scripted.py`
- `eval_waypoint_nav.py`
- `eval_waypoint_nav_scripted.py`

这些脚本的差异主要集中在：

- 控制器来源不同：
  - `world-model checkpoint`
  - `scripted controller`
- 少量默认参数不同：
  - `device`
  - `action_mode`
  - 是否暴露 `--no_randomization`
- 少量历史输出细节不同。

除此之外，以下部分高度重复：

- `argparse` 公共参数拼装
- `UniversalEnv` 构造
- episode reset / step / done loop
- `mission_status` 解析
- 指标聚合与统计打印

### 2.2 已有通用化基础已经存在，但未贯彻到入口层

仓库已经有一些共享工具：

- [tools/eval/eval_utils.py](../../../../tools/eval/eval_utils.py)
- [tools/eval/waypoint_eval_utils.py](../../../../tools/eval/waypoint_eval_utils.py)
- [tools/eval/world_model_eval_utils.py](../../../../tools/eval/world_model_eval_utils.py)

这说明问题不在于“无法抽象”，而在于“抽象只做到局部，没有推进到入口收敛”。

### 2.3 启动阶段暂不一口气处理的区域

启动阶段开始时，下面这些区域虽然也存在表面相似性，但不纳入首批实现：

- `tools/diagnostics/diagnose_cooperative_takeoff_trajectory.py`
- `tools/diagnostics/diagnose_cooperative_takeoff_to_cruise_trajectory.py`
- `scripts/*.sh` 中的 HMoE / pipeline 壳脚本

原因：

- cooperative 轨迹诊断不只是“入口不同”，还带有 world/slot 聚合与图表语义差异。
- 这部分脚本近期刚服务过正式实验，风险高于单机 task eval。
- 更适合作为后续阶段单独处理。

## 3. 分阶段冻结计划

### 3.1 阶段 1：单机 task eval 入口收敛

目标：

- 统一 `stable_flight / takeoff_roll / centerline / waypoint_nav` 的单机 task eval 入口
- 移除 `scripted / world-model` 成对壳脚本

冻结范围：

- 新增共享评估驱动
- 新增正式统一 CLI
- 删除旧的 8 个 task eval 入口壳

验收标准：

- 单机 task eval 只保留一个正式 CLI
- 不再在多入口之间复制完整 episode loop
- 语法与 `--help` 烟测通过

实施结果：

- 新增 [tools/eval/task_eval_driver.py](../../../../tools/eval/task_eval_driver.py)
- 新增 [tools/eval/eval_task.py](../../../../tools/eval/eval_task.py)
- 删除旧的 8 个 task eval 入口壳

已完成烟测：

- `python -m py_compile tools/eval/task_eval_driver.py ...`
- `./.venv/bin/python tools/eval/eval_task.py --help`
- `./.venv/bin/python tools/eval/eval_task.py --task stable_flight --backend world_model --help`
- `./.venv/bin/python tools/eval/eval_task.py --task takeoff_roll --backend scripted --help`

阶段备注：

- `takeoff_roll` 的 `wheel_off` 判定保留了历史上 scripted/world-model 的轻微语义差异，避免改变已有指标口径。
- `centerline` 输出样式统一，但指标内容保持等价。

### 3.2 阶段 2：SB3 eval 共享底座收敛

目标：

- 抽取旧双入口 `eval_sb3_policy.py` 与 `eval_sb3_cooperative_policy.py` 的共享底座
- 不合并 CLI，只减少重复实现

冻结范围：

- JSON 配置加载
- SB3 / AdaptiveKLPPO 模型加载
- `resolve_env_settings` 覆写
- 公共 argparse 参数
- `json_out` 落盘

明确不做：

- 单机 SB3 与 cooperative SB3 合并成一个命令
- cooperative world/slot 聚合逻辑重写

实施结果：

- 新增 [tools/eval/sb3_eval_base.py](../../../../tools/eval/sb3_eval_base.py)
- 阶段 2 完成时，旧双入口已切换到共享底座
- 阶段 4 已在此基础上进一步统一为 [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py)

已完成烟测：

- `python -m py_compile tools/eval/sb3_eval_base.py`
- 阶段 4 统一 CLI 烟测见 `3.4`

### 3.3 阶段 3：cooperative trajectory diagnostic 入口收敛

目标：

- 抽取 cooperative trajectory diagnostic 的共享底座
- 将 `takeoff` 与 `takeoff_to_cruise` 收敛为一个正式 CLI

冻结范围：

- 共享的配置加载与模型加载
- 共享的 cooperative env 构造与 curriculum 应用
- 共享的 trace 采样驱动、导出与通用绘图骨架
- 统一 cooperative trajectory CLI，并删除旧双入口壳

明确不做：

- 强行统一不同任务的 slot summary schema
- 输出图表语义的大改

阶段判断：

- 两个脚本共享大骨架，但在采样字段、slot summary 与图表面板上存在结构性差异
- 这些差异更适合保留在任务分支逻辑里，而不是继续保留两个顶层入口

实施结果：

- 新增 [tools/diagnostics/cooperative_trajectory_base.py](../../../../tools/diagnostics/cooperative_trajectory_base.py)
- 新增 [tools/diagnostics/diagnose_cooperative_trajectory.py](../../../../tools/diagnostics/diagnose_cooperative_trajectory.py)
- 删除旧的 `tools/diagnostics/diagnose_cooperative_takeoff_trajectory.py`
- 删除旧的 `tools/diagnostics/diagnose_cooperative_takeoff_to_cruise_trajectory.py`

已完成烟测：

- `python -m py_compile tools/diagnostics/cooperative_trajectory_base.py tools/diagnostics/diagnose_cooperative_trajectory.py`
- `./.venv/bin/python tools/diagnostics/diagnose_cooperative_trajectory.py --help`
- `./.venv/bin/python tools/diagnostics/diagnose_cooperative_trajectory.py --task takeoff --help`

### 3.4 阶段 4：SB3 eval 正式 CLI 收敛

目标：

- 将单机 `SB3` 与 cooperative `SB3` 评估收敛到一个正式入口
- 清理最后一组仍然保留的 CLI 兼容层
- 将脚本、文档、测试全部切换到统一入口

冻结范围：

- 新增统一 CLI
- 删除旧的两个 `SB3` eval 入口
- 迁移 README、脚本、测试与任务文档引用

验收标准：

- `tools/eval/` 下只保留一个正式 `SB3` 评估入口
- 现有单机与协同评估 JSON schema 保持兼容
- `--help`、`py_compile` 与 cooperative runtime 烟测通过

实施结果：

- 新增 [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py)
- 删除旧的 `tools/eval/eval_sb3_policy.py`
- 删除旧的 `tools/eval/eval_sb3_cooperative_policy.py`
- 相关脚本、README、专项文档与 runtime test 已迁移到统一入口

已完成烟测：

- `python -m py_compile tools/eval/eval_sb3.py tools/eval/sb3_eval_base.py`
- `./.venv/bin/python tools/eval/eval_sb3.py --help`
- `./.venv/bin/python tools/eval/eval_sb3.py --mode single --help`
- `./.venv/bin/python tools/eval/eval_sb3.py --mode cooperative --help`
- `./.venv/bin/python -m pytest -q tests/eval/test_evaluation_cli_contracts.py`

## 4. 文档约束

本主计划是本主题唯一的阶段计划文档，当前冻结阶段已全部完成。

后续若继续推进：

- 优先回填本文件的对应阶段
- 只有在需要记录专项调研细节时，才新增辅助文档
- 辅助文档不得再次与本文件并列承担“阶段计划”职责
