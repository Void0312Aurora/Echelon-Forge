# US Army Profile

本文档定义项目在陆战/地面行动建模时采用的 US Army profile。

## 1. 官方现实基础

Army 官方资料显示，陆军的关键不是像空军那样的 air component C2，
而是分层梯队和 command and control / mission command。

当前公开官方依据：

- [Army MCCoE](https://usacac.army.mil/Organizations/Centers-of-Excellence-CoE/MCCoE)
- [Army doctrinal references](https://www.ikn.army.mil/apps/IKNHostedWebsites/Home/LoadPublishedPage?PageUID=30c204aa-de54-471a-8252-2df7d9f5a5cc)
- [Army force structure reference](https://www.army.mil/core/support/best-practices/ap/ap_stylebook_quick_reference.html)

从这些官方页面可以确认：

- Army 当前使用 `Command and Control Warfighting Function`
- 当前公开 doctrinal baseline 包括 `ADP 3-0 (March 2025)`、`ADP 6-0 (July 2019)`、
  `FM 3-90 (May 2023)`、`FM 3-96 (January 2021)`、`FM 3-94 (July 2021)`
- Army 的常规层级稳定存在：`squad/section -> platoon -> company/troop/battery -> battalion/squadron -> brigade -> division -> corps -> army`

## 2. 建模结论

### 2.1 不应进入 tight-loop runtime 的层

- corps
- division
- brigade

这些层级更适合作为：

- scenario / campaign tasking
- operation-level resource and boundary setting

### 2.2 更适合进入 tight-loop runtime 的层

- `squad / section`
- `platoon`
- `company / troop / battery`

项目若后续进入陆战建模，应优先把 tight-loop tactical unit 放在这些层。

## 3. 对项目通用模板的影响

陆战 profile 说明：

- 不能把空战的 `element / wingman` 结构直接推广到 land
- land 更需要：
  - echelon-aware task organization
  - support / supported relation
  - maneuver element / fires / sustainment separation

因此，joint/core 层应保留：

- `tactical_unit_type`
- `supported/supporting relation`
- `role_code`

而不是硬编码空战术语。
