---
name: maa-diagnose
description: Diagnose unexplained MaaFramework failures by driving the externally managed latest MaaEvidenceKit diagnostic runtime (formerly MaaDiagnosticExpert) read-only over local logs, project sources, and run-state context. Use when a run, task, or test already failed and the owner of the defect is still unknown, including maafw.log, timestamped maafw.bak logs, or other maafw.*.log files - resource or schema load failures, environment or dependency problems, device errors, runtime timeouts, wrong branches, Custom exceptions, or large MaaFramework logs that need timeline and node correlation. Produces normalized findings, evidence, artifacts, and one bounded failure owner, and never applies a repair. Route project scaffold health checks to $maa-project-create doctor and focused recognition retuning to $maa-pipeline-generate.
---

# Maa Diagnose

Drive the externally managed latest diagnostic runtime to turn an unexplained MaaFramework failure into normalized evidence and one bounded failure owner. This skill owns discovery, invocation, and normalization. It does not parse MaaFramework logs itself and does not contain a diagnostic engine.

Read [references/runtime-discovery.md](references/runtime-discovery.md) before the first invocation. Read [references/failure-map.md](references/failure-map.md) before reporting an owner.

## Decide whether to diagnose

Run this skill only when the failing owner is still unknown after the evidence already in hand.

- Do not run it when `$maa-pipeline-testing` already attributed the failure to a node, option, state model, or integration defect. Route that evidence to the owner directly.
- Do not run it as a routine phase of every workflow, and do not run it before a failure exists.
- Do not run it for project scaffold or managed-file health; that is `$maa-project-create` doctor.
- Do not run it for Project Interface schema review; that is `$maa-interface-guide`.

Broad diagnosis is for cross-tool correlation: a runtime failure whose cause could live in the logs, the static project definition, the environment, or the harness.
Treat `maafw.log`, `maafw.bak.<timestamp>.log`, and another `maafw.*.log` path as diagnostic input only when the failure owner is still unknown.

## Load the authoritative upstream Skill

Before composing a MaaEvidenceKit command, locate and read the authoritative upstream `maa-evidence` Skill. This handoff is part of a legitimate diagnosis; it does not broaden this Skill into an entry point for evidence extraction when no failure needs diagnosis.

1. If the user supplies a MaaEvidenceKit checkout, package root, skill directory, or `SKILL.md`, pass each candidate to the locator with `--root PATH`.
2. Run `node scripts/find-maa-evidence-skill.mjs`. The read-only locator searches installed standalone skills, project and user installations, and npm/pnpm global packages while excluding this Skill's own root.
3. For every locator result, read the latest formal GitHub Release of `Windsland52/MaaEvidenceKit`, preferring its integrated `maa-evidence` Skill and falling back to its README. The locator result reports local candidates; it never makes a local `skillPath` authoritative for the latest runtime.
4. If the latest formal release does not expose the integrated Skill or README, use the disclosed default-branch handoff.

Preserve the latest upstream Skill or README's installation, privacy, telemetry, evidence, and version requirements. If no complete authoritative document can be read, stop and report every latest-release and default-branch route attempted. Do not improvise MaaEvidenceKit commands from this Skill alone.

## Discover the runtime before invoking it

1. Resolve the runtime surface with the discovery sequence in `references/runtime-discovery.md`. Never assume a command catalog from memory; the upstream project has already been renamed and has already changed its command names.
2. Record the resolved surface, package version, and output schema id as evidence.
3. Apply one precedence policy: supported local MCP surface first when it is already configured and provably matches npm latest, then the on-demand latest CLI, then a user-supplied local checkout entry point only when its reported version exactly matches npm latest. If that proof is unavailable, stop rather than using an old runtime. Do not mix surfaces inside one diagnosis.
4. If no surface resolves, or the discovered schema id is outside the supported set, stop with `status: error`, `failure_owner: user`, and a `stop_reason`. Never persistently install, build, or upgrade the runtime to make a diagnosis possible.

## Collect bounded local inputs

Pass only what the failure needs, as already-extracted local paths:

- the Maa project root, when static definitions are in question;
- one log file or an extracted log folder, never an archive the runtime must unpack;
- the specific source paths under investigation;
- the entry task, controller, and resource names already known from the run state;
- a time range when the failing run is known, so unrelated sessions stay out of the evidence;
- an optional runtime profile only when discovery proved the installed runtime defines one.

Validate every argument against the discovered contract before invoking. Drop an input the runtime does not accept instead of guessing a flag.

## Prefer the cross-tool pipeline

Use the runtime's cross-tool entry point when both runtime logs and project sources are available, so its correlated relations are produced in one pass. Fall back to a single-adapter command only when just one material kind exists.

Reuse the runtime's own adapters - filesystem discovery, the MaaLogAnalyzer log adapter, the maa-support-extension static adapter, and the local corpus inventory. Do not re-implement discovery, parsing, or retrieval here.

## Read the structured contract

- Request the structured output format and parse the JSON envelope. Never treat the human-readable text or diagram renderer as the primary contract.
- Honour the envelope's own gap fields. Missing evidence, warnings, and truncation flags are results, not noise, and must reach the report.
- Do not claim absence from a truncated or time-filtered view. Say the view was bounded.
- Follow up with the runtime's evidence-lookup commands against the saved result instead of re-running the analysis.

## Stay read-only

Never mutate the project, write into the project tree, install dependencies, connect a device, or rerun a side-effecting task to diagnose it. Disable the runtime's own self-updating behavior and keep its optional upload paths off, as described in `references/runtime-discovery.md`. Write result files only to a scratch path the user accepted, and report that path.

## Report one owner

Map findings to exactly one `failure_owner` using `references/failure-map.md`, and emit:

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

Keep `next_actions` to safe, bounded steps for that owner. Recommend a repair; do not apply one. Return the result to `$maa-workflow-build` `RECOVER`, which decides whether to retry, replan, delegate, request user action, or stop.
