# Failure mapping and normalized output

Every diagnosis ends in exactly one `failure_owner` and a safe next action for that owner. A finding that cannot be attributed is reported as an open gap, not forced onto an owner.

## Normalized result

```yaml
status: success | warning | error
summary: one-line diagnostic result
findings: []
evidence: []
artifacts: []
next_actions: []
failure_owner: generate | option | testing | workflow-design | workflow-implement | project-create | user
stop_reason: null
```

| Field | Rule |
| --- | --- |
| `status` | `success` when the owner is attributed from complete evidence; `warning` when the view was bounded, truncated, or the runtime reported gaps; `error` when the runtime was unavailable, incompatible, or failed |
| `summary` | One line naming the observed failure and the attributed owner |
| `findings` | Observed facts plus the attribution reasoning, each traceable to an evidence entry |
| `evidence` | Runtime evidence ids with the source locators the runtime returned - file, line, timestamp, task, node - plus the source log and project paths that were read |
| `artifacts` | Every produced report path, saved structured result, referenced screenshot path, and the resolved runtime surface and version |
| `next_actions` | Bounded, non-mutating steps for the named owner |
| `failure_owner` | Exactly one value from the enumeration |
| `stop_reason` | `null` unless the diagnosis stopped early; then a stable reason such as `diagnostic-runtime-unavailable`, `diagnostic-contract-unsupported`, `diagnostic-inputs-insufficient`, or `authority-boundary` |

Preserve the runtime's evidence ids verbatim so the owner can reopen the same fact with the runtime's lookup commands instead of re-running the analysis.

## Owner map

| Observed failure class | `failure_owner` | Safe next action to recommend |
| --- | --- | --- |
| Recognition never matched, wrong candidate won, ROI or threshold contradicts the observed candidates | `generate` | Re-tune the named recognition node against the cited candidate evidence, then rerun the focused test |
| Action reported success but the expected state change is absent | `generate` | Add or correct the post-action observable check on the named node |
| Runtime override or option surface changed behavior away from the static definition | `option` | Repair the option default, override path, or parameter wiring, then test enabled and disabled behavior |
| The failing node exists but nothing in the run proves the acceptance criterion was ever checked | `testing` | Add the missing focused check before further repair |
| The run reached a state the designed state machine does not model, or a loop had no reachable exit candidate | `workflow-design` | Add or correct the missing start, no-op, failure, recovery, or stop state |
| A referenced node, entry, Custom registration, or file placement is missing from the static definition | `workflow-implement` | Repair the cross-node link or registration, then rerun structural checks |
| Resource or schema load failure, managed project file drift, or a template or scaffold inconsistency | `project-create` | Run `$maa-project-create` doctor on the cited path before editing anything by hand |
| Environment or dependency failure, incompatible runtime version, missing binary or model | `user` | State the smallest explicit unblock request; do not install anything |
| Device, emulator, permission, or connection failure | `user` | Ask for the device or permission state to be restored, then re-collect the run |
| Diagnostic runtime unavailable, unsupported, or unparsable | `user` | Report the discovered state and the smallest install or version action the user could take |
| Evidence is genuinely insufficient to attribute an owner | `testing` | Name the one additional bounded observation that would attribute it, and set `stop_reason: diagnostic-inputs-insufficient` |

## Required coverage

A diagnosis must handle at least these four cases end to end:

1. **Resource or schema failure.** Correlate the load error with the static definition, attribute to `project-create` for managed scaffold drift or `workflow-implement` for an authored reference defect.
2. **Environment or dependency failure.** Attribute to `user` with the discovered version facts, and never repair by installing.
3. **Runtime log failure.** Correlate the failing node in the log with the static definition and route to `generate`, `option`, `workflow-design`, or `workflow-implement` according to the table.
4. **Missing runtime.** Stop with `status: error`, `failure_owner: user`, and `stop_reason: diagnostic-runtime-unavailable`, leaving the original failure explicitly unattributed.

## Attribution rules

- One diagnosis, one owner. When several findings point at different owners, name the owner that blocks the others first and list the rest in `findings`.
- Runtime facts are observations, not causes. A logged success does not prove a business result, and time adjacency does not prove causation.
- A bounded or truncated view cannot prove absence. Say the view was bounded instead of concluding a node or override does not exist.
- Never widen an already-attributed failure. If focused testing named the owner, this skill has nothing to add.
- Never auto-apply a repair, edit project files, or rerun a side-effecting task as part of the recommendation.
