# Run State

Keep one compact run state for the active task. Update it after every meaningful observation, mutation, verification result, or phase transition.

```yaml
task_id: stable-local-identifier
phase: SPECIFY | DISCOVER | EXPLORE | DESIGN | IMPLEMENT | VERIFY | COMPLETE | RECOVER
status: success | warning | error
summary: one-line current result

current_state:
  project: known project facts
  runtime: observed UI or device state
  verification: current acceptance coverage

exploration:
  gate: open | closed
  guessed_states: []
  round_trip_complete: false
  observed_transitions:
    - state: stable-state-name
      artifact: screenshot path or capture identifier
      recognized: {text: read text, box: [x, y, w, h], source: ocr | template | color | manual-read}
      action: what was done to leave this state
      next_state: state observed after the action
  unreachable_states: []

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
- Move to `EXPLORE` when any required start or success state is still `evidence_status: guessed` or lacks a non-empty `evidence_artifact`, and keep `exploration.gate: open` until every one of them is `evidence_status: observed` with a non-empty `evidence_artifact`.
- Leave `EXPLORE` for `DESIGN` only with `exploration.gate: closed` and `round_trip_complete: true`. Nodes and Custom code are written after that transition, never before it.
- Move to `RECOVER` when an expected observation, tool call, edit, or test fails.
- Return from `RECOVER` to the phase that owns the failed result after re-observation or replanning.
- Move to `COMPLETE` only after all required acceptance criteria have observable evidence.
- Keep `status: warning` when progress is safe but evidence is incomplete.
- Use `status: error` with a `stop_reason` when no safe action remains.
- Never erase failed attempts; summarize them so the same ineffective action is not repeated.

At phase boundaries, keep only the stable task contract, current run state, artifact paths, and evidence needed by the next specialist skill.
