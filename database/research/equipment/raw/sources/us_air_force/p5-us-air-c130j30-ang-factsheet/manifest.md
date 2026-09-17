# 130th Airlift Wing (Air National Guard) — C-130J-30 fact sheet

Source ID: `p5-us-air-c130j30-ang-factsheet`
Tier: `A`
Publisher: 130th Airlift Wing, Air National Guard, United States Air Force
Author / maintainer: 130th Airlift Wing public affairs
Title: Fact Sheet: The C-130J-30 Super Hercules
URL: https://www.130aw.ang.af.mil/About-Us/Fact-Sheets/Display/Article/4525571/fact-sheet-the-c-130j-30-super-hercules
Retrieval:
  attempted_at: 2026-09-17T18:12:30Z
  method: tavily_proxy
  status: success
  returned: the full comparison table through search indexing of this URL, on two separate queries: Length 112 ft 9 in (34.37 m) against 97 ft 9 in (29.79 m), span 132 ft 7 in (40.41 m) for both, Max Take-off Weight 164,000 lb (74,389 kg) for both with the note that it is an identical structural MTOW limit, and Max Payload 46,700 lb (21,183 kg) against 47,000 lb (21,319 kg)
  did_not_return: the plain page fetch
  note: This package previously said no retrieval attempt had been made. The URL was then retrieved successfully, twice, and the block above records it. An independent confirmation of the same figure exists on the 139th Airlift Wing fact sheet, which prints C-130J-30: 164,000 pounds (74,393 kilograms).
Domain: air
Equipment: C-130J-30
Configuration: The page is written as a direct comparison between the stretched C-130J-30 and the standard C-130J, which makes it the source that supplies the J-30 columns the main Air Force fact sheet does not publish.
Estimation / uncertainty: Tier A official United States Air Force publication. The page states the maximum take-off weight as an identical structural limit for both bodies rather than as a J-30-specific reduction.
Retention: manifest and extracted parameter notes only

## Extracted parameter notes

| Feature | C-130J-30 (stretched) | Standard C-130J | Stretch effect |
| --- | --- | --- | --- |
| Length | 112 ft 9 in (page prints 34.37 m) | 97 ft 9 in (29.79 m) | 15 ft (4.58 m as printed) longer fuselage |
| Wingspan | 132 ft 7 in (40.41 m) | 132 ft 7 in (40.41 m) | identical |
| Maximum take-off weight | 164,000 lb (74,389 kg) | 164,000 lb (74,389 kg) | identical structural limit |
| Maximum payload | 46,700 lb (21,183 kg) | 47,000 lb (21,319 kg) | the standard model is slightly higher |

## Conversion check on this page, run 2026-09-17

112 ft 9 in is 34.366 m, so this page's 34.37 m is correct to two decimal places. An earlier revision of this manifest asserted that 112 ft 9 in is 34.69 m and that this page's conversion was therefore wrong. That assertion was wrong and is withdrawn: the arithmetic was run carelessly, and the value printed by the 130th Airlift Wing is right.

The main Air Force C-130 fact sheet prints 34.69 m for the same 112 ft 9 in. That is the page carrying the conversion error, and the ambiguity over which number is correct was resolved in the wrong direction by the earlier revision. The leaf now records the imperial value as the source value, both printed metric values, and the calculated value.

97 ft 9 in is 29.79 m and this page is correct. 164,000 lb is 74,389 kg and this page is correct. 46,700 lb is 21,183 kg and 47,000 lb is 21,319 kg, both correct. The 15 ft stretch is 4.572 m, so this page's 4.58 m is correct to two decimal places.

## Why this package was added

The main Air Force C-130 fact sheet publishes a maximum takeoff weight of 164,000 lb for the C-130J column only and leaves the J-30 column without one, which is why the C-130J-30 leaf previously recorded that field as not published. This page supplies it and states that the limit is identical between the two, which is a substantive fact about the stretch rather than a gap-filling number.

An earlier commit in this session created a second package, `p5-us-air-c130j30-130aw`, which named this same URL and carried the same title. Two source ids therefore pointed at one artifact. The duplicate has been deleted and this is the single package for the artifact.
