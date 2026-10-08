---
name: maa-project-init
description: Scan and initialize a MaaFramework game or app automation project for Maa skills and MaaMCP workflows. Use when asked for maa-project-init, project-pipeline-init, basic_info.md, researching a Maa project, loading a Project Interface bundle, scanning declared resources and pipeline nodes, finding common Back/Return/Exit/Confirm nodes, mapping node relationships, generating entry flowcharts, summarizing image assets and OCR conventions, or reducing discovery cost for later Maa skill work.
---

# Maa Project Init

Use this skill to turn a MaaFramework consumer project into a compact onboarding document for future AI sessions. It scans the project's pipeline and image resources, identifies reusable control nodes, and writes `basic_info.md` at the target project root.

The generated file is a producer/consumer handoff: `maa-project-init` produces project context, while `maa-pipeline-guide`, `maa-pipeline-generate`, `maa-pipeline-graph`, `maa-pipeline-option`, and `maa-pipeline-testing` consume the relevant sections before broad repository discovery.

Do not run this skill against MaaMCP itself unless the user explicitly asks to analyze MaaMCP as a consumer project. MaaMCP is the tool runtime; the normal target is a MaaFramework consumer project with a main `interface.json` or `interface.jsonc`.

## Project Discovery Contract

The main Interface is the source of truth. Do not infer a MaaFramework project from an `assets/...` directory convention.

- Accept a root-level `interface.json` / `interface.jsonc` or an `assets/interface.json` / `assets/interface.jsonc` as the main Interface. Both are common valid project layouts. If both locations exist, use the root-level Interface first as a deterministic tie-breaker.
- Resolve every `import[]` path relative to the main Interface directory. Imports may contribute only top-level `task`, `option`, and `preset`; controller, resource, agent, and other project-level declarations remain in the main Interface.
- Resolve every `resource[].path` relative to the main Interface directory. Pipeline and image files are read from those declared resource roots.
- Resolve `languages[]` relative to the main Interface directory when it is present.
- Accept `agent` in either object form or array form; collect `.py` paths from every config's `child_args`.
- If the main Interface or an import is missing or malformed, report the diagnostic and continue with the declarations that can be loaded. Do not silently guess resource or task roots from unrelated directories.

M9A is a standard root-Interface project: the root `interface.json` imports `tasks/**/*.json`, declares resource combinations such as `resource/base` plus channel overlays, and uses array-form `agent` with `agent/bootstrap.py`. Boilerplate-family projects such as MAAPVZ, MaaDuDuL, and MaaNTE commonly place the main Interface at `assets/interface.json` or `assets/interface.jsonc`; their task entries may live in the main Interface or come entirely from imports. Treat both shape families as valid acceptance cases.

## Core Workflow

1. Locate the target project root.
   - Prefer a user-provided path.
   - Otherwise look for the main Interface using the Project Discovery Contract above.
   - Treat the loaded Interface bundle as the source of resource groups, controller types, task entries, options, and agent settings.

2. Run the analyzer in summary mode first:

   ```bash
   python "<skill-dir>/scripts/analyze_pipeline_project.py" "<project-root>"
   ```

3. Inspect the summary for:
   - resource groups and task entries from `interface.json`
   - Interface import diagnostics and warnings
   - pipeline file count and unique node count
   - high in-degree common nodes
   - Back / Return / Exit / Close / Confirm / Wait / Flag nodes
   - entry task flowcharts and primary path previews
   - unresolved references, isolated nodes, and cycle candidates
   - image directory inventory and TemplateMatch usage
   - Python `context.run_task()` / `run_recognition()` external entries
   - orphan candidates after excluding interface and Python entry points
   - agent script paths (declared `child_args` resolution + project_root 与 4 层 ancestor 约定入口候选 + 交叉对比)

Task counts describe the merged Interface bundle's total top-level `task[]` entries after imports. Separator and other display-only task entries remain counted; if a report separately claims a functional-task count, it must state the filter used.

