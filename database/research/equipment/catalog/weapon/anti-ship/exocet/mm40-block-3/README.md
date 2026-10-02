# Exocet MM40 Block 3

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/weapon/anti-ship/exocet/mm40-block-3/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-fr-weapon-exocetmm40` |
| Family / variant | Exocet / MM40 Block 3 surface-launched missile |
| Role | Ship- or coastal-battery-launched sea-skimming anti-ship cruise missile with limited land-attack capability |
| Configuration boundary | French MM40 Block 3 baseline; Block 3C seeker/ECCM upgrade is used only as a continuity cross-check, while AM39/SM39 and older MM38/Block 2 are excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Mass | 780 kg all-up launch round including jettisoned booster; about 530 kg post-booster missile | `p5-fr-weapon-exocetmm40-mindef`; `p5-fr-weapon-exocetmm40-mbda` | A/C | MBDA B3C sheet gives missile body mass; 780 kg all-up value includes launcher booster from French MoD family data |
| Dimensions | 5.8-5.9 m all-up with booster; 4.70 m missile body; 350 mm diameter | `p5-fr-weapon-exocetmm40-mindef`; `p5-fr-weapon-exocetmm40-mbda` | A/C | Published dimensions differ by whether booster/canister are counted; simulation separates both states |
| Propulsion / motor | Jettisoned solid rocket booster followed by Microturbo TRI-40 turbojet sustainer | `p5-fr-weapon-exocetmm40-mbda` | C | B3/B3C engine details are public at family level; fuel flow and thrust curve are not public |
| Guidance / seeker | INS/GPS waypoint navigation, radar altimeter and active J-band RF terminal seeker; adaptive sea-skimming | `p5-fr-weapon-exocetmm40-mbda`; `p5-fr-weapon-exocetmm40-mindef` | A/C | Block 3C coherent seeker is a later ECCM improvement; baseline B3 seeker behavior is represented functionally |
| Range / flight envelope | 180-200 km class Block 3 operational range; high-subsonic speed; very-low-altitude sea-skimming terminal flight | `p5-fr-weapon-exocetmm40-mindef`; `p5-fr-weapon-exocetmm40-mbda` | A/C | Public sources state class/range rather than exact profile; range depends on waypoint and terminal maneuver plan |
| Warhead | Approximately 160-165 kg insensitive high-explosive blast-fragmentation warhead | `p5-fr-weapon-exocetmm40-mbda`; `p5-fr-weapon-exocetmm40-mindef` | A/C | Exact fill and liner are not public; value bounded from Exocet family technical references |
| Fuze / trigger | Impact fuze with proximity function for terminal ship attack | `p5-fr-weapon-exocetmm40-mbda` | C | Fuze model and selectable delay are not public; functional impact/proximity behavior retained |

## Source References

- `p5-fr-weapon-exocetmm40-mindef`: `raw/sources/ministere_des_armees/p5-fr-weapon-exocetmm40-mindef/manifest.md`
- `p5-fr-weapon-exocetmm40-mbda`: `raw/sources/mbda/p5-fr-weapon-exocetmm40-mbda/manifest.md`
