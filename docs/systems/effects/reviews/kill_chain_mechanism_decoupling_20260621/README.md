# Kill-Chain Mechanism Decoupling Review - 2026-06-21

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/README.md`
Owner: `systems/effects/reviews`
Last verified: `2026-08-08`
Review basis: retained `2026-06-21` mechanism, facade, load, response, and admission evidence.

## Scope

This package reviews the separation of approach, fuze decision, warhead load,
component response, and consequence projection. It preserves Chinese detailed
records plus machine-readable diagnostic packets.

## Retained Evidence

- [Mechanism analysis](kill_chain_mechanism_decoupling_analysis_20260621.zh.md)
- [Decoupling probe results](kill_chain_decoupling_probe_results_20260621.zh.md)
- [Component load-factor view](kill_chain_component_load_factor_view_20260621.zh.md)
- [Component response boundary](kill_chain_component_response_boundary_20260621.zh.md)
- [Calibration admission gate](kill_chain_calibration_admission_gate_20260621.zh.md)
- [Machine-readable review packet](review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json)

## Verdict And Limitations

Accepted as retained diagnostic and implementation-boundary evidence. The
package does not authorize runtime retuning, real weapon/target calibration,
deterministic-fuze claims, Pk claims, or cross-layer calibration.

Current behavior must be read from code, tests, and maintained system
standards; these dated notes are not an active task queue.
