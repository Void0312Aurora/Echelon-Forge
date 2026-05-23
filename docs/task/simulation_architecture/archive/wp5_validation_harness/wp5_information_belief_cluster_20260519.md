# WP5-D Dispatch Sheet: Information And Belief Gates

Status: `2026-05-19` second-wave dispatch sheet.

Language:

- English canonical: `wp5_information_belief_cluster_20260519.md`
- Chinese companion: [wp5_information_belief_cluster_20260519.zh.md](wp5_information_belief_cluster_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP5 first-wave acceptance review](../review/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-A harness inventory notes](wp5_harness_inventory_notes_20260519.md)
- [WP4-H agent shim implementation notes](wp4_agent_shim_implementation_notes_20260519.md)
- Current `python/rl/runtime/agent_shim.py`
- Current `tests/runtime/test_agent_shim.py`
- Current policy/runtime adapter paths under `python/rl/runtime/`, `python/rl/control/`, and `gym_envs/`

## 1. Purpose

WP5-D validates information-state and belief boundaries without banning legacy
compatibility or diagnostics paths. It should prove maintained decision paths
can be labeled as `ObservationPacket` or declared `DecisionBelief` consumers,
while truth/oracle paths stay diagnostics-only.

This is a high-reasoning stream because over-broad guards can block legitimate
diagnostics and legacy migration paths.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP5-D1 Shim Vocabulary Gate` | Strengthen or document tests for `ObservationProvenance`, `AgentRole`, action intent, and coordination intent labels. | `tests/runtime/test_agent_shim.py`, docs. | High. |
| `WP5-D2 Maintained-Path Allowlist Sketch` | Identify maintained adapter modules where future direct `sim.*` restrictions are safe, and list compatibility/diagnostics modules that must stay allowed. | `docs/task/simulation_architecture`, optional architecture test if low-risk. | High. |
| `WP5-D3 Truth/Oracle Leakage Review` | Add docs-backed checks or notes distinguishing `raw_world_truth` / `diagnostics_oracle` labels from maintained policy inputs. | docs, optional narrow tests. | High. |
| `WP5-D4 DecisionBelief Deferral Boundary` | Record what can be tested before a typed `DecisionBelief` DTO exists and what must remain metadata-dependent. | docs. | High. |
| `WP5-D5 Smoke Candidate Advice` | Recommend information/belief tests for WP5-E smoke promotion. | docs. | Medium. |

## 3. Non-Goals

- Do not add a broad repository-wide direct `sim.*` ban.
- Do not require runtime `ObservationViewSpec`, packet snapshot/barrier/source
  metadata, or typed `DecisionBelief` before DTO support exists.
- Do not change policy inference behavior.
- Do not remove diagnostics/oracle helpers.
- Do not edit smoke-suite membership directly.

## 4. Acceptance Gates

This cluster is accepted when:

1. Shim label tests or notes distinguish maintained, compatibility, and
   diagnostics-only information sources.
2. Future direct `sim.*` enforcement has a concrete maintained-path allowlist
   sketch and a compatibility/diagnostics exception list.
3. `DecisionBelief` is either testable through existing labels or explicitly
   deferred pending typed metadata.
4. Focused tests pass locally.
