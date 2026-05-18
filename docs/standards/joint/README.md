# Joint Standards Overview

This directory defines the common joint layer templates used when modeling air, sea, and land operations in the project.

Core principles:

- The `joint` layer defines only common authority relationships, task organization, and reporting interfaces.
- Do not write `wingman`, `runway`, `destroyer screen`, or `platoon wedge` directly in the `joint` layer.
- Specific service semantics are deferred to the `service profile`.

## 1. Why the Joint Layer Must Come First

According to official documents from the Joint Chiefs and each service, the U.S. military does not operate under a completely unified tactical chain of command.

The actual structure is closer to:

- The joint layer unifies authority relationships.
- The service layer defines tactical organization.
- The platform layer defines execution and physical behavior.

Therefore, generic templates in the project should prioritize:

- `command relationship`
- `authority scope`
- `task organization`
- `intent / order / report`

## 2. Recommended Reading Order

1. [Joint Command Relationships and Modeling Baseline](command_and_modeling_baseline.md)

## 3. Key Official References

- [Joint Chiefs Service Publications](https://www.jcs.mil/Doctrine/Service-Publications/)
- [CJCSM 3150.13C, Joint Reporting Structure](https://www.jcs.mil/Portals/36/Documents/Library/Manuals/m315013.pdf)

Note:

- The above references are used to confirm common joint relationships and the joint reporting structure.
- Differences in service tactical organization are handled under `services/` respectively.
