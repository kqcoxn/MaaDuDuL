# Acceptance Protocol

Treat acceptance as a mapping from every required criterion to observable evidence. The agent's confidence, a generated file, or a successful tool call is not evidence of user-visible behavior by itself.

## Verification ladder

1. **Static:** parse files, validate schema and resources, resolve node references.
2. **Structural:** inspect graph reachability, exits, cycles, option paths, and Custom registration.
3. **Recognition:** run non-mutating probes against known stable screens.
4. **Behavioral:** exercise normal, no-op, disabled, failure, recovery, and retry-limit paths.
5. **End to end:** execute the real flow only when side effects are understood and authorized.
6. **Postcondition:** observe the success state and verify the system can return or continue safely.

## Evidence record

```yaml
criterion: AC-1
status: pass | fail | blocked
evidence:
  type: file | test | graph | screenshot | log | runtime-trace
  artifact: path, command result, or stable identifier
  observation: what the evidence demonstrates
limitations: []
```

## Completion gate

Declare completion only when:

- every required criterion is `pass`;
- every pass has observable evidence;
- no high-risk warning remains unexplained;
- temporary probes and test state are handled;
- the final UI or project state is known and stable;
- limitations are compatible with the task contract.

If runtime verification is unavailable, report the implementation as unverified or partially verified. Do not silently weaken the acceptance criteria.
