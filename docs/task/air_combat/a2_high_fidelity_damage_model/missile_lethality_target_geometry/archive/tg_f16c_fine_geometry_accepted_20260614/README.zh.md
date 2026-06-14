# A2 TG F-16C 精细几何代理验收包

状态：`2026-06-14` accepted / retained archive record。F-16C 外形与部件精细几何工程代理已按几何-only 验收门闭合；运行时默认路径替换、训练收益、杀伤概率、结构解体、残骸和具体弹种结论不在本验收包内。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

入口：

- 当前子项目指针：[../../README.zh.md](../../README.zh.md)
- 验收记录：[target_geometry_acceptance_20260614.zh.md](target_geometry_acceptance_20260614.zh.md)
- 稳定 review packet：[../../review_packets/f16c_20260611/](../../review_packets/f16c_20260611/)
- 几何审阅测试：[../../../../../../../tests/tools/test_airframe_geometry_review.py](../../../../../../../tests/tools/test_airframe_geometry_review.py)

## 归档决定

本包确认 `missile_lethality_target_geometry` 子项目的 F-16C 精细几何建模范围已闭合。验收对象是工程代理：来源清楚、尺度可查、网格外形对齐、部件关系可审阅、内部 receiver 先验受外壳约束、跨区 receiver 被拆成 parse-ready 候选，并且全部禁止声明仍保持关闭。

review packet 保留在原稳定路径 `review_packets/f16c_20260611/`，没有物理移动到本归档包内。原因是维护中的工具、聚焦测试和 opt-in 训练配置仍引用该路径；强行迁移会把本次闭合审查扩大成路径迁移工作。本归档包记录验收和生命周期状态，原路径作为 retained evidence surface 保留。

## 已验收范围

- F-16C 来源、许可、hash、坐标轴和公开尺寸审计。
- `14` 个外壳区域和 mesh-derived 精细代理轮廓。
- `26/26` 个现有部件绑定，`0` 个 geometry hard blocker。
- 鼻向、尾向、侧向、上方、下方共 `10` 个测试点距离诊断。
- `14` 个表面部件候选、`14` 个语义外壳体积候选和 `26` 个受约束内部 receiver prior。
- 语义父子布局、跨区 held 分段、R22 `8` 个 split receiver candidate。
- 整机 silhouette 约束和子部件摆放修正；后续投影网格整机轮廓诊断保留 `10` 个 review-only protrusion 复核项，但不进入运行时验收路径。

## 不在本验收内

- 默认 F-16 unit database 或默认近炸投影替换。
- policy/reward 诊断、训练效果、learned weapon employment 或胜负语义。
- 真实 F-16C Block 50 厂商工程几何或内部设备边界声明。
- 结构解体、残骸、Pk 或具体 AIM-120C/MQ-9 杀伤结论。
- MQ-9 或其他机型复用。

## 验证

验收时重新核验：

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/tools/test_airframe_geometry_review.py
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
```

结果：几何审阅测试 `5 passed`；diff whitespace check 无输出。
