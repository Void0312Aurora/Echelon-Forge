# 战斗部空间结构准入

状态：已实现基线探针；未宣称杀伤链整体准入。

本批工作绕过制导和引信决策，在维护中的 F-16C 命中盒包络外侧，扫描前、后、左、右、上、下六个方向、四个脱靶距离和八个战斗部航向，并分别运行 `blast_fragmentation` 与 `continuous_rod`。每一行都通过姿态感知调试接口进入真实 `DefaultEffectsModel`，不在 Python 侧重算效果。

事件现在导出模型实际使用的投影轨迹：

`base -> max(base, near_field_floor) -> axis * orientation * armor * exposure * sampling -> clamp`

硬门只检查这条分解、截断边界以及聚合值的一致性。距离单调、镜像、旋转步长和姿态符号对称性作为结构残差保留。当前基线的 384 行均通过硬门；48 行出现 0/180 度姿态符号折叠，空间战斗部准入仍保持 `held`。

完整基线没有发现距离单调和左右镜像违规。近场托底在 66 行生效，最终截断在 50 行生效；相邻 45 度姿态的最大 `effect_scale` 变化为 `0.3717697996152012`。这只证明诊断轨迹可解释且当前 surrogate 的基础不变量成立，并不证明空间拓扑已经足够真实。破片模型仍是球面密度叠加标量方向权重，连续杆模型仍缺少膨胀杆环/环带与目标几何的显式相交，因此 Component Load 和整体杀伤链准入尚未开展。

生成的原始 JSON 包保留在仓库外的
`artifacts/kill_chain/20260915/raw_review_packets/warhead_spatial_structural_admission_20260913/warhead_spatial_structural_admission_baseline_20260913.json`；仓库内保留本说明作为维护面。
