# Policy Tests

`tests/policy/` contains maintained regressions for policy-side behavior:

- policy routing and route statistics
- execution-policy head surfaces and hybrid action distributions
- auxiliary training update paths
- first-event timing labels and event-head update contracts
- grouped stopping loss contracts
- policy bootstrap and control-config parity

File names should describe the capability under test. Historical mechanism
labels such as `A6`, `A7`, `M3S1`, or `M3S2` may remain in individual test
names when they are needed for traceability, but they should not define new
test-file or directory names.
