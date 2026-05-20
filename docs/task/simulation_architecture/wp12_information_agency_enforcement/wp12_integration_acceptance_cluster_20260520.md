# WP12-E Integration And Acceptance Handoff

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_integration_acceptance_cluster_20260520.md`
- Chinese companion:
  [wp12_integration_acceptance_cluster_20260520.zh.md](wp12_integration_acceptance_cluster_20260520.zh.md)

Inputs:

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.md)
- [WP12-A Law 14 read-side enforcement](wp12_law14_read_side_enforcement_cluster_20260520.md)
- [WP12-B agency role authority boundary](wp12_agency_role_authority_cluster_20260520.md)
- [WP12-C information transformation surface](wp12_information_transformation_surface_cluster_20260520.md)
- [WP12-D intent injection authority guard](wp12_intent_injection_authority_guard_cluster_20260520.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

`WP12-E` is the serial integration and acceptance handoff lane. It reconciles
A-D implementation evidence, records residuals honestly, prepares the acceptance
review, and synchronizes task/review indexes after the implementation streams
are mergeable.

It must not make documentation closure block implementation mergeability.

## 2. Scope

In scope:

- collect A-D touched files, tests, commands, and residuals;
- resolve shared validator naming and duplicated fixtures;
- run the final focused validation set or record precise blockers;
- draft `wp12_information_agency_enforcement_acceptance_review_20260520.md`
  and the Chinese companion only after implementation evidence exists;
- update route, README, review index, and bilingual references as closure-lane
  work;
- archive or index only when acceptance actually happens.

Out of scope:

- accepting a gate from prose-only evidence;
- broadening WP12 to backend/fidelity or capability work;
- hiding failed or blocked validation commands;
- rewriting worker-owned code without first inspecting their handoff notes.

## 3. Integration Checklist

Required checks:

- `WP12-A` evidence proves focused Law 14 read-side enforcement and explicit
  diagnostics-only truth access.
- `WP12-B` evidence proves role authority validation and rejected invalid-role
  fixtures.
- `WP12-C` evidence proves transformation vocabulary/evidence is
  machine-checkable for the selected slice.
- `WP12-D` evidence proves authorized belief-to-intent or coordination injection
  through the facade-compatible seam.
- Acceptance text does not claim full Agency Graph runtime, repository-wide Law
  14 coverage, backend/fidelity expansion, or full producer migration.

## 4. Validation Commands

Expected final commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_policy_belief_boundaries.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP12
```

If a command is too broad for the integration pass, record the narrower command
that actually ran and the reason.

## 5. Acceptance Review Shape

The final review should include:

- verdict;
- gate verdict table for `WP12-A` through `WP12-E`;
- exact validation commands and observed outcomes;
- implementation notes;
- residuals and next plan;
- scope caveats.

The review is not required during planning. Missing acceptance review means
`WP12` is open, not failed.

## 6. Handoff Contract

Return:

- A-D stream status table;
- final validation commands and outcomes;
- acceptance review files created or blocked;
- README/route/review index files touched;
- residual register;
- next-WP recommendation, without opening backend/fidelity unless WP12 evidence
  is accepted.
