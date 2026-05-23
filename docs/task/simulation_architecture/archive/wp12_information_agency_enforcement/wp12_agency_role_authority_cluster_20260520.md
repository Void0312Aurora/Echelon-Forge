# WP12-B Agency Role Authority Boundary

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_agency_role_authority_cluster_20260520.md`
- Chinese companion:
  [wp12_agency_role_authority_cluster_20260520.zh.md](wp12_agency_role_authority_cluster_20260520.zh.md)

Inputs:

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)

## 1. Purpose

`WP12-B` makes the `AgentRole` five-part schema enforceable for the first
maintained authority slice. It verifies that a maintained action or
coordination output has a role, authority scope, information-state source,
decision-model reference, and action interface before it is treated as
authorized.

This is an Agency Graph boundary, not the full Agency Graph runtime.

## 2. Scope

In scope:

- add or extend `AgentRole` validation helpers for maintained paths;
- reject missing, unknown, or incompatible authority scopes;
- reject information-state sources that are incompatible with the consumer's
  maintained/diagnostics status;
- reject action interfaces that do not match the produced action or
  coordination packet family;
- add binding/runtime/architecture tests proving accepted and rejected roles.

Out of scope:

- full decision-model dispatcher for scripted, learned, human, LLM, or MCTS
  agents;
- complete role-based access control for every information producer;
- orchestration UI or mission editor work;
- capability-bundle migration;
- backend/fidelity promotion.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/mission/test_policy_contract_shape.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/test_policy_belief_boundaries.py`

Preferred approach:

- introduce reusable validation at the contract/facade boundary rather than
  hard-coding a role table into a single test;
- keep authority vocabulary narrow and explicit for the first slice;
- preserve existing DTO compatibility where possible, but fail closed for
  maintained authorization.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Valid maintained role | Declares role, authority scope, information-state source, decision-model reference, and action interface. |
| Missing role field | Rejected for maintained authorization. |
| Incompatible information source | Rejected unless the path is diagnostics-only and explicitly labeled. |
| Incompatible action interface | Rejected before intent injection. |
| Unknown authority scope | Fails closed unless explicitly added to the accepted vocabulary. |

## 5. Acceptance Tests

Minimum tests:

- valid role authorizes the focused maintained action or coordination path;
- missing authority scope fails;
- maintained role with diagnostics-only/truth source fails;
- role action interface mismatch fails;
- binding or Python-visible shape preserves role fields;
- tests explicitly state this is not full Agency Graph runtime dispatch.

## 6. Handoff Contract

Return:

- contract/facade/binding files touched;
- accepted authority vocabulary and rejected cases;
- tests added or updated;
- exact commands run and outcomes;
- blockers and residuals for full Agency Graph runtime;
- integration notes for `WP12-D` and `WP12-E`.
