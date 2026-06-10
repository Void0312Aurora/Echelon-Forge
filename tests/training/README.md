# Training Tests

`tests/training/` contains maintained contracts for training orchestration
surfaces:

- bootstrap and CLI acceptance
- active training entry gates
- diagnostics callback logging contracts
- deterministic fault-localization probes

File names should describe the training capability being protected. Domain,
stage, or mechanism labels such as air-combat, naval, A6, A7, M3S1, M3S2, or
N4 may remain in individual test names when needed for traceability, but they
should not define new test-file names.

Temporary learning probes and ad hoc debugging scripts belong under
`tools/diagnostics/` until they are stable enough to promote into one of the
maintained surfaces above.
