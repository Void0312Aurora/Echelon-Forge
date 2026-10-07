# Air EW 旧分支提交审计与提取（2026-10-07）

## 基准与结论

本次基准为 `origin/main=70bd92eb142aaa34e98688907f65fc3365dc25df`（PR #110 合并）。
“独有提交”是 Git 历史差异，不能直接解释为相同数量的缺失功能。旧工作经过拆分、
移植和审阅修复后，以不同提交进入主线；仍有少量修复和测试没有被吸收。

五个远端分支合计包含 29 个不同的非合并提交对象，其中 3 个是另一个分支上的
相同补丁副本。汇总分支另有两个合并提交；其 remerge diff 为空，没有额外冲突解决改动。
`git cherry` 仅识别出两个完整补丁等价项，其余项进一步按当前代码和审阅后的实现判定。

| 旧远端分支 | tip | 主线独有 / 分支独有 | 处置 |
| --- | --- | --- | --- |
| `work/air-electronic-warfare` | `6bbdc9b01` | 251 / 28 | 保留；28 包含两个合并提交 |
| `work/air-ew-decoy` | `bca354fbe` | 251 / 20 | 保留；包含共享的未合入修复 |
| `work/air-ew-rl` | `14497b665` | 251 / 19 | 保留；包含共享的未合入修复 |
| `work/air-ew-script` | `8e5a8bddb` | 251 / 20 | 保留；包含共享的未合入修复 |
| `work/air-preexisting-reds` | `969ade7a0` | 251 / 8 | 保留；包含未合入修复及补丁副本 |

## 逐项处置

下表覆盖上述 29 个非合并提交对象。旧补丁只提供提取来源，当前主线的 RF、ESM、
诱饵、Ground、命令接口、生成清单及后续审阅修复保持其现有实现。

| 旧提交 | 内容与当前处置 |
| --- | --- |
| `812ceeabe` | 武器站向下量化与开火身份检查已在主线实现；不重复提取。 |
| `749fe264d` | MAWS 单一生产者、扫描提前返回、来源归属、入射方位、首次释放修复仍缺失；提取至 #112，并保留当前 ESM 合并器。 |
| `408c75465` | 有界 RWR 表面的 launch/lock/plain 排序仍缺失；提取至 #112，排序位置覆盖当前合并后的 RWR/ESM 表面。 |
| `c4d663075` | 补丁等价于主线 `5eb8250c1`；已吸收。 |
| `2170e11b0` | 部分已吸收（两个 EW 模型身份、先验证 roster、显式 NAV 观察测试）；遗漏的 engagement 模型身份、facade 默认观察和帧身份测试提取至 #114，种子伤害测试提取至本记录所在 PR。 |
| `53cad60ba` | 旧原生修复和种子 trace 的历史说明；保留在历史，不把旧通过数重写为当前证据。 |
| `40f7fbb66` | jammer 命令 owner、v2 传输已由主线 `ef53d3a11` 及后续修复吸收；补回仍缺失的原生 cockpit 控制和无 pod 两个测试。 |
| `1eda7b7b6` | 旧 jammer 节点的生成证据重封；主线已包含更新的节点与后续证据，不覆盖当前生成文件。 |
| `e9fbc4483` | cockpit 请求到敌方雷达的运行时测试仍缺失；提取并修正距离前提，DRFM 描述改为本数据库零偏移配置。 |
| `e35faaba0` | 旧 jammer owner 决策说明；实现已有更新，历史说明不重放。 |
| `d018ebbd3` | burst 释放程序已在主线 EW model 中实现；不重复提取。 |
| `54876a839` | cooperative jammer doctrine 已由当前模型、`b14ade972` CLI 与 `c2c88488a` 路由测试覆盖；不重复提取。 |
| `f6135d499`, `de13b7da7` | 同一 MQ-9 K=16 补丁的两个提交对象；仅提取一份，保留完整 launch/effect/damage 断言、非空条件和损伤状态优先级。 |
| `a1eee5d39`, `0c816a9b5` | 同一诊断隔离补丁的两个提交对象；仅提取缺失部分至 #115。保留主线 geodetic 和 Ground 分组，pre-Ground 数量修正为 90。 |
| `a4c41fd35`, `969ade7a0` | 同一 RNG 计数归属补丁的两个提交对象；提取一份至 #113，保留 Ground 武器接口，新增字序、reset/restore 和溢出原子性测试。 |
| `8cdffb398` | 旧 burst/jammer/red closure 账本；历史保留，以本次复跑结果为当前证据。 |
| `aa5912dd4` | 上述旧账本措辞修正；不单独移植旧账本。 |
| `eb0daaa3d` | composed engagement/EW 已由主线 `915018512` 吸收。 |
| `411e56a15` | 补丁等价于主线 `501584eb1`；已吸收。 |
| `8e5a8bddb` | 旧 combat-EW entry/review 说明；不覆盖当前后续验收与残余项。 |
| `f2b6ef29b` | 中立运行时调用和武器站 fixture pin 仍缺失；提取至 #114，并同步当前 wrapper resolver 名称。 |
| `8bef12607` | typed decoy 已由 PR #93 / `3a54d3098` 及审阅修复吸收。 |
| `eb310067d` | seeker seduction 已由 PR #93 / `3a54d3098` 及审阅修复吸收。 |
| `bca354fbe` | decoy 原生/运行时证据已在主线后续修复版中保留。 |
| `455ba080d` | canonical v1/v2 action admission 已由 PR #109 / `c18b71f2c` 吸收。 |
| `14497b665` | opt-in `ew_state` 已在主线，且有后续 temporal EW 工作；不覆盖当前观察实现。 |

