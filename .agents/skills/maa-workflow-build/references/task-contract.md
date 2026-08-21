# Task Contract

Create this contract before editing. Keep facts, decisions, assumptions, and open questions separate. Update the contract only when new evidence or a user decision changes the intended outcome.

```yaml
task_id: stable-local-identifier
goal: observable outcome in one sentence
non_goals: []

start_states:
  - id: stable-state-name
    evidence: how the state is recognized
  - id: unknown-state
    evidence: unexpected or insufficient observation

success_states:
  - id: completed-state
    evidence: observable postcondition

failure_states:
  - id: bounded-failure
    response: recover | stop | request-user

constraints: []
allowed_side_effects: []
forbidden_side_effects: []

facts: []
user_decisions: []
assumptions:
  - statement: reversible working assumption
    validation: how and when to verify it
open_questions: []

acceptance_criteria:
  - id: AC-1
    behavior: externally observable behavior
    evidence_required: test, screenshot, log, graph, or file inspection
    required: true
```

## Contract rules

- Express the goal as a result, not an implementation choice.
- Describe every start and success state using observable evidence.
- Include a no-op path when the requested action is unnecessary or disabled.
- Make unsafe fallback behavior forbidden by default.
- Require a post-action observation; an attempted click or executed node is not success.
- Ask the user only when an unresolved choice changes safety, irreversible behavior, or the meaning of success.
- Keep optional enhancements outside the required acceptance criteria.

## Example: stamina recovery

```yaml
goal: Resume the original task after using at most one owned normal stamina item when stamina is insufficient.
non_goals:
  - Buy stamina items.
  - Spend premium currency.
start_states:
  - id: original-task
    evidence: the task entry or its stable pre-action screen is recognized
  - id: stamina-insufficient-dialog
    evidence: the insufficient-stamina message is recognized
  - id: recovery-dialog
    evidence: the owned normal item and its use control are recognized
  - id: unknown-state
    evidence: none of the supported stable states is recognized
success_states:
  - id: resumed
    evidence: stamina increased or the insufficient dialog disappeared, and the original task resumed
constraints:
  - Never purchase an item or spend premium currency.
  - Never repeat consumption after an unverified attempt.
acceptance_criteria:
  - id: AC-1
    behavior: Sufficient stamina follows the no-op path.
    evidence_required: behavioral test
    required: true
  - id: AC-2
    behavior: An owned normal item is used at most once and recovery is observed.
    evidence_required: authorized end-to-end trace
    required: true
  - id: AC-3
    behavior: Missing items, paid-only recovery, and ambiguous recognition stop safely.
    evidence_required: failure-path tests
    required: true
```
