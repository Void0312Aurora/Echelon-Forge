# K2 Black Panther

Language: English canonical. Chinese companion: not provided.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/k-2/k-2/README.md`
Owner: `database/equipment-data`
Content status: extracted simulation-parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-kr-ground-k2` |
| Family / variant | K2 / K2 Black Panther |
| Role | Main battle tank |
| Configuration scope | Republic of Korea baseline production K2; Batch I-IV engine/transmission and export K2GF/K2PL armor packages are not silently merged |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 10.80 m overall length (7.50 m hull), 3.60 m width, 2.40 m height; 0.45 m nominal ground clearance | `p5-kr-ground-k2-armyguide` | C | Army Guide technical table; suspension posture can vary height/clearance, and gun-forward/rear conventions are not separately stated |
| Combat mass | 56 t official combat weight; 55 t Army Guide/early production reference | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Retain 56 t as current Korean planning value; 55 t is an early/curb convention, not blended into the combat value |
| Powerplant | 1,500 hp diesel; public references identify STX/Doosan and temporary MTU packages as batch alternatives | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Engine supplier/model differs by batch; horsepower is common, thermal/fuel curves require batch-specific data |
| Transmission | Automatic, 5 forward + 3 reverse gears | `p5-kr-ground-k2-hyundairotem` | A | Official baseline gear count; supplier/model and control software differ by batch and export customer |
| Road / off-road speed | 70 km/h paved-road maximum; 50 km/h off-road official (Army Guide test narrative: 48 km/h sustained off-road) | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | 70/50 km/h is the current manufacturer envelope; 48 km/h is an independent test-era value |
| Operational range | 450 km | `p5-kr-ground-k2-hyundairotem` | A | Manufacturer nominal range; terrain, external tanks and fuel reserve are not itemized |
| Crew / payload | 3 crew (commander, gunner, driver); 40 x 120 mm rounds (16-round autoloader magazine + 24 hull stowage); no embarked infantry | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Crew and main ammunition are direct; secondary ammunition is bounded below because public official page gives no count |
| Main armament | 120 mm 55-caliber CN08 smoothbore cannon with automatic loader; KSTAM top-attack round capability | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Korean production gun package; export ammunition integration is customer-dependent |
| Secondary armament / ammunition | 12.7 mm K6 heavy machine gun and 7.62 mm coaxial machine gun; 12.7 mm 300-500 rounds and 7.62 mm 2,000-3,000 rounds (simulation bounds) | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Calibers/mounts are direct; ammunition counts are bounded estimates based on comparable MBT ready/stowed practice, not a counted K2 inventory |
| Mission systems | KGPS gunner sight and KCPS commander panoramic sight (day/night thermal, 2-axis stabilization, laser rangefinder), automatic target search/track, hunter-killer FCS, millimeter-wave radar/MAWS, GPS/INS, C4I-linked BMS, IVIS/IFF, DTTS and posture-control ISU | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Manufacturer confirms core sights, tracking, BMS and navigation; radar/IVIS detail comes from Army Guide and remains subject to batch software cross-check |
| Protection | Composite and reactive armor, collective CBR protection, automatic fire suppression, VIRSS smoke (12 launchers), soft-kill warning/jamming; hard-kill APS optional/PIP rather than guaranteed on early baseline | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Armor array and RHAe are undisclosed; optional hard-kill APS is explicitly kept separate from baseline |
| Water crossing | Submersible to 4.1 m with snorkel; vehicle resurfaces combat-ready | `p5-kr-ground-k2-hyundairotem` / `p5-kr-ground-k2-armyguide` | A/C | Deep-wading requires kit/procedure; no swimming capability is claimed |

All target fields contain a direct value or an explicitly bounded estimate. Source conflicts (55 versus 56 t, 48 versus 50 km/h off-road, and batch-specific engine/transmission suppliers) remain visible; export K2GF/K2PL armor, electronics and ammunition fits require separate leaves.

## Source References

- `p5-kr-ground-k2-hyundairotem`
- `p5-kr-ground-k2-armyguide`
