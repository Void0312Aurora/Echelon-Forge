# 强化学习与自博弈前瞻

Language: Chinese companion of [the English canonical document](rl_selfplay.md).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/rl_selfplay.md`
Owner: `learning/training`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

本文件定义强化学习与自博弈的设计路线，确保训练闭环可控、可复现。

## 最小训练闭环（已实现）
- 单步观测 -> 动作 -> 环境更新 -> 奖励 -> 终止。
- 动作空间：速率型（转向/加速/爬升/开火）。
- 对手策略：自博弈（对称策略），或脚本追逐/随机。

## 观测设计建议
- 相对位置/速度、相对方位、距离。
- 自身速度/高度/航向、目标速度/高度。
- 传感器信息：是否探测/锁定、最近一次探测距离。

## 奖励设计建议
- 主要：击毁奖励、被击毁惩罚。
- 过程：缩短距离、保持探测、处于有利方位。
- 约束：高机动惩罚、能量不足惩罚。

## 终止条件建议
- 击毁/任务杀伤。
- 脱战距离持续超过阈值。
- 弹药耗尽且空中无弹体。
- 能量过低持续超过阈值。

## 自博弈策略
- 同步更新：双方同时使用同一训练算法。
- 历史策略池：随机挑选旧策略对抗，避免过拟合。
- Elo/胜率评估：跟踪策略演化。

## 基础设施建议
- 统一日志：记录状态/动作/奖励。
- 可复现：固定随机种子、记录配置。
- 训练指标：胜率、平均交战时长、命中率。

## 下一步
- 引入策略池与评估循环。
- 将奖励/终止条件配置化（scenario）。
- 接入深度网络（PyTorch）与 GPU。

## 当前仓库状态
- 本文件仍是前瞻路线图，不是维护中的自博弈入口。
- 当前仓库不存在 `examples/training/train_self_play.py` 或
  `examples/training/selfplay_config.json`。
- 维护中的训练入口与配置位于 `train.py`、`python/training/` 和
  `examples/config/training/`。
- 空战训练配置与脚本化对手 fixture 已存在，但独立的历史策略池与自博弈评估
  闭环仍需先通过 `plan/` 或 `task/` 提升，本文档才能把它们声明为已实现。