## 提取与验证

按审阅顺序构建五个小 PR：

1. [#112 原生 MAWS/RWR 修复](https://github.com/Void0312Aurora/Echelon-Forge/pull/112)。
2. [#113 RNG 计数归属](https://github.com/Void0312Aurora/Echelon-Forge/pull/113)。
3. [#114 脚本运行时契约](https://github.com/Void0312Aurora/Echelon-Forge/pull/114)。
4. [#115 诊断接口精确隔离](https://github.com/Void0312Aurora/Echelon-Forge/pull/115)。
5. 本记录所在 PR：原生 cockpit 回归、jammer 运行时、MQ-9 多种子和 facade 伤害证据。

HEI-LAN 隔离源码构建 `ef_test` 与 `ef_py`：

- #112 的相关原生 EW 套件：42 passed / 920 assertions。
- 恢复 Stack 的完整原生套件：271 passed / 155216 assertions。
- Air、simulation、tasking、jammer、weapon consumer 运行时：215 passed / 7 既有 xfail。
- CLI 与 binding 架构套件：15 passed；CLI 导入使用现有 Windows Python 3.12 扩展，
  功能运行时使用上述 HEI 新编译扩展。
- weapon-release、stochastic-draw、identity、composition 架构套件：另 15 passed。
- 全库 Ruff、变化 C++ 的 clang-format、增量 internal-code governance 通过。

测试调整保留了明确的前提和非空要求：APG-68 目标重获最多等待两次重扫；
远距 jammer 用较短窗口并逐帧核对距离；MQ-9 允许已记录的 fuze failure，
但要求至少一个种子满足引爆前提并逐项检查损伤链。这些是仿真契约证据，
不构成真实平台校准、因果 EW 战果或完整可玩性验收。

## PR 审阅修复

2026-10-07 的 bot 审阅在 #112 指出 ECS 迁移摘要未随 RWR 反射表更新，
导致 #112–#116 的 Linux 状态迁移校验共同失败；后四层没有独立阻塞项。
在 #112 按原有校验算法重新计算并固定摘要为
`0ccfffb0fdd8031691e4ad830cf853a199f673a54882fd2796a2c460037612cb`，
保留完整的摘要检查，并依次 rebase 后四层。

新增的真实 state-owner 回归还复现了发射来源列表与导弹 ID 未绑定目标世界的问题。
已将这两处纳入逻辑实体引用映射，并解析 Flecs 为带 generation 的 uint64 ID
输出的十进制字符串。重复载入后仍验证目标实体归属与序列化一致性。
旧 RWR payload 缺少两个新增容器时，恢复流程保留旧 launch flag、雷达列表与灵敏度，
将新容器初始化为空，不保留目标世界的旧警报；不需要额外的迁移 normalizer。

HEI-LAN 对修复后的 Stack 源码编译 `ef_runtime_host_candidate_test`：

- 新增 RWR 状态迁移回归：2 passed / 59 assertions。
- 完整 runtime host/state-owner 原生套件：70 passed / 1848 assertions。
- 同步显式补齐 host 测试的 `<algorithm>`，使 GCC 15 构建不依赖间接头文件。

上述结果补充前一节的原生与运行时证据；新的 GitHub CI 状态须以本次更新后的
PR head 为准。

## 本地清理与后续边界

五个旧本地分支及其 `.worktrees/air-ew`、`air-decoy`、`air-ew-rl`、`air-ew-script`、
`air-reds` 工作树实际上均停在 `c982a4c31044e909999713b1ac08ad378b686fac`。
它们已确认无未提交和未跟踪文件、分支仅被对应工作树使用、tip 为主线祖先，
且 `git cherry origin/main <local-branch>` 无 `+`。已删除这些本地工作树和分支，并核对物理目录消失。

恢复引用在 `refs/archive/20261007-ew-legacy-audit/`：五个 `local-work-*` 保存上述本地 tip，
五个 `origin-work-*` 保存表中的真实远端旧 tip，均仅在本地。
主工作区 `codex/root-docs-wip-20261002` 保持原状；其他领域工作树和既有备份保持原状。

五个远端旧分支仍含此次提取而尚未合入主线的工作，因此本次不删除。
新 PR 合并后应重新获取 `origin/main`，核对提取的最终接受版本，再退役旧远端 refs。
本次构建 PR，不执行合并。
