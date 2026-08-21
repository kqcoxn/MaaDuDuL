# maafw-cli 0.1.6 command contract

Use the verified external release:

```bash
uvx --from maafw-cli==0.1.6 maafw-cli --version
uvx --from maafw-cli==0.1.6 maafw-cli --json COMMAND
```

The package requires Python 3.10 or later and is currently alpha software. Keep the version pin because command and JSON contracts may change.

## Runtime selection

| Need | Command shape |
| --- | --- |
| Check local models | `--json resource status` |
| Discover controllers | `--json device adb`, `--json device win32`, or `--json device all` |
| Connect ADB | `--on NAME --json connect adb ADDRESS` |
| Connect Win32 | `--on NAME --json connect win32 TITLE_OR_HWND` |
| List sessions | `--json session list` |
| Inspect daemon | `--json daemon status` |

Put global options such as `--json` and `--on NAME` before the subcommand.

## Recognition and actions

```bash
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json ocr
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json reco OCR expected=Settings
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json reco TemplateMatch template=button.png threshold=0.8
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json click e3
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json screenshot
```

Supported recognition types are `TemplateMatch`, `FeatureMatch`, `ColorMatch`, and `OCR`. Use `reco --raw JSON` when the recognition config cannot be represented safely as `key=value` arguments.

## Pipeline operations

```bash
uvx --from maafw-cli==0.1.6 maafw-cli --json pipeline validate ./assets/resource/base/pipeline
uvx --from maafw-cli==0.1.6 maafw-cli --json pipeline load ./assets/resource/base/pipeline
uvx --from maafw-cli==0.1.6 maafw-cli --json pipeline show Start
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json pipeline run ./assets/resource/base/pipeline Start
uvx --from maafw-cli==0.1.6 maafw-cli --on phone --json pipeline run ./pipeline.json Start --override '{"Start":{"timeout":5000}}'
```

`pipeline validate` and `pipeline load` do not execute a task. `pipeline run` uses the selected controller and may perform every action reachable from the entry node.

## Resources and custom code

```bash
uvx --from maafw-cli==0.1.6 maafw-cli --json resource status
uvx --from maafw-cli==0.1.6 maafw-cli --json resource download-ocr
uvx --from maafw-cli==0.1.6 maafw-cli --json resource load-image ./assets/resource/base/image
uvx --from maafw-cli==0.1.6 maafw-cli --json custom list
uvx --from maafw-cli==0.1.6 maafw-cli --json custom load ./agent/main.py
```

Resource download changes the user cache. `custom load` imports and executes Python code; inspect the file and dependencies first.

## Output contract

- Parse stdout as one JSON value when `--json` is present.
- Treat a nonzero process status as command failure even when stderr contains a structured explanation.
- Do not assume all successful commands return the same keys; validate the fields needed by the operation.
- Keep screenshot paths and element references tied to the named session that produced them.
