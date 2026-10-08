# Frozen-force integrator contract

Issue: #123  
Owner: `systems/physics`  
Status: implemented

`LeapfrogIntegrate` receives one `ForceAccumulator` sample per frame. It uses
that sample for both half-kicks around the semi-implicit position drift:

```text
v_half = v + (F / m) * dt / 2
x_new  = x + v_half * dt
v_new  = v_half + (F / m) * dt / 2
```

This is exact for constant acceleration. It does not claim general
Störmer-Verlet or Velocity-Verlet behavior, symplecticity, bounded energy error,
or second-order convergence for state-dependent forces, damping, or contact.
The ground contact solver uses the same single-force discretization, so changing
to a second force evaluation requires a separate contact update and acceptance
plan.

The angle helper returns non-finite inputs unchanged before normalization. This
keeps diagnostics finite-safe without changing the result for ordinary angles.

Regression coverage includes a one-step constant-acceleration closed form and
NaN/infinity angle inputs.
