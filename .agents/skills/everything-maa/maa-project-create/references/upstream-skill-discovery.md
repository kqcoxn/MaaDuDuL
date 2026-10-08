# Upstream Skill discovery

`create-maa-project` is integrated as a moving latest runtime. The Python wheel contains only the launcher; it does not contain `skills/create-maa-project/SKILL.md`. Discovery therefore uses local installed Skills/packages first, then the upstream integrated Skill or README.

## Locator

Run from the `maa-project-create` Skill root:

```bash
node scripts/find-create-maa-project-skill.mjs
```

For user-provided checkouts, package roots, standalone Skill directories, or `SKILL.md` files:

```bash
node scripts/find-create-maa-project-skill.mjs --root PATH
```

The locator validates the frontmatter `name: create-maa-project`, excludes Everything Maa's wrapper copy, and returns JSON with:

| Field | Meaning |
| --- | --- |
| `versionPolicy` / `guidanceAuthority` | Runtime follows `latest`; guidance follows the latest formal release |
| `status` | `found`, `package-without-skill`, or `not-found`; local candidates are diagnostics only |
| `skillPath` | Local `SKILL.md`, when found |
| `packageRoot` / `packageVersion` | npm package metadata, when applicable |
| `skillVersion` | Version declared by the local Skill, when present |
| `latestReleaseUrl` | Latest formal-release handoff entry point |
| `defaultBranchReadmeUrl` / `defaultBranchSkillUrl` | Disclosed default-branch fallback routes |

Search precedence is an explicit candidate, then an installed standalone Skill, then a project npm package, then npm/pnpm globals. Package metadata is not a substitute for the runtime version; query the CLI itself with `--cli-version`.

## Latest handoff

For every locator result, resolve the latest formal release from:

```text
https://github.com/Windsland52/create-maa-project/releases/latest
```

Then read the integrated Skill at `skills/create-maa-project/SKILL.md` for that release. If the release does not expose the Skill, read the upstream README, using `defaultBranchReadmeUrl` from the locator only as the disclosed fallback. Read the complete document and only the references needed for the requested operation.

Do not select a historical tag or substitute a local Skill from this repository. The runtime and authoritative guidance both follow latest.

## Version and updates

Check the latest runtime before operation:

```bash
uvx --upgrade --from create-maa-project create-maa-project --cli-version
```

The launcher may also synchronize its managed Skill. Let that latest-runtime behavior run, and do not cache a command catalog across sessions. If authoritative guidance cannot be read, stop instead of composing commands from memory.
