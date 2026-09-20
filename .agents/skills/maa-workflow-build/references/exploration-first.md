# Exploration First

Read this when the exploration gate is open. An unexplored scene is discovered, not predicted: the UI flow, its intermediate screens, and the entry preconditions of the components you intend to reuse are unknown until a screenshot or recognition result shows them.

## Gate condition

The gate is mechanical. For every entry in `start_states` and `success_states` that the task contract marks `required`:

| `evidence_status` | Means | Gate |
|---|---|---|
| `observed` | A `screencap`, `ocr`, or recognition trace captured in this task shows the state, and the run state names that artifact. | closed for this state |
| `guessed` | Inferred from documentation, a node name, a reused component's assumed precondition, a similar game, a previous project, or model expectation. | open |

One `guessed` required state opens the gate for the whole task. A reused artifact only closes the gate when it is a real capture of the current target and the run state can point at it; a plausible description is not a capture.

## What exploration-first mode forbids

While the gate is open, do not:

- write or edit Pipeline nodes, templates, or resource images;
- write CustomAction or CustomRecognition code;
- publish a full implementation plan or a node list as if the flow were known;
- call a reused processor, node chain, or CustomAction whose entry state has not been observed;
- take a side effect that the task contract does not already authorize.

Observation, navigation between screens the user authorized, and note-taking in the run state are allowed. This is the phase where questions about the flow get answered by the device, not by the model.

## Round-trip definition

Drive the UI with the MaaMCP tools: `ocr` to read a screen and collect boxes, `screencap` to keep the artifact, `click` and `swipe` to move between states. A scene counts as explored after **at least one complete round-trip**:

1. start from an observed start state;
2. reach the success state by driving the real UI, one observed transition at a time;
3. observe the success state itself, not only the action that should have produced it;
4. return to a stable state the workflow can hand back or repeat from.

Every hop in that chain is one transition, and every transition needs its own observation. A chain that jumps from a banner straight to "battle running" without the preparation screen, the entry confirmation, and the start confirmation is not a round-trip; it is a guess with screenshots at both ends.

Record each hop:

```yaml
- state: stable-state-name
  artifact: screenshot path or capture identifier
  recognized:
    text: text read on the screen
    box: [x, y, w, h]
    source: ocr | template | color | manual-read
  action: what was done to leave this state
  next_state: the state observed after the action
  notes: popups, loading screens, animations, or timing seen on the way
```

The `box` values collected here are the ROI and target evidence the DESIGN phase turns into nodes. Nodes are written from these observations; observations are never back-filled to justify nodes that already exist.

## Reused components have preconditions

Most exploration failures in the wild are not recognition failures, they are precondition failures: an existing processor was called from the wrong screen. Before reusing a node, a node chain, a processor, or a CustomAction:

- find the state it expects on entry, from its own code or Pipeline definition;
- add that state to the contract and observe it like any other state;
- explore the chain of UI steps that actually reaches it.

An auto-battle component that expects a battle already in progress is not an entry point for an event; the banner, the preparation screen, the entry confirmation, and the battle-start confirmation are all states that must be explored first.

## Exit criteria

Close the gate and move to DESIGN only when all of the following hold:

- every required start and success state is `evidence_status: observed` with a named artifact;
- one complete round-trip is recorded, hop by hop;
- every intermediate state, popup, and loading screen met on the way is in the run state, including the ones the contract did not predict;
- the entry precondition of every component the design intends to reuse is observed;
- the device is left in a known, stable state.

States that were explored but not reached stay `guessed`. Either the design drops the branch that depends on them, or the contract records the branch as an explicit unverified limitation. Silently promoting a state to `observed` because the flow "must" work that way defeats the gate.

## When exploration cannot run

If no device is connected, no authorized entry point exists, or the only path to the success state crosses a side effect the contract forbids, stop with `status: warning` or `status: error` and report:

- which states are still `guessed`;
- what capture or authorization would close the gate;
- the smallest safe action the user can take to unblock it.

Do not fall back to writing the plan anyway. An implementation designed against guessed states is the failure this gate exists to prevent.

## Efficient exploration

- `ocr` already captures the screen; do not call `screencap` first just to feed it.
- Read the whole screen while exploring, then narrow the ROI when writing nodes. ROI candidates come from the boxes recorded above.
- Keep single-node verification separate from exploration. Full-screen recognition through `run_pipeline` is slow and can time out; see the testing skill for the limits of the current MaaMCP tooling.
- Re-observe after every navigation. Animation, loading, and popup states are part of the flow and belong in the record.
