# Execution Coarse-Grained Route Segment Plan

Status: Closed on 2026-03-24.
Phase 0 prototype code and benchmark tooling exist. This line is not being
advanced into the training mainline because the execution acceleration focus has
shifted to the GPU simulation path.

## Goal

Reduce `p5`-style long-horizon execution training wall-clock without relaxing the
realism requirement for the phases that are most dynamics-sensitive.

The target is not a fully approximate mission simulator. The target is a
two-layer system:

- truth layer:
  high-fidelity `UniversalEnv -> ScenarioLoader -> SimulationKernel`
- coarse segment layer:
  route-leg propagator for long, comparatively stable cruise / return segments

Takeoff rotation, terminal approach, flare, and rollout remain on the truth
layer.

## Why This Cut

Current profiling shows the main bottleneck is not single-step kernel cost. The
main bottleneck is the serial horizon of the continuous route task:

- many low-level steps
- delayed terminal feedback
- long route geometry before landing becomes relevant

That means the first acceleration target should be the route middle section,
not the runway-sensitive ends.

## Realism Constraints

This design keeps realism by separating "judge" from "accelerator":

- the truth simulator remains the only acceptance authority
- the coarse layer only replaces segments whose dynamics are already mission-
  constrained and comparatively smooth
- the coarse layer uses only realism-safe inputs already visible to the policy
  or mission shell:
  - current kinematic state
  - mission command / active waypoint targets
  - route geometry
  - wind estimate

The coarse layer does not get privileged future state, reward, or hidden
controller internals.

## Scope Of Phase 0

Phase 0 is a benchmark-first prototype, not a training replacement.

Deliverables:

- a route-segment propagator in
  [coarse_route_propagator.py](/home/void0312/Workshop/CMO/python/rl/planning/coarse_route_propagator.py)
- a benchmark in
  [tools/diagnostics/benchmarks/coarse_route_segments.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmarks/coarse_route_segments.py)
- a first error / risk report from real `p5` traces

Phase 0 explicitly excludes:

- takeoff coarse-graining
- landing coarse-graining
- world-model-only rollout authority
- direct training-loop integration

## Coarse Segment Model

The current prototype models only active route following.

State carried through a coarse window:

- planar position
- altitude
- ground track / heading
- ground speed
- vertical speed
- active waypoint index

Commands and geometry:

- active waypoint position / radius
- waypoint altitude / speed targets
- LNAV bank limit
- current wind estimate

Dynamics approximation:

- track aligns toward active waypoint bearing with a bank-limited turn-rate cap
- ground speed relaxes toward target speed plus tailwind component
- vertical speed relaxes toward the altitude target with climb / descent caps
- waypoint advancement happens when the projected state enters capture radius

This is intentionally conservative. It is a route propagator, not a surrogate
for terminal handling.

## What Must Be Measured First

Before integrating this into training, we need two classes of evidence.

### 1. State Error

For each candidate coarse horizon, compare coarse prediction against the fine
rollout endpoint:

- horizontal position error
- altitude error
- ground-speed error
- track error
- waypoint-index mismatch rate

### 2. Training Downside Proxies

The coarse layer may speed up rollout but still damage learning. We therefore
measure:

- waypoint-boundary rate inside a coarse window
- command-change rate inside a coarse window
- reward standard deviation inside the fine window
- action delta RMS inside the fine window

Interpretation:

- high boundary rate means event aliasing risk
- high reward std means dense shaping may be smeared out
- high action delta means the policy is still actively correcting inside that
  window, so replacing it with a macro propagation is riskier

## Immediate Acceptance Logic

Phase 0 does not freeze hard thresholds up front. It establishes the baseline
curve first.

For each horizon, the benchmark should answer:

- what decision reduction is possible
- how error grows with horizon
- where reward / action aliasing becomes unacceptable

The likely useful horizon is the longest one that still keeps route error and
event aliasing in a range we can tolerate for training.

## Likely Next Step If The Curve Looks Good

If the benchmark shows a safe horizon on mid-route segments, the next code step
should be an `ExecutionSegmentRuntime`:

- truth simulation for takeoff / terminal / rollout
- coarse propagation only for route windows that satisfy eligibility checks
- truth re-entry at waypoint / terminal boundaries

That is the point where `WorldBatchRuntime` becomes relevant again: not by
threading a single world harder, but by evaluating many coarse segment worlds or
hypotheses in parallel.
