# Naval Ship Unit References

This note records the first real-world ship units selected for the minimal naval screen scenario. The intent is to keep unit data traceable to public sources and to separate measured/public facts from runtime estimates.

## Scenario Seed

The first naval example should be a single escort protecting a logistics high-value unit:

- Escort/screen: USS Arleigh Burke (DDG-51), Arleigh Burke-class Flight I guided-missile destroyer.
- Supported/HVU: USNS Lewis and Clark (T-AKE-1), Lewis and Clark-class dry cargo/ammunition ship.

This pair maps directly to the existing naval tasking skeleton:

- DDG-51: `TASK_SCREEN`, `ScreenCommander`, `Screen`.
- T-AKE-1: `TASK_SUPPORT`, `LogisticsCoordinator`, `Support`.

## Public Source Baseline

### DDG-51 Flight I / USS Arleigh Burke

Primary public sources:

- U.S. Navy / SURFLANT USS Arleigh Burke characteristics page: https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/USS-Arleigh-Burke-DDG-51/About-Us/Characteristics/
- U.S. Navy / SURFLANT destroyer ship-class page: https://www.surflant.usff.navy.mil/Organization/Operational-Forces/Destroyers/Destroyer-Ship-Class-DDG-Info-Page/

Recorded public values:

- Dimensions: 153.8 m x 20.4 m x 9.3 m from the ship-specific page.
- Flight I full-load displacement: 8,230 long tons from the ship-class page.
- Speed: 30+ knots from the ship-specific page; 30 knots from the ship-class page.
- Range: 4,400 nautical miles at 20 knots.
- Crew: 300+ from the ship-specific page; 303 from the ship-class page.
- Publicly identified systems include Aegis Combat System, AN/SPY-1D, AN/SPS-67(V), Mk 41 VLS, 5-inch/54 gun, Harpoon launchers, and CIWS for early-flight ships.

Runtime conversions in `examples/config/database/ships/units/ddg51_flight_i_uss_arleigh_burke.json`:

- Full-load displacement: 8,230 long tons -> 8,362,000 kg, rounded.
- Light displacement: 6,711 long tons -> 6,819,000 kg, rounded.
- Length: 153.8 m.
- Beam: 20.4 m.
- Draft: 9.3 m.
- Maximum speed: 30 kt -> 15.43 m/s.
- Range speed: 20 kt -> 10.29 m/s.

### T-AKE-1 / USNS Lewis and Clark

Primary public sources:

- U.S. Navy T-AKE fact file: https://www.navy.mil/Resources/Fact-Files/Display-FactFiles/Article/2211797/dry-cargoammunition-ships-t-ake/
- General Dynamics NASSCO T-AKE fact sheet for metric-ton displacement and 14,000 nmi range: https://www.nassco.com/pdfs/T-AKE_FactSheet_Jan_2007.pdf

Recorded public values:

- Length: 689 ft.
- Beam: 106 ft.
- Draft: 30 ft.
- Displacement: 41,000 tons from the Navy fact file; 41,000 metric tons at design draft from the NASSCO fact sheet.
- Speed: 20 knots.
- Range: 14,000 nautical miles at design speed and draft from the NASSCO fact sheet.
- Listed crewing: 53 civilian from the Navy fact file.

Runtime conversions in `examples/config/database/ships/units/take1_usns_lewis_and_clark.json`:

- Full-load displacement: 41,000 metric tons -> 41,000,000 kg.
- Length: 689 ft -> 210.0 m.
- Beam: 106 ft -> 32.31 m.
- Draft: 30 ft -> 9.14 m.
- Maximum speed: 20 kt -> 10.29 m/s.

## Modeling Boundaries

The new `ShipPlatform` fields are public-parameter fields, not convenience placeholders. They represent displacement, dimensions, speed, range, and crew.

Known estimates:

- `height_above_waterline_m` is a runtime estimate for line-of-sight and future radar-horizon work because the public ship-characteristics pages list draft, not exact sensor/mast height.
- Surface-search radar runtime range is currently set by radar-horizon reasoning, not by a classified or unsourced maximum radar range:
  - DDG-51 surface search: 3.57 * (sqrt(25 m owner antenna) + sqrt(5 m target)) = 25.8 nmi = 46.3 km.
  - T-AKE navigation/surface search: 3.57 * (sqrt(15 m owner antenna) + sqrt(5 m target)) = 19.6 nmi = 36.3 km.
- Ship `health` is scaled as one HP per metric tonne of full-load displacement until a naval damage/lethality calibration exists.
- Combat-system weapon inventories are recorded in metadata only. Current runtime `Ammo` represents generic missile count, so VLS cells, guns, CIWS, and replenishment cargo are intentionally not flattened into misleading generic ammo.

## First Scenario Recommendation

Start with a no-shoot screen-keeping/contact scenario:

1. Spawn T-AKE-1 on a steady 20 kt course as the supported unit.
2. Spawn DDG-51 5-8 nmi ahead or abeam as the screen.
3. Add one unknown surface contact outside the HVU's horizon but inside the DDG screen's search picture.
4. Score early behavior on maintained screen geometry, contact reporting, and whether the HVU remains outside the contact's closest approach threshold.

This keeps the first naval scene realistic: it begins with surface movement, horizons, tasking, and contact management before inventing missile/gun engagements that the runtime does not yet model faithfully.
