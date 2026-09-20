# Diagnostic runtime discovery and compatibility

The diagnostic runtime is an external latest-tracking project that is not vendored or persistently installed by Everything Maa. The user remains responsible for the Node.js/npm environment. Everything Maa may invoke the package on demand with `npx`, which can refresh the user-level npm cache, but it never adds a global install or project dependency.

## Runtime identity

| Field | Value |
| --- | --- |
| Upstream | [Windsland52/MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit), formerly `MaaDiagnosticExpert` |
| npm package | `maa-evidence-kit@latest` |
| Executable | `maa-evidence` |
| Version policy | Resolve `latest`; never replace it with a historical Everything Maa pin |
| Structured schemas | Discover from the current runtime result and upstream guidance |
| MCP surface | Discover from the current runtime's help and configured harness |

The rename is the reason discovery is mandatory. Command names from older planning notes are not authoritative.

## Authoritative Skill handoff

Before using any command surface below, run the locator in `scripts/find-maa-evidence-skill.mjs` and follow its result:

- any locator result: read the latest formal upstream Release, preferring the integrated Skill and falling back to its README; use the default branch only with a disclosed fallback.

The locator reports `guidanceAuthority: "latest-release"`. Local skill and package candidates are diagnostic locator results only; they do not override the latest upstream handoff. This document only routes discovery; it is not a substitute for the upstream guidance. If authoritative guidance cannot be loaded, do not compose commands from this reference alone.

## Discovery sequence

Run these before composing any analysis command, and treat their output as the authoritative catalog:

```bash
MAA_EVIDENCE_AUTO_UPDATE=0 npx --yes --package maa-evidence-kit@latest maa-evidence --version
MAA_EVIDENCE_AUTO_UPDATE=0 npx --yes --package maa-evidence-kit@latest maa-evidence --help
```

Record, as evidence:

- the reported package version;
- the subcommand list actually printed by help;
- the flags the intended subcommand accepts;
- the `schema` id of the first structured result.

If a responsibility or flag named by the upstream guidance is absent from the discovered help output, it does not exist in the installed build. Use what help reports, not a remembered command table.

## Precedence and fallback policy

Apply exactly one policy, in this order, and record which surface was used:

1. **Local MCP surface.** Resolve npm latest with the version command above, then use the local server only when the harness already has it configured and its package metadata reports exactly that version.
2. **On-demand latest CLI.** Invoke the `npx --package maa-evidence-kit@latest` command documented above.
3. **User-supplied local checkout.** Use the entry point the user named only when the user explicitly authorized that checkout and its reported version exactly matches the version resolved from npm latest. If npm latest cannot be resolved or the checkout cannot prove that match, stop.

Do not mix surfaces inside one diagnosis, and do not fall back to a surface the user did not authorize. Do not invoke a bare `maa-evidence` from `PATH`; a previously installed executable is not proof that it matches npm latest. If on-demand latest resolution fails, stop rather than silently using a stale executable. Never globally install, build, or upgrade the runtime to reach a later step.

## Failing safely

| Condition | Result |
| --- | --- |
| No surface resolves | `status: error`, `failure_owner: user`, `stop_reason: diagnostic-runtime-unavailable` |
| Guidance or help cannot be read | `status: error`, `failure_owner: user`, `stop_reason: diagnostic-runtime-unavailable` |
| Discovered schema id is unknown | `status: error`, `failure_owner: user`, `stop_reason: diagnostic-contract-unsupported`; do not guess field meanings |
| Runtime reports an unsupported host | `status: error`, `failure_owner: user`, `stop_reason: diagnostic-runtime-host-unsupported` |
| Command exits non-zero | Treat it as a tool failure, keep stderr as evidence, and do not present it as a project defect |

In every failing case, report what would unblock the diagnosis as a `next_actions` entry for the user, and keep the original failure that triggered the request unresolved rather than guessing an owner.

## When the contract changes

The upstream contract is expected to move. Handle a change without editing this skill first:

- Re-run discovery every session; never cache a command catalog across sessions.
- Prefer the envelope's own `schema` id over the package version when deciding whether output is readable.
- If a field this skill relies on is missing, degrade to what is present, mark the gap in `findings`, and lower `status` to `warning`.
- If the structured envelope cannot be parsed at all, stop with `stop_reason: diagnostic-contract-unsupported` rather than falling back to the human-readable renderer.
- Raise a repository change only after the latest upstream guidance and discovered help agree on a stable routing change.

## Side effects to suppress

The runtime has opt-out behavior that would otherwise mutate the environment or leave the machine:

- Set `MAA_EVIDENCE_AUTO_UPDATE=0` for every invocation. Outer `npx @latest` resolution owns version freshness; the runtime's self-update mechanism must not perform an additional persistent install.
- Check `telemetry status` before a first run and report it. Do not enable telemetry, and do not disable a setting the user chose.
- Never run `feedback`; it uploads material and requires interactive confirmation.
- Write structured results to a scratch path outside the target project, and report the path in `artifacts`.
