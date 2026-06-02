# N5 RL 动作面拆分

状态：`2026-06-02` 归档指针。完整证据包已移入
[archive/n5_rl_action_surface_split](../archive/n5_rl_action_surface_split/README.zh.md)。

本路径仅保留为轻量工作说明和导航入口。目录名是历史名称：已完成工作是已接受的
N4 pre-fire training-entry repair，不是 active N5 weapon-engagement release。

该包把第一段维护中的 naval RL action/observation surface 从 air `takeoff4` /
formation-role 路径中拆出，把 active N4 入口提升到 single-policy-slot cooperative
runtime，并继续拒绝 weapon release 与 damage authority。

新的海军工作应从 [../README.zh.md](../README.zh.md) 和活跃的
[domain-surface split](../naval_domain_surface_split/README.zh.md) 继续。
