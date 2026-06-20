# Test System Governance P2-C Mixin Evidence 2026-06-21

Status: `2026-06-21` P2-C collection decision documented; focused package
execution is failing and remains a local residual.

## Decision

`tests/runtime/air_combat/weapon_guidance_realism` keeps the current
unittest-wrapper plus capability-mixin pattern for now. The pattern is
intentional and is now documented in
[../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md](../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md).

This is not a claim that the package is small, green, or smoke-safe. It is a
scoped collection-visibility decision: the hidden mixin tests are justified
because five wrapper files provide independently runnable runtime-realism
surfaces.

## Wrapper Map

| Wrapper | Collected class | Capability mixins |
| --- | --- | --- |
| `test_a8_consumer_validation.py` | `A8ConsumerValidationTests` | `A8Mq9Aim120ValidationRuntimeMixin`, `A8AeroConsumerRuntimeMixin`, `A8SensorDataLinkConsumerRuntimeMixin`, `A8FireConsequenceRuntimeMixin` |
| `test_geometry_and_edge_cases.py` | `GeometryAndEdgeCaseTests` | `GeometryFixtureRuntimeMixin`, `BoundaryCaseRuntimeMixin` |
| `test_launch_guidance_and_dynamics.py` | `LaunchGuidanceAndDynamicsTests` | `LaunchGuidanceRuntimeMixin`, `MissileDynamicsRuntimeMixin`, `FuzeRuntimeMixin` |
| `test_vulnerability_authority.py` | `VulnerabilityAuthorityTests` | `VulnerabilityAuthorityRuntimeMixin`, `VulnerabilityScaffoldRuntimeMixin` |
| `test_warhead_and_component_damage.py` | `WarheadAndComponentDamageTests` | `WarheadEffectsRuntimeMixin`, `AircraftDamageRuntimeMixin`, `ComponentDamageRuntimeMixin`, `DefaultEffectsModularizationRuntimeMixin` |

## Evidence

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/runtime/air_combat/weapon_guidance_realism
# 192 tests collected

cmo_python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism
# 45 failed, 167 passed, 221 subtests passed

cmo_python tools/runners/audit_test_system.py --format json --limit 300
# Hidden mixin files remain visible as risk flags; wrapper collection is documented.
```

Audit examples retained as governance signals:

- `fuze.py`: `hidden_mixin_tests`, `oversized_file`,
  `oversized_test_item`, `literal_heavy`, `not_smoke_gated`.
- `warhead_effects.py`: `hidden_mixin_tests`, `oversized_file`,
  `oversized_test_item`, `literal_heavy`, `not_smoke_gated`.
- `vulnerability_authority.py`: `hidden_mixin_tests`, `oversized_file`,
  `literal_heavy`, `source_scan_guard`, `not_smoke_gated`.
- `component_damage.py`: `hidden_mixin_tests`, `oversized_file`,
  `literal_heavy`, `source_scan_guard`, `not_smoke_gated`.

## Boundaries

- No runtime behavior was changed.
- P2-C does not promote this package into smoke.
- The package-level focused run currently fails; those failures are retained as
  behavior/test-expectation drift, not repaired inside this collection-visibility
  slice.
- The mixin pattern is allowed only while wrapper files remain the explicit
  collection and triage surface.
- Future new mixins must update the package README wrapper table.
- A mixin with distinct setup, failure policy, or suite tier should become a
  direct semantic `test_*.py` module instead of another hidden inheritance
  layer.
