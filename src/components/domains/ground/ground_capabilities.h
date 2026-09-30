#pragma once

// Authored content capability for entities that represent an individual
// dismounted infantry actor.  Ground type alone is intentionally insufficient:
// aggregates such as platoons may be Ground without owning the infantry
// movement or weapon slices.
struct GroundInfantryCapability {};
