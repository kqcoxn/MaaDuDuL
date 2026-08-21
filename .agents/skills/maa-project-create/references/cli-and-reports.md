# CLI fallback and report contract

Use the pinned external runtime. Do not use a moving release tag in automated workflows.

## Base command

```bash
uvx --from create-maa-project==2.0.0 create-maa-project
```

The 2.0.0 CLI does not expose a conventional `--help` option. Use the documented commands below and require `--report` for non-interactive agent use.

## Create examples

```bash
# Pipeline project
uvx --from create-maa-project==2.0.0 create-maa-project ./maa-example \
  --template pipeline --controller Adb --license MIT \
  --add dev-tools --add github --no-interactive --yes --report

# Python Agent project without network downloads during scaffolding
uvx --from create-maa-project==2.0.0 create-maa-project ./maa-agent \
  --template agent --controller Adb,Win32 --license MIT \
  --skip-download --no-interactive --yes --report
```

Set the process working directory to the target project for maintenance commands:

```bash
uvx --from create-maa-project==2.0.0 create-maa-project --doctor --report
uvx --from create-maa-project==2.0.0 create-maa-project --diff --report
uvx --from create-maa-project==2.0.0 create-maa-project --add agent --report
uvx --from create-maa-project==2.0.0 create-maa-project --update schema --diff --report
uvx --from create-maa-project==2.0.0 create-maa-project --update schema --report
```

## Report fields

The CLI writes a single JSON document to stdout in report mode. Read these fields:

| Field | Meaning |
| --- | --- |
| `ok` / `exitCode` | Operation result; doctor findings may intentionally produce a failing status |
| `command` | `create`, `doctor`, `diff`, `sync`, or `update` |
| `root` | Project root used by the operation |
| `written` / `skipped` | Files changed or intentionally left alone |
| `pending` | Follow-up commands with reasons |
| `changedManagedFiles` | Drift in files owned by the scaffold tool |
| `changedUserFiles` | Changes in project-owned files |
| `suggestedCommands` | Explicit next actions and whether the tool considers them auto-runnable |
| `logPath` | Diagnostic log to retain on failure |
| `error` | Structured failure message and optional code |

Do not parse human-readable stderr as the primary result when a JSON report exists.
