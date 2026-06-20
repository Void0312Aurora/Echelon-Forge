# Weapon Guidance Realism Tests

This directory intentionally uses unittest wrapper modules around capability
mixins. The mixin modules hold reusable runtime realism checks, and the
`test_*.py` wrapper modules are the only pytest discovery entry points.

## Collection Contract

Run the package with:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/runtime/air_combat/weapon_guidance_realism
```

Current collection: 192 tests.

| Wrapper | Collected class | Capability mixins |
| --- | --- | --- |
| `test_a8_consumer_validation.py` | `A8ConsumerValidationTests` | `A8Mq9Aim120ValidationRuntimeMixin`, `A8AeroConsumerRuntimeMixin`, `A8SensorDataLinkConsumerRuntimeMixin`, `A8FireConsequenceRuntimeMixin` |
| `test_geometry_and_edge_cases.py` | `GeometryAndEdgeCaseTests` | `GeometryFixtureRuntimeMixin`, `BoundaryCaseRuntimeMixin` |
| `test_launch_guidance_and_dynamics.py` | `LaunchGuidanceAndDynamicsTests` | `LaunchGuidanceRuntimeMixin`, `MissileDynamicsRuntimeMixin`, `FuzeRuntimeMixin` |
| `test_vulnerability_authority.py` | `VulnerabilityAuthorityTests` | `VulnerabilityAuthorityRuntimeMixin`, `VulnerabilityScaffoldRuntimeMixin` |
| `test_warhead_and_component_damage.py` | `WarheadAndComponentDamageTests` | `WarheadEffectsRuntimeMixin`, `AircraftDamageRuntimeMixin`, `ComponentDamageRuntimeMixin`, `DefaultEffectsModularizationRuntimeMixin` |

## Why This Pattern Exists

The wrappers keep five independently runnable runtime-realism surfaces while
letting large capability checks share fixtures and assertion helpers without
duplicating setup across many `test_*.py` files. This is a maintained exception
to the default preference for direct semantic test modules.

The non-wrapper mixin modules may be flagged by the test-system audit as
`hidden_mixin_tests`. That flag is retained as governance visibility, not as a
deletion instruction.

Full package execution is a local/focused regression surface, not CI smoke. Do
not promote this directory to smoke until the full package run is green and the
suite tier decision is recorded.

## Boundaries

- Do not add a new mixin module without adding it to a wrapper class and this
  table.
- Do not rely on direct pytest discovery of non-`test_*.py` mixin modules.
- If a mixin grows a distinct setup, failure policy, or suite tier, convert that
  surface into a direct `test_*.py` module instead of adding another hidden
  inheritance layer.
- Keep smoke/focused/local promotion in suite manifests or node IDs, not by
  moving capability code into more physical files.
