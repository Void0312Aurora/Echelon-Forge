# Equipment Module Catalog

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/research/equipment/catalog/module/README.md`
Owner: `database/equipment-data`
Content status: provisional shared-module hierarchy for simulation-parameter collection.

## Responsibility

Owns reusable engine, mobility-subsystem, and sensor research records. Module leaves keep shared parameters in one cited location instead of copying them into every equipment variant.

## Hierarchy

- Parent: `../`
- Children: `engine/`, `mobility/`, `sensor/`

These documents are research inputs. They do not define runtime composition,
inheritance, or final interface contracts. A module `Equipment ID` is a stable
research identity for the reusable subsystem; a vehicle or weapon leaf must
cite the module explicitly when it uses the module's values, and may not inherit
them silently.
