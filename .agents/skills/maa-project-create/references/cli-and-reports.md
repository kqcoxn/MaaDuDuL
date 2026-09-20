# CLI fallback and report contract

Use the latest external runtime and read its current integrated Skill or README first as described in [upstream-skill-discovery.md](upstream-skill-discovery.md). Do not compose a project-changing command until that handoff and the current `--help` output have been read.

## Base command

```bash
uvx --upgrade --from create-maa-project create-maa-project
```

Verify the resolved CLI before use:

```bash
uvx --upgrade --from create-maa-project create-maa-project --cli-version
uvx --upgrade --from create-maa-project create-maa-project --help
```

The upstream Skill or README and `--help` define the command contract. Require the current report mode for non-interactive agent use unless the operation is only version or help discovery.

## Create and maintenance routing

Use the smallest operation named by the current upstream contract. Set the process working directory to the target project for maintenance commands. Do not chain partial create operations, invent an update-all operation, or substitute remembered 3.x examples for the current help surface.

Before restore, list backups, inspect the selected backup, run a dry-run preview when available, and obtain explicit confirmation when restoration can replace current work.

## Report fields

When the current contract provides a JSON report, read the structured document rather than human-readable stderr. Preserve command results, pending actions, doctor checks, backup identifiers, Git decisions, log paths, and structured errors verbatim enough for the user to audit the operation.

Do not parse human-readable stderr as the primary result when a JSON report exists.
