# WP6 Backend Profile Policy Acceptance Review

Status: `2026-05-19` WP6 acceptance completed.

Scope: WP6-A backend profile taxonomy and registry, WP6-B parity budget and
comparison rules, WP6-C resident-state and capability projection alignment, and
WP6-D publication/index sync.

Related documents:

- [WP6 backend profile policy](../simulation_architecture/backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile registry](../simulation_architecture/wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](../simulation_architecture/wp6_parity_budget_registry_20260519.md)
- [WP6-C1 resident-state boundary rules](../simulation_architecture/wp6_resident_state_boundary_rules_20260519.md)
- [WP6-C/D integration and index sync](../simulation_architecture/wp6_integration_and_index_sync_20260519.md)

## 1. Acceptance Decision

WP6 backend profile policy is accepted.

The accepted WP6 line defines backend profile metadata, profile-owned parity
budgets, resident-state ownership and sync gates, and conservative runtime
capability projection. It does not promote exact GPU execution,
resident-state truth, device observation views, or shadow comparison to
maintained support.

## 2. Accepted Outputs

Accepted WP6 outputs:

1. `cpu_exact.reference` is the only maintained exact baseline in the initial
   backend profile registry.
2. `gpu_helpers.diagnostics_only`, `gpu_exact.unmaintained_candidate`,
   `resident_state.unmaintained_candidate`, and
   `shadow_compare.unmaintained_candidate` remain diagnostics-only or
   unmaintained candidates.
3. `parity_budget.cpu_exact.reference.v1` is the maintained reference budget;
   GPU helper, GPU exact, resident-state, and shadow budgets remain
   diagnostics-only or candidate records.
4. `event_order` and `snapshot_versions` are exact-only identity domains.
5. Numeric tolerance requires explicit field family, comparator, and threshold.
6. Observation export has an exact envelope; payload comparison inherits
   `numeric_state`.
7. Diagnostics prose is excluded from maintained truth.
8. `RuntimeCapabilities` remains a projection. It may not infer exact GPU,
   resident-state, or shadow support from helper/probe availability.

## 3. Validation

Build command:

```bash
cmake --build build-workshop --target ef_py -j2
```

Result: passed.

Focused WP6 command:

```bash
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade -q
```

Result: `31 passed`.

Documentation checks:

```bash
git diff --check
rg -n "backend_profile_id|profile_class|parity_budget_ref|validation_gate" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "budget_id|comparison_domains|sync_barriers|mismatch_policy|acceptance_gate" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
rg -n "resident_state\\.unmaintained_candidate|supports_resident_state|backend thread completion order|unsynced backend-local state" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519*.md
```

Result: passed.

## 4. Deferred Follow-Up

These items remain visible but do not block WP6 acceptance:

1. A maintained exact GPU backend profile requires a future registry revision,
   exact parity budget, replay evidence, ownership/sync declaration, and
   validation gate.
2. A maintained resident-state profile requires backend-owned state scope,
   host-visible reconstruction or export rules, sync barriers, and a maintained
   parity budget.
3. A maintained shadow-compare profile requires non-interference rules,
   diagnostics separation, and a maintained comparison budget if it is promoted
   beyond diagnostics-only reporting.
4. A dedicated `BackendCapabilityFacade` can be introduced later, but it must
   consume declared registry metadata rather than hidden implementation truth.
5. Machine-readable registry generation can follow after the documentation
   registry shape stabilizes.

## 5. Closure

WP6 completes the backend profile policy layer for the current architecture
line. Follow-on backend work should revise the registries and cite this
acceptance review before changing maintained capability projection.
