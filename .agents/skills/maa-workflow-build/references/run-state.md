# Run State

Keep one compact run state for the active task. Update it after every meaningful observation, mutation, verification result, or phase transition.

```yaml
task_id: stable-local-identifier
phase: SPECIFY | DISCOVER | DESIGN | IMPLEMENT | VERIFY | COMPLETE | RECOVER
status: success | warning | error
summary: one-line current result

current_state:
  project: known project facts
  runtime: observed UI or device state
  verification: current acceptance coverage

observations: []
assumptions: []
decisions: []
plan: []
next_actions: []
artifacts: []
evidence: []

recovery:
  root_cause_hint: null
  retry_count: 0
  safe_retry: null
  stop_condition: null

stop_reason: null
```

## Transition rules

- Move forward only when the current phase has produced its required artifact or evidence.
- Move to `RECOVER` when an expected observation, tool call, edit, or test fails.
- Return from `RECOVER` to the phase that owns the failed result after re-observation or replanning.
- Move to `COMPLETE` only after all required acceptance criteria have observable evidence.
- Keep `status: warning` when progress is safe but evidence is incomplete.
- Use `status: error` with a `stop_reason` when no safe action remains.
- Never erase failed attempts; summarize them so the same ineffective action is not repeated.

At phase boundaries, keep only the stable task contract, current run state, artifact paths, and evidence needed by the next specialist skill.
