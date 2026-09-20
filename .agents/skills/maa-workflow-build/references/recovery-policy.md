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
- Explore instead of retrying when the failure shows the flow was never observed: a node aimed at a screen that does not exist, or a reused component called from a state it does not accept, is an exploration gap, not a tuning problem.
- Request user input when a material product or safety decision cannot be inferred.
- Stop when the retry limit is reached, no safe observation is available, or the next action would cross the task's authority boundary.

## Route failures to the owner

Classify test evidence before retrying. Do not restart every specialist for a local defect.

| Failure class | Return to | Required response |
|---|---|---|
| Recognition or action-node failure | `$maa-pipeline-generate` | Adjust the recognition/action node, ROI, asset, or screenshot-derived evidence, then rerun the focused test. |
| Option-surface or override-wiring failure | `$maa-pipeline-option` | Repair the user-facing option, default, override path, or Python parameter wiring, then test enabled and disabled behavior. |
| Unexplored-scene or assumed-precondition failure | `EXPLORE` in `$maa-workflow-build` | Reset the state's `evidence_status` to `guessed`, reopen the exploration gate, and observe the real screens and the reused component's entry precondition before writing more nodes or Custom code. |
| State-model failure | `DESIGN` in `$maa-workflow-build` | Add or correct start, success, no-op, failure, recovery, or stop states before changing more nodes. |
| Integration or control-flow failure | `IMPLEMENT` in `$maa-workflow-build` | Repair cross-node links, file placement, Custom registration, or specialist-output assembly, then rerun structural checks. |
| Environment, device, permission, or authority failure | `RECOVER` or user handoff | Gather a safe observation, use an authorized fallback, or stop with the smallest explicit unblock request. |
| Unknown failure class after focused testing | `$maa-diagnose` | Request read-only cross-tool evidence, then route from the returned `failure_owner`. |

Report the latest stable state, attempted recoveries, preserved artifacts, and the smallest action that could unblock the task.

## Request diagnosis only when the owner is unknown

Diagnosis is an evidence step inside `RECOVER`, not a phase of every task. Route to `$maa-diagnose` only when all of these hold:

- a failure already occurred, with a real log, error, or failed run to inspect;
- focused testing did not attribute the failure to a node, option, state model, or integration defect;
- the cause could plausibly live in more than one place - runtime logs, static project definition, environment, or harness;
- the needed evidence cannot be obtained by one more safe local observation.

Do not request diagnosis when:

- `$maa-pipeline-testing` already named the owner. A focused recognition or action-node failure stays with `$maa-pipeline-generate` and its focused rerun, and must not trigger a broad diagnostic pipeline;
- an option-surface or override-wiring failure is already isolated. That stays with `$maa-pipeline-option`;
- the problem is project scaffold or managed-file health. That is `$maa-project-create` doctor;
- no failure has happened yet, or the request is exploratory rather than a recovery.

### Consume the diagnostic result

`$maa-diagnose` returns a read-only result with `status`, `summary`, `findings`, `evidence`, `artifacts`, `next_actions`, one `failure_owner`, and `stop_reason`. Treat it as evidence, not as a decision:

| Returned `failure_owner` | `RECOVER` decision |
|---|---|
| `generate` or `option` | Delegate the repair to that specialist, then rerun the focused test. |
| `testing` | Add the missing focused check before any repair. |
| `workflow-design` | Replan in `DESIGN` before changing more nodes. |
| `workflow-implement` | Repair assembly, links, or registration in `IMPLEMENT`, then rerun structural checks. |
| `project-create` | Delegate the authorized project repair to `$maa-project-create`. |
| `user` | Stop with the smallest explicit unblock request. |

A `status: error` result with a `stop_reason` such as `diagnostic-runtime-unavailable` means the diagnosis did not happen. Keep the original failure unattributed, do not install the diagnostic runtime, and continue recovery without it. Never apply a `next_actions` entry as an automatic repair; each one still passes through the owning specialist and this control loop.
