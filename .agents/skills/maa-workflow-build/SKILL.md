---
name: maa-workflow-build
description: Orchestrate ambiguous end-to-end MaaFramework automation requests into verified implementations. Use when a user asks to build, add, or change a complete Maa workflow or task—such as automatic stamina recovery—without already providing a full Pipeline design, start states, safety constraints, failure handling, or acceptance criteria. Compile intent into a task contract, discover project and UI state, design the state machine, route work across Maa skills, recover from failed observations or tests, and require evidence before completion.
---

# Maa Workflow Build

Own an end-to-end Maa automation request from ambiguous intent through evidence-backed completion. Treat the other Maa skills as specialist capabilities; keep this skill responsible for goal compilation, phase state, routing, recovery, and acceptance.

## Operating contract

- Do not jump from a vague request directly to Pipeline nodes.
- Maintain one task contract and one current run state throughout the task.
- Separate observed facts, user decisions, working assumptions, and unresolved questions.
- Ask only about choices that materially change behavior, safety, or acceptance. Make reversible, low-risk assumptions explicit and continue.
- Define verification before implementation. Do not declare completion because files were written or a single smoke test passed.

Read [references/task-contract.md](references/task-contract.md) before finalizing the goal. Read [references/run-state.md](references/run-state.md) before the first action and at every phase transition.

## Specialist roles

- Keep this orchestrator responsible for the task contract, state-machine design, failure routing, and final acceptance. The orchestrator owns state-machine assembly and integration; specialist outputs do not become a finished workflow until they are connected and verified against the contract.
- Treat `$maa-pipeline-guide` as a reference and constraint source, not a sequential execution phase or node producer. Load only the sections needed to design, edit, or review the current control flow.
- Treat `$maa-pipeline-generate` as the primary producer for recognition and action nodes, especially OCR, TemplateMatch, ColorMatch, ROI selection, and screenshot-derived snippets. Integrate its output into the designed state machine instead of treating generated nodes as task completion.
- Invoke `$maa-pipeline-option` only when the task contract requires a user-facing toggle, selector, checkbox, switch, or input. Do not create options merely because the skill is available.
- Run `$maa-pipeline-testing` after each coherent implementation increment and again against the integrated end-to-end flow. Use its evidence to route a failure back to the specialist or orchestrator phase that owns the defect.
- Treat `$maa-cli-operate` as an execution backend for repeatable checks or guarded runtime operations, not a mandatory business phase.
- Treat `$maa-wiki` as an official-knowledge reference provider. Use it when the task contract, design, or acceptance criteria depend on MaaFramework documentation, schema, API, binding, release, or semantic-change facts; navigate to original sources before treating those facts as authoritative.

Do not treat the specialists as a fixed `guide -> generate -> option -> testing` sequence. Call only the capability required by the current task state, then return its artifacts and evidence to this control loop.

## Control loop

### 1. SPECIFY

Compile the request into a task contract. Define the goal, non-goals, observable start states, success and failure states, constraints, allowed and forbidden side effects, assumptions, and acceptance criteria.

Treat start state as a set of observable states, not one ideal screen. Include safe behavior for an unknown or unexpected state. Resolve project-independent product choices before editing, such as whether paid currency, purchases, repeated consumptions, or destructive actions are allowed.

### 2. DISCOVER

Locate the target project and check for optional project-level context artifacts before broad discovery:

- If `basic_info.md` exists and is current enough for the task, read its routed sections as a cache and verify every touched fact against current source.
- If an ignored graph output such as `pipeline_overview.html`, `pipeline_external_entries.html`, or its `index.html` exists and is current enough, use it for orientation and verify affected edges against current Pipeline and Python files.
- If either artifact is missing, incomplete, or stale, continue with targeted source discovery and record the optional context gap. Do not block the workflow or regenerate the artifact.

Never invoke `$maa-project-init` or `$maa-pipeline-graph` automatically. Use those one-time or low-frequency project tools only when the user explicitly requests initialization, refresh, visualization, or graph regeneration. Confirm current Pipeline files, task entries, resource groups, public return/recovery nodes, option surfaces, Python entries, device availability, and current UI evidence directly from the project and environment.

### 3. DESIGN

Design the complete state machine before generating nodes. Include:

- every supported start state;
- normal progress and success states;
- no-op and already-complete paths;
- recoverable failures and bounded retries;
- unsafe or ambiguous states that must stop;
- an observable post-action success check;
- a stable return or handoff state.

Use `$maa-pipeline-guide` to choose Pipeline state transitions versus CustomAction or CustomRecognition. Define the required files, nodes, options, and verification ladder. For actions that spend currency, consume items, start battles, or change an account, design a non-mutating probe before the real action.

### 4. IMPLEMENT

Apply the smallest coherent change that can satisfy the task contract:

- assemble and edit the overall Pipeline control flow in this orchestrator according to the designed state machine;
- consult `$maa-pipeline-guide` while designing, editing, or reviewing that control flow;
- use `$maa-pipeline-generate` to produce recognition/action nodes and ROI sweeps;
- use `$maa-pipeline-option` only for required user-facing controls and their end-to-end wiring;
- use `$maa-cli-operate` for compact repeatable validation and guarded runtime operations;
- use `$maa-pipeline-testing` after each coherent increment for recognition, Custom wiring, and behavioral validation, then run the integrated verification ladder.

Keep temporary probes distinguishable from deliverable nodes. Preserve the target project's existing schema and naming conventions. Update the run state after each meaningful observation, edit, or failed attempt.

### 5. VERIFY

Read [references/acceptance-protocol.md](references/acceptance-protocol.md). Verify in increasing-risk order:

1. syntax, schema, references, and resource loading;
2. graph integrity and option/Custom wiring;
3. non-mutating recognition probes on known stable screens;
4. normal, no-op, disabled, failure, and recovery branches;
5. an end-to-end run only when its side effects are authorized;
6. post-action state and regressions against the task contract.

Attach observable evidence to each acceptance criterion. A skipped or unavailable check remains open unless the contract explicitly permits a documented limitation.

### 6. COMPLETE

Complete only when every required acceptance criterion has supporting evidence, no unexplained high-risk finding remains, temporary artifacts are handled, and the final state is stable.

Do not declare completion based only on generated JSON, a clean resource load, an unverified plan, or the model's own assessment. Report changed artifacts, verification evidence, remaining limitations, and safe follow-up actions.

### 7. RECOVER

Read [references/recovery-policy.md](references/recovery-policy.md) whenever an observation, tool call, edit, or test fails. Record the root cause or best bounded hypothesis, a safe retry, retry count, evidence needed from the retry, and an explicit stop condition.

Re-observe after navigation or unexpected output. Replan when the state model is wrong. Stop instead of repeating ambiguous clicks, resource-consuming actions, or an unchanged failing attempt.

## Phase output

At each phase boundary, update a compact result with:

```yaml
status: success | warning | error
summary: one-line phase result
next_actions: []
artifacts: []
evidence: []
stop_reason: null
```

Keep the task contract stable unless new evidence or a user decision changes it. Compact context at phase boundaries; load only the specialist skill and reference needed for the next action.
