# M2A2 ODS Bradley

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/ground/vehicles/bradley/m2a2ods/README.md`
Owner: `database/equipment-data`
Content status: post-Cold-War variant parameter draft; not a runtime record.

## Identity

| Field | Value |
| --- | --- |
| Equipment ID | `eq-us-ground-m2a2ods` |
| Family / variant | Bradley Fighting Vehicle / M2A2 ODS (Operation Desert Storm) |
| Service state | 1990s ODS upgrade of M2A2; M2A3, ODS-E and M2A4 are separate configurations |
| Role | Infantry fighting vehicle |
| Configuration scope | US Army M2A2 ODS with the standard armor kit and ODS electronics; export ODS-SA and later BUSK kits excluded |

## Parameters

| Field | Value | Source | Tier | Configuration / uncertainty |
| --- | --- | --- | --- | --- |
| Geometry | 6.55 m operating length x 3.33 m operating width x 3.03 m operating height; transport-reduced width 2.97 m and height 2.64 m | `p5-us-ground-m2a2ods-tm552350` | A | TM 55-2350-252-14 dimensions for M2A2; width/height include the operating armor and commander-hatch convention |
| Combat mass | 66,401 lb (30,119 kg) combat loaded | `p5-us-ground-m2a2ods-fm3221` | A | FM 3-22.1 ODS table; TM M2A2 operational-weight convention is 67,282 lb (30,518 kg), retained as a cross-check rather than blended |
| Powerplant | Cummins VTA-903T liquid-cooled turbocharged V-8 diesel, 600 gross hp at 2,600 rpm | `p5-us-ground-m2a2ods-fm3221` | A | ODS-specific table; no later 675 hp M2A4 powerpack substituted |
| Transmission | General Electric HMPT-500-3EC hydromechanical automatic, 3 forward / 1 reverse range | `p5-us-ground-m2a2ods-fm3221` | A | FM model table; detailed ratios and control software are not public |
| Road / water mobility | 61 km/h land; 8 km/h track-propelled water speed; 60% grade, 0.91 m vertical wall, 2.54 m trench | `p5-us-ground-m2a2ods-fm3221` | A | ODS table values; realized cross-country speed is terrain/load dependent |
| Operational range | 400 km (250 mi) at the ODS table load and 175 US gal fuel | `p5-us-ground-m2a2ods-fm3221` | A | ODS-specific cruising range; other Bradley tables report 402-441 km under different loads |
| Crew / carried infantry | 3 crew (commander, gunner, driver) + 7 infantry | `p5-us-ground-m2a2ods-fm3221` | A | FM table lists 7 passengers for M2A2 ODS; some secondary pages use 2+6, so station/seat convention remains a cross-check |
| Main armament | 25 mm M242 Bushmaster chain gun; 300 ready + 600 stowed rounds (900 total) | `p5-us-ground-m2a2ods-fm3221` | A | ODS gunnery table; ammunition mix is not itemized |
| Anti-armour armament | Twin TOW launcher; 2 ready missiles + 5 stowed missiles; TOW-2/2A/2B compatible | `p5-us-ground-m2a2ods-fm3221` | A | FM table and note; Javelin carriage is an alternate later fit and excluded from the baseline |
| Secondary armament | 7.62 mm M240C coaxial machine gun; 800 ready + 1,400 stowed rounds | `p5-us-ground-m2a2ods-fm3221` | A | ODS gunnery table |
| Mission systems | Integrated thermal day/night sight; eye-safe laser rangefinder (200-9,995 m, +/-10 m); TACNAV with PLGR GPS receiver and digital compass; combat-identification system; FBCB2 battle-command network; AN/WS-2 driver night viewer | `p5-us-ground-m2a2ods-fm3221` | A | ELRF/TACNAV ranges and functions are stated in FM; network waveform and thermal identification performance are not disclosed |
| Protection | Additional hull/turret steel armor for 30 mm APDS threat, Kevlar spall liners, internal ammunition relocation, reactive-tile mounting provisions, NBC protection, automatic fire suppression and eight smoke launchers | `p5-us-ground-m2a2ods-armyrecognition` | C | Army Recognition describes ODS/M2A2 protection; exact array thickness, tile fit and kit mass are configuration-sensitive |
| Amphibious / fording | Track-propelled water movement at 8 km/h; unprepared fording approximately 0.46 m and prepared/deeper crossing up to 1.07 m | `p5-us-ground-m2a2ods-fm3221` | A | FM explicitly gives water speed; the 0.46-1.07 m fording bound is a driver-training estimate and must be checked against the ODS operator manual |

All target fields contain direct values or explicitly bounded estimates. The ODS baseline is not populated from M2A4 or generic Bradley family values.

## Source References

- `p5-us-ground-m2a2ods-fm3221`
- `p5-us-ground-m2a2ods-tm552350`
- `p5-us-ground-m2a2ods-armyrecognition`
