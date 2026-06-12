# Naval Domain Surface Split Dispatch Queue

Status: `2026-06-12`; `P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` accepted.
`P2-B` remains ready and must be serial if it touches runtime contracts; `P5-A`
remains held until command projection is resolved or explicitly held.

Parent project: [Naval Domain Surface Split](README.md)

## Queue Rules

- Dispatch only clusters listed in
  [naval_domain_surface_split_task_clusters_20260601.md](naval_domain_surface_split_task_clusters_20260601.md).
- One packet maps to one cluster.
- Do not edit parent README, current status, and acceptance docs in parallel with
  implementation workers.
- Runtime contract edits are serial unless the integration owner confirms
  disjoint symbols and tests.
- Worker output must classify remaining air-first dependencies.

## Ready Packets

| Packet | Cluster | Status | Write set | Validation |
| --- | --- | --- | --- | --- |
| `DS-P1-A-inventory` | `P1-A` | returned/pass, accepted from `Linnaeus` | status docs and optional diagnostics notes | read-only inventory plus `git diff --check -- docs/task/naval` |
| `DS-P1-B-guards` | `P1-B` | returned/pass, accepted from `Locke` | training/eval guard tests | focused naval pytest |
| `DS-P2-A-action-transport` | `P2-A` | returned/pass, accepted from `Locke` | action/runtime contracts and adapters | C++/binding if touched plus world-batch naval tests |
| `DS-P2-B-command-projection` | `P2-B` | ready, choose serially | command contracts, naval profile, command-chain tests | command roundtrip and world-batch tests |
| `DS-P3-A-observation-packet` | `P3-A` | returned/pass, accepted from main thread | observation taxonomy/runtime/tests | mission observation and naval runtime tests |
| `DS-P3-B-config-alias` | `P3-B` | returned/pass, accepted from `Linnaeus` | env config, train CLI, docs/tests | env-config and bootstrap tests |
| `DS-P4-A-integration` | `P4-A` | returned/pass, accepted from main thread | active configs, eval, runtime naval tests | active entry, eval, scenario contract gates |
| `DS-P5-A-closeout` | `P5-A` | held until `P2-B` disposition | docs only | acceptance gate plus `git diff --check` |

## Worker Packet Template

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
air-first dependency classification:
```

## No-Dispatch Conditions

Do not dispatch implementation workers while:

- the inventory does not identify whether `PilotAction` and `MissionCommand`
  dependencies are adapter, blocker, or accepted shared infrastructure;
- a worker would need to claim N5/N6 maturity to close its packet;
- tests would require broad air runtime rewrites outside the cluster write set.
