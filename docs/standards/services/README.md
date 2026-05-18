<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/README.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/services/README.md. Review before treating this file as authoritative. -->

# Service Profile Overview

This directory defines service profiles based on publicly available U.S. military information.

Currently included:

- [US Air Force](air_force.md)
- [US Army](army.md)
- [US Navy](navy.md)
- [US Marine Corps](marine_corps.md)

The supporting platform-specific supplementary standards currently only include:

- [Air Platform-Specific Standards](../air/README.md)

## 1. Usage Principles

These documents are not intended to lock the project into a "service encyclopedia," but rather to answer three questions:

1. What is the actual tactical organization and control scope of each service?
2. Which levels are suitable for entering the tight-loop runtime?
3. Which levels should only serve as scenario / campaign / operation metadata?

## 2. Unified Conclusion

All four services do not support directly inserting the "administrative organization tree" into tight-loop RL.

A more reasonable approach is:

- Keep the high-level service/joint layer as the task publication and resource allocation layer
- Place the tight-loop runtime on actual tactical units
- The specific form of tactical units is determined by each service's profile
