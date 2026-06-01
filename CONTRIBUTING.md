# Contributing

## Current Collaboration Model

This repository is currently maintained in a conservative, owner-led mode.

- The default assumption is that planning, implementation, and release
  decisions stay with the repository owner.
- External pull requests are not the primary development path for the project
  at this stage.
- Small bug reports, factual corrections, and scoped clarifications are more
  useful than broad unsolicited redesign proposals.

If you want to suggest a non-trivial change, open an issue first and wait for
scope confirmation before investing in a pull request.

## Before Opening Work

Please check the following first:

- [README.md](README.md) for project layout, build flow, and validation entrypoints
- [docs/README.md](docs/README.md) for maintained documentation navigation
- [SECURITY.md](SECURITY.md) before reporting anything security-sensitive

For changes that affect architecture, runtime contracts, or maintained
documentation, include the relevant document or test references in your issue
or proposal.

## Pull Request Expectations

Unsolicited pull requests may be closed when they:

- change architecture without prior discussion
- introduce large dependency, packaging, or build-policy shifts
- add generated artifacts, datasets, or bulky experiment outputs
- bypass existing naming, layering, or documentation conventions

If a pull request is invited or clearly in-scope, keep it focused:

- prefer small diffs over bundled refactors
- update documentation when behavior or operator workflow changes
- add or adjust tests when contracts or maintained behavior change
- avoid mixing unrelated cleanup into the same change

## Local Validation

Use the repository-local environment and maintained helpers described in
[README.md](README.md).

Typical Linux/macOS validation flow:

```bash
source .venv/bin/activate
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

Run narrower targeted tests when your change only touches a maintained slice.

## Documentation Rules

- English `.md` files are the canonical maintained documents
- Chinese `.zh.md` files are companion documents where maintained
- keep one language per file body whenever practical
- preserve repository paths, command lines, identifiers, and code fences

For the maintained documentation policy, see:

- [docs/standards/governance/bilingual_documentation_policy.md](docs/standards/governance/bilingual_documentation_policy.md)

## Licensing Status

The project is licensed under the Apache License, Version 2.0. See
[LICENSE](LICENSE).

Unless explicitly stated otherwise, any contribution intentionally submitted
for inclusion in this repository is submitted under the same Apache-2.0 terms.

Third-party assets, datasets, generated artifacts, and copied upstream code
must include their own source and license information. Do not add material with
unclear redistribution rights. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
for the current local notice inventory.

## Communication Style

When opening issues or proposed changes:

- state the observed problem first
- point to the file, command, scenario, or test involved
- separate confirmed facts from proposed interpretation
- keep screenshots and logs trimmed to the relevant failure surface
