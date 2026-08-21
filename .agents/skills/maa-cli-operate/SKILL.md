---
name: maa-cli-operate
description: Operate MaaFramework devices and Pipeline resources through the maafw-cli command line with strict JSON output. Use for low-context, repeatable or scripted device discovery, ADB/Win32/PlayCover/wlroots connections, OCR and recognition, screenshots and guarded actions, named sessions, Pipeline validation or execution, resource checks, and CI-friendly Maa automation; route persistent exploratory debugging to MaaMCP instead.
---

# Maa CLI Operate

Use the pinned external `maafw-cli` runtime. Read [references/command-contract.md](references/command-contract.md) before composing commands or interpreting output.

## Choose the runtime

Use `maafw-cli` for one-shot, repeatable operations with compact JSON output: device discovery, resource checks, Pipeline validation, scripted recognition/action sequences, and CI jobs.

Use MaaMCP instead when the task benefits from a long-lived exploratory session, repeated visual inspection, interactive Pipeline debugging, or an MCP-native tool schema. Do not run both against the same device session unless the user deliberately wants separate controllers.

## Prepare safely

1. Run the pinned version check and require the tested version.
2. Use `--json` for every non-help operation that supports it. Parse stdout as JSON; keep stderr for diagnostics.
3. Check `resource status` before OCR. Treat `download-ocr` as an explicit network and disk mutation.
4. Discover devices before connecting. Resolve an exact ADB address, Win32 title/handle, PlayCover application, or wlroots target instead of guessing.
5. Use a named `--on` session whenever more than one command or device is involved. Record whether the daemon or session existed before the task.

## Validate and run Pipeline

1. Run `pipeline validate PATH` before loading or executing a Pipeline.
2. Inspect the returned nodes and resolve the intended entry explicitly when more than one entry is plausible.
3. Use `pipeline load` and `pipeline show NODE` for inspection without task execution.
4. Use `pipeline run PATH ENTRY` only after the controller, resource paths, entry node, and expected device effects are known.
5. Pass runtime overrides as one valid JSON object through `--override`. Do not rewrite source Pipeline files for a temporary runtime change.
6. Route Pipeline authoring problems to `$maa-pipeline-guide`, graph questions to `$maa-pipeline-graph`, and behavior validation to `$maa-pipeline-testing`.

## Observe, act, verify

1. Prefer `ocr`, `reco`, or `screenshot` before an action.
2. Prefer the returned element reference over raw coordinates when the reference is current and unambiguous.
3. Treat element references as session-scoped and short-lived. Re-observe after navigation, scrolling, window changes, or unexpected output.
4. For clicks, typing, keys, swipes, long presses, and shell actions, state the expected effect and perform the smallest action needed.
5. Re-run an observation after the action and verify the expected state. Stop on ambiguity instead of issuing compensating clicks.

## Handle advanced features

- Inspect Python files before `custom load`; loading them executes local code in the runtime.
- Treat `action shell` as arbitrary command execution on the selected controller. Use it only when explicitly required and scoped.
- Do not use `session close-all`, `daemon stop`, or `daemon restart` as routine cleanup. Close only sessions created for the current task; leave a pre-existing daemon running.
- Never download resources, connect to a device, or execute a Pipeline merely to answer a read-only architecture question.

## Report results

Report the pinned CLI version, selected session/controller, command category, JSON result, screenshot path when present, and verification outcome. Separate tool failures from recognition misses and Pipeline task failures. Preserve stderr and any output paths needed for diagnosis.
