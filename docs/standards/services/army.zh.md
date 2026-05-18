# 美国陆军配置文件

本文档定义项目在陆战/地面行动建模时采用的美国陆军配置文件。

## 1. 官方现实基础

美国陆军官方资料显示，陆军的关键并非像空军那样的空中组成部分 C2，而是分层梯队与指挥控制 / 任务式指挥。

当前公开官方依据：

- [陆军指挥参谋学院（MCCoE）](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [陆军条令参考资料](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [陆军部队结构参考资料](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)

从这些官方页面可以确认：

- 陆军当前使用“指挥控制作战职能”
- 当前公开的条令基线包括《ADP 3-0（2025年3月）》《ADP 6-0（2019年7月）》《FM 3-90（2023年5月）》《FM 3-96（2021年1月）》《FM 3-94（2021年7月）》
- 陆军的常规层级稳定存在：班/组 -> 排 -> 连/队/炮连 -> 营/中队 -> 旅 -> 师 -> 军 -> 集团军

## 2. 建模结论

### 2.1 不应进入紧耦合运行时的层级

- 军
- 师
- 旅

这些层级更适合作为：

- 想定/战役任务
- 战役级资源与边界设定

### 2.2 更适合进入紧耦合运行时的层级

- `班 / 组`
- `排`
- `连 / 队 / 炮连`

项目若后续进入陆战建模，应优先将紧耦合战术单位放在这些层级。

## 3. 对项目通用模板的影响

陆战配置文件说明：

- 不能将空战的 `编组 / 僚机` 结构直接推广到地面
- 地面更需要：
  - 考虑梯队的任务编组
  - 支援 / 被支援关系
  - 机动部队 / 火力 / 保障分离

因此，联合/核心层应保留：

- `tactical_unit_type`
- `supported/supporting relation`（支援 / 被支援关系）
- `role_code`（角色代码）

而不是硬编码空战术语。
