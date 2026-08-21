# Recovery Policy

Use this contract for every failed observation, tool call, edit, or test:

```yaml
failure: concise symptom
root cause: confirmed cause or bounded hypothesis
safe retry: one action that changes the conditions or gathers new evidence
evidence_expected: result that would confirm or reject the hypothesis
retry_limit: finite count
stop condition: condition that forbids another retry
fallback: replan | use-another-tool | request-user | stop
```

## Rules

- Re-observe before retrying after navigation, scrolling, timing changes, or unexpected UI output.
- Change one relevant condition per retry so the result is attributable.
- Do not repeat an unchanged failed action.
- Do not retry a resource-consuming or destructive action when its outcome is unknown.
- Use a non-mutating probe before retrying a click, confirmation, purchase, battle, or item consumption.
- Replan when observed states contradict the designed state machine.
- Request user input when a material product or safety decision cannot be inferred.
- Stop when the retry limit is reached, no safe observation is available, or the next action would cross the task's authority boundary.

## Route failures to the owner

Classify test evidence before retrying. Do not restart every specialist for a local defect.

| Failure class | Return to | Required response |
|---|---|---|
| Recognition or action-node failure | `$maa-pipeline-generate` | Adjust the recognition/action node, ROI, asset, or screenshot-derived evidence, then rerun the focused test. |
| Option-surface or override-wiring failure | `$maa-pipeline-option` | Repair the user-facing option, default, override path, or Python parameter wiring, then test enabled and disabled behavior. |
| State-model failure | `DESIGN` in `$maa-workflow-build` | Add or correct start, success, no-op, failure, recovery, or stop states before changing more nodes. |
| Integration or control-flow failure | `IMPLEMENT` in `$maa-workflow-build` | Repair cross-node links, file placement, Custom registration, or specialist-output assembly, then rerun structural checks. |
| Environment, device, permission, or authority failure | `RECOVER` or user handoff | Gather a safe observation, use an authorized fallback, or stop with the smallest explicit unblock request. |

Report the latest stable state, attempted recoveries, preserved artifacts, and the smallest action that could unblock the task.
