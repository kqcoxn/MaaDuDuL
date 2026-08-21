---
name: maa-project-create
description: Create, extend, diagnose, and update MaaFramework application projects through the create-maa-project MCP server or CLI. Use when asked to start or scaffold a Maa project, choose Pipeline versus Python Agent templates, add dev tools, GitHub workflows, Agent support, or resource packs, run project doctor or diff, sync metadata, update schema/runtime/OCR/dependencies, or hand a newly created project to other Maa skills.
---

# Maa Project Create

## 官方兼容性核对

创建或更新项目涉及 MaaFramework schema、runtime、binding 兼容性或依赖版本时，通过 `$maa-wiki` 定位官方来源后再执行 `update` 或解释报告。`create-maa-project` 的报告是执行结果，不是 MaaFramework 官方契约本身。

Use `create-maa-project` as the project lifecycle engine. Do not reproduce its templates or manually imitate its managed-file behavior.

## Route the request

Choose the smallest operation that matches the user's intent:

| Intent | MCP tool | Mutation |
| --- | --- | --- |
| Create a project | `create_project` | Yes |
| Check project health | `doctor` | No |
| Inspect managed-file drift | `diff` | No |
| Change supported metadata | `sync` | Yes |
| Add Agent, resource pack, CI, or dev tooling | `add` | Yes |
| Update schema, MaaFW, runtime, OCR, or dependencies | `update` | Yes |
| Accept intentional managed-file drift | `accept_changes` | Yes, high judgement |
| Restore a backup | `restore` | Yes, potentially destructive |
| Remove local cache | `clean_cache` | Yes |

Prefer MCP when it is configured. Use the pinned CLI fallback in [references/cli-and-reports.md](references/cli-and-reports.md) when MCP is unavailable or when a follow-up command must run with a different working directory.

## Create workflow

1. Resolve the target directory and inspect whether it already exists. Do not use force flags or allow a non-Git non-empty directory without explicit user approval.
2. Collect the choices that materially affect the result:
   - project folder/path;
   - `pipeline` or `agent` template;
   - ASCII kebab-case slug and human display name when they differ;
   - controller targets (`Adb`, `Win32`, `MacOS`, `PlayCover`, `Gamepad`, `WlRoots`);
   - license;
   - Git initialization;
   - add-ons and optional resource-pack slug.
3. Default to `pipeline` only when the user does not need Python custom logic. Choose `agent` when they ask for CustomAction, CustomRecognition, AgentServer, or Python business logic.
4. For a normal maintained repository, recommend `dev-tools` and `github`; do not silently add them when the user asked for a minimal resource-only project.
5. Require `resourcePackSlug` whenever `resource-pack` is selected. Keep it ASCII kebab-case; use the label for localized display text.
6. Call `create_project` once with the resolved choices. Avoid a sequence of partially overlapping create calls.
7. Inspect the returned report before declaring success. Report written files, skipped files, pending actions, and suggested commands.
8. Run `doctor` from the new project root. The MCP server keeps the working directory it was launched with, so use the CLI fallback with its working directory set to the new project when necessary.
9. Run `$maa-project-init` against the completed project to create `basic_info.md`, then route further work to the relevant Maa skill.

## Maintain an existing project

1. Confirm the target is a create-maa-project project by locating `maa-project.json` and `maa-project.lock.json`.
2. Run `doctor` first. Run `diff` before changing drifted managed files.
3. Prefer `sync`, `add`, or a specific `update` target over manual edits to tool-managed files.
4. Never invent an `update all` operation. Use explicit update targets so pending actions and failures stay attributable.
5. Treat `accept_changes` as adopting the current file content as the new baseline, not restoring the upstream template. Use it only after reviewing the diff and confirming user intent.
6. List backups before `restore`, identify the selected backup, and obtain explicit confirmation when restoration can replace current work.

## Interpret reports

Treat the structured report as the source of truth:

- `ok: true` means the requested operation completed, but `pending` may still require follow-up.
- A doctor report with `ok: false` is a health finding, not proof that project creation failed.
- Show `pending[].command` and its reason. Execute it only when it is safe, in scope, and authorized.
- Distinguish `changedManagedFiles` from `changedUserFiles`; do not accept or overwrite user-file changes as a template repair.
- Preserve the log path when reporting a failure.

## Safety boundaries

- Do not copy create-maa-project source or templates into Everything Maa. It remains an external AGPL runtime.
- Do not pass `--force`, `--allow-non-git-dir`, `--accept-changes`, or restore operations by default.
- Do not hide downloads behind a dry-looking command. State when OCR models, runtimes, or dependencies may be fetched.
- Do not claim the project is ready while doctor findings or pending actions remain unexplained.
- Do not commit, push, publish, or create remote repositories unless the user requested those actions.
