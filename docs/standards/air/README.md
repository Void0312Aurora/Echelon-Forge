<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/README.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/README.md. Review before treating this file as authoritative. -->

# Overview of Air Platform-Specific Standards

This directory defines **platform- and mission-specific standards** for the project under the air profile.

Note:

- This directory is not the joint/common core
- This directory is also not the main document for the service organization profile
- This directory is solely responsible for the semantics of observation, action, command, and reporting for the air platform

Currently, the following should be read first:

1. [Standardization Documentation Overview](../README.md)
2. [USAF Profile](../services/air_force.md)
3. [obs.md](obs.md)
4. [act.md](act.md)
5. [aim.md](aim.md)
6. [rep.md](rep.md)

## 1. Positioning of This Directory

This directory deals with:

- aircraft/platform-level observation
- pilot action semantics
- air-specific mission / execution command semantics
- air-specific reporting semantics

It does not deal with:

- joint/common command relationships
- tactical organizational structures of the Army/Navy/Marine Corps
- the project-wide unified common core data model

## 2. Relationship with the Old `air/com` Documents

`docs/Archive/air_first_standards/com/*.md` and `docs/Archive/air_first_standards/com/two_ship/*.md` are now archived,
because they were built on an older air-first standardization approach.

If air combat coordination or two-ship/four-ship-specific standards are needed in the future,
they should be rewritten under the new framework of `joint/common core + USAF profile + air specialization`,
rather than continuing to extend the old directory.
