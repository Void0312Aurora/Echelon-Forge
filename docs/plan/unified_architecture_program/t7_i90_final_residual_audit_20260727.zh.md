# T7 I90 终局残余审计（2026-07-27）

语言：
- 英文正本：`t7_i90_final_residual_audit_20260727.md`
- 中文对照：[t7_i90_final_residual_audit_20260727.zh.md](t7_i90_final_residual_audit_20260727.zh.md)

文档种类：`report`
生命周期：`maintained`
正本：`docs/plan/unified_architecture_program/t7_i90_final_residual_audit_20260727.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-27`
基线/源落地 head：`5a2c75f7`

状态：**I90 已接受——终局残余审计干净轮 2。**

本报告是 I89 窄修复包之后的 T7 最终证据记录，记录修复后的两轮 clean 与所有幸存项分类；不授权删除、不规范化用户工作树，也不重开 held 工作。

## 1. 范围与两轮证据

I89 的实质修复落在 `a272fc04`；`5a2c75f7` 是随后的台账/哈希收口。两轮均使用同一源码树和匹配的 `EF-landing\build-local-win` 构建：

| 轮次 | checkout | 证据 | 独立评审 |
|---|---|---|---|
| 修复后确认轮 | `EF-landing` 的 `5a2c75f7` | maintained smoke `753 passed, 4 skipped, 45 subtests`；`ef_test` 143 / 19,147；CTest 8/8；聚焦 content 26、I87 13、T8/T9 99；生成器新鲜；Ruff 干净 | `i89_landing_review`：PASS |
| I90 fresh 轮 | 新建 `codex/i90-final-residual-audit`，`5a2c75f7` | maintained smoke `753 passed, 4 skipped, 45 subtests`；`ef_test` 143 / 19,147；CTest 8/8；registry 90/90；链接 182 文档 / 2,802 链接 / 0 issues；无 >= 0.1 MB 精确重复；测试系统普查完成 | `i90_bounded_review`：PASS/CLEAN |

唯一环境噪声是 sandbox 无法读取用户级 global Git ignore 文件；worktree porcelain、源码状态与项目门禁均可读且干净。

加入本报告及其双语/索引登记后，文档只读收口门也通过：registry 91/91
同步，链接审计 184 文档 / 2,820 链接 / 0 issues。该收口步骤没有改动源码或测试文件。

## 2. 最终幸存项分类

每个幸存项均在下表分类。详细证据与 owner-gated 下一步保留在 [I89 残留裁定](t7_i89_residual_disposition_20260727.zh.md)。

| ID | 分类 | 最终理由/保留边界 |
|---|---|---|
| D-01 | `held` | GPU packed/SoA helper 布局没有获接受的维护 GPU ABI/投影 owner；需要 exact-runtime/GPU 证据。 |
| D-02 | `held` | I83 只抽取经测量的 WorldBatchCore seam；模式专属所有权等待 WP4 平价与性能证据。 |
| D-03 | `held` | 三个 active naval N4 配置尚无 typed Experiment owner；领域 protocol 与逐字节 freshness 门是前置。 |
| D-04 | `intentional` / `uneconomic` | 两个 MATRIX_DIR 扩展契约不同且有 freshness 钉；合并只增加改动。 |
| D-05 | `intentional` 治理 / 产品预期 `held` | T6 xfail 与条件 skip 按节点、带理由治理，等待校准或产品授权。 |
| D-06 | 文本已修 / 剩余语义 `held` | I87 文案已为 accepted/landed；声明但未收敛的 reader 保留语义 owner 边界。 |
| D-07 | 证据指针已修 / 行为 `held` | T9 adapter 引用已更新；no-mapping 仍是有证据判定。 |
| D-08 | `fixed` | I96 flag 与 I89 sensor_refs 平价匹配 C++ loader，覆盖空/非数组/非字符串/非空形状。 |
| D-09 | `held` | rollback 扫描暂不含 scripts/根入口，等待 caller 分类与正向清单。 |
| D-10 | `held` | logistics fuel-blocked command 语义没有 owner 与 typed rejection/hold 契约。 |
| D-11 | `held` | loadout 补给语义与 int-keyed codec 边界没有获接受的 typed 契约。 |
| D-12 | `held` | jettison drag 没有权威 aero/model owner 或经验证的转移。 |
| D-13 | `held` | 主工作树保留 58 个临时目录中的 857 个 untracked 条目（11,745 文件 / 198.93 MiB）；无保留授权。 |
| D-14 | `held` | 六个非目标 dirty worktree 在 provenance 与清理决策明确前保持用户/agent 所有。 |
| D-15 | `held` | `.git/worktrees/EF-w24-i88/refs` 空目录曾被报 garbage，但 linked worktree 仍在；不授权元数据变更。 |

## 3. 停止条件判定

- 维护入口导航在审计快照中干净：182 文档、2,802 链接，零问题；维护双语 registry 90/90。随后文档只读收口为 91/91 与 184/2,820（零问题），如上所记。
- 活跃审计面未发现不可达生产体或无 owner 的兼容路径。三个 logistics TODO 与外部工作区残余均有命名 owner 和下一道门。
- 剩余 schema/helper 重复项均有 owner、刻意保留，或由 exact-runtime、领域、性能、清理授权明确 held。
- 未删除任何 archive/evidence 或用户所有工作区。
- 修复后连续两轮 clean 已完成，且每轮有独立评审。

**T7 完成。I90 已接受并是队列最后一项。** 未来重开任何 held 项都必须使用新的、单独编号的证据切片；不得追加到 I90，也不得改写本 clean-pass 结果。

## 相关

- [I89 残留裁定](t7_i89_residual_disposition_20260727.zh.md)
- [I72+ 迭代队列](iteration_queue_i72_plus_20260726.zh.md)
- [仓库整合计划](../repository_consolidation/README.zh.md)
- [T6 残差台账](t6_residual_ledger.zh.md)