4. Generate `basic_info.md` only after the summary looks reasonable:

   ```bash
   python "<skill-dir>/scripts/analyze_pipeline_project.py" "<project-root>" --write-basic-info
   ```

   If `basic_info.md` already exists, the script refuses to overwrite it. Use `--overwrite` only after the user explicitly confirms.

5. Report where `basic_info.md` was written and name the most important sections that still need human review.

6. When handing off to another Maa skill:
   - tell it to read `basic_info.md` section 0 and the routed sections for its task
   - treat the document as a cache, not as source of truth
   - re-check every touched node in current JSON/Python and every live claim on the current device
   - if relevant source files are newer than `basic_info.md`, rerun summary mode and report staleness; do not overwrite silently

## What The Analyzer Reads

- the main `interface.json` / `interface.jsonc` and its direct `import[]` declaration files
- `pipeline/**/*.json` and `default_pipeline.json` under each resource path declared by the main Interface
- all files under each declared resource root's `image/**`
- static string targets passed to `context.run_task()` and `context.run_recognition()` under `agent/**/*.py`
- `@AgentServer.custom_action(...)` registrations under `agent/**/*.py`
- Interface `agent[]` / `agent.child_args` 里每条 `.py` 的磁盘解析状态（与运行时 `maa_mcp/agent_supervisor._build_subprocess_cmd` 同步上溯 4 层）
- project_root 与 4 层 ancestor 内 `agent/main.py`、`agent/server.py` 等约定入口的候选存在性（`AGENT_DIR_NAMES × AGENT_ENTRY_BASENAMES`，不递归子目录）

For a legacy MaaGumballs-style layout, the script should discover entries such as `Start_Up`, `DailyTask`, `Reward_Execute`, `Shop`, `AutoSky`, `JJC`, `Mars`, `DivineForgeLand_Start`, `TSD_Entry`, `AutoCdk`, and `StopGumballs`, then connect them to the pipeline nodes that define them. For M9A, the same acceptance check is root `interface.json`, all loaded task imports, all declared resource roots, and the declared bootstrap agent. For boilerplate-family projects, the equivalent check is the `assets/` main Interface, all loaded task imports, declared resource roots, and the declared agent path.

## Relationship Rules

Parse these pipeline link fields:

- `next`
- `on_error`
- `interrupt`

Support these node reference forms:

- plain strings: `"ConfirmButton"`
- lists: `["A", "B"]`
- NodeAttr objects: `{ "name": "A", "jump_back": true }`
- prefixed strings: `"[JumpBack]BackText"`, `"[Anchor]SomeNode"`

Strip bracket prefixes when resolving the target node, but preserve the prefix in summaries where useful.

### Node-level `anchor` declarations

A node's own top-level `anchor` field (`string | list | object`) is a distinct concept from the `next`-element `anchor` attribute above: it declares an anchor *name* that `[Anchor]X` references resolve against, not a reference itself.

- `"anchor": "Cooking"` — anchor `Cooking` now targets this node.
- `"anchor": ["A", "B"]` — several anchors now target this node.
- `"anchor": { "Cooking": "TargetNode" }` — object form: explicit target, which need not be this node.
- `"anchor": { "Cooking": "" }` — clears the anchor; the name stays declared with no current target.

Resolve every `[Anchor]X` / `{"anchor": true}` reference through the anchor name → target node table built from these declarations (case-insensitive on the `anchor` attr) before computing unresolved references, in-degree, isolated nodes, and orphan candidates — otherwise every anchor reference is misreported as a dangling node reference. One anchor name may legitimately map to many target nodes (whichever node declared it last wins at runtime); treat that as normal, not a conflict. Report an anchor name that is never declared (`unresolved_anchor_refs`) separately from a declared anchor whose explicit object-form target does not exist (`dangling_anchor_targets`) — they indicate different problems.

## Entry Flowcharts

