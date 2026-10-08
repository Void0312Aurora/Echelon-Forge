# Native invariant and training process boundary

Issue: #124

## Policy and caller inventory

| Boundary | Handling before callbacks |
|---|---|
| `SimulationKernel.set_time_step` | Catchable invalid-argument/ValueError for non-positive, non-finite, unrepresentable or draw-clock-overflowing dt |
| `SimulationKernel.step` | Catchable refusal before `ecs.progress` for clock overflow or missing identity singleton |
| Command APIs accepting raw entity IDs | Existing invalid-entity and missing-serial warning/refusal before the command-link draw |
| Weapon release and damage debug APIs | Existing live-participant/serial checks and false/status result before stochastic evaluation |
| Factory, EW decoy creation, pilot weapon release | Internal stamping; double stamp, invalid lifecycle, or missing identity singleton is a defect |
| Sensor, acoustic, weapon, EW, command-link draw callbacks | Internal participants and clock must have passed the owner boundary; no fallback to raw IDs |

The two explicit abort statements remain in the identity and stochastic helper
headers. They emit operation/draw-site, reason, and entity ID to flushed stderr.
Exceptions must not unwind through Flecs C callback frames. The pure
`stamp_refusal` and `stochastic_draw::valid_time` predicates allow safe preflight;
quantization also rejects integer-conversion overflow.

## Worker supervision

Expected invalid input is refused in the same worker, which remains usable.
An internal invariant terminates that worker and cannot be caught by Python.
Process-isolated training must capture stderr and the exit code/signal, mark the
active rollout incomplete, and start a new worker with a fresh/reset episode.
Do not retry the same corrupt in-memory world or silently count the rollout as
successful. The current kernel does not provide automatic worker supervision or
crash checkpoint recovery; applications using one Python process share its fate.

The regression launches native stamp/draw fault probes in separate processes,
asserts the abort classification and diagnostic, then starts a replacement
Python worker. The native probes are skipped in the ordinary in-process suite
and require an explicit fault environment variable plus `--no-skip`.
