# Full scenario setup timestep

Full batch and single-world layout setup restores the kernel's canonical
`SimulationKernel::kDefaultTimeStepS` (1/60 s) when a scenario omits
`environment.time_step`. It never inherits an earlier scenario's timestep.
The Python binding exports the same value as `ef_py.DEFAULT_TIME_STEP_S` for
legacy kernel scenario setup. Plain episode reset preserves the selected dt.

Authored scenario dt must be a finite positive number; null, booleans, strings,
zero, negatives and nonfinite numbers are errors. Native setup keeps its
existing empty-vector and zero-sentinel encoding of absence, supports a single
value or one value per world, and rejects bad counts, negatives and nonfinite
values before mutating any world. Callers can inspect the effective result with
`RuntimeFacade.world_time_step(world_index)`.

Regression coverage exercises fresh/reused A/B/A worlds, one/multiple worlds,
single layout and legacy kernel setup, and invalid native inputs with entity
survival to prove a rejected call did not reset the world.