Generate bounded Mermaid flowcharts from each `interface.json` task entry. These diagrams are meant to orient MaaMCP and future skills quickly, not to replace a full graph database.

- Start from the task `entry` node.
- Expand `next`, `on_error`, and `interrupt` edges with edge labels.
- Preserve branch hints such as `JumpBack`, `jump_back`, and `anchor` in edge labels.
- Limit depth and edge count so loops and shared utility nodes do not overwhelm `basic_info.md`.
- Include a short primary path text summary for agents that cannot render Mermaid.
- When a reachable node uses `action: Custom` (including v2 object form), add a
  separate Python Agent block. Link the Pipeline node to the block as a
  `CustomAction call`, link the block back as `returns`, and show the matched
  `@AgentServer.custom_action(...)` handler and source location when available.

## Public Node Detection

Treat a node as likely reusable when either condition is true:

- it has high in-degree across the merged graph
- its name or behavior indicates a common UI operation

Important common categories:

- Back / Return / Exit / Close / Logout / Stop
- Confirm / Cancel / Retry
- Wait / Loading / Communicating / PowerLack
- Flag / Check / State probe
- `ClickKey` with Android key `4`
- shared TemplateMatch assets such as back buttons, return buttons, confirm buttons, settings buttons

## `basic_info.md` Contents

The generated document must be concise and useful to an AI agent. Include:

1. Project overview
2. Resource groups and task entries
3. Main pipeline inventory
4. Common public nodes
5. Back / Return / Exit / popup handling
6. Node relationship summary
7. OCR expected text conventions
8. TemplateMatch image inventory
9. Resolution and ROI conventions
10. Risks and TODOs
11. Maa skill handoff routing and live verification status

For section 2, the "Agent script paths" subsection includes three parts:

- **Declared**: each `child_args` `.py` with `Status` (`resolved` / `unresolved` / `non-py` / `absolute`) and the absolute path of resolution (if any).
- **Discovered**: every `AGENT_DIR_NAMES × AGENT_ENTRY_BASENAMES` candidate under root + 4 ancestor levels with an `Exists` column.
- **Cross-check**: unresolved declarations and discovered-but-unreferenced candidates. A resolved declaration is authoritative even when its filename is outside the conventional candidate list; do not call `agent/bootstrap.py` an orphan.

Warnings are emitted when an agent config has malformed `child_args`, when the aggregate `child_args` is empty or has no `.py` entries, or when a declared `.py` cannot be resolved. Discovered-but-unused conventional entries are compatibility context, not warnings. The scanner mirrors `maa_mcp/agent_supervisor._build_subprocess_cmd`'s parent-walk semantics (`AGENT_PARENT_WALK_LIMIT = 4`); keep the two limits in sync if you change one.

Keep automatically detected facts separate from TODOs. Do not invent game semantics that are not present in the project files.

## Optional Live MaaMCP Research

If a device or window is available and the user wants deeper game research, use MaaMCP after file scanning:

1. connect to the simulator/window
2. take a default `screencap`
3. infer portrait or landscape from image width/height
4. use OCR for visible text and key buttons
5. add stable UI facts to `basic_info.md`

Live observations must include time, controller/device, screenshot size/orientation, visible page evidence, tested node, score, and whether an action ran. If OCR and screenshot catch different frames during a transition, record them as separate observations and do not promote either one to a stable project fact.

For safe initialization validation, prefer a temporary `DoNothing` recognition probe derived from a known public node. Run it with `start_agent=false` when Custom code is unnecessary, inspect `recognition.all_results`, call `stop_pipeline`, and remove the temporary file.

This is an enhancement, not a blocker. File scanning must work without a live device.

## Do Not

- Do not overwrite an existing non-empty `basic_info.md` without explicit confirmation.
- Do not commit generated `basic_info.md` from another repository into MaaMCP.
- Do not modify unrelated target-project files while scanning.
- Do not treat OCR/image guesses as facts unless they came from files or live MaaMCP verification.
